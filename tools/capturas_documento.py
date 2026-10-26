"""Genera las capturas reproducibles que ilustran la especificación técnica.

GUI Python: ventana real en modo offscreen con datos ficticios (``PRUEBA-``) y con
el catálogo de ejemplo del parcial. TUI C++: las capturas de texto de
``pea-cpp --autoprueba`` se representan como imagen de terminal.

Uso (desde la raíz del repositorio)::

    .venv\\Scripts\\python.exe tools/capturas_documento.py [--catalogo-real RUTA.json]

``--catalogo-real`` admite un catálogo descargado con ``indicador --guardar-catalogo``
para fotografiar el cálculo del grupo GISICO; no se versiona.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["PEA_SIN_ANIMACIONES"] = "1"

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from PySide6.QtCore import QThreadPool  # noqa: E402
from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

DESTINO = RAIZ / "docs" / "imagenes"


def _esperar(app: QApplication, ciclos: int = 6) -> None:
    for _ in range(ciclos):
        QThreadPool.globalInstance().waitForDone(4000)
        app.processEvents()


def capturas_gui(catalogo_real: Path | None) -> list[str]:
    from pea.gui.recursos.cargador import cargar_fuentes
    from pea.gui.ventana_principal import Pantalla, VentanaPrincipal

    app = QApplication.instance() or QApplication([])
    app.setFont(QFont(cargar_fuentes(), 11))
    ventana = VentanaPrincipal()
    ventana._servicio.cargar_demostracion()
    ventana.actualizar_estado_global()
    ventana.resize(1366, 768)
    ventana.show()
    _esperar(app)
    hechas = []
    for pantalla, nombre in [
        (Pantalla.INICIO, "gui_01_inicio"),
        (Pantalla.INVESTIGADORES, "gui_02_investigadores"),
        (Pantalla.GRUPOS, "gui_03_grupos"),
        (Pantalla.PRODUCTOS, "gui_04_productos"),
        (Pantalla.REDES, "gui_05_redes"),
        (Pantalla.IMPORTAR, "gui_06_importar"),
        (Pantalla.CONFIGURACION, "gui_07_configuracion"),
        (Pantalla.ACERCA, "gui_08_acerca"),
    ]:
        ventana.seleccionar_pantalla(pantalla)
        _esperar(app)
        ventana.grab().save(str(DESTINO / f"{nombre}.png"), "PNG")
        hechas.append(nombre)

    def indicador(archivo: Path, codigo: str, nombre: str, estimar: bool, ambito: str = "grupo") -> None:
        ventana._servicio.iniciar_local(str(archivo))
        ventana.actualizar_estado_global()
        ventana.seleccionar_pantalla(Pantalla.INDICADORES)
        ventana.resize(1366, 1700)
        pantalla = ventana._pantalla_indicadores
        pantalla.ambito.setCurrentIndex(pantalla.ambito.findData(ambito))
        _esperar(app)
        pantalla.entidad.setCurrentIndex(max(0, pantalla.entidad.findData(codigo)))
        pantalla.estimar.setChecked(estimar)
        pantalla.calcular.click()
        _esperar(app, 10)
        ventana.grab().save(str(DESTINO / f"{nombre}.png"), "PNG")
        hechas.append(nombre)

    indicador(RAIZ / "datos" / "ejemplo-parcial.json", "PRUEBA-G1", "gui_09_indicador_ejemplo", False)
    indicador(RAIZ / "datos" / "ejemplo-parcial.json", "PRUEBA-G1", "gui_10_indicador_estimado", True)
    if catalogo_real and catalogo_real.exists():
        indicador(catalogo_real, "00000000002099", "gui_11_indicador_gisico", True)
    ventana.close()
    return hechas


def _fuente_mono(tam: int) -> ImageFont.FreeTypeFont:
    for ruta in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        if Path(ruta).exists():
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def terminal_a_png(texto: Path, salida: Path, titulo: str) -> None:
    lineas = texto.read_text(encoding="utf-8").splitlines()
    fuente = _fuente_mono(15)
    ancho_car = int(fuente.getlength("M"))
    alto_car = 20
    ancho = max(len(linea) for linea in lineas) * ancho_car + 32
    alto = len(lineas) * alto_car + 64
    img = Image.new("RGB", (ancho, alto), (24, 26, 31))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, ancho, 28), fill=(45, 49, 58))
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((12 + i * 20, 8, 24 + i * 20, 20), fill=color)
    d.text((80, 5), titulo, font=_fuente_mono(14), fill=(190, 195, 205))
    for fila, linea in enumerate(lineas):
        d.text((16, 40 + fila * alto_car), linea, font=fuente, fill=(214, 220, 229))
    img.save(salida)


def capturas_tui() -> list[str]:
    origen = RAIZ / "datos" / "capturas" / "terminal"
    hechas = []
    for archivo, nombre in [
        ("inicio-100x28.txt", "tui_01_inicio"),
        ("investigadores-100x28.txt", "tui_02_investigadores"),
        ("grupos-100x28.txt", "tui_03_grupos"),
        ("productos-100x28.txt", "tui_04_productos"),
        ("indicadores-100x28.txt", "tui_05_indicadores"),
    ]:
        ruta = origen / archivo
        if ruta.exists():
            terminal_a_png(ruta, DESTINO / f"{nombre}.png", "pea-cpp · terminal interactiva FTXUI")
            hechas.append(nombre)
    return hechas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogo-real", type=Path)
    args = parser.parse_args()
    DESTINO.mkdir(parents=True, exist_ok=True)
    print("GUI:", ", ".join(capturas_gui(args.catalogo_real)))
    print("TUI:", ", ".join(capturas_tui()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
