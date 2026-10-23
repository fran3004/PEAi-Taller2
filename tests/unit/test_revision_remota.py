"""ControladorRevision.consultar_remota: RPC, respaldo en meta y fallo explícito.

Contrato equivalente a cpp/src/datos/revision.cpp: solo se aceptan revisiones mayores
que cero y, si ni la RPC ni la tabla meta entregan una válida, se lanza ErrorConexion.
"""

from __future__ import annotations

from typing import Any

import pytest

from pea.datos.revision import ControladorRevision
from pea.excepciones import ConflictoRevision, ErrorConexion, ErrorServidor


class _Fallo:
    """Marca una respuesta que debe lanzarse en vez de devolverse."""

    def __init__(self, error: Exception) -> None:
        self.error = error


class ClienteFalso:
    """Cliente mínimo con rpc() y get(); no hace red."""

    def __init__(self, rpc: Any, meta: Any) -> None:
        self._rpc = rpc
        self._meta = meta
        self.llamadas: list[str] = []

    def rpc(self, funcion: str, params: dict[str, Any] | None = None) -> Any:
        self.llamadas.append(f"rpc:{funcion}")
        if isinstance(self._rpc, _Fallo):
            raise self._rpc.error
        return self._rpc

    def get(self, tabla: str, params: dict[str, Any] | None = None) -> Any:
        self.llamadas.append(f"get:{tabla}")
        if isinstance(self._meta, _Fallo):
            raise self._meta.error
        return self._meta


_RED_CAIDA = ErrorConexion("Fallo en la conexión de red HTTPS con Supabase", "host inexistente")


# (a) ---------------------------------------------------------------------
@pytest.mark.parametrize("respuesta_rpc", [7, {"revision": 7}])
def test_rpc_correcta_devuelve_su_valor_sin_consultar_meta(respuesta_rpc: Any) -> None:
    cliente = ClienteFalso(rpc=respuesta_rpc, meta=_Fallo(_RED_CAIDA))
    controlador = ControladorRevision(revision_inicial=3)

    assert controlador.consultar_remota(cliente) == 7  # type: ignore[arg-type]
    assert cliente.llamadas == ["rpc:obtener_revision_actual"]
    assert controlador.revision_local == 3


# (b) ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "respuesta_rpc",
    [_Fallo(_RED_CAIDA), _Fallo(ErrorServidor("Error 500")), None, 0, -1, True, "basura"],
)
def test_rpc_fallida_o_invalida_usa_la_tabla_meta(respuesta_rpc: Any) -> None:
    cliente = ClienteFalso(rpc=respuesta_rpc, meta=[{"revision": 9}])
    controlador = ControladorRevision(revision_inicial=3)

    assert controlador.consultar_remota(cliente) == 9  # type: ignore[arg-type]
    assert cliente.llamadas == ["rpc:obtener_revision_actual", "get:meta"]


# (c) ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "fallo_meta",
    [_Fallo(_RED_CAIDA), _Fallo(ErrorServidor("Error 500 en meta")), _Fallo(RuntimeError("inesperado"))],
)
def test_rpc_y_meta_fallan_lanza_error_conexion_con_ambos_detalles(fallo_meta: _Fallo) -> None:
    cliente = ClienteFalso(rpc=_Fallo(ErrorServidor("RPC caída")), meta=fallo_meta)
    controlador = ControladorRevision(revision_inicial=3)

    with pytest.raises(ErrorConexion) as info:
        controlador.consultar_remota(cliente)  # type: ignore[arg-type]

    texto = info.value.mensaje
    assert texto.startswith("No fue posible verificar la revisión remota. RPC: ")
    assert "RPC caída" in texto
    assert " Consulta meta: " in texto
    assert str(fallo_meta.error) in texto
    assert controlador.revision_local == 3


# (d) ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "respuesta_meta",
    [[], [{}], [{"revision": 0}], [{"revision": -4}], [{"revision": None}], [{"revision": True}], {}, None],
)
def test_meta_vacia_o_revision_no_valida_lanza_error_conexion(respuesta_meta: Any) -> None:
    cliente = ClienteFalso(rpc=_Fallo(_RED_CAIDA), meta=respuesta_meta)
    controlador = ControladorRevision(revision_inicial=3)

    with pytest.raises(ErrorConexion) as info:
        controlador.consultar_remota(cliente)  # type: ignore[arg-type]

    assert "La tabla meta no devolvió una revisión válida." in info.value.mensaje
    assert controlador.revision_local == 3


def test_verificar_consistencia_no_da_por_sincronizado_lo_que_no_pudo_comprobar() -> None:
    cliente = ClienteFalso(rpc=_Fallo(_RED_CAIDA), meta=[])
    controlador = ControladorRevision(revision_inicial=1)

    with pytest.raises(ErrorConexion):
        controlador.verificar_consistencia(cliente)  # type: ignore[arg-type]


def test_verificar_consistencia_sigue_detectando_cambios() -> None:
    cliente = ClienteFalso(rpc=6, meta=_Fallo(_RED_CAIDA))
    controlador = ControladorRevision(revision_inicial=5)

    with pytest.raises(ConflictoRevision):
        controlador.verificar_consistencia(cliente)  # type: ignore[arg-type]


def test_sincronizar_conserva_la_revision_local_si_no_puede_comprobar() -> None:
    cliente = ClienteFalso(rpc=_Fallo(_RED_CAIDA), meta=[{"revision": 0}])
    controlador = ControladorRevision(revision_inicial=4)

    with pytest.raises(ErrorConexion):
        controlador.sincronizar(cliente)  # type: ignore[arg-type]
    assert controlador.revision_local == 4

    cliente_ok = ClienteFalso(rpc=11, meta=[])
    assert controlador.sincronizar(cliente_ok) == 11  # type: ignore[arg-type]
    assert controlador.revision_local == 11

