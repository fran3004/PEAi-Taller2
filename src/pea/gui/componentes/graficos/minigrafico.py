"""Minigráfico de tendencia (sparkline) de 56×18 px sin ejes para fichas KPI.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.4).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.gui.estilo import COLOR_DTI, LINEA_FUERTE


class Minigrafico(QWidget):
    """Minigráfico de tendencia sin ejes de 56×18 px."""

    def __init__(
        self,
        datos: list[float] | list[int] | None = None,
        color_linea: str = COLOR_DTI,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("minigrafico")
        self.setFixedSize(QSize(56, 18))
        self._datos: list[float] = [float(v) for v in datos] if datos else []
        self._color_linea = color_linea

    def esta_vacio(self) -> bool:
        return len(self._datos) == 0

    def actualizar_datos(self, datos: list[float] | list[int]) -> None:
        """Actualiza la serie temporal del minigráfico y repinta."""
        self._datos = [float(v) for v in datos]
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width() - 4)
        h = float(self.height() - 4)

        if len(self._datos) < 2:
            # Línea neutra tenue si no hay datos suficientes
            painter.setPen(QPen(QColor(LINEA_FUERTE), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(2.0, h / 2.0 + 2.0), QPointF(w + 2.0, h / 2.0 + 2.0))
            painter.end()
            return

        min_v = min(self._datos)
        max_v = max(self._datos)
        rango = max_v - min_v if max_v != min_v else 1.0

        puntos: list[QPointF] = []
        paso_x = w / float(len(self._datos) - 1)
        for i, val in enumerate(self._datos):
            x = 2.0 + i * paso_x
            y = 2.0 + h - ((val - min_v) / rango) * h
            puntos.append(QPointF(x, y))

        # 1. Área bajo la curva con degradado suave
        path_area = QPainterPath()
        path_area.moveTo(puntos[0].x(), h + 2.0)
        for p in puntos:
            path_area.lineTo(p)
        path_area.lineTo(puntos[-1].x(), h + 2.0)
        path_area.closeSubpath()

        degradado = QLinearGradient(0, 2, 0, h + 2)
        c_inicio = QColor(self._color_linea)
        c_inicio.setAlpha(60)
        c_fin = QColor(self._color_linea)
        c_fin.setAlpha(0)
        degradado.setColorAt(0.0, c_inicio)
        degradado.setColorAt(1.0, c_fin)

        painter.fillPath(path_area, QBrush(degradado))

        # 2. Línea principal suavizada
        path_linea = QPainterPath()
        path_linea.moveTo(puntos[0])
        for p in puntos[1:]:
            path_linea.lineTo(p)

        pen_linea = QPen(QColor(self._color_linea), 1.75)
        pen_linea.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen_linea.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen_linea)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_linea)

        # 3. Punto destacado en el último valor
        ultimo = puntos[-1]
        painter.setBrush(QBrush(QColor(self._color_linea)))
        painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.0))
        painter.drawEllipse(QRectF(ultimo.x() - 2.5, ultimo.y() - 2.5, 5.0, 5.0))

        painter.end()
