"""Pruebas unitarias para el cliente HTTPS de Supabase en Python."""

import pytest
import requests
import responses

from pea.cliente_http import ClienteHTTPSupabase
from pea.excepciones import (
    ConflictoRevision,
    ErrorAutenticacion,
    ErrorAutorizacion,
    ErrorConexion,
    ErrorServidor,
    ErrorValidacion,
    RecursoNoEncontrado,
)


@pytest.fixture
def cliente() -> ClienteHTTPSupabase:
    return ClienteHTTPSupabase("https://ejemplo.supabase.co", "anon-key-123", timeout=2.0)


def test_cliente_configuracion_y_tokens(cliente: ClienteHTTPSupabase) -> None:
    assert cliente.base_url == "https://ejemplo.supabase.co"
    assert cliente.anon_key == "anon-key-123"
    assert cliente.token_acceso is None

    # Almacenar token en memoria volátil
    cliente.establecer_token_acceso("jwt-token-sesion")
    assert cliente.token_acceso == "jwt-token-sesion"

    # Limpieza de token
    cliente.cerrar_sesion()
    assert cliente.token_acceso is None


@responses.activate
def test_cliente_get_exitoso(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/grupos",
        json=[{"id": 1, "nombre": "Grupo Test"}],
        status=200,
    )

    datos = cliente.get("grupos")
    assert isinstance(datos, list)
    assert len(datos) == 1
    assert datos[0]["nombre"] == "Grupo Test"


@responses.activate
def test_cliente_post_exitoso(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/grupos",
        json=[{"id": 1, "nombre": "Nuevo Grupo"}],
        status=201,
    )

    datos = cliente.post("grupos", {"nombre": "Nuevo Grupo"})
    assert datos[0]["id"] == 1


@responses.activate
def test_cliente_patch_exitoso(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.PATCH,
        "https://ejemplo.supabase.co/rest/v1/grupos?id=eq.1",
        json=[{"id": 1, "nombre": "Grupo Actualizado"}],
        status=200,
    )

    datos = cliente.patch("grupos", {"nombre": "Grupo Actualizado"}, {"id": "eq.1"})
    assert datos[0]["nombre"] == "Grupo Actualizado"


@responses.activate
def test_cliente_eliminar_exitoso(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.DELETE,
        "https://ejemplo.supabase.co/rest/v1/grupos?id=eq.1",
        status=204,
    )

    cliente.eliminar("grupos", {"id": "eq.1"})


@responses.activate
def test_cliente_rpc_exitoso(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.POST,
        "https://ejemplo.supabase.co/rest/v1/rpc/obtener_revision",
        json={"revision": 42},
        status=200,
    )

    datos = cliente.rpc("obtener_revision")
    assert datos["revision"] == 42


@responses.activate
def test_cliente_get_paginado(cliente: ClienteHTTPSupabase) -> None:
    # Simula 2 páginas de 2 elementos
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/grupos",
        json=[{"id": 1}, {"id": 2}],
        status=200,
    )
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/grupos",
        json=[{"id": 3}],
        status=200,
    )

    resultado = cliente.get_paginado("grupos", lote_tamano=2)
    assert len(resultado) == 3
    assert [r["id"] for r in resultado] == [1, 2, 3]


@responses.activate
def test_cliente_mapeo_errores_tipados(cliente: ClienteHTTPSupabase) -> None:
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t401", status=401, json={"error": "no auth"})
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t403", status=403, json={"error": "forbidden"})
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t404", status=404, json={"error": "not found"})
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t409", status=409, json={"error": "conflict"})
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t422", status=422, json={"error": "unprocessable"})
    responses.add(responses.GET, "https://ejemplo.supabase.co/rest/v1/t500", status=500, json={"error": "server error"})

    with pytest.raises(ErrorAutenticacion):
        cliente.get("t401")

    with pytest.raises(ErrorAutorizacion):
        cliente.get("t403")

    with pytest.raises(RecursoNoEncontrado):
        cliente.get("t404")

    with pytest.raises(ConflictoRevision):
        cliente.get("t409")

    with pytest.raises(ErrorValidacion):
        cliente.get("t422")

    with pytest.raises(ErrorServidor):
        cliente.get("t500")


@responses.activate
def test_cliente_error_conexion(cliente: ClienteHTTPSupabase) -> None:
    responses.add(
        responses.GET,
        "https://ejemplo.supabase.co/rest/v1/timeout",
        body=requests.exceptions.ConnectionError("Fallo red"),
    )

    with pytest.raises(ErrorConexion):
        cliente.get("timeout")
