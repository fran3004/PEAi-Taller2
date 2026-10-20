"""Configuración común de pruebas GUI.

Estas variables deben estar activas antes de que pytest-qt cree QApplication.
No se aplican al arranque de producción de pea.gui.
"""

import os
from typing import Any

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PEA_SIN_ANIMACIONES"] = "1"


@pytest.fixture
def fuente_inter(qapp: Any) -> None:
    """Configura la misma fuente que usa la aplicación para pruebas de geometría."""
    from PySide6.QtGui import QFont

    from pea.gui.recursos.cargador import cargar_fuentes

    qapp.setFont(QFont(cargar_fuentes(), 11))
