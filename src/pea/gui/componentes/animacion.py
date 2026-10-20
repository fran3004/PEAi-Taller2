"""Utilidades de animación para la GUI de PEA-i.

Respeta la variable de entorno PEA_SIN_ANIMACIONES para ejecuciones de prueba,
autoprueba y entornos con accesibilidad de movimiento reducido.
"""

from __future__ import annotations

import os
from typing import Final

VARIABLE_SIN_ANIMACIONES: Final[str] = "PEA_SIN_ANIMACIONES"


def animaciones_habilitadas() -> bool:
    """Indica si las animaciones de la interfaz están activadas en el entorno actual."""
    valor = os.environ.get(VARIABLE_SIN_ANIMACIONES, "").strip().lower()
    return valor not in ("1", "true", "si", "yes", "on")


def duracion_efectiva(duracion_deseada_ms: int) -> int:
    """Devuelve la duración en milisegundos, o 0 si las animaciones están desactivadas."""
    return duracion_deseada_ms if animaciones_habilitadas() else 0
