"""Paquete de componentes nativos de visualización gráfica de PEA-i (Sección 9).

Renderizado exclusivo mediante QPainter sin dependencias externas pesadas.
Incluye exportación PNG de doble resolución, estado vacío accesible,
animaciones fluidas con OutCubic y tooltips institucionales oscuros.
"""

from __future__ import annotations

from pea.gui.componentes.graficos.antiguos import (
    GraficoBarras,
    GraficoSeries,
    GraficoTorta,
)
from pea.gui.componentes.graficos.barras_apiladas import GraficoBarrasApiladas
from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.componentes.graficos.dona_doble import GraficoDonaDoble
from pea.gui.componentes.graficos.mini_red import MiniRed
from pea.gui.componentes.graficos.minigrafico import Minigrafico
from pea.gui.componentes.graficos.serie_anual import GraficoSerieAnual

__all__ = [
    "GraficoBarras",
    "GraficoBarrasApiladas",
    "GraficoBase",
    "GraficoDonaDoble",
    "GraficoSerieAnual",
    "GraficoSeries",
    "GraficoTorta",
    "MiniRed",
    "Minigrafico",
]
