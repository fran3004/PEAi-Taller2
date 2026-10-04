"""Fachada de servicios para la interfaz gráfica de PEA-i.

La GUI solo habla con esta clase. Aquí se decide si los cambios se persisten (modo Supabase)
o quedan en memoria (modo demostración), se bloquea la escritura sin conexión o con la base
cambiada, y se traducen las estructuras internas a modelos de vista (vistas.py).

Reglas que se cumplen aquí (AGENTS.md):
- La GUI no recibe ListaDoble, Multilista ni Hipercubo5D: solo DTO y tipos simples.
- Las estadísticas salen de ServicioEstadisticas (hipercubo), nunca de SQL.
- Los tokens viven solo en memoria (Sesion y ClienteHTTPSupabase); nada se escribe en disco.
- Esta clase no es segura para hilos: la GUI la usa desde UN único hilo de trabajo serial.
"""

from __future__ import annotations

import base64
import datetime
import json
import os
import platform
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from pydantic import ValidationError

from pea.cliente_http import ClienteHTTPSupabase
from pea.datos.sesion import Sesion
from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.cola import EstadoTarea, TareaIngesta
from pea.estructuras.hipercubo import Hipercubo5D
from pea.estructuras.lista_doble import ListaDoble
from pea.excepciones import ConflictoRevision, ErrorConexion, ErrorPEA, ErrorValidacion, RecursoNoEncontrado
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.datos_demostracion import cargar_datos_demostracion
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from pea.servicios.servicio_exportacion import ServicioExportacion
from pea.servicios.servicio_verificacion_cruzada import (
    ResultadoVerificacionCruzada,
    ServicioVerificacionCruzada,
)
from pea.servicios.vistas import (
    ANIO_CORTE_MODELO_2024,
    EstadoAplicacion,
    FiltroAnios,
    ModoConexion,
    ModoFiltroAnios,
    TablaDatos,
)
from pea.version import APP_NAME, APP_VERSION, INSTITUCION

T = TypeVar("T")

TIPOLOGIAS: tuple[str, ...] = ("GNC", "DTI", "ASC", "FRH")
VALIDACIONES: tuple[str, ...] = ("Avalado", "Con soporte", "No avalado")
ENTIDADES: tuple[str, ...] = ("grupo", "investigador", "producto")

_ETIQUETA_ESTADO_TAREA: dict[str, str] = {
    EstadoTarea.PENDIENTE: "Pendiente",
    EstadoTarea.PROCESANDO: "Procesando",
    EstadoTarea.TERMINADA: "Terminada",
    EstadoTarea.CON_ERROR: "Error",
}

_CAMPOS_EDITABLES_GRUPO = (
    "nombre",
    "categoria",
    "lider",
    "institucion_principal",
    "departamento_ciudad",
    "gran_area_ocde",
    "area_ocde",
    "fecha_creacion",
)
_CAMPOS_EDITABLES_INVESTIGADOR = (
    "nombre_completo",
    "nombre_en_citas",
    "categoria",
    "formacion_academica",
    "nacionalidad",
    "sexo",
)
_CAMPOS_EDITABLES_PRODUCTO = (
    "titulo",
    "tipo_mayor",
    "subtipo",
    "ano",
    "mes",
    "pais",
    "estado_validacion",
    "codigo_grupo",
)


def _limpiar(datos: dict[str, Any]) -> dict[str, Any]:
    """Recorta textos y convierte cadenas vacías en None."""
    limpio: dict[str, Any] = {}
    for clave, valor in datos.items():
        if isinstance(valor, str):
            valor = valor.strip()
            limpio[clave] = valor if valor != "" else None
        else:
            limpio[clave] = valor
    return limpio


def _mensaje_validacion(err: ValidationError) -> str:
    partes = []
    for e in err.errors():
        campo = ".".join(str(x) for x in e.get("loc", ()))
        partes.append(f"campo «{campo}» inválido o vacío")
    return "Datos inválidos: " + "; ".join(partes)


def _es_libro_o_patente(subtipo: str | None) -> bool:
    """Misma regla que Hipercubo5D.poblar_desde_multilista para las ventanas de 10 años."""
    s = (subtipo or "").upper()
    return "LIB" in s or "PA" in s or "PATENTE" in s


