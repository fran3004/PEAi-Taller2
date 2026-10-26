"""Paquete de interfaz gráfica de usuario (PySide6) para PEA-i."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from pea.gui.recursos.cargador import cargar_fuentes
from pea.gui.ventana_principal import Pantalla, VentanaPrincipal, ejecutar_autoprueba
from pea.version import APP_NAME, APP_VERSION, INSTITUCION

__all__ = ["Pantalla", "VentanaPrincipal", "ejecutar_autoprueba", "main"]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la interfaz gráfica PySide6."""
    args = argv if argv is not None else sys.argv[1:]
    es_autoprueba = "--autoprueba" in args

    if es_autoprueba:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication.instance()
    if app is None:
        app = QApplication([sys.argv[0]] + list(args))

    familia = cargar_fuentes()
    app.setFont(QFont(familia, 11))
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(INSTITUCION)

    ventana = VentanaPrincipal()

    if es_autoprueba:
        codigo = ejecutar_autoprueba(app, ventana)
        if codigo == 0:
            print("Autoprueba de GUI Python completada exitosamente.")
        else:
            print(f"Autoprueba de GUI Python fallida (código {codigo}).")
        return codigo

    ventana.show()
    def elegir_inicio():
        if "--archivo" in args:
            try:
                ruta = args[args.index("--archivo") + 1]
                ventana._servicio.iniciar_local(ruta)
                ventana.actualizar_estado_global()
            except (IndexError, OSError, ValueError) as error:
                QMessageBox.critical(ventana, "Archivo local", str(error))
            return
        if "--vacio" in args:
            ventana._servicio.iniciar_local()
            ventana.actualizar_estado_global()
            return
        if "--auto-conectar" in args:
            ventana.iniciar_conexion_automatica()
            return
        dialogo = QMessageBox(ventana)
        dialogo.setWindowTitle("PEA-i · Elegir datos de trabajo")
        dialogo.setText("Elija cómo iniciar el catálogo de investigación.")
        remoto = dialogo.addButton("Supabase", QMessageBox.ButtonRole.AcceptRole)
        archivo = dialogo.addButton("Abrir archivo local", QMessageBox.ButtonRole.ActionRole)
        dialogo.addButton("Sin datos", QMessageBox.ButtonRole.RejectRole)
        dialogo.exec()
        if dialogo.clickedButton() is remoto:
            ventana.iniciar_conexion_automatica()
        elif dialogo.clickedButton() is archivo:
            ruta, _ = QFileDialog.getOpenFileName(ventana, "Abrir catálogo", "", "JSON (*.json)")
            if ruta:
                try:
                    ventana._servicio.iniciar_local(ruta)
                except (OSError, ValueError) as error:
                    QMessageBox.critical(ventana, "Archivo local", str(error))
        else:
            ventana._servicio.iniciar_local()
        ventana.actualizar_estado_global()
        ventana._pantalla_inicio.refrescar()
    QTimer.singleShot(0, elegir_inicio)
    return app.exec()
