"""Gráfico de evolución temporal anual mediante barras simples con QPainter.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.3).
- Barras simples en color petróleo ({estilo.COLOR_DTI}) con valor numérico encima.
- Sin línea de tendencia artificial.
- Eje X con años y líneas de referencia horizontales punteadas {estilo.SUPERFICIE_GRAFICO_GUIA}.
- Tooltip oscuro institucional ({estilo.ENCABEZADO_INICIO}) al pasar el cursor.
- Diseñado para fichas laterales de grupos e investigadores.
"""

from __future__ import annotations

import math

from PySide6.QtCore import (
    QEvent,
    QPointF,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.estilo import (
    COLOR_DTI,
    LINEA,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import formatear_entero


def _calcular_maximo_redondo(valor_max: int) -> int:
    if valor_max <= 0:
        return 5
    if valor_max <= 5:
        return 5
    if valor_max <= 10:
        return 10
    if valor_max <= 20:
        return 20
    if valor_max <= 50:
        return 50
    if valor_max <= 100:
        return 100

    potencia = 10 ** int(math.floor(math.log10(valor_max)))
    fraccion = valor_max / potencia
    if fraccion <= 1.0:
        factor = 1.0
    elif fraccion <= 2.0:
        factor = 2.0
    elif fraccion <= 2.5:
        factor = 2.5
    elif fraccion <= 5.0:
        factor = 5.0
    else:
        factor = 10.0
    return int(factor * potencia)


class GraficoSerieAnual(GraficoBase):
    """Componente de serie anual con barras simples en color petróleo."""

    def __init__(
        self,
        titulo: str = "Producción anual",
        subtitulo: str = "",
        datos: dict[int, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)
        self.setObjectName("grafico_serie_anual")
        self._datos: dict[int, int] = dict(datos or {})
        self._columna_hover: int | None = None
        self._rects_columnas: list[tuple[int, QRectF]] = []

    def esta_vacio(self) -> bool:
        if not self._datos:
            return True
        return sum(self._datos.values()) == 0

    def establecer_datos(self, datos: dict[int, int]) -> None:
        """Actualiza la serie anual con animación."""
        self._datos = dict(datos)
        self._columna_hover = None
        self._iniciar_animacion(duracion_ms=400)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        self._pos_cursor = pos
        col_hover_previa = self._columna_hover
        self._columna_hover = None

        for anio, rect_col in self._rects_columnas:
            if rect_col.contains(pos):
                self._columna_hover = anio
                break

        if self._columna_hover != col_hover_previa:
            self._tooltip_visible = self._columna_hover is not None
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._columna_hover = None
        self._tooltip_visible = False
        self._pos_cursor = None
        self.update()
        super().leaveEvent(event)

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))
        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 16.0

        if self.esta_vacio():
            rect_vacio = rect.adjusted(margen, alto_encabezado + 10, -margen, -margen)
            self.dibujar_estado_vacio(painter, rect_vacio)
            return

        anios = sorted(self._datos.keys())
        valores = [self._datos[a] for a in anios]
        max_val = max(valores) if valores else 1
        max_redondo = _calcular_maximo_redondo(max_val)

        area_grafico = QRectF(
            rect.left() + margen + 32.0,
            rect.top() + alto_encabezado + 12.0,
            rect.width() - (2 * margen + 36.0),
            rect.height() - (alto_encabezado + margen + 32.0),
        )

        if area_grafico.height() < 40.0 or area_grafico.width() < 40.0:
            return

        # 1. Líneas guía horizontales punteadas del Eje Y
        lineas_y = 3
        paso_y_val = max_redondo / lineas_y
        fuente_eje = QFont()
        fuente_eje.setPointSize(estilo.TAMANO_AUXILIAR)
        painter.setFont(fuente_eje)

        pen_guia = QPen(QColor(estilo.SUPERFICIE_GRAFICO_GUIA), 1, Qt.PenStyle.DashLine)
        pen_eje = QPen(QColor(LINEA), 1)

        for i in range(lineas_y + 1):
            val_y = int(round(i * paso_y_val))
            y_pos = area_grafico.bottom() - (float(val_y) / float(max_redondo)) * area_grafico.height()

            painter.setPen(pen_guia if i > 0 else pen_eje)
            painter.drawLine(QPointF(area_grafico.left(), y_pos), QPointF(area_grafico.right(), y_pos))

            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_lbl = QRectF(rect.left() + margen, y_pos - 8.0, 28.0, 16.0)
            painter.drawText(rect_lbl, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, formatear_entero(val_y))

        # 2. Barras anuales simples en color petróleo {estilo.COLOR_DTI}
        n_anios = max(1, len(anios))
        paso_col = area_grafico.width() / float(n_anios)
        ancho_barra = min(32.0, paso_col * 0.55)

        self._rects_columnas = []
        fuente_total = QFont()
        fuente_total.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_total.setBold(True)

        fuente_anio = QFont()
        fuente_anio.setPointSize(estilo.TAMANO_AUXILIAR)

        prog = min(1.0, max(0.0, self._progreso_animacion))

        for i, anio in enumerate(anios):
            x_centro = area_grafico.left() + (i + 0.5) * paso_col
            x_barra = x_centro - ancho_barra / 2.0

            rect_col_interactiva = QRectF(x_centro - paso_col / 2.0, area_grafico.top(), paso_col, area_grafico.height() + 24.0)
            self._rects_columnas.append((anio, rect_col_interactiva))

            val = self._datos[anio]
            fraccion = float(val) / float(max_redondo)
            alto_b = fraccion * area_grafico.height() * prog
            rect_barra = QRectF(x_barra, area_grafico.bottom() - alto_b, ancho_barra, alto_b)

            # Barra con esquinas superiores redondeadas (4 px)
            if alto_b >= 4.0:
                path = QPainterPath()
                path.moveTo(rect_barra.left(), rect_barra.bottom())
                path.lineTo(rect_barra.left(), rect_barra.top() + 4.0)
                path.quadTo(rect_barra.left(), rect_barra.top(), rect_barra.left() + 4.0, rect_barra.top())
                path.lineTo(rect_barra.right() - 4.0, rect_barra.top())
                path.quadTo(rect_barra.right(), rect_barra.top(), rect_barra.right(), rect_barra.top() + 4.0)
                path.lineTo(rect_barra.right(), rect_barra.bottom())
                path.closeSubpath()

                painter.setBrush(QBrush(QColor(COLOR_DTI)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(path)
            elif alto_b > 0.0:
                painter.fillRect(rect_barra, QColor(COLOR_DTI))

            # Valor numérico encima de la barra
            if val > 0 and prog >= 0.7:
                painter.setFont(fuente_total)
                painter.setPen(QPen(QColor(TEXTO)))
                rect_val = QRectF(x_centro - 20.0, rect_barra.top() - 18.0, 40.0, 16.0)
                painter.drawText(rect_val, Qt.AlignmentFlag.AlignCenter, formatear_entero(val))

            # Año debajo en el eje X
            painter.setFont(fuente_anio)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_anio = QRectF(x_centro - 24.0, area_grafico.bottom() + 6.0, 48.0, 16.0)
            painter.drawText(rect_anio, Qt.AlignmentFlag.AlignCenter, str(anio))

        # 3. Tooltip interactivo si hay hover
        if self._tooltip_visible and self._columna_hover is not None and self._pos_cursor is not None:
            anio_h = self._columna_hover
            val_h = self._datos.get(anio_h, 0)
            txt_tit = f"{anio_h} · {val_h} {'producto' if val_h == 1 else 'productos'}"
            filas_tt = [("Producción", str(val_h), COLOR_DTI)]
            self._dibujar_tooltip(painter, rect, self._pos_cursor, txt_tit, filas_tt)
