"""Paquete de interfaz gráfica de usuario (PySide6) para PEA-i."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from pea.gui.ventana_principal import VentanaPrincipal, ejecutar_autoprueba
from pea.version import APP_NAME, APP_VERSION, INSTITUCION

__all__ = ["VentanaPrincipal", "ejecutar_autoprueba", "main"]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la interfaz gráfica PySide6."""
    args = argv if argv is not None else sys.argv[1:]
    es_autoprueba = "--autoprueba" in args

    if es_autoprueba:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication.instance()
    if app is None:
        app = QApplication([sys.argv[0]] + list(args))

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(INSTITUCION)

    ventana = VentanaPrincipal()

    if es_autoprueba:
        codigo = ejecutar_autoprueba(app, ventana)
        print("Autoprueba de GUI Python completada exitosamente.")
        return codigo

    ventana.show()
    return app.exec()