def _rol_jwt(clave: str) -> str | None:
    partes = clave.split(".")
    if len(partes) != 3:
        return None
    try:
        relleno = "=" * (-len(partes[1]) % 4)
        carga = json.loads(base64.urlsafe_b64decode(partes[1] + relleno).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    rol = carga.get("role") if isinstance(carga, dict) else None
    return str(rol) if rol is not None else None


class ServicioAplicacion:
    """Punto único de entrada de la interfaz gráfica a la lógica de PEA-i."""

    def __init__(
        self,
        fabrica_cliente: Callable[[str, str], ClienteHTTPSupabase] | None = None,
        verificacion: ServicioVerificacionCruzada | None = None,
        anio_actual: Callable[[], int] | None = None,
        directorio_salida: Path | None = None,
    ) -> None:
        self._fabrica_cliente = fabrica_cliente or (
            lambda url, clave: ClienteHTTPSupabase(base_url=url, anon_key=clave, timeout=15.0)
        )
        self._verificacion = verificacion or ServicioVerificacionCruzada()
        self._anio_actual = anio_actual or (lambda: datetime.date.today().year)
        self._directorio_salida = directorio_salida or Path("datos/fuentes")

        self._cliente: ClienteHTTPSupabase | None = None
        self._sesion = Sesion()
        self._catalogo = CatalogoInvestigacion()
        self._ingesta = ServicioIngesta(self._catalogo)
        self._historial_ingesta: ListaDoble[TareaIngesta] = ListaDoble()
        self._modo = ModoConexion.DESCONECTADO
        self._sin_conexion = False
        self._cambio_remoto = False
        self._revision_remota: int | None = None
        self._revision_demo_remota = 0
        self._mensaje = "Sin conexión con PEA-i."

    # =========================================================================
    # CONEXIÓN, SESIÓN Y REVISIÓN
    # =========================================================================

    @staticmethod
    def configuracion_entorno() -> dict[str, Any]:
        """Valores sugeridos para el formulario de conexión (sin devolver contraseñas)."""
        url = os.environ.get("PEA_SUPABASE_URL_PROD") or os.environ.get("PEA_SUPABASE_URL_TEST") or ""
        clave = (
            os.environ.get("PEA_SUPABASE_KEY_PROD")
            or os.environ.get("PEA_SUPABASE_ANON_PROD")
            or os.environ.get("PEA_SUPABASE_KEY_TEST")
            or ""
        )
        return {
            "url": url,
            "clave_publicable": clave,
            "correo": os.environ.get("PEA_USUARIO_CORREO", ""),
            "hay_clave_usuario_en_entorno": bool(os.environ.get("PEA_USUARIO_CLAVE")),
        }

    @staticmethod
    def _validar_parametros_conexion(url: str, clave_publicable: str) -> None:
        if not url.lower().startswith("https://"):
            raise ErrorValidacion("La URL del proyecto debe usar HTTPS (https://...).")
        if not clave_publicable:
            raise ErrorValidacion("Falta la clave publicable del proyecto.")
        if clave_publicable.startswith("sb_secret_") or _rol_jwt(clave_publicable) == "service_role":
            raise ErrorValidacion(
                "Esa clave es secreta (secret/service_role). PEA-i solo acepta la clave publicable."
            )

    def conectar(
        self,
        url: str,
        clave_publicable: str,
        correo: str = "",
        clave: str = "",
        usar_clave_entorno: bool = False,
    ) -> EstadoAplicacion:
        """Autentica (si hay correo), descarga todo por HTTPS y reemplaza el catálogo en memoria."""
        url = url.strip()
        clave_publicable = clave_publicable.strip()
        self._validar_parametros_conexion(url, clave_publicable)

        clave_usuario = clave or (os.environ.get("PEA_USUARIO_CLAVE", "") if usar_clave_entorno else "")
        cliente = self._fabrica_cliente(url, clave_publicable)
        sesion = Sesion()
        if correo.strip() and clave_usuario:
            cuerpo = cliente.autenticar(correo.strip(), clave_usuario)
            sesion.iniciar_sesion(
                token=str(cuerpo.get("access_token", "")),
                correo=correo.strip(),
                tiempo_expiracion_segundos=float(cuerpo.get("expires_in", 3600)),
            )
        clave_usuario = ""  # no se conserva la contraseña

        catalogo = CatalogoInvestigacion(cliente=cliente, sesion=sesion)
        try:
            catalogo.recargar_todo()
        except Exception:
            cliente.cerrar_sesion()
            sesion.cerrar_sesion()
            raise

        if self._cliente is not None:
            self._cliente.cerrar_sesion()
        self._cliente = cliente
        self._sesion = sesion
        self._instalar_catalogo(catalogo, ModoConexion.SUPABASE)
        self._revision_remota = catalogo.controlador_revision.revision_local
        self._mensaje = f"Conectado a {url}"
        return self.estado()

    def desconectar(self) -> EstadoAplicacion:
        if self._cliente is not None:
            self._cliente.cerrar_sesion()
        self._sesion.cerrar_sesion()
        self._cliente = None
        self._sesion = Sesion()
        self._instalar_catalogo(CatalogoInvestigacion(), ModoConexion.DESCONECTADO)
        self._mensaje = "Sesión cerrada. Los datos se retiraron de la memoria."
        return self.estado()

    def cargar_demostracion(self) -> EstadoAplicacion:
        """Carga el conjunto ficticio en memoria; nada se envía a la base de datos."""
        if self._cliente is not None:
            self._cliente.cerrar_sesion()
        self._cliente = None
        self._sesion = Sesion()
        catalogo = CatalogoInvestigacion()
        cargar_datos_demostracion(catalogo)
        self._instalar_catalogo(catalogo, ModoConexion.DEMOSTRACION)
        self._revision_demo_remota = catalogo.controlador_revision.revision_local
        self._revision_remota = self._revision_demo_remota
        self._mensaje = "Datos de demostración cargados (ficticios, no se guardan en la base)."
        return self.estado()

    def _instalar_catalogo(self, catalogo: CatalogoInvestigacion, modo: ModoConexion) -> None:
        self._catalogo = catalogo
        self._ingesta = ServicioIngesta(catalogo)
        self._historial_ingesta = ListaDoble()
        self._modo = modo
        self._sin_conexion = False
        self._cambio_remoto = False
        self._revision_remota = None

    def simular_cambio_remoto(self) -> EstadoAplicacion:
        """Solo en demostración: imita que otro programa escribió en la base."""
        if self._modo != ModoConexion.DEMOSTRACION:
            raise ErrorPEA("La simulación de cambios solo existe en el modo de demostración.")
        self._revision_demo_remota += 1
        return self.estado()

    def verificar_cambios_remotos(self) -> EstadoAplicacion:
        """Consulta meta.revision (o la revisión simulada) y marca si la base cambió."""
        if self._modo == ModoConexion.SUPABASE and self._cliente is not None:
            try:
                remota = self._catalogo.controlador_revision.consultar_remota(self._cliente)
            except ErrorConexion as err:
                self._sin_conexion = True
                self._mensaje = f"Sin conexión: {err.mensaje}"
                return self.estado()
            self._sin_conexion = False
            self._revision_remota = remota
            self._cambio_remoto = remota != self._catalogo.controlador_revision.revision_local
        elif self._modo == ModoConexion.DEMOSTRACION:
            self._revision_remota = self._revision_demo_remota
            self._cambio_remoto = self._revision_demo_remota != self._catalogo.controlador_revision.revision_local
        if self._cambio_remoto:
            self._mensaje = "La base de datos cambió"
        return self.estado()

    def recargar(self) -> EstadoAplicacion:
        """Reconstruye las estructuras desde la base (o resincroniza la demostración)."""
        if self._modo == ModoConexion.SUPABASE:
            try:
                self._catalogo.recargar_todo()
            except ErrorConexion:
                self._sin_conexion = True
                raise
            self._revision_remota = self._catalogo.controlador_revision.revision_local
        elif self._modo == ModoConexion.DEMOSTRACION:
            self._catalogo.controlador_revision.actualizar_local(self._revision_demo_remota)
            self._revision_remota = self._revision_demo_remota
        else:
            raise ErrorPEA("No hay conexión: no hay nada que recargar.")
        # Tras recargar, las operaciones previas ya no son reversibles con seguridad.
        self._catalogo.pila_deshacer.limpiar()
        self._sin_conexion = False
        self._cambio_remoto = False
        self._mensaje = "Datos recargados."
        return self.estado()

    def estado(self) -> EstadoAplicacion:
        cat = self._catalogo
        hay_datos = len(cat.grupos) > 0 or len(cat.investigadores) > 0 or len(cat.multilista_productos) > 0
        return EstadoAplicacion(
            modo=self._modo,
            sin_conexion=self._sin_conexion,
            correo=self._sesion.correo,
            base_url=self._cliente.base_url if self._cliente is not None else None,
            revision_local=cat.controlador_revision.revision_local if self._modo != ModoConexion.DESCONECTADO else None,
            revision_remota=self._revision_remota,
            cambio_remoto=self._cambio_remoto,
            operaciones_deshacer=len(cat.pila_deshacer),
            tareas_pendientes=len(cat.cola_importacion),
            hay_datos=hay_datos,
            mensaje=self._mensaje,
            historial_deshacer=tuple(c.descripcion for c in cat.pila_deshacer),
        )

    # =========================================================================
    # ESCRITURA CONTROLADA
    # =========================================================================

    def _exigir_escritura(self) -> None:
        motivo = self.estado().motivo_bloqueo
        if motivo is not None:
            raise ErrorPEA(motivo)

    def _escribir(self, accion: Callable[[bool], T]) -> T:
        """Ejecuta una mutación persistiendo solo en modo Supabase y registra conflictos."""
        self._exigir_escritura()
        persistir = self._modo == ModoConexion.SUPABASE
        try:
            resultado = accion(persistir)
        except ConflictoRevision as err:
            if err.mensaje == "La base de datos cambió":
                self._cambio_remoto = True
                self._mensaje = "La base de datos cambió"
            raise
        except ErrorConexion as err:
            self._sin_conexion = True
            self._mensaje = f"Sin conexión: {err.mensaje}"
            raise
        except ValidationError as err:
            raise ErrorValidacion(_mensaje_validacion(err)) from err
        except ValueError as err:
            raise ErrorValidacion(str(err)) from err
        if self._modo == ModoConexion.DEMOSTRACION:
            # En demostración, cada escritura propia avanza ambas revisiones a la par.
            self._catalogo.controlador_revision.actualizar_local(self._catalogo.controlador_revision.revision_local + 1)
            self._revision_demo_remota += 1
            self._revision_remota = self._revision_demo_remota
        return resultado

    # ------------------------------------------------------------------ grupos
    def crear_grupo(self, datos: dict[str, Any]) -> str:
        valores = _limpiar(datos)

        def accion(persistir: bool) -> str:
            grupo = Grupo.model_validate({k: v for k, v in valores.items() if v is not None})
            self._catalogo.crear_grupo(grupo, persistir=persistir)
            return f"Grupo {grupo.codigo_gruplac} creado."

        return self._escribir(accion)

    def actualizar_grupo(self, codigo: str, datos: dict[str, Any]) -> str:
        valores = {k: v for k, v in _limpiar(datos).items() if k in _CAMPOS_EDITABLES_GRUPO}
        if not valores.get("nombre"):
            raise ErrorValidacion("El nombre del grupo es obligatorio.")

        def accion(persistir: bool) -> str:
            self._catalogo.actualizar_grupo(codigo, valores, persistir=persistir)
            return f"Grupo {codigo} actualizado."

        return self._escribir(accion)

    # ------------------------------------------------------------------ investigadores
    def crear_investigador(self, datos: dict[str, Any]) -> str:
        valores = _limpiar(datos)

        def accion(persistir: bool) -> str:
            inv = Investigador.model_validate({k: v for k, v in valores.items() if v is not None})
            self._catalogo.crear_investigador(inv, persistir=persistir)
            return f"Investigador {inv.codigo_rh} creado."

        return self._escribir(accion)

    def actualizar_investigador(self, codigo: str, datos: dict[str, Any]) -> str:
        valores = {k: v for k, v in _limpiar(datos).items() if k in _CAMPOS_EDITABLES_INVESTIGADOR}
        if not valores.get("nombre_completo"):
            raise ErrorValidacion("El nombre del investigador es obligatorio.")

        def accion(persistir: bool) -> str:
            self._catalogo.actualizar_investigador(codigo, valores, persistir=persistir)
            return f"Investigador {codigo} actualizado."

        return self._escribir(accion)

    def vincular_integrante(self, codigo_grupo: str, codigo_rh: str, rol: str = "Investigador") -> str:
        def accion(persistir: bool) -> str:
            existente = self._catalogo.integrantes.buscar_dato(
                lambda m: m.codigo_gruplac == codigo_grupo and m.codigo_rh == codigo_rh
            )
            if existente is not None:
                raise ErrorValidacion("El investigador ya es integrante de ese grupo.")
            self._catalogo.vincular_integrante(codigo_grupo, codigo_rh, rol=rol, persistir=persistir)
            return f"{codigo_rh} vinculado a {codigo_grupo} como {rol}."

        return self._escribir(accion)

    # ------------------------------------------------------------------ productos
    def crear_producto(
        self,
        datos: dict[str, Any],
        codigo_grupo: str | None = None,
        codigos_autores: tuple[str, ...] | list[str] = (),
    ) -> str:
        valores = _limpiar(datos)
        if valores.get("tipo_mayor") not in TIPOLOGIAS:
            raise ErrorValidacion("La tipología debe ser GNC, DTI, ASC o FRH.")
        if valores.get("estado_validacion") not in VALIDACIONES:
            raise ErrorValidacion("La validación debe ser Avalado, Con soporte o No avalado.")
        try:
            anio = int(valores.get("ano") or 0)
        except (TypeError, ValueError) as err:
            raise ErrorValidacion("El año debe ser un número entero.") from err
        if not 1900 <= anio <= self._anio_actual() + 1:
            raise ErrorValidacion(f"El año debe estar entre 1900 y {self._anio_actual() + 1}.")
        valores["ano"] = anio

        def accion(persistir: bool) -> str:
            prod = Producto.model_validate({k: v for k, v in valores.items() if v is not None})
            self._catalogo.crear_producto(
                prod,
                codigo_gruplac=codigo_grupo or None,
                codigos_rh_autores=list(codigos_autores),
                persistir=persistir,
            )
            return f"Producto {prod.codigo_identificador} creado."

        return self._escribir(accion)

    def actualizar_producto(self, codigo: str, datos: dict[str, Any]) -> str:
        bruto = _limpiar(datos)
        # Normalizar sinónimos comunes
        if "tipologia" in bruto and "tipo_mayor" not in bruto:
            bruto["tipo_mayor"] = bruto["tipologia"]
        if "validacion" in bruto and "estado_validacion" not in bruto:
            bruto["estado_validacion"] = bruto["validacion"]
        if "grupo" in bruto and "codigo_grupo" not in bruto:
            bruto["codigo_grupo"] = bruto["grupo"]
        if "anio" in bruto and "ano" not in bruto:
            bruto["ano"] = bruto["anio"]

        valores = {k: v for k, v in bruto.items() if k in _CAMPOS_EDITABLES_PRODUCTO}

        if "titulo" in valores and not valores.get("titulo"):
            raise ErrorValidacion("El título del producto es obligatorio.")
        if "tipo_mayor" in valores and valores["tipo_mayor"] not in TIPOLOGIAS:
            raise ErrorValidacion("La tipología debe ser GNC, DTI, ASC o FRH.")
        if "estado_validacion" in valores and valores["estado_validacion"] not in VALIDACIONES:
            raise ErrorValidacion("La validación debe ser Avalado, Con soporte o No avalado.")
        if "ano" in valores:
            try:
                anio = int(valores["ano"] or 0)
            except (TypeError, ValueError) as err:
                raise ErrorValidacion("El año debe ser un número entero.") from err
            if not 1900 <= anio <= self._anio_actual() + 1:
                raise ErrorValidacion(f"El año debe estar entre 1900 y {self._anio_actual() + 1}.")
            valores["ano"] = anio
        if "codigo_grupo" in valores and valores["codigo_grupo"]:
            grp = self._catalogo.buscar_grupo(str(valores["codigo_grupo"]))
            if grp is None:
                raise RecursoNoEncontrado(f"Grupo {valores['codigo_grupo']} no encontrado")

        def accion(persistir: bool) -> str:
            self._catalogo.actualizar_producto(codigo, valores, persistir=persistir)
            return f"Producto {codigo} actualizado."

        return self._escribir(accion)

    # ------------------------------------------------------------------ comunes
    def cambiar_estado(self, entidad: str, codigo: str, activo: bool) -> str:
        """Activa o desactiva (activo=false, reversible) una entidad."""
        if entidad not in ENTIDADES:
            raise ErrorValidacion(f"Entidad desconocida: {entidad}")
        cat = self._catalogo

        def accion(persistir: bool) -> str:
            metodo = {
                ("grupo", True): cat.activar_grupo,
                ("grupo", False): cat.desactivar_grupo,
                ("investigador", True): cat.activar_investigador,
                ("investigador", False): cat.desactivar_investigador,
                ("producto", True): cat.activar_producto,
                ("producto", False): cat.desactivar_producto,
            }[(entidad, activo)]
            metodo(codigo, persistir=persistir)
            cat.sincronizar_hipercubo()
            return f"{entidad.capitalize()} {codigo} {'activado' if activo else 'desactivado'}."

        return self._escribir(accion)

    def describir_cascada(self, entidad: str, codigo: str) -> str:
        """Texto para confirmar una eliminación física con sus efectos en cascada."""
        cat = self._catalogo
        if entidad == "grupo":
            n_int = sum(1 for m in cat.integrantes if m.codigo_gruplac == codigo)
            n_prod = len(cat.multilista_productos.obtener_productos_grupo(codigo))
            return (
                f"Se eliminará el grupo {codigo}, se retirarán {n_int} membresías y "
                f"{n_prod} productos quedarán sin grupo (los productos no se borran)."
            )
        if entidad == "investigador":
            n_int = sum(1 for m in cat.integrantes if m.codigo_rh == codigo)
            n_prod = len(cat.multilista_productos.obtener_productos_investigador(codigo))
            return (
                f"Se eliminará el investigador {codigo}, se retirarán {n_int} membresías y "
                f"se quitará su autoría de {n_prod} productos (los productos no se borran)."
            )
        if entidad == "producto":
            return f"Se eliminará el producto {codigo} y sus enlaces con grupo y autores."
        raise ErrorValidacion(f"Entidad desconocida: {entidad}")

    def eliminar(self, entidad: str, codigo: str) -> str:
        if entidad not in ENTIDADES:
            raise ErrorValidacion(f"Entidad desconocida: {entidad}")
        cat = self._catalogo

        def accion(persistir: bool) -> str:
            metodo = {
                "grupo": cat.eliminar_grupo,
                "investigador": cat.eliminar_investigador,
                "producto": cat.eliminar_producto,
            }[entidad]
            metodo(codigo, persistir=persistir)
            return f"{entidad.capitalize()} {codigo} eliminado."

        return self._escribir(accion)

    def deshacer(self) -> str:
        def accion(persistir: bool) -> str:
            comando = self._catalogo.deshacer(persistir=persistir)
            if comando is None:
                return "No hay operaciones para deshacer."
            return f"Deshecho: {comando.descripcion}"

        return self._escribir(accion)

    # =========================================================================
    # CONSULTAS (MODELOS DE VISTA)
    # =========================================================================

    def _rango(self, filtro: FiltroAnios) -> tuple[int | None, int | None, bool]:
        return filtro.resolver(self._anio_actual())

    def _producto_en_filtro(self, prod: Producto, filtro: FiltroAnios) -> bool:
        inicio, fin, modelo = self._rango(filtro)
        if modelo:
            duracion = 10 if _es_libro_o_patente(prod.subtipo) else 5
            return ANIO_CORTE_MODELO_2024 - duracion + 1 <= prod.ano <= ANIO_CORTE_MODELO_2024
        if inicio is not None and prod.ano < inicio:
            return False
        return not (fin is not None and prod.ano > fin)

    def _nombre_grupo(self, codigo: str) -> str:
        g = self._catalogo.buscar_grupo(codigo)
        return g.nombre if g is not None else codigo

    def _nombre_investigador(self, codigo: str) -> str:
        i = self._catalogo.buscar_investigador(codigo)
        return i.nombre_completo if i is not None else codigo

    def opciones_grupos(self) -> tuple[tuple[str, str], ...]:
        return tuple((g.codigo_gruplac, g.nombre) for g in self._catalogo.grupos)

    def opciones_investigadores(self) -> tuple[tuple[str, str], ...]:
        return tuple((i.codigo_rh, i.nombre_completo) for i in self._catalogo.investigadores)

    def descripcion_filtro(self, filtro: FiltroAnios) -> str:
        return filtro.descripcion(self._anio_actual())

    def resumen_general(self, filtro: FiltroAnios) -> dict[str, Any]:
        cat = self._catalogo
        inicio, fin, modelo = self._rango(filtro)
        vista = cat.estadisticas.obtener_vista_institucional(modelo_2024=modelo, anio_inicio=inicio, anio_fin=fin)
        top_inv = tuple((c, self._nombre_investigador(c), n) for c, n in vista["top_5_investigadores"])
        top_grp = tuple((c, self._nombre_grupo(c), n) for c, n in vista["top_5_grupos"])
        return {
            "filtro": self.descripcion_filtro(filtro),
            "grupos_activos": sum(1 for g in cat.grupos if g.activo),
            "grupos_totales": len(cat.grupos),
            "investigadores_activos": sum(1 for i in cat.investigadores if i.activo),
            "investigadores_totales": len(cat.investigadores),
            "productos_totales": len(cat.multilista_productos),
            "total_productos": vista["total_productos"],
            "promedio_por_investigador": vista["promedio_por_investigador"],
            "productos_por_anio": dict(vista["productos_por_anio"]),
            "productos_por_categoria": dict(vista["productos_por_categoria"]),
            "porcentajes_categoria": dict(vista["porcentajes_categoria"]),
            "productos_por_validacion": dict(vista["productos_por_validacion"]),
            "porcentajes_validacion": dict(vista["porcentajes_validacion"]),
            "top_investigadores": TablaDatos(
                columnas=("Código", "Investigador", "Productos"),
                filas=tuple((c, nom, n) for c, nom, n in top_inv),
                claves=tuple(c for c, _, _ in top_inv),
            ),
            "top_grupos": TablaDatos(
                columnas=("Código", "Grupo", "Productos"),
                filas=tuple((c, nom, n) for c, nom, n in top_grp),
                claves=tuple(c for c, _, _ in top_grp),
            ),
            "hay_datos": vista["total_productos"] > 0,
        }

    def vista_grupo(self, codigo: str, filtro: FiltroAnios) -> dict[str, Any]:
        cat = self._catalogo
        grupo = cat.buscar_grupo(codigo)
        if grupo is None:
            raise RecursoNoEncontrado(f"Grupo {codigo} no encontrado")
        inicio, fin, modelo = self._rango(filtro)
        vista = cat.estadisticas.obtener_vista_grupo(codigo, modelo_2024=modelo, anio_inicio=inicio, anio_fin=fin)
        conteo_inv = {k: v for k, v in vista["investigadores"].items() if k != "SIN_INVESTIGADOR"}
        integrantes = [m for m in cat.integrantes if m.codigo_gruplac == codigo]
        filas_int = []
        for m in integrantes:
            filas_int.append((m.codigo_rh, self._nombre_investigador(m.codigo_rh), m.rol, conteo_inv.get(m.codigo_rh, 0)))
        # Autores con productos en el grupo que no figuran como integrantes
        for cod, n in sorted(conteo_inv.items()):
            if not any(m.codigo_rh == cod for m in integrantes):
                filas_int.append((cod, self._nombre_investigador(cod), "Coautor externo", n))
        filas_int.sort(key=lambda f: (-int(f[3]), str(f[1])))
        estudiantes = sum(
            1 for m in integrantes if "estudiante" in (m.rol or "").lower()
        )
        prod_avalados = int(vista["productos_por_validacion"].get("Avalado", 0))
        return {
            "codigo": codigo,
            "nombre": grupo.nombre,
            "categoria": grupo.categoria or "Sin clasificar",
            "lider": grupo.lider or "—",
            "activo": grupo.activo,
            "filtro": self.descripcion_filtro(filtro),
            "total_productos": vista["total_productos"],
            "productos_avalados": prod_avalados,
            "estudiantes": estudiantes,
            "porcentaje_sobre_institucion": vista["porcentaje_sobre_institucion"],
            "promedio_por_investigador": vista["promedio_por_investigador"],
            "productos_por_anio": dict(vista["productos_por_anio"]),
            "productos_por_categoria": dict(vista["productos_por_categoria"]),
            "porcentajes_categoria": dict(vista["porcentajes_categoria"]),
            "productos_por_validacion": dict(vista["productos_por_validacion"]),
            "integrantes": TablaDatos(
                columnas=("Código", "Investigador", "Rol", "Productos"),
                filas=tuple(filas_int),
                claves=tuple(str(f[0]) for f in filas_int),
            ),
            "productos": self.tabla_productos(filtro, codigo_grupo=codigo),
        }

    def vista_investigador(self, codigo: str, filtro: FiltroAnios) -> dict[str, Any]:
        cat = self._catalogo
        inv = cat.buscar_investigador(codigo)
        if inv is None:
            raise RecursoNoEncontrado(f"Investigador {codigo} no encontrado")
        inicio, fin, modelo = self._rango(filtro)
        vista = cat.estadisticas.obtener_vista_investigador(
            codigo, modelo_2024=modelo, anio_inicio=inicio, anio_fin=fin
        )
        filas_aporte = []
        for cod_grp, datos in sorted(vista["contribuciones_grupos"].items()):
            filas_aporte.append(
                (
                    cod_grp,
                    self._nombre_grupo(cod_grp),
                    datos["productos_propios_en_grupo"],
                    datos["total_productos_grupo"],
                    f"{datos['porcentaje_aporte']:.2f} %",
                )
            )
        membresias = tuple(
            (m.codigo_gruplac, self._nombre_grupo(m.codigo_gruplac), m.rol)
            for m in cat.integrantes
            if m.codigo_rh == codigo
        )
        anios_con_prod = sum(1 for cant in vista["productos_por_anio"].values() if cant > 0)
        coautores_set: set[str] = set()
        for nodo in cat.multilista_productos.iterar_nodos():
            if not nodo.producto.activo:
                continue
            autores_rh = [a.codigo_rh for a in nodo.autores if getattr(a, "codigo_rh", None)]
            if codigo in autores_rh:
                for a_rh in autores_rh:
                    if a_rh != codigo:
                        coautores_set.add(a_rh)
        prod_avalados = int(vista["productos_por_validacion"].get("Avalado", 0))
        return {
            "codigo": codigo,
            "nombre": inv.nombre_completo,
            "categoria": inv.categoria or "Sin categoría",
            "formacion": inv.formacion_academica or "—",
            "activo": inv.activo,
            "filtro": self.descripcion_filtro(filtro),
            "total_productos": vista["total_productos"],
            "productos_avalados": prod_avalados,
            "anios_con_produccion": anios_con_prod,
            "coautores": len(coautores_set),
            "productos_por_anio": dict(vista["productos_por_anio"]),
            "productos_por_categoria": dict(vista["productos_por_categoria"]),
            "porcentajes_categoria": dict(vista["porcentajes_categoria"]),
            "productos_por_validacion": dict(vista["productos_por_validacion"]),
            "aportes": TablaDatos(
                columnas=("Código", "Grupo", "Productos propios", "Total del grupo", "Aporte"),
                filas=tuple(filas_aporte),
                claves=tuple(str(f[0]) for f in filas_aporte),
            ),
            "membresias": TablaDatos(
                columnas=("Código", "Grupo", "Rol"),
                filas=membresias,
                claves=tuple(m[0] for m in membresias),
            ),
            "productos": self.tabla_productos(filtro, codigo_investigador=codigo),
        }

    def datos_ficha_grupo(self, codigo: str, filtro: FiltroAnios) -> dict[str, Any]:
        """Datos consolidados para la FichaGrupo (lateral o Inicio en modo grupo)."""
        vg = self.vista_grupo(codigo, filtro)
        return {
            "codigo": vg["codigo"],
            "nombre": vg["nombre"],
            "categoria": vg["categoria"],
            "lider": vg["lider"],
            "activo": vg["activo"],
            "filtro": vg["filtro"],
            "total_productos": vg["total_productos"],
            "productos_avalados": vg["productos_avalados"],
            "estudiantes": vg["estudiantes"],
            "porcentaje_sobre_institucion": vg["porcentaje_sobre_institucion"],
            "promedio_por_investigador": vg["promedio_por_investigador"],
            "productos_por_anio": vg["productos_por_anio"],
            "productos_por_categoria": vg["productos_por_categoria"],
            "productos_por_validacion": vg["productos_por_validacion"],
        }

    def datos_ficha_investigador(self, codigo: str, filtro: FiltroAnios) -> dict[str, Any]:
        """Datos consolidados para la FichaInvestigador (lateral en pantalla Investigadores)."""
        vi = self.vista_investigador(codigo, filtro)
        mems = vi["membresias"].filas
        grp_ppal = mems[0][1] if mems else "Sin grupo"
        return {
            "codigo": vi["codigo"],
            "nombre": vi["nombre"],
            "categoria": vi["categoria"],
            "formacion": vi["formacion"],
            "grupo_principal": grp_ppal,
            "activo": vi["activo"],
            "filtro": vi["filtro"],
            "total_productos": vi["total_productos"],
            "productos_avalados": vi["productos_avalados"],
            "anios_con_produccion": vi["anios_con_produccion"],
            "coautores": vi["coautores"],
            "productos_por_anio": vi["productos_por_anio"],
            "productos_por_categoria": vi["productos_por_categoria"],
            "productos_por_validacion": vi["productos_por_validacion"],
        }

    def serie_anual_por_categoria(
        self,
        filtro: FiltroAnios,
        codigo_grupo: str | None = None,
    ) -> dict[int, dict[str, int]]:
        """Calcula la matriz año × tipología (GNC, DTI, ASC, FRH) desde el hipercubo con rebanada y enrollar."""
        cat = self._catalogo
        if codigo_grupo:
            grp = cat.buscar_grupo(codigo_grupo)
            if grp is None:
                raise RecursoNoEncontrado(f"Grupo {codigo_grupo} no encontrado")
            cubo_base = cat.hipercubo.rebanada(Hipercubo5D.DIM_GRUPO, codigo_grupo)
        else:
            cubo_base = cat.hipercubo

        inicio, fin, modelo = self._rango(filtro)
        cubo_ventana = cat.estadisticas._resolver_cubo(
            cubo=cubo_base,
            modelo_2024=modelo,
            anio_inicio=inicio,
            anio_fin=fin,
        )
        return cat.estadisticas.serie_anual_por_categoria(cubo_ventana)

    def red_coautoria(
        self,
        filtro: FiltroAnios,
        codigo_grupo: str | None = None,
        min_coautorias: int = 2,
    ) -> dict[str, Any]:
        """Calcula el grafo de coautorías y sus métricas topológicas desde la Multilista.

        - Nodos: código, nombre, categoría, grupo principal, grado e intermediación de Brandes.
        - Aristas: origen, destino y productos compartidos (>= min_coautorias).
        - Resumen: investigadores, vínculos y densidad de la red.
        - Si se filtra por grupo, incluye a sus integrantes y a los coautores externos participantes.
        - Todo el cálculo y ordenamiento es determinista.
        """
        cat = self._catalogo
        if codigo_grupo:
            if cat.buscar_grupo(codigo_grupo) is None:
                raise RecursoNoEncontrado(f"Grupo {codigo_grupo} no encontrado")

        candidate_nodes: set[str] = set()
        if codigo_grupo:
            for m in cat.integrantes:
                if m.codigo_gruplac == codigo_grupo:
                    candidate_nodes.add(m.codigo_rh)

        pesos: dict[tuple[str, str], int] = {}
        for nodo in cat.multilista_productos.iterar_nodos():
            prod: Producto = nodo.producto
            if not prod.activo:
                continue
            if not self._producto_en_filtro(prod, filtro):
                continue
            cod_grp = getattr(nodo.grupo, "codigo_gruplac", None)
            if codigo_grupo and cod_grp != codigo_grupo:
                continue

            autores_rh = sorted(
                list({a.codigo_rh for a in nodo.autores if getattr(a, "codigo_rh", None)})
            )
            for a_rh in autores_rh:
                candidate_nodes.add(a_rh)

            if len(autores_rh) >= 2:
                for i in range(len(autores_rh)):
                    for j in range(i + 1, len(autores_rh)):
                        par = (autores_rh[i], autores_rh[j])
                        pesos[par] = pesos.get(par, 0) + 1

        aristas: list[dict[str, Any]] = []
        vecinos: dict[str, set[str]] = {u: set() for u in candidate_nodes}
        for (u, v), peso in sorted(pesos.items()):
            if peso >= min_coautorias:
                aristas.append({"origen": u, "destino": v, "productos_compartidos": peso})
                vecinos[u].add(v)
                vecinos[v].add(u)

        aristas.sort(key=lambda e: (-e["productos_compartidos"], e["origen"], e["destino"]))

        # Algoritmo de Brandes para intermediación (Betweenness Centrality)
        V = sorted(list(candidate_nodes))
        n = len(V)
        cb: dict[str, float] = {v: 0.0 for v in V}
        for s in V:
            S: list[str] = []
            P: dict[str, list[str]] = {w: [] for w in V}
            sigma: dict[str, int] = {w: 0 for w in V}
            sigma[s] = 1
            d: dict[str, int] = {w: -1 for w in V}
            d[s] = 0
            Q: list[str] = [s]
            q_idx = 0
            while q_idx < len(Q):
                v = Q[q_idx]
                q_idx += 1
                S.append(v)
                for w in sorted(vecinos.get(v, set())):
                    if d[w] < 0:
                        d[w] = d[v] + 1
                        Q.append(w)
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)
            delta: dict[str, float] = {w: 0.0 for w in V}
            while S:
                w = S.pop()
                coeff = (1.0 + delta[w]) / sigma[w]
                for v in P[w]:
                    delta[v] += sigma[v] * coeff
                if w != s:
                    cb[w] += delta[w]

        cb = {v: cb[v] / 2.0 for v in V}
        norm_factor = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 0.0
        cb_norm = {v: round(cb[v] * norm_factor, 4) if n > 2 else 0.0 for v in V}

        nodos: list[dict[str, Any]] = []
        for u in V:
            inv = cat.buscar_investigador(u)
            nombre = inv.nombre_completo if inv else u
            cat_inv = inv.categoria if inv and inv.categoria else "Sin categoría"
            mems = [m for m in cat.integrantes if m.codigo_rh == u]
            grp_ppal = self._nombre_grupo(mems[0].codigo_gruplac) if mems else "Sin grupo"
            es_externo = bool(codigo_grupo and not any(m.codigo_gruplac == codigo_grupo for m in mems))
            grado = len(vecinos.get(u, set()))
            nodos.append(
                {
                    "codigo": u,
                    "nombre": nombre,
                    "categoria": cat_inv,
                    "grupo_principal": grp_ppal,
                    "grado": grado,
                    "intermediacion": cb_norm[u],
                    "es_externo": es_externo,
                }
            )

        nodos.sort(key=lambda nd: (-nd["grado"], -nd["intermediacion"], nd["codigo"]))
        densidad = round((2.0 * len(aristas)) / (n * (n - 1)), 4) if n > 1 else 0.0

        return {
            "nodos": tuple(nodos),
            "aristas": tuple(aristas),
            "resumen": {
                "investigadores": n,
                "vinculos": len(aristas),
                "densidad": densidad,
            },
        }

    def tabla_productos(
        self,
        filtro: FiltroAnios | None = None,
        texto: str = "",
        tipo_mayor: str | None = None,
        validacion: str | None = None,
        codigo_grupo: str | None = None,
        codigo_investigador: str | None = None,
        incluir_inactivos: bool = True,
    ) -> TablaDatos:
        filtro = filtro or FiltroAnios()
        texto_bajo = texto.strip().lower()
        filas: list[tuple[Any, ...]] = []
        claves: list[str] = []
        for nodo in self._catalogo.multilista_productos.iterar_nodos():
            prod: Producto = nodo.producto
            if not incluir_inactivos and not prod.activo:
                continue
            if not self._producto_en_filtro(prod, filtro):
                continue
            if tipo_mayor and prod.tipo_mayor != tipo_mayor:
                continue
            if validacion and prod.estado_validacion != validacion:
                continue
            cod_grp = getattr(nodo.grupo, "codigo_gruplac", None)
            if codigo_grupo and cod_grp != codigo_grupo:
                continue
            autores = [a for a in nodo.autores]
            if codigo_investigador and not any(a.codigo_rh == codigo_investigador for a in autores):
                continue
            nombres_autores = ", ".join(a.nombre_completo for a in autores)
            if texto_bajo and texto_bajo not in f"{prod.codigo_identificador} {prod.titulo} {nombres_autores}".lower():
                continue
            filas.append(
                (
                    prod.codigo_identificador,
                    prod.titulo,
                    prod.tipo_mayor,
                    prod.subtipo or "",
                    prod.ano,
                    prod.estado_validacion,
                    getattr(nodo.grupo, "nombre", "") or "Sin grupo",
                    nombres_autores or "Sin autores",
                    "Activo" if prod.activo else "Inactivo",
                )
            )
            claves.append(prod.codigo_identificador)
        return TablaDatos(
            columnas=("Código", "Título", "Tipología", "Subtipo", "Año", "Validación", "Grupo", "Autores", "Estado"),
            filas=tuple(filas),
            claves=tuple(claves),
        )

    def detalle_producto(self, codigo: str) -> dict[str, Any]:
        nodo = self._catalogo.multilista_productos.buscar_nodo(codigo)
        if nodo is None:
            raise RecursoNoEncontrado(f"Producto {codigo} no encontrado")
        prod: Producto = nodo.producto
        return {
            "codigo": prod.codigo_identificador,
            "titulo": prod.titulo,
            "tipo_mayor": prod.tipo_mayor,
            "subtipo": prod.subtipo or "—",
            "ano": prod.ano,
            "validacion": prod.estado_validacion,
            "activo": prod.activo,
            "es_ejemplo": prod.es_ejemplo,
            "grupo": getattr(nodo.grupo, "nombre", None) or "Sin grupo",
            "autores": tuple(f"{a.nombre_completo} ({a.codigo_rh})" for a in nodo.autores),
            "en_ventana_modelo_2024": self._producto_en_filtro(prod, FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)),
        }

    def tabla_grupos(self, texto: str = "") -> TablaDatos:
        cat = self._catalogo
        texto_bajo = texto.strip().lower()
        filas: list[tuple[Any, ...]] = []
        for g in cat.grupos:
            if texto_bajo and texto_bajo not in f"{g.codigo_gruplac} {g.nombre} {g.lider or ''}".lower():
                continue
            n_int = sum(1 for m in cat.integrantes if m.codigo_gruplac == g.codigo_gruplac)
            n_prod = sum(1 for p in cat.multilista_productos.obtener_productos_grupo(g.codigo_gruplac) if p.activo)
            filas.append(
                (
                    g.codigo_gruplac,
                    g.nombre,
                    g.categoria or "",
                    g.lider or "",
                    n_int,
                    n_prod,
                    "Activo" if g.activo else "Inactivo",
                )
            )
        return TablaDatos(
            columnas=("Código", "Nombre", "Categoría", "Líder", "Integrantes", "Productos activos", "Estado"),
            filas=tuple(filas),
            claves=tuple(str(f[0]) for f in filas),
        )

    def tabla_investigadores(self, texto: str = "") -> TablaDatos:
        cat = self._catalogo
        texto_bajo = texto.strip().lower()
        filas: list[tuple[Any, ...]] = []
        for i in cat.investigadores:
            if texto_bajo and texto_bajo not in f"{i.codigo_rh} {i.nombre_completo}".lower():
                continue
            grupos = ", ".join(m.codigo_gruplac for m in cat.integrantes if m.codigo_rh == i.codigo_rh)
            n_prod = sum(1 for p in cat.multilista_productos.obtener_productos_investigador(i.codigo_rh) if p.activo)
            filas.append(
                (
                    i.codigo_rh,
                    i.nombre_completo,
                    i.categoria or "",
                    i.formacion_academica or "",
                    grupos,
                    n_prod,
                    "Activo" if i.activo else "Inactivo",
                )
            )
        return TablaDatos(
            columnas=("Código", "Nombre", "Categoría", "Formación", "Grupos", "Productos activos", "Estado"),
            filas=tuple(filas),
            claves=tuple(str(f[0]) for f in filas),
        )

    def datos_grupo(self, codigo: str) -> dict[str, Any]:
        g = self._catalogo.buscar_grupo(codigo)
        if g is None:
            raise RecursoNoEncontrado(f"Grupo {codigo} no encontrado")
        return g.model_dump(exclude={"id"})

    def datos_investigador(self, codigo: str) -> dict[str, Any]:
        i = self._catalogo.buscar_investigador(codigo)
        if i is None:
            raise RecursoNoEncontrado(f"Investigador {codigo} no encontrado")
        return i.model_dump(exclude={"id"})

    # =========================================================================
    # IMPORTACIÓN (COLA PROPIA)
    # =========================================================================

    def _persistir_importacion(self) -> bool:
        self._exigir_escritura()
        return self._modo == ModoConexion.SUPABASE

    def encolar_csv(self, ruta: str | Path, tipo: str | None = None) -> str:
        persistir = self._persistir_importacion()
        tarea = self._ingesta.encolar_csv(ruta, tipo_entidad=tipo or None, persistir=persistir)
        return f"Tarea {tarea.id_tarea} encolada ({tarea.tipo_fuente})."

    def encolar_pdf(self, ruta: str | Path) -> str:
        tarea = self._ingesta.encolar_pdf(ruta, salida_dir=self._directorio_salida / "pdf")
        return f"Tarea {tarea.id_tarea} encolada (PDF)."

    def encolar_url(self, url: str) -> str:
        persistir = self._persistir_importacion()
        tarea = self._ingesta.encolar_url(
            url.strip(),
            persistir=persistir,
            es_privado=True,  # las páginas de SCIENTI contienen datos personales
            salida_dir=self._directorio_salida / "extraccion",
        )
        return f"Tarea {tarea.id_tarea} encolada ({tarea.tipo_fuente})."

    def procesar_siguiente_tarea(self) -> dict[str, Any] | None:
        """Procesa la tarea del frente de la cola y la pasa al historial."""
        tarea = self._ingesta.cola_tareas.ver_frente()
        if tarea is None:
            return None
        informe = self._ingesta.procesar_siguiente()
        self._historial_ingesta.insertar_final(tarea)
        self._catalogo.sincronizar_hipercubo()
        if informe is None:
            return None
        return {
            "id_tarea": tarea.id_tarea,
            "exito": informe.exito and tarea.estado == EstadoTarea.TERMINADA,
            "mensaje": informe.mensaje or tarea.mensaje_error or "",
            "grupos": informe.grupos_procesados,
            "investigadores": informe.investigadores_procesados,
            "productos": informe.productos_procesados,
            "autores": informe.autores_procesados,
            "filas_erroneas": len(informe.filas_erroneas),
            "advertencias": tuple(informe.advertencias),
        }

    def tareas_pendientes(self) -> int:
        return len(self._ingesta.cola_tareas)

    def tabla_cola(self) -> TablaDatos:
        filas: list[tuple[Any, ...]] = []

        def fila(t: TareaIngesta) -> tuple[Any, ...]:
            return (
                t.id_tarea,
                t.tipo_fuente,
                Path(t.origen).name if not t.origen.startswith("http") else t.origen,
                _ETIQUETA_ESTADO_TAREA.get(t.estado, str(t.estado)),
                t.elementos_procesados,
                t.mensaje_error or "",
            )

        for t in self._historial_ingesta:
            filas.append(fila(t))
        for t in self._ingesta.cola_tareas:
            filas.append(fila(t))
        return TablaDatos(
            columnas=("Tarea", "Tipo", "Origen", "Estado", "Elementos", "Mensaje"),
            filas=tuple(filas),
            claves=tuple(str(f[0]) for f in filas),
        )

    # =========================================================================
    # EXPORTACIÓN, VERIFICACIÓN CRUZADA E INFORMACIÓN
    # =========================================================================

    @staticmethod
    def exportar_tabla_csv(tabla: TablaDatos, ruta: str | Path) -> str:
        destino = ServicioExportacion.exportar_tabla_csv(tabla, ruta)
        return str(destino)

    def ejecutar_verificacion_cruzada(self, usar_base: bool = False) -> ResultadoVerificacionCruzada:
        return self._verificacion.ejecutar(usar_base=usar_base)

    @staticmethod
    def informacion_proyecto() -> dict[str, str]:
        return {
            "nombre": APP_NAME,
            "version": APP_VERSION,
            "institucion": INSTITUCION,
            "python": platform.python_version(),
            "plataforma": f"{platform.system()} {platform.release()}",
        }
