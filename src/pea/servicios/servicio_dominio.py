"""Servicio central de dominio (Catálogo de Investigación) para PEA-i.

Gestiona las entidades exclusivamente en estructuras de datos hechas a mano,
aplica transaccionalidad local con compensación en caso de fallo remoto,
registra historial en la Pila de Deshacer y controla la concurrencia optimista.
"""

from typing import Any

from pea.cliente_http import ClienteHTTPSupabase
from pea.datos.repositorios import (
    RepositorioGrupos,
    RepositorioIntegrantes,
    RepositorioInvestigadores,
    RepositorioProductos,
    RepositorioProyectos,
)
from pea.datos.revision import ControladorRevision
from pea.datos.sesion import Sesion
from pea.dominio.grupo import Grupo
from pea.dominio.integrante import IntegranteGrupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.dominio.proyecto import Proyecto
from pea.estructuras.cola import Cola, TareaIngesta
from pea.estructuras.lista_doble import ListaDoble
from pea.estructuras.multilista import Multilista
from pea.estructuras.pila import ComandoInverso, Pila
from pea.excepciones import ErrorAutenticacion, RecursoNoEncontrado


class CatalogoInvestigacion:
    """Núcleo del dominio que custodia las colecciones maestras en estructuras propias."""

    def __init__(
        self,
        cliente: ClienteHTTPSupabase | None = None,
        sesion: Sesion | None = None,
    ) -> None:
        self.cliente = cliente
        self.sesion = sesion or Sesion()
        self.controlador_revision = ControladorRevision()

        # Colecciones principales en estructuras hechas a mano (NO list/dict)
        self.grupos: ListaDoble[Grupo] = ListaDoble()
        self.investigadores: ListaDoble[Investigador] = ListaDoble()
        self.integrantes: ListaDoble[IntegranteGrupo] = ListaDoble()
        self.multilista_productos: Multilista = Multilista()
        self.proyectos: ListaDoble[Proyecto] = ListaDoble()

        # Historial de operaciones e ingesta
        self.pila_deshacer: Pila[ComandoInverso] = Pila()
        self.cola_importacion: Cola[TareaIngesta] = Cola()

        # Repositorios
        if self.cliente is not None:
            self.repo_grupos = RepositorioGrupos(self.cliente)
            self.repo_investigadores = RepositorioInvestigadores(self.cliente)
            self.repo_integrantes = RepositorioIntegrantes(self.cliente)
            self.repo_productos = RepositorioProductos(self.cliente)
            self.repo_proyectos = RepositorioProyectos(self.cliente)
        else:
            self.repo_grupos = None
            self.repo_investigadores = None
            self.repo_integrantes = None
            self.repo_productos = None
            self.repo_proyectos = None

    def _verificar_autenticacion_si_aplica(self) -> None:
        """Verifica que la sesión no haya expirado si hay cliente conectado."""
        if self.cliente is not None and self.sesion.esta_expirada():
            self.sesion.cerrar_sesion()
            raise ErrorAutenticacion("La sesión ha expirado.")

    # =========================================================================
    # GESTIÓN DE GRUPOS
    # =========================================================================

    def crear_grupo(self, grupo: Grupo, persistir: bool = True) -> Grupo:
        """Registra un nuevo grupo en la ListaDoble y lo persiste opcionalmente."""
        self._verificar_autenticacion_si_aplica()

        # Verificar unicidad en memoria
        existente = self.grupos.buscar(lambda g: g.codigo_gruplac == grupo.codigo_gruplac)
        if existente is not None:
            raise ValueError(f"Ya existe un grupo registrado con código {grupo.codigo_gruplac}")

        # 1. Aplicar cambio en memoria
        nodo = self.grupos.insertar_final(grupo)

        # 2. Persistir en Supabase
        if persistir and self.cliente is not None and self.repo_grupos is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                grupo_creado = self.repo_grupos.crear(grupo)
                if grupo_creado.id is not None:
                    grupo.id = grupo_creado.id
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                # Compensación: revertir la estructura en memoria ante fallo
                self.grupos.eliminar_nodo(nodo)
                raise

        # 3. Registrar en la Pila de Deshacer
        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="crear",
                tipo_entidad="grupo",
                identificador=grupo.codigo_gruplac,
                descripcion=f"Crear grupo {grupo.nombre}",
            )
        )
        return grupo

    def buscar_grupo(self, codigo_gruplac: str) -> Grupo | None:
        return self.grupos.buscar_dato(lambda g: g.codigo_gruplac == codigo_gruplac)

    def actualizar_grupo(self, codigo_gruplac: str, datos: dict[str, Any], persistir: bool = True) -> Grupo:
        """Actualiza atributos de un grupo con compensación y registro de reversión."""
        self._verificar_autenticacion_si_aplica()
        grupo = self.buscar_grupo(codigo_gruplac)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo con código {codigo_gruplac} no encontrado")

        valores_anteriores: dict[str, Any] = {}
        for campo, valor in datos.items():
            if hasattr(grupo, campo):
                valores_anteriores[campo] = getattr(grupo, campo)
                setattr(grupo, campo, valor)

        if persistir and self.cliente is not None and self.repo_grupos is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_grupos.actualizar(codigo_gruplac, datos)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                # Compensación en memoria
                for campo, val_ant in valores_anteriores.items():
                    setattr(grupo, campo, val_ant)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="editar",
                tipo_entidad="grupo",
                identificador=codigo_gruplac,
                datos_reversion=valores_anteriores,
                descripcion=f"Editar grupo {codigo_gruplac}",
            )
        )
        return grupo

    def desactivar_grupo(self, codigo_gruplac: str, persistir: bool = True) -> None:
        """Desactiva lógicamente un grupo (activo=false)."""
        self._verificar_autenticacion_si_aplica()
        grupo = self.buscar_grupo(codigo_gruplac)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo {codigo_gruplac} no encontrado")

        grupo.desactivar()

        if persistir and self.cliente is not None and self.repo_grupos is not None and grupo.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_grupos.desactivar(grupo.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                grupo.activar()
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="desactivar",
                tipo_entidad="grupo",
                identificador=codigo_gruplac,
                descripcion=f"Desactivar grupo {codigo_gruplac}",
            )
        )

    def activar_grupo(self, codigo_gruplac: str, persistir: bool = True) -> None:
        """Reactiva lógicamente un grupo (activo=true)."""
        self._verificar_autenticacion_si_aplica()
        grupo = self.buscar_grupo(codigo_gruplac)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo {codigo_gruplac} no encontrado")

        grupo.activar()

        if persistir and self.cliente is not None and self.repo_grupos is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_grupos.actualizar(codigo_gruplac, {"activo": True})
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                grupo.desactivar()
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="activar",
                tipo_entidad="grupo",
                identificador=codigo_gruplac,
                descripcion=f"Activar grupo {codigo_gruplac}",
            )
        )

    def eliminar_grupo(self, codigo_gruplac: str, persistir: bool = True) -> Grupo:
        """Elimina físicamente un grupo aplicando reglas de cascada sobre multilista e integrantes."""
        self._verificar_autenticacion_si_aplica()
        grupo = self.buscar_grupo(codigo_gruplac)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo {codigo_gruplac} no encontrado")

        # 1. Desenlazar productos del grupo en la multilista
        self.multilista_productos.desvincular_grupo_de_todos(codigo_gruplac)

        # 2. Desvincular integrantes asociados en memoria
        self.integrantes.eliminar_por_criterio(lambda m: m.codigo_gruplac == codigo_gruplac)

        # 3. Remover de la lista de grupos
        self.grupos.eliminar_por_criterio(lambda g: g.codigo_gruplac == codigo_gruplac)

        # 4. Persistir eliminación remota
        if persistir and self.cliente is not None and self.repo_grupos is not None and grupo.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_grupos.eliminar(grupo.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                # Compensación ante fallo
                self.grupos.insertar_final(grupo)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="eliminar",
                tipo_entidad="grupo",
                identificador=codigo_gruplac,
                datos_reversion=grupo.model_dump(),
                descripcion=f"Eliminar grupo {codigo_gruplac}",
            )
        )
        return grupo

    # =========================================================================
    # GESTIÓN DE INVESTIGADORES
    # =========================================================================

    def crear_investigador(self, investigador: Investigador, persistir: bool = True) -> Investigador:
        """Registra un nuevo investigador en la ListaDoble y Supabase."""
        self._verificar_autenticacion_si_aplica()

        existente = self.investigadores.buscar(lambda inv: inv.codigo_rh == investigador.codigo_rh)
        if existente is not None:
            raise ValueError(f"Ya existe un investigador con código {investigador.codigo_rh}")

        nodo = self.investigadores.insertar_final(investigador)

        if persistir and self.cliente is not None and self.repo_investigadores is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                inv_creado = self.repo_investigadores.crear(investigador)
                if inv_creado.id is not None:
                    investigador.id = inv_creado.id
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.investigadores.eliminar_nodo(nodo)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="crear",
                tipo_entidad="investigador",
                identificador=investigador.codigo_rh,
                descripcion=f"Crear investigador {investigador.nombre_completo}",
            )
        )
        return investigador

    def buscar_investigador(self, codigo_rh: str) -> Investigador | None:
        return self.investigadores.buscar_dato(lambda inv: inv.codigo_rh == codigo_rh)

    def actualizar_investigador(
        self,
        codigo_rh: str,
        datos: dict[str, Any],
        persistir: bool = True,
    ) -> Investigador:
        self._verificar_autenticacion_si_aplica()
        inv = self.buscar_investigador(codigo_rh)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador con código {codigo_rh} no encontrado")

        valores_anteriores: dict[str, Any] = {}
        for campo, valor in datos.items():
            if hasattr(inv, campo):
                valores_anteriores[campo] = getattr(inv, campo)
                setattr(inv, campo, valor)

        if persistir and self.cliente is not None and self.repo_investigadores is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_investigadores.actualizar(codigo_rh, datos)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                for campo, val_ant in valores_anteriores.items():
                    setattr(inv, campo, val_ant)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="editar",
                tipo_entidad="investigador",
                identificador=codigo_rh,
                datos_reversion=valores_anteriores,
                descripcion=f"Editar investigador {codigo_rh}",
            )
        )
        return inv

    def desactivar_investigador(self, codigo_rh: str, persistir: bool = True) -> None:
        self._verificar_autenticacion_si_aplica()
        inv = self.buscar_investigador(codigo_rh)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador {codigo_rh} no encontrado")

        inv.desactivar()

        if persistir and self.cliente is not None and self.repo_investigadores is not None and inv.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_investigadores.desactivar(inv.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                inv.activar()
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="desactivar",
                tipo_entidad="investigador",
                identificador=codigo_rh,
                descripcion=f"Desactivar investigador {codigo_rh}",
            )
        )

    def activar_investigador(self, codigo_rh: str, persistir: bool = True) -> None:
        self._verificar_autenticacion_si_aplica()
        inv = self.buscar_investigador(codigo_rh)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador {codigo_rh} no encontrado")

        inv.activar()

        if persistir and self.cliente is not None and self.repo_investigadores is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_investigadores.actualizar(codigo_rh, {"activo": True})
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                inv.desactivar()
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="activar",
                tipo_entidad="investigador",
                identificador=codigo_rh,
                descripcion=f"Activar investigador {codigo_rh}",
            )
        )

    def eliminar_investigador(self, codigo_rh: str, persistir: bool = True) -> Investigador:
        """Elimina un investigador en cascada (removiendo coautorías y membresías)."""
        self._verificar_autenticacion_si_aplica()
        inv = self.buscar_investigador(codigo_rh)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador {codigo_rh} no encontrado")

        # 1. Remover de listas de coautorías en la multilista
        self.multilista_productos.desvincular_investigador_de_todos(codigo_rh)

        # 2. Desvincular de integrantes en memoria
        self.integrantes.eliminar_por_criterio(lambda m: m.codigo_rh == codigo_rh)

        # 3. Remover de la lista de investigadores
        self.investigadores.eliminar_por_criterio(lambda i: i.codigo_rh == codigo_rh)

        if persistir and self.cliente is not None and self.repo_investigadores is not None and inv.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_investigadores.eliminar(inv.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.investigadores.insertar_final(inv)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="eliminar",
                tipo_entidad="investigador",
                identificador=codigo_rh,
                datos_reversion=inv.model_dump(),
                descripcion=f"Eliminar investigador {codigo_rh}",
            )
        )
        return inv

    # =========================================================================
    # GESTIÓN DE INTEGRANTES (MEMBRESÍAS)
    # =========================================================================

    def vincular_integrante(
        self,
        codigo_gruplac: str,
        codigo_rh: str,
        rol: str = "Investigador",
        persistir: bool = True,
    ) -> IntegranteGrupo:
        self._verificar_autenticacion_si_aplica()
        grupo = self.buscar_grupo(codigo_gruplac)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo {codigo_gruplac} no encontrado para vinculación")
        inv = self.buscar_investigador(codigo_rh)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador {codigo_rh} no encontrado para vinculación")

        integrante = IntegranteGrupo(
            grupo_id=grupo.id,
            codigo_gruplac=codigo_gruplac,
            investigador_id=inv.id,
            codigo_rh=codigo_rh,
            rol=rol,
        )
        nodo = self.integrantes.insertar_final(integrante)

        if persistir and self.cliente is not None and self.repo_integrantes is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                creado = self.repo_integrantes.vincular(integrante)
                if creado.id is not None:
                    integrante.id = creado.id
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.integrantes.eliminar_nodo(nodo)
                raise

        return integrante

    def desvincular_integrante(self, codigo_gruplac: str, codigo_rh: str, persistir: bool = True) -> None:
        self._verificar_autenticacion_si_aplica()
        integrante = self.integrantes.eliminar_por_criterio(
            lambda m: m.codigo_gruplac == codigo_gruplac and m.codigo_rh == codigo_rh
        )
        if integrante is None:
            raise RecursoNoEncontrado(f"Membresía {codigo_gruplac} - {codigo_rh} no encontrada")

        if persistir and self.cliente is not None and self.repo_integrantes is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_integrantes.desvincular(codigo_gruplac, codigo_rh)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.integrantes.insertar_final(integrante)
                raise

    # =========================================================================
    # GESTIÓN DE PRODUCTOS Y MULTILISTA
    # =========================================================================

    def crear_producto(
        self,
        producto: Producto,
        codigo_gruplac: str | None = None,
        codigos_rh_autores: list[str] | None = None,
        persistir: bool = True,
    ) -> Producto:
        """Crea un producto garantizando instancia única en memoria y enlace en Multilista."""
        self._verificar_autenticacion_si_aplica()

        existente = self.multilista_productos.buscar_producto(producto.codigo_identificador)
        if existente is not None:
            raise ValueError(f"Ya existe un producto con código {producto.codigo_identificador}")

        grupo = self.buscar_grupo(codigo_gruplac) if codigo_gruplac else None
        autores: list[Investigador] = []
        if codigos_rh_autores:
            for crh in codigos_rh_autores:
                inv = self.buscar_investigador(crh)
                if inv is not None:
                    autores.append(inv)

        # 1. Insertar en Multilista
        self.multilista_productos.agregar_producto(producto, grupo=grupo, autores=autores)

        # 2. Persistir en Supabase
        if persistir and self.cliente is not None and self.repo_productos is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                grupo_id = grupo.id if grupo else None
                inv_ids = [inv.id for inv in autores if inv.id is not None]

                prod_id = self.repo_productos.crear_con_rpc(
                    producto,
                    grupo_id=grupo_id,
                    investigadores_ids=inv_ids,
                    revision_esperada=self.controlador_revision.revision_local,
                )
                if prod_id > 0:
                    producto.id = prod_id
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                # Compensación
                self.multilista_productos.eliminar_producto(producto.codigo_identificador)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="crear",
                tipo_entidad="producto",
                identificador=producto.codigo_identificador,
                descripcion=f"Crear producto {producto.titulo}",
            )
        )
        return producto

    def buscar_producto(self, codigo_identificador: str) -> Producto | None:
        return self.multilista_productos.buscar_producto(codigo_identificador)

    def desactivar_producto(self, codigo_identificador: str, persistir: bool = True) -> None:
        self._verificar_autenticacion_si_aplica()
        prod = self.buscar_producto(codigo_identificador)
        if prod is None:
            raise RecursoNoEncontrado(f"Producto {codigo_identificador} no encontrado")

        self.multilista_productos.desactivar_producto(codigo_identificador)

        if persistir and self.cliente is not None and self.repo_productos is not None and prod.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_productos.desactivar(prod.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.multilista_productos.activar_producto(codigo_identificador)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="desactivar",
                tipo_entidad="producto",
                identificador=codigo_identificador,
                descripcion=f"Desactivar producto {codigo_identificador}",
            )
        )

    def activar_producto(self, codigo_identificador: str, persistir: bool = True) -> None:
        self._verificar_autenticacion_si_aplica()
        prod = self.buscar_producto(codigo_identificador)
        if prod is None:
            raise RecursoNoEncontrado(f"Producto {codigo_identificador} no encontrado")

        self.multilista_productos.activar_producto(codigo_identificador)

        if persistir and self.cliente is not None and self.repo_productos is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.cliente.patch("productos", {"activo": True}, params={"codigo_identificador": f"eq.{codigo_identificador}"})
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                self.multilista_productos.desactivar_producto(codigo_identificador)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="activar",
                tipo_entidad="producto",
                identificador=codigo_identificador,
                descripcion=f"Activar producto {codigo_identificador}",
            )
        )

    def eliminar_producto(self, codigo_identificador: str, persistir: bool = True) -> Producto:
        self._verificar_autenticacion_si_aplica()
        prod = self.buscar_producto(codigo_identificador)
        if prod is None:
            raise RecursoNoEncontrado(f"Producto {codigo_identificador} no encontrado")

        nodo = self.multilista_productos.buscar_nodo(codigo_identificador)
        grupo_asoc = nodo.grupo if nodo else None
        autores_asoc = [inv for inv in nodo.autores] if nodo else []

        prod_eliminado = self.multilista_productos.eliminar_producto(codigo_identificador)

        if persistir and self.cliente is not None and self.repo_productos is not None and prod.id is not None:
            try:
                self.controlador_revision.verificar_consistencia(self.cliente)
                self.repo_productos.eliminar_cascada(prod.id, self.controlador_revision.revision_local)
                self.controlador_revision.actualizar_local(self.controlador_revision.revision_local + 1)
            except Exception:
                # Compensación
                if prod_eliminado is not None:
                    self.multilista_productos.agregar_producto(prod_eliminado, grupo=grupo_asoc, autores=autores_asoc)
                raise

        self.pila_deshacer.apilar(
            ComandoInverso(
                tipo_operacion="eliminar",
                tipo_entidad="producto",
                identificador=codigo_identificador,
                datos_reversion=prod.model_dump(),
                descripcion=f"Eliminar producto {codigo_identificador}",
            )
        )
        return prod

    # =========================================================================
    # MECANISMO DE DESHACER (UNDO)
    # =========================================================================

    def deshacer(self, persistir: bool = True) -> ComandoInverso | None:
        """Revierte la última operación apilada aplicando su delta inverso."""
        if self.pila_deshacer.esta_vacia():
            return None

        comando = self.pila_deshacer.desapilar()

        if comando.tipo_operacion == "crear":
            # Si se creó, el inverso es eliminar
            if comando.tipo_entidad == "grupo":
                self.eliminar_grupo(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "investigador":
                self.eliminar_investigador(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "producto":
                self.eliminar_producto(comando.identificador, persistir=persistir)

        elif comando.tipo_operacion == "desactivar":
            # Si se desactivó, el inverso es activar
            if comando.tipo_entidad == "grupo":
                self.activar_grupo(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "investigador":
                self.activar_investigador(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "producto":
                self.activar_producto(comando.identificador, persistir=persistir)

        elif comando.tipo_operacion == "activar":
            # Si se activó, el inverso es desactivar
            if comando.tipo_entidad == "grupo":
                self.desactivar_grupo(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "investigador":
                self.desactivar_investigador(comando.identificador, persistir=persistir)
            elif comando.tipo_entidad == "producto":
                self.desactivar_producto(comando.identificador, persistir=persistir)

        elif comando.tipo_operacion == "editar":
            # Si se editó, se restauran los valores previos
            if comando.tipo_entidad == "grupo":
                self.actualizar_grupo(comando.identificador, comando.datos_reversion, persistir=persistir)
            elif comando.tipo_entidad == "investigador":
                self.actualizar_investigador(comando.identificador, comando.datos_reversion, persistir=persistir)

        # Remueve de la pila el comando generado por la propia acción de reversión
        if not self.pila_deshacer.esta_vacia():
            self.pila_deshacer.desapilar()

        return comando

    # =========================================================================
    # RECARGA TOTAL Y DETECCIÓN DE CONFLICTOS
    # =========================================================================

    def recargar_todo(self) -> None:
        """Descarga todas las entidades desde Supabase y reconstruye las estructuras en memoria."""
        if self.cliente is None:
            return

        self._verificar_autenticacion_si_aplica()

        # 1. Vaciar estructuras
        self.grupos.limpiar()
        self.investigadores.limpiar()
        self.integrantes.limpiar()
        self.multilista_productos.limpiar()
        self.proyectos.limpiar()

        # 2. Cargar grupos
        grupos_remotos = self.repo_grupos.listar() if self.repo_grupos else []
        for g in grupos_remotos:
            self.grupos.insertar_final(g)

        # 3. Cargar investigadores
        invs_remotos = self.repo_investigadores.listar() if self.repo_investigadores else []
        for inv in invs_remotos:
            self.investigadores.insertar_final(inv)

        # 4. Cargar integrantes
        ints_remotos = self.repo_integrantes.listar() if self.repo_integrantes else []
        for m in ints_remotos:
            self.integrantes.insertar_final(m)

        # 5. Cargar productos y relaciones
        prods_remotos = self.repo_productos.listar() if self.repo_productos else []
        rels_grupos = self.repo_productos.listar_relaciones_grupos() if self.repo_productos else []
        rels_autores = self.repo_productos.listar_relaciones_autores() if self.repo_productos else []

        # Mapas auxiliares temporales para resolución O(1) de vinculaciones
        prod_por_id: dict[int, Producto] = {}
        for p in prods_remotos:
            if p.id is not None:
                prod_por_id[p.id] = p

        grupo_por_id: dict[int, Grupo] = {}
        for g in self.grupos:
            if g.id is not None:
                grupo_por_id[g.id] = g

        inv_por_id: dict[int, Investigador] = {}
        for inv in self.investigadores:
            if inv.id is not None:
                inv_por_id[inv.id] = inv

        grupo_de_prod: dict[int, Grupo] = {}
        for rg in rels_grupos:
            pid = rg.get("producto_id")
            gid = rg.get("grupo_id")
            if pid in prod_por_id and gid in grupo_por_id:
                grupo_de_prod[pid] = grupo_por_id[gid]

        autores_de_prod: dict[int, list[Investigador]] = {}
        for ra in rels_autores:
            pid = ra.get("producto_id")
            iid = ra.get("investigador_id")
            if pid in prod_por_id and iid in inv_por_id:
                if pid not in autores_de_prod:
                    autores_de_prod[pid] = []
                autores_de_prod[pid].append(inv_por_id[iid])

        for p in prods_remotos:
            grp = grupo_de_prod.get(p.id) if p.id else None
            auts = autores_de_prod.get(p.id, []) if p.id else []
            self.multilista_productos.agregar_producto(p, grupo=grp, autores=auts)

        # 6. Sincronizar número de revisión
        self.controlador_revision.sincronizar(self.cliente)

    def verificar_revision(self) -> bool:
        """Comprueba si la base remota fue modificada concurrentemente."""
        if self.cliente is None:
            return False
        remota = self.controlador_revision.consultar_remota(self.cliente)
        return remota != self.controlador_revision.revision_local

    def resumen_dict(self) -> dict[str, int]:
        """Calcula el resumen de KPIs institucionales ordenado alfabéticamente."""
        total_grupos = len(self.grupos)
        grupos_activos = sum(1 for g in self.grupos if g.activo)
        total_invs = len(self.investigadores)
        invs_activos = sum(1 for i in self.investigadores if i.activo)
        total_prods = len(self.multilista_productos)
        prods_activos = sum(1 for p in self.multilista_productos if p.activo)
        pila_tam = len(self.pila_deshacer)
        return {
            "grupos_activos": grupos_activos,
            "grupos_totales": total_grupos,
            "investigadores_activos": invs_activos,
            "investigadores_totales": total_invs,
            "pila_deshacer_tamano": pila_tam,
            "productos_activos": prods_activos,
            "productos_totales": total_prods,
        }

    def resumen_json(self) -> str:
        """Genera el JSON compacto canónico byte-a-byte interoperable con C++."""
        import json
        return json.dumps(self.resumen_dict(), sort_keys=True, separators=(",", ":"))

