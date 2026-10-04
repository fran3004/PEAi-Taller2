"""Paquete del motor interactivo de red de coautorías académicas."""

from __future__ import annotations

from pea.gui.red.arista import AristaGrafoItem
from pea.gui.red.disposicion import calcular_disposicion_fuerzas
from pea.gui.red.nodo import NodoGrafoItem, abreviar_nombre_investigador
from pea.gui.red.vista_red import LeyendaRed, VistaRed

__all__ = [
    "AristaGrafoItem",
    "LeyendaRed",
    "NodoGrafoItem",
    "VistaRed",
    "abreviar_nombre_investigador",
    "calcular_disposicion_fuerzas",
]
