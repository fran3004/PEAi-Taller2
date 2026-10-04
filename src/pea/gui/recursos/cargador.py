"""Cargador de recursos gráficos (iconos SVG e imágenes PNG) con caché en memoria."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

CARPETA_RECURSOS: Final[Path] = Path(__file__).resolve().parent
CARPETA_ICONOS: Final[Path] = CARPETA_RECURSOS / "iconos"

_CACHE_RENDERERS: dict[str, QSvgRenderer] = {}
_CACHE_PIXMAPS: dict[tuple[str, int | None, int | None], QPixmap] = {}
_CACHE_ICONOS: dict[str, QIcon] = {}


def resolver_ruta_recurso(nombre: str | Path) -> Path:
    """Resuelve la ruta absoluta de un recurso gráfico dado su nombre o clave.

    Busca en:
    1. La ruta directa si existe.
    2. CARPETA_RECURSOS / nombre
    3. CARPETA_ICONOS / nombre
    4. CARPETA_ICONOS / {nombre}.svg
    5. CARPETA_RECURSOS / {nombre}.svg
    6. CARPETA_RECURSOS / {nombre}.png
    """
    ruta = Path(nombre)
    if ruta.is_absolute() and ruta.is_file():
        return ruta

    posibles = [
        CARPETA_RECURSOS / ruta,
        CARPETA_ICONOS / ruta,
        CARPETA_ICONOS / f"{ruta.stem}.svg",
        CARPETA_RECURSOS / f"{ruta.stem}.svg",
        CARPETA_RECURSOS / f"{ruta.stem}.png",
    ]

    for p in posibles:
        if p.is_file():
            return p

    raise FileNotFoundError(f"Recurso gráfico no encontrado: {nombre}")


def cargar_svg_renderer(nombre: str | Path) -> QSvgRenderer:
    """Carga y cachea un QSvgRenderer a partir de un archivo SVG."""
    ruta = resolver_ruta_recurso(nombre)
    clave = str(ruta.resolve())
    if clave not in _CACHE_RENDERERS:
        renderer = QSvgRenderer(str(ruta))
        if not renderer.isValid():
            raise ValueError(f"El archivo SVG no es válido: {ruta}")
        _CACHE_RENDERERS[clave] = renderer
    return _CACHE_RENDERERS[clave]


def cargar_pixmap(nombre: str | Path, ancho: int | None = None, alto: int | None = None) -> QPixmap:
    """Carga un QPixmap escalado opcionalmente, con soporte para SVG y PNG y caché."""
    ruta = resolver_ruta_recurso(nombre)
    clave = (str(ruta.resolve()), ancho, alto)
    if clave in _CACHE_PIXMAPS:
        return _CACHE_PIXMAPS[clave]

    if ruta.suffix.lower() == ".svg":
        renderer = cargar_svg_renderer(ruta)
        tamano_def = renderer.defaultSize()
        w = ancho if ancho is not None else (tamano_def.width() if tamano_def.width() > 0 else 24)
        h = alto if alto is not None else (tamano_def.height() if tamano_def.height() > 0 else 24)

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
    else:
        pixmap = QPixmap(str(ruta))
        if ancho is not None and alto is not None:
            pixmap = pixmap.scaled(
                ancho,
                alto,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        elif ancho is not None:
            pixmap = pixmap.scaledToWidth(ancho, Qt.TransformationMode.SmoothTransformation)
        elif alto is not None:
            pixmap = pixmap.scaledToHeight(alto, Qt.TransformationMode.SmoothTransformation)

    _CACHE_PIXMAPS[clave] = pixmap
    return pixmap


def cargar_icono(nombre: str | Path, tamano: int = 24) -> QIcon:
    """Carga un QIcon a partir del recurso especificado."""
    ruta = resolver_ruta_recurso(nombre)
    clave = f"{ruta.resolve()}:{tamano}"
    if clave in _CACHE_ICONOS:
        return _CACHE_ICONOS[clave]

    pixmap = cargar_pixmap(ruta, tamano, tamano)
    icono = QIcon(pixmap)
    # También añadimos versión original como base
    icono.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.Off)
    _CACHE_ICONOS[clave] = icono
    return icono


def limpiar_cache_recursos() -> None:
    """Limpia las cachés en memoria de renderers, pixmaps e iconos."""
    _CACHE_RENDERERS.clear()
    _CACHE_PIXMAPS.clear()
    _CACHE_ICONOS.clear()


def listar_iconos_disponibles() -> list[str]:
    """Retorna los nombres base de todos los iconos SVG disponibles en el paquete."""
    if not CARPETA_ICONOS.exists():
        return []
    return sorted(p.stem for p in CARPETA_ICONOS.glob("*.svg"))
