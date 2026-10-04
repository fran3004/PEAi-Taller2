"""Recursos gráficos institucionales de PEA-i (iconos SVG, logos e imágenes)."""

from __future__ import annotations

from pea.gui.recursos.cargador import (
    CARPETA_ICONOS,
    CARPETA_RECURSOS,
    cargar_icono,
    cargar_pixmap,
    cargar_svg_renderer,
    limpiar_cache_recursos,
    listar_iconos_disponibles,
    resolver_ruta_recurso,
)

__all__ = [
    "CARPETA_ICONOS",
    "CARPETA_RECURSOS",
    "cargar_icono",
    "cargar_pixmap",
    "cargar_svg_renderer",
    "limpiar_cache_recursos",
    "listar_iconos_disponibles",
    "resolver_ruta_recurso",
]
