"""Utilidades de animación para la GUI de PEA-i.

Respeta la variable de entorno PEA_SIN_ANIMACIONES para ejecuciones de prueba,
autoprueba y entornos con accesibilidad de movimiento reducido.
"""

from __future__ import annotations

import os
from typing import Final

from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from pea.gui.estilo import (
    DURACION_HOVER_MS,
    DURACION_TRANSICION_PANTALLA_MS,
)

VARIABLE_SIN_ANIMACIONES: Final[str] = "PEA_SIN_ANIMACIONES"


def animaciones_habilitadas() -> bool:
    """Indica si las animaciones de la interfaz están activadas en el entorno actual."""
    valor = os.environ.get(VARIABLE_SIN_ANIMACIONES, "").strip().lower()
    return valor not in ("1", "true", "si", "yes", "on")


def duracion_efectiva(duracion_deseada_ms: int) -> int:
    """Devuelve la duración en milisegundos, o 0 si las animaciones están desactivadas."""
    return duracion_deseada_ms if animaciones_habilitadas() else 0


def animar_desvanecimiento(
    widget: QWidget,
    inicio: float = 0.0,
    fin: float = 1.0,
    duracion_ms: int = DURACION_TRANSICION_PANTALLA_MS,
) -> QPropertyAnimation | None:
    """Aplica una animación de opacidad/desvanecimiento sobre el widget indicado."""
    efecto = widget.graphicsEffect()
    if not isinstance(efecto, QGraphicsOpacityEffect):
        efecto = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(efecto)

    dur = duracion_efectiva(duracion_ms)
    if dur == 0:
        efecto.setOpacity(fin)
        return None

    efecto.setOpacity(inicio)
    anim = QPropertyAnimation(efecto, b"opacity", widget)
    anim.setDuration(dur)
    anim.setStartValue(inicio)
    anim.setEndValue(fin)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


def crear_animacion_propiedad(
    objetivo: object,
    propiedad: bytes,
    inicio: object,
    fin: object,
    duracion_ms: int = DURACION_HOVER_MS,
    curva: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
) -> QPropertyAnimation:
    """Crea una QPropertyAnimation configurada que respeta duracion_efectiva."""
    anim = QPropertyAnimation(objetivo, propiedad)
    anim.setDuration(duracion_efectiva(duracion_ms))
    anim.setStartValue(inicio)
    anim.setEndValue(fin)
    anim.setEasingCurve(curva)
    return anim
