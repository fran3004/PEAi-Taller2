"""Selección de etiquetas legibles para ejes temporales con muchos años."""

from __future__ import annotations

import math
from collections.abc import Sequence


def seleccionar_anios_eje(anios: Sequence[int], ancho_px: float, separacion_minima_px: float = 48.0) -> set[int]:
    """Devuelve años espaciados para el eje X, manteniendo siempre los extremos."""
    if not anios:
        return set()
    if ancho_px <= 0 or separacion_minima_px <= 0:
        return {anios[0], anios[-1]}

    paso = max(1, math.ceil(separacion_minima_px * len(anios) / ancho_px))
    indices = set(range(0, len(anios), paso))
    ultimo = len(anios) - 1
    if ultimo not in indices:
        indice_previo = max(indices)
        separacion_final = (ultimo - indice_previo) * ancho_px / len(anios)
        if separacion_final < separacion_minima_px:
            indices.remove(indice_previo)
        indices.add(ultimo)
    return {anios[indice] for indice in indices}
