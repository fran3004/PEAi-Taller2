"""Repositorios especializados para persistencia REST y RPC en Supabase."""

from typing import Any

from pea.cliente_http import ClienteHTTPSupabase
from pea.dominio.grupo import Grupo
from pea.dominio.integrante import IntegranteGrupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.dominio.proyecto import Proyecto


class RepositorioGrupos:
    """Acceso a datos de Grupos de Investigación."""

    def __init__(self, cliente: ClienteHTTPSupabase) -> None:
        self.cliente = cliente

    def listar(self, es_ejemplo: bool | None = None) -> list[Grupo]:
        params: dict[str, Any] = {"select": "*"}
        if es_ejemplo is not None:
            params["es_ejemplo"] = f"eq.{str(es_ejemplo).lower()}"
        filas = self.cliente.get_paginado("grupos", params=params)
        return [Grupo.model_validate(f) for f in filas]

    def obtener_por_codigo(self, codigo_gruplac: str) -> Grupo | None:
        filas = self.cliente.get("grupos", params={"codigo_gruplac": f"eq.{codigo_gruplac}", "select": "*"})
        if isinstance(filas, list) and len(filas) > 0:
            return Grupo.model_validate(filas[0])
        return None

    def crear(self, grupo: Grupo) -> Grupo:
        datos = grupo.model_dump(exclude={"id"}, exclude_none=True)
        res = self.cliente.post("grupos", datos)
        if isinstance(res, list) and len(res) > 0:
            return Grupo.model_validate(res[0])
        return grupo

    def actualizar(self, codigo_gruplac: str, datos: dict[str, Any]) -> Grupo:
        res = self.cliente.patch("grupos", datos, params={"codigo_gruplac": f"eq.{codigo_gruplac}"})
        if isinstance(res, list) and len(res) > 0:
            return Grupo.model_validate(res[0])
        g = self.obtener_por_codigo(codigo_gruplac)
        if g is None:
            raise ValueError(f"Grupo con código {codigo_gruplac} no encontrado tras actualizar")
        return g

    def desactivar(self, id_grupo: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_desactivar_nodo",
            {"p_tipo": "grupo", "p_id": id_grupo, "p_revision_esperada": revision_esperada},
        )

    def eliminar(self, id_grupo: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_eliminar_cascada",
            {"p_tipo": "grupo", "p_id": id_grupo, "p_revision_esperada": revision_esperada},
        )


class RepositorioInvestigadores:
    """Acceso a datos de Investigadores."""

    def __init__(self, cliente: ClienteHTTPSupabase) -> None:
        self.cliente = cliente

    def listar(self, es_ejemplo: bool | None = None) -> list[Investigador]:
        params: dict[str, Any] = {"select": "*"}
        if es_ejemplo is not None:
            params["es_ejemplo"] = f"eq.{str(es_ejemplo).lower()}"
        filas = self.cliente.get_paginado("investigadores", params=params)
        return [Investigador.model_validate(f) for f in filas]

    def obtener_por_codigo(self, codigo_rh: str) -> Investigador | None:
        filas = self.cliente.get("investigadores", params={"codigo_rh": f"eq.{codigo_rh}", "select": "*"})
        if isinstance(filas, list) and len(filas) > 0:
            return Investigador.model_validate(filas[0])
        return None

    def crear(self, investigador: Investigador) -> Investigador:
        datos = investigador.model_dump(exclude={"id"}, exclude_none=True)
        res = self.cliente.post("investigadores", datos)
        if isinstance(res, list) and len(res) > 0:
            return Investigador.model_validate(res[0])
        return investigador

    def actualizar(self, codigo_rh: str, datos: dict[str, Any]) -> Investigador:
        res = self.cliente.patch("investigadores", datos, params={"codigo_rh": f"eq.{codigo_rh}"})
        if isinstance(res, list) and len(res) > 0:
            return Investigador.model_validate(res[0])
        inv = self.obtener_por_codigo(codigo_rh)
        if inv is None:
            raise ValueError(f"Investigador con código {codigo_rh} no encontrado tras actualizar")
        return inv

    def desactivar(self, id_investigador: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_desactivar_nodo",
            {"p_tipo": "investigador", "p_id": id_investigador, "p_revision_esperada": revision_esperada},
        )

    def eliminar(self, id_investigador: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_eliminar_cascada",
            {"p_tipo": "investigador", "p_id": id_investigador, "p_revision_esperada": revision_esperada},
        )


class RepositorioIntegrantes:
    """Acceso a membresías de grupos."""

    def __init__(self, cliente: ClienteHTTPSupabase) -> None:
        self.cliente = cliente

    def listar(self, codigo_gruplac: str | None = None) -> list[IntegranteGrupo]:
        params: dict[str, Any] = {"select": "*"}
        if codigo_gruplac is not None:
            params["codigo_gruplac"] = f"eq.{codigo_gruplac}"
        filas = self.cliente.get_paginado("integrantes_grupo", params=params)
        return [IntegranteGrupo.model_validate(f) for f in filas]

    def vincular(self, integrante: IntegranteGrupo) -> IntegranteGrupo:
        datos = integrante.model_dump(exclude={"id"}, exclude_none=True)
        res = self.cliente.post("integrantes_grupo", datos)
        if isinstance(res, list) and len(res) > 0:
            return IntegranteGrupo.model_validate(res[0])
        return integrante

    def desvincular(self, codigo_gruplac: str, codigo_rh: str) -> None:
        self.cliente.eliminar(
            "integrantes_grupo",
            params={"codigo_gruplac": f"eq.{codigo_gruplac}", "codigo_rh": f"eq.{codigo_rh}"},
        )


