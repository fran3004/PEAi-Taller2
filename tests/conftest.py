"""Configuración común de pruebas GUI.

Estas variables deben estar activas antes de que pytest-qt cree QApplication.
No se aplican al arranque de producción de pea.gui.
"""

import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PEA_SIN_ANIMACIONES"] = "1"
