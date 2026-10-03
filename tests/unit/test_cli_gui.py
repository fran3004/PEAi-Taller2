"""Pruebas unitarias para CLI y GUI de Python."""

import pytest
from PySide6.QtWidgets import QApplication

from pea.cli import main as cli_main
from pea.gui import VentanaPrincipal
from pea.gui import main as gui_main
from pea.version import APP_NAME, APP_VERSION, INSTITUCION, obtener_version


def test_version_e_identidad() -> None:
    cadena = obtener_version()
    assert APP_NAME in cadena
    assert APP_VERSION in cadena
    assert INSTITUCION in cadena


def test_cli_info(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = cli_main(["info"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert APP_NAME in captura.out
    assert APP_VERSION in captura.out


def test_cli_ping_sin_credenciales(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = cli_main(["ping"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert "Aviso" in captura.out


def test_gui_ventana_principal(qapp: QApplication) -> None:
    ventana = VentanaPrincipal()
    assert APP_NAME in ventana.windowTitle()
    assert ventana.minimumWidth() >= 960
    assert ventana.minimumHeight() >= 540
    assert ventana.centralWidget() is not None


def test_gui_autoprueba(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = gui_main(["--autoprueba"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert "Autoprueba de GUI Python completada exitosamente." in captura.out
