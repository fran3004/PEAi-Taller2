"""Sin conexión: los llamadores de consultar_remota avisan con claridad y no se cuelgan."""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from pea import cli
from pea.excepciones import ErrorConexion
from pea.gui.ventana_principal import VentanaPrincipal
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_dominio import CatalogoInvestigacion
from pea.servicios.vistas import ModoConexion


class ClienteSinRed:
    """Simula Supabase inalcanzable (o meta sin fila válida) sin tocar la red."""

    base_url = "https://host-inexistente.invalid"
    tiene_sesion_evaluacion = False

    def __init__(self, meta: Any = None, rpc: Any = None) -> None:
        self.meta = meta
        self.rpc_valor = rpc

    def rpc(self, funcion: str, params: dict[str, Any] | None = None) -> Any:
        if self.rpc_valor is None:
            raise ErrorConexion("Fallo en la conexión de red HTTPS con Supabase", "host inexistente")
        return self.rpc_valor

    def get(self, tabla: str, params: dict[str, Any] | None = None) -> Any:
        if self.meta is None:
            raise ErrorConexion("Fallo en la conexión de red HTTPS con Supabase", "host inexistente")
        return self.meta

    def cerrar_sesion(self) -> None:
        pass


def _servicio_supabase(cliente: ClienteSinRed, revision_local: int = 5) -> ServicioAplicacion:
    servicio = ServicioAplicacion()
    catalogo = CatalogoInvestigacion()
    catalogo.controlador_revision.actualizar_local(revision_local)
    servicio._instalar_catalogo(catalogo, ModoConexion.SUPABASE)
    servicio._cliente = cliente  # type: ignore[assignment]
    return servicio


@pytest.mark.parametrize("meta", [None, [], [{"revision": 0}]])
def test_servicio_marca_sin_conexion_en_vez_de_dar_por_sincronizado(meta: Any) -> None:
    servicio = _servicio_supabase(ClienteSinRed(meta=meta))

    estado = servicio.verificar_cambios_remotos()

    assert estado.sin_conexion is True
    assert estado.cambio_remoto is False
    assert estado.mensaje.startswith("Sin conexión: No fue posible verificar la revisión remota.")
    assert estado.motivo_bloqueo is not None  # las escrituras quedan bloqueadas


def test_servicio_recupera_la_conexion_cuando_vuelve_la_red() -> None:
    cliente = ClienteSinRed(meta=None)
    servicio = _servicio_supabase(cliente)
    assert servicio.verificar_cambios_remotos().sin_conexion is True

    cliente.rpc_valor = 5
    estado = servicio.verificar_cambios_remotos()
    assert estado.sin_conexion is False
    assert estado.cambio_remoto is False


def test_modo_demostracion_no_consulta_la_red() -> None:
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    assert servicio.verificar_cambios_remotos().sin_conexion is False
    servicio.simular_cambio_remoto()
    estado = servicio.verificar_cambios_remotos()
    assert estado.sin_conexion is False
    assert estado.cambio_remoto is True
    assert servicio.recargar().cambio_remoto is False


def test_ventana_muestra_la_franja_sin_conexion_tras_la_verificacion_periodica(
    qapp: QApplication, qtbot: Any
) -> None:
    cliente = ClienteSinRed(meta=[])
    servicio = _servicio_supabase(cliente)
    ventana = VentanaPrincipal(servicio=servicio)
    qtbot.addWidget(ventana)
    ventana.show()
    ventana._timer_revision.stop()  # se dispara a mano para no esperar 10 s
    assert not ventana._franja_sin_conexion.isVisible()

    ventana._verificar_revision_en_segundo_plano()
    qtbot.waitUntil(ventana._franja_sin_conexion.isVisible, timeout=5000)
    assert "Sin conexión" in ventana._lbl_estado_conexion.text()
    assert ventana.isVisible()

    cliente.rpc_valor = 5
    ventana._verificar_revision_en_segundo_plano()
    qtbot.waitUntil(lambda: not ventana._franja_sin_conexion.isVisible(), timeout=5000)
    assert "Conectado a Supabase" in ventana._lbl_estado_conexion.text()


def test_cli_verificar_informa_el_fallo_y_no_dice_conectividad_ok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "_obtener_cliente_desde_entorno", lambda: ClienteSinRed(meta=[]))

    codigo = cli.comando_verificar()

    salida = capsys.readouterr()
    assert codigo == 1
    assert "Conectividad: OK" not in salida.out
    assert "No fue posible verificar la revisión remota." in salida.err

