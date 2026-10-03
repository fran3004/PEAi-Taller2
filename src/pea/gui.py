"""Ventana principal y arranque de la interfaz gráfica PySide6 de PEA-i."""

import os
import sys

from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pea.version import APP_NAME, APP_VERSION, INSTITUCION


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación PEA-i (Python / PySide6)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Programa Estadístico de Análisis de Investigación ({INSTITUCION})")
        self.resize(1280, 720)
        self.setMinimumSize(960, 540)

        self._configurar_estilo()
        self._construir_ui()

    def _configurar_estilo(self) -> None:
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F9FA;
            }
            QStatusBar {
                background-color: #003366;
                color: #FFFFFF;
                font-size: 12px;
                padding: 4px;
            }
            QStatusBar QLabel {
                color: #FFFFFF;
            }
        """)

    def _construir_ui(self) -> None:
        widget_central = QWidget(self)
        self.setCentralWidget(widget_central)

        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(24, 24, 24, 24)
        layout_principal.setSpacing(20)

        # Cabecera institucional
        frame_cabecera = QFrame(self)
        frame_cabecera.setStyleSheet("background-color: #003366; border-radius: 8px; padding: 16px;")
        layout_cabecera = QVBoxLayout(frame_cabecera)

        lbl_titulo = QLabel("PEA-i · Programa Estadístico de Análisis de Investigación", frame_cabecera)
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")
        layout_cabecera.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel(
            f"{INSTITUCION} · Versión {APP_VERSION} (Python 3.12 / PySide6)",
            frame_cabecera,
        )
        lbl_subtitulo.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        layout_cabecera.addWidget(lbl_subtitulo)

        layout_principal.addWidget(frame_cabecera)

        # Contenedor central informativo
        frame_contenido = QFrame(self)
        frame_contenido.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 24px;"
        )
        layout_contenido = QVBoxLayout(frame_contenido)

        lbl_estado = QLabel("Esqueleto operativo Python / PySide6 listo para integración.", frame_contenido)
        lbl_estado.setStyleSheet("color: #2D3748; font-size: 15px; font-weight: bold;")
        layout_contenido.addWidget(lbl_estado)

        lbl_detalle = QLabel(
            "Módulos arquitectónicos verificados:\n"
            " • Interfaz Gráfica de Usuario (PySide6 / QMainWindow)\n"
            " • Cliente HTTPS / REST / RPC Supabase (requests + TLS nativo)\n"
            " • Gestión segura de credenciales en memoria volátil\n"
            " • Pruebas unitarias pytest y pytest-qt",
            frame_contenido,
        )
        lbl_detalle.setStyleSheet("color: #4A5568; font-size: 13px; line-height: 1.6;")
        layout_contenido.addWidget(lbl_detalle)

        layout_contenido.addStretch()
        layout_principal.addWidget(frame_contenido)

        # Barra de estado
        barra_estado = QStatusBar(self)
        self.setStatusBar(barra_estado)
        barra_estado.showMessage(f"Listo · {INSTITUCION}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    autoprueba = "--autoprueba" in args

    if autoprueba:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication.instance()
    if app is None:
        app = QApplication([sys.argv[0]] + args)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(INSTITUCION)

    ventana = VentanaPrincipal()

    if autoprueba:
        ventana.show()
        app.processEvents()
        print("Autoprueba de GUI Python completada exitosamente.")
        return 0

    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
