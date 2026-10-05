"""Recursos gráficos institucionales de PEA-i (iconos SVG, logos e imágenes)."""

from __future__ import annotations

from pea.gui.recursos.cargador import (
    CARPETA_FUENTES,
    CARPETA_ICONOS,
    CARPETA_RECURSOS,
    FUENTES_INTER,
    SIMBOLOS_ESPECIALES,
    cargar_fuentes,
    cargar_icono,
    cargar_pixmap,
    cargar_svg_renderer,
    fuente_inter_cargada,
    limpiar_cache_recursos,
    listar_iconos_disponibles,
    resolver_ruta_recurso,
)

__all__ = [
    "CARPETA_FUENTES",
    "CARPETA_ICONOS",
    "CARPETA_RECURSOS",
    "FUENTES_INTER",
    "cargar_icono",
    "cargar_fuentes",
    "cargar_pixmap",
    "cargar_svg_renderer",
    "fuente_inter_cargada",
    "limpiar_cache_recursos",
    "listar_iconos_disponibles",
    "resolver_ruta_recurso",
    "SIMBOLOS_ESPECIALES",
]