class RepositorioProductos:
    """Acceso a datos de Productos y sus relaciones."""

    def __init__(self, cliente: ClienteHTTPSupabase) -> None:
        self.cliente = cliente

    def listar(self, es_ejemplo: bool | None = None) -> list[Producto]:
        params: dict[str, Any] = {"select": "*"}
        if es_ejemplo is not None:
            params["es_ejemplo"] = f"eq.{str(es_ejemplo).lower()}"
        filas = self.cliente.get_paginado("productos", params=params)
        return [Producto.model_validate(f) for f in filas]

    def obtener_por_codigo(self, codigo_identificador: str) -> Producto | None:
        filas = self.cliente.get(
            "productos",
            params={"codigo_identificador": f"eq.{codigo_identificador}", "select": "*"},
        )
        if isinstance(filas, list) and len(filas) > 0:
            return Producto.model_validate(filas[0])
        return None

    def crear_con_rpc(
        self,
        producto: Producto,
        grupo_id: int | None,
        investigadores_ids: list[int],
        revision_esperada: int,
    ) -> int:
        """Crea el producto atómicamente con grupo y autores mediante RPC."""
        params = {
            "p_codigo_identificador": producto.codigo_identificador,
            "p_titulo": producto.titulo,
            "p_tipo_mayor": producto.tipo_mayor,
            "p_subtipo": producto.subtipo,
            "p_ano": producto.ano,
            "p_mes": producto.mes,
            "p_pais": producto.pais,
            "p_estado_validacion": producto.estado_validacion,
            "p_detalles": producto.detalles,
            "p_es_ejemplo": producto.es_ejemplo,
            "p_grupo_id": grupo_id,
            "p_investigadores_ids": investigadores_ids,
            "p_revision_esperada": revision_esperada,
        }
        res = self.cliente.rpc("transaccion_crear_producto", params)
        if isinstance(res, dict) and "producto_id" in res:
            return int(res["producto_id"])
        return 0

    def crear_directo(self, producto: Producto) -> Producto:
        datos = producto.model_dump(exclude={"id"}, exclude_none=True)
        res = self.cliente.post("productos", datos)
        if isinstance(res, list) and len(res) > 0:
            return Producto.model_validate(res[0])
        return producto

    def asociar_grupo(self, producto_id: int, grupo_id: int, es_ejemplo: bool = False) -> None:
        self.cliente.post(
            "producto_grupos",
            {"producto_id": producto_id, "grupo_id": grupo_id, "activo": True, "es_ejemplo": es_ejemplo},
        )

    def asociar_autor(
        self,
        producto_id: int,
        investigador_id: int,
        orden: int = 1,
        es_ejemplo: bool = False,
    ) -> None:
        self.cliente.post(
            "producto_autores",
            {
                "producto_id": producto_id,
                "investigador_id": investigador_id,
                "orden_autoria": orden,
                "activo": True,
                "es_ejemplo": es_ejemplo,
            },
        )

    def listar_relaciones_grupos(self) -> list[dict[str, Any]]:
        return self.cliente.get_paginado("producto_grupos", params={"select": "*"})

    def listar_relaciones_autores(self) -> list[dict[str, Any]]:
        return self.cliente.get_paginado("producto_autores", params={"select": "*"})

    def desactivar(self, id_producto: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_desactivar_nodo",
            {"p_tipo": "producto", "p_id": id_producto, "p_revision_esperada": revision_esperada},
        )

    def eliminar_cascada(self, id_producto: int, revision_esperada: int) -> None:
        self.cliente.rpc(
            "transaccion_eliminar_cascada",
            {"p_tipo": "producto", "p_id": id_producto, "p_revision_esperada": revision_esperada},
        )


class RepositorioProyectos:
    """Acceso a datos de Proyectos."""

    def __init__(self, cliente: ClienteHTTPSupabase) -> None:
        self.cliente = cliente

    def listar(self, codigo_gruplac: str | None = None) -> list[Proyecto]:
        params: dict[str, Any] = {"select": "*"}
        if codigo_gruplac is not None:
            params["codigo_gruplac"] = f"eq.{codigo_gruplac}"
        filas = self.cliente.get_paginado("proyectos", params=params)
        return [Proyecto.model_validate(f) for f in filas]

    def crear(self, proyecto: Proyecto) -> Proyecto:
        datos = proyecto.model_dump(exclude={"id"}, exclude_none=True)
        res = self.cliente.post("proyectos", datos)
        if isinstance(res, list) and len(res) > 0:
            return Proyecto.model_validate(res[0])
        return proyecto
