"""Pruebas de resiliencia: persistencia fallida, sesión expirada, revisión cambiada y paginación."""

import pytest
import requests
import responses

from pea.cliente_http import ClienteHTTPSupabase
from pea.datos.revision import ControladorRevision
from pea.datos.sesion import Sesion
from pea.dominio.grupo import Grupo
from pea.dominio.producto import Producto
from pea.excepciones import ConflictoRevision, ErrorAutenticacion, ErrorConexion, ErrorPEA
from pea.servicios.servicio_dominio import CatalogoInvestigacion


@responses.activate
def test_compensacion_persistencia_fallida_grupo() -> None:
    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")
    catalogo = CatalogoInvestigacion(cliente=cliente)

    # Simular RPC de revisión OK
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/obtener_revision_actual",
        json=1,
        status=200,
    )
    # Simular fallo de conexión al intentar insertar grupo
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/grupos",
        body=requests.exceptions.ConnectionError("Corte de red intempestivo"),
    )

    grupo = Grupo(codigo_gruplac="GRP-FAIL-01", nombre="Grupo Falla")

    # Al fallar la persistencia, debe lanzar ErrorConexion y compensar en memoria
    with pytest.raises(ErrorConexion):
        catalogo.crear_grupo(grupo, persistir=True)

    # La estructura en memoria debe haber sido revertida limpiamente
    assert len(catalogo.grupos) == 0
    assert catalogo.buscar_grupo("GRP-FAIL-01") is None


@responses.activate
def test_compensacion_persistencia_fallida_producto() -> None:
    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")
    catalogo = CatalogoInvestigacion(cliente=cliente)

    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/obtener_revision_actual",
        json=1,
        status=200,
    )
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/transaccion_crear_producto",
        status=500,
        json={"error": "Fallo interno en base de datos"},
    )

    prod = Producto(
        codigo_identificador="P-FAIL-01",
        titulo="Producto Fallido",
        tipo_mayor="GNC",
        ano=2024,
    )

    with pytest.raises(ErrorPEA):
        catalogo.crear_producto(prod, persistir=True)

    # Reversión de la Multilista en memoria
    assert len(catalogo.multilista_productos) == 0
    assert catalogo.buscar_producto("P-FAIL-01") is None


def test_sesion_expirada_bloquea_operacion() -> None:
    sesion = Sesion()
    sesion.iniciar_sesion("token-jwt-prueba", "usuario@upc.edu.co", tiempo_expiracion_segundos=3600.0)
    assert sesion.esta_autenticado()

    # Simular que el tiempo expiró
    sesion.simular_expiracion()
    assert sesion.esta_expirada()

    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")
    catalogo = CatalogoInvestigacion(cliente=cliente, sesion=sesion)

    grupo = Grupo(codigo_gruplac="GRP-EXP-01", nombre="Grupo Sesion Expirada")

    with pytest.raises(ErrorAutenticacion):
        catalogo.crear_grupo(grupo, persistir=True)

    # No se aplicó ninguna mutación en memoria
    assert len(catalogo.grupos) == 0


@responses.activate
def test_revision_cambiada_conflicto_concurrencia() -> None:
    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")
    controlador = ControladorRevision(revision_inicial=5)

    # Supongamos que otro usuario modificó la base y la revisión remota subió a 6
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/obtener_revision_actual",
        json=6,
        status=200,
    )

    with pytest.raises(ConflictoRevision) as exc_info:
        controlador.verificar_consistencia(cliente)

    assert "La base de datos cambió" in str(exc_info.value)


@responses.activate
def test_paginacion_multiples_lotes() -> None:
    cliente = ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key")

    # Simular 3 lotes de 2 elementos
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/investigadores",
        json=[{"codigo_rh": "RH-1", "nombre_completo": "Inv 1"}, {"codigo_rh": "RH-2", "nombre_completo": "Inv 2"}],
        status=200,
    )
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/investigadores",
        json=[{"codigo_rh": "RH-3", "nombre_completo": "Inv 3"}, {"codigo_rh": "RH-4", "nombre_completo": "Inv 4"}],
        status=200,
    )
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/investigadores",
        json=[{"codigo_rh": "RH-5", "nombre_completo": "Inv 5"}],
        status=200,
    )

    filas = cliente.get_paginado("investigadores", lote_tamano=2)
    assert len(filas) == 5
    assert [f["codigo_rh"] for f in filas] == ["RH-1", "RH-2", "RH-3", "RH-4", "RH-5"]
