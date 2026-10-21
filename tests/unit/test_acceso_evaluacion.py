"""Contrato de arranque portable y sesion automatica, sin red."""

import json
import sys

import pytest
import responses

from pea.cliente_http import ClienteHTTPSupabase
from pea.datos.configuracion_portable import leer_configuracion_portable
from pea.datos.sesion import Sesion
from pea.dominio.grupo import Grupo
from pea.excepciones import ErrorAutenticacion, ErrorValidacion
from pea.servicios.servicio_dominio import CatalogoInvestigacion

URL = "https://wdmchsncexayqbjueamb.supabase.co"


@pytest.fixture
def configuracion(tmp_path, monkeypatch):
    ejecutable = tmp_path / "PEAi-Python/pea-gui.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(ejecutable))
    monkeypatch.delenv("PEA_OMITIR_CONFIG_PUBLICA", raising=False)
    ruta = tmp_path / "config/pea.config.json"
    ruta.parent.mkdir()
    ruta.write_text(json.dumps({
        "url": URL, "clave_publishable": "sb_publishable_ficticia", "acceso_evaluacion": True,
    }), encoding="utf-8")
    return ruta


def test_configuracion_portable_no_depende_del_directorio_actual(configuracion, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path.parent)
    assert leer_configuracion_portable()["url"] == URL


def test_comprobaciones_sin_red_omiten_configuracion(configuracion, monkeypatch):
    monkeypatch.setenv("PEA_OMITIR_CONFIG_PUBLICA", "1")
    assert leer_configuracion_portable() == {}


def test_rechaza_credenciales_agregadas_al_json(configuracion):
    datos = json.loads(configuracion.read_text())
    datos["password"] = "ficticia"
    configuracion.write_text(json.dumps(datos))
    with pytest.raises(ErrorValidacion):
        leer_configuracion_portable()


@responses.activate
def test_sesion_automatica_sin_correo_contrasena_ni_bearer_publicable():
    responses.post(URL + "/auth/v1/signup", json={
        "access_token": "jwt-ficticio", "expires_in": 3600, "user": {"is_anonymous": True},
    })
    cliente = ClienteHTTPSupabase(URL, "sb_publishable_ficticia")
    cuerpo = cliente.autenticar_evaluacion()
    assert json.loads(responses.calls[0].request.body) == {}
    assert "Authorization" not in responses.calls[0].request.headers
    assert cliente.token_acceso == "jwt-ficticio"
    sesion = Sesion()
    sesion.iniciar_sesion(cuerpo["access_token"], "Evaluación", metadatos=cuerpo["user"])
    assert sesion.es_evaluacion
    sesion.cerrar_sesion()
    assert not sesion.es_evaluacion


@responses.activate
def test_rechaza_respuesta_sin_sesion_de_evaluacion():
    responses.post(URL + "/auth/v1/signup", json={"access_token": "ficticio", "user": {}})
    with pytest.raises(ErrorAutenticacion):
        ClienteHTTPSupabase(URL, "sb_publishable_ficticia").autenticar_evaluacion()


def test_catalogo_no_altera_los_datos_creados_en_la_sesion_academica():
    sesion = Sesion()
    sesion.iniciar_sesion("ficticio", "Evaluación", metadatos={"is_anonymous": True})
    catalogo = CatalogoInvestigacion(sesion=sesion)
    grupo = Grupo(codigo_gruplac="GRUPO-NUEVO", nombre="PRUEBA-Grupo", categoria="C")
    catalogo.crear_grupo(grupo)
    assert grupo.codigo_gruplac == "GRUPO-NUEVO"
    assert not grupo.es_ejemplo
    assert catalogo.buscar_grupo("GRUPO-NUEVO") is grupo


@responses.activate
def test_renovacion_automatica_conserva_tokens_solo_en_memoria():
    responses.post(URL + "/auth/v1/signup", json={
        "access_token": "anterior", "refresh_token": "refresco-ficticio",
        "user": {"is_anonymous": True},
    })
    responses.post(URL + "/auth/v1/token", json={
        "access_token": "nuevo", "refresh_token": "refresco-nuevo",
        "user": {"is_anonymous": True}, "expires_in": 3600,
    })
    cliente = ClienteHTTPSupabase(URL, "sb_publishable_ficticia")
    cliente.autenticar_evaluacion()
    sesion = Sesion()
    sesion.iniciar_sesion("anterior", "Evaluación", -1, {"is_anonymous": True})
    catalogo = CatalogoInvestigacion(cliente=cliente, sesion=sesion)
    catalogo.renovar_sesion_evaluacion()
    assert sesion.esta_autenticado()
    assert sesion.token_acceso == cliente.token_acceso == "nuevo"
    cliente.cerrar_sesion()
    assert not cliente.tiene_sesion_evaluacion


def test_ventana_inicia_conexion_sin_pedir_datos(qtbot, monkeypatch):
    from pea.gui.ventana_principal import VentanaPrincipal
    from pea.servicios import servicio_aplicacion

    monkeypatch.setattr(servicio_aplicacion, "_cargar_env_local", lambda: None)
    servicio = servicio_aplicacion.ServicioAplicacion()
    monkeypatch.setattr(servicio, "configuracion_entorno", lambda: {"acceso_evaluacion": True})
    ventana = VentanaPrincipal(servicio=servicio)
    qtbot.addWidget(ventana)
    llamadas = []
    monkeypatch.setattr(ventana._pantalla_inicio, "_al_clic_conectar", lambda: llamadas.append(True))
    ventana.iniciar_conexion_automatica()
    assert llamadas == [True]
