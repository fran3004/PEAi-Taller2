"""Diagnostica restricciones horizontales de las pantallas Qt en modo offscreen."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QAbstractScrollArea, QWidget

from pea.gui.pantallas.inicio import PantallaInicio
from pea.servicios.servicio_aplicacion import ServicioAplicacion


TAMANOS_OFICIALES = ((1100, 700), (1366, 768), (1920, 1080))


def diagnosticar(pantalla: QWidget, ancho: int, alto: int) -> None:
    pantalla.resize(QSize(ancho, alto))
    pantalla.show()
    QApplication.processEvents()

    widgets = sorted(
        (
            (widget.minimumSizeHint().width(), widget.objectName() or widget.metaObject().className())
            for widget in pantalla.findChildren(QWidget)
        ),
        reverse=True,
    )
    print(f"\n=== {ancho}x{alto} ===")
    print("15 mayores minimumSizeHint().width():")
    for minimo, nombre in widgets[:15]:
        print(f"  {minimo:4d}px  {nombre}")

    barras = [
        widget.objectName() or widget.metaObject().className()
        for widget in pantalla.findChildren(QAbstractScrollArea)
        if widget.horizontalScrollBar().isVisible()
    ]
    print("Areas con barra horizontal visible:")
    print("  " + (", ".join(barras) if barras else "ninguna"))


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    pantalla = PantallaInicio(servicio=servicio)
    for ancho, alto in TAMANOS_OFICIALES:
        diagnosticar(pantalla, ancho, alto)
    pantalla.close()
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
