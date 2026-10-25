"""Límites de escritura del comprobador remoto, sin acceso a la red."""

from unittest.mock import patch

import pytest

from pea.cliente_http import ClienteHTTPSupabase
from tools.db.verificar_autores_remoto import ClienteSintetico, error_seguro, limpiar


@pytest.fixture
def escenario():
    return {"lenguaje": "python", "codigo_p": "PRUEBA-X-P", "codigo_i": "PRUEBA-X-I",
            "producto": {"id": 11}, "investigador": {"id": 21}}


@pytest.mark.parametrize("metodo,tabla,datos,filtro", [
    ("POST", "productos", {"codigo_identificador": "REAL", "es_ejemplo": True}, None),
    ("POST", "productos", {"codigo_identificador": "PRUEBA-X-P", "es_ejemplo": False}, None),
    ("POST", "producto_autores", {"producto_id": 11, "investigador_id": 999, "es_ejemplo": True}, None),
    ("DELETE", "producto_autores", None, {"producto_id": "eq.11", "es_ejemplo": "eq.true"}),
    ("DELETE", "productos", None, {"es_ejemplo": "eq.true"}),
    ("PATCH", "productos", {"activo": False}, {"codigo_identificador": "eq.PRUEBA-X-P"}),
    ("POST", "rpc/reiniciar_datos_prueba", {}, None),
])
def test_rechaza_escrituras_fuera_del_fixture(escenario, metodo, tabla, datos, filtro):
    cliente = ClienteSintetico("https://prueba.supabase.co", "publica", [escenario])
    with patch.object(ClienteHTTPSupabase, "_ejecutar") as remoto:
        with pytest.raises(RuntimeError, match="bloqueada"):
            cliente._ejecutar(metodo, f"rest/v1/{tabla}", json_data=datos, params=filtro)
        remoto.assert_not_called()


def test_admite_solo_el_par_sintetico_exacto(escenario):
    cliente = ClienteSintetico("https://prueba.supabase.co", "publica", [escenario])
    with patch.object(ClienteHTTPSupabase, "_ejecutar") as remoto:
        cliente.post("producto_autores", {"producto_id": 11, "investigador_id": 21, "es_ejemplo": True})
        remoto.assert_called_once()


def test_colision_no_habilita_limpieza(escenario):
    cliente = ClienteSintetico("https://prueba.supabase.co", "publica", [escenario])
    with patch.object(cliente, "get") as consulta, patch.object(cliente, "eliminar") as borrar:
        limpiar(cliente, [escenario], [])
        consulta.assert_not_called()
        borrar.assert_not_called()


def test_limpieza_encuentra_producto_aunque_se_perdiera_respuesta_post(escenario):
    escenario.update(escritura_iniciada=True, producto=None, investigador=None)
    cliente = ClienteSintetico("https://prueba.supabase.co", "publica", [escenario])
    producto = {"id": 11, "codigo_identificador": escenario["codigo_p"], "es_ejemplo": True}
    errores = []
    # Lecturas iniciales de padres; comprobación previa al DELETE; ausencia final de ambos.
    with patch.object(cliente, "get", side_effect=[[producto], [], [producto], [], [], []]), \
         patch.object(cliente, "eliminar") as borrar:
        limpiar(cliente, [escenario], errores)
    assert not errores
    assert escenario["limpieza"] is True
    borrar.assert_called_once_with("productos", {
        "codigo_identificador": "eq.PRUEBA-X-P", "es_ejemplo": "eq.true"})


def test_fallo_de_limpieza_queda_reportado(escenario):
    escenario["escritura_iniciada"] = True
    cliente = ClienteSintetico("https://prueba.supabase.co", "publica", [escenario])
    errores = []
    with patch.object(cliente, "get", side_effect=ConnectionError("No imprimir detalle sensible")):
        limpiar(cliente, [escenario], errores)
    assert errores == [{"etapa": "limpieza_python", "tipo": "ConnectionError", "codigo_postgres": None}]
    assert not escenario.get("limpieza")


def test_diagnostico_no_incluye_secretos():
    from pea.excepciones import ErrorPEA

    error = ErrorPEA("token=SECRETO", {"code": "23502", "details": "clave=SECRETA"})
    assert error_seguro(error, "fixture") == {"etapa": "fixture", "tipo": "ErrorPEA", "codigo_postgres": "23502"}
