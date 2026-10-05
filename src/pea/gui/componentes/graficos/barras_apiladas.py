"""Gráfico de barras apiladas por tipología Minciencias con QPainter.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.1).
- Datos: dict[int, dict[str, int]] (año -> tipología -> cantidad).
- Apilado de abajo hacia arriba: GNC, DTI, ASC, FRH.
- Eje Y con líneas punteadas {estilo.SUPERFICIE_GRAFICO_GUIA} y escala redondeada.
- Esquinas superiores redondeadas (4 px) solo en el segmento más alto.
- Leyenda inferior interactiva con clic para atenuar/restaurar series.
- Tooltip oscuro institucional ({estilo.ENCABEZADO_INICIO}, radio 8, texto blanco).
- Alternancia con tabla accesible mediante botón «Ver como tabla».
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Final

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
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.estilo import (
    COLOR_ASC,
    COLOR_DTI,
    COLOR_FRH,
    COLOR_GNC,
    LINEA,
    LINEA_FUERTE,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import NOMBRES_TIPOLOGIAS, formatear_entero

TIPOLOGIAS_ORDEN: Final[tuple[str, ...]] = ("GNC", "DTI", "ASC", "FRH")
COLORES_ORDEN: Final[dict[str, str]] = {
    "GNC": COLOR_GNC,
    "DTI": COLOR_DTI,
    "ASC": COLOR_ASC,
    "FRH": COLOR_FRH,
}


def _calcular_maximo_redondo(valor_max: int) -> int:
    """Calcula un valor máximo 'redondo' para el eje Y (5, 10, 25, 50, 100...)."""
    if valor_max <= 0:
        return 10
    if valor_max <= 5:
        return 5
    if valor_max <= 10:
        return 10
    if valor_max <= 20:
        return 20
    if valor_max <= 30:
        return 30
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


class _LienzoBarrasApiladas(GraficoBase):
    """Lienzo interno que dibuja el gráfico de barras apiladas."""

    def __init__(
        self,
        titulo: str = "",
        subtitulo: str = "",
        datos: dict[int, dict[str, int]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)
        self._datos: dict[int, dict[str, int]] = dict(datos or {})
        self._series_atenuadas: set[str] = set()
        self._rect_leyenda_items: list[tuple[str, QRectF]] = []
        self._columna_hover: int | None = None
        self._rects_columnas: list[tuple[int, QRectF]] = []

    def esta_vacio(self) -> bool:
        if not self._datos:
            return True
        total = sum(sum(cat_dict.values()) for cat_dict in self._datos.values())
        return total == 0

    def establecer_datos(self, datos: dict[int, dict[str, int]]) -> None:
        self._datos = dict(datos)
        self._columna_hover = None
        r = QRectF(self.rect())
        self._calcular_geometria(r if r.width() > 10 else QRectF(0, 0, 600, 400))
        self._iniciar_animacion(duracion_ms=400)

    def _calcular_geometria(self, rect: QRectF) -> None:
        margen = 16.0
        alto_enc = self.dibujar_encabezado(None, rect) if hasattr(self, "_calc_enc") else 0.0
        if self.titulo or self.subtitulo:
            alto_enc = 38.0
        alto_leyenda = 42.0
        area_grafico = QRectF(
            rect.left() + margen + 38.0,
            rect.top() + alto_enc + 14.0,
            rect.width() - (2 * margen + 46.0),
            rect.height() - (alto_enc + alto_leyenda + margen + 24.0),
        )
        self._area_grafico = area_grafico

        anios = sorted(self._datos.keys())
        n_anios = max(1, len(anios))
        paso_col = area_grafico.width() / float(n_anios)

        self._rects_columnas = []
        for i, anio in enumerate(anios):
            x_centro = area_grafico.left() + (i + 0.5) * paso_col
            rect_col = QRectF(x_centro - paso_col / 2.0, area_grafico.top(), paso_col, area_grafico.height() + 24.0)
            self._rects_columnas.append((anio, rect_col))

        # Leyenda
        y_leyenda = area_grafico.bottom() + 26.0
        ancho_util = rect.width() - 32.0
        ancho_col = ancho_util / 2.0
        self._rect_leyenda_items = []
        items_por_col = [
            [("GNC", NOMBRES_TIPOLOGIAS.get("GNC", "Generación de nuevo conocimiento")),
             ("DTI", NOMBRES_TIPOLOGIAS.get("DTI", "Desarrollo tecnológico e innovación"))],
            [("ASC", NOMBRES_TIPOLOGIAS.get("ASC", "Apropiación social del conocimiento")),
             ("FRH", NOMBRES_TIPOLOGIAS.get("FRH", "Formación de recurso humano"))],
        ]
        for col_idx, items in enumerate(items_por_col):
            x_col = rect.left() + 16.0 + col_idx * ancho_col
            for row_idx, (sigla, _) in enumerate(items):
                y_item = y_leyenda + row_idx * 18.0
                rect_click = QRectF(x_col, y_item, ancho_col - 10.0, 16.0)
                self._rect_leyenda_items.append((sigla, rect_click))

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            # Clic en leyenda para atenuar/restaurar
            for tipo, rect_item in self._rect_leyenda_items:
                if rect_item.contains(pos):
                    if tipo in self._series_atenuadas:
                        self._series_atenuadas.remove(tipo)
                    else:
                        self._series_atenuadas.add(tipo)
                    self.update()
                    return
        super().mousePressEvent(event)

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        # Fondo blanco limpio
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))

        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 16.0

        if self.esta_vacio():
            rect_vacio = rect.adjusted(margen, alto_encabezado + 10, -margen, -margen)
            self.dibujar_estado_vacio(painter, rect_vacio)
            return

        anios = sorted(self._datos.keys())
        totales_por_anio = {
            a: sum(self._datos[a].get(t, 0) for t in TIPOLOGIAS_ORDEN)
            for a in anios
        }
        max_total = max(totales_por_anio.values()) if totales_por_anio else 1
        max_redondo = _calcular_maximo_redondo(max_total)

        # Dimensiones de áreas
        alto_leyenda = 42.0
        area_grafico = QRectF(
            rect.left() + margen + 38.0,
            rect.top() + alto_encabezado + 14.0,
            rect.width() - (2 * margen + 46.0),
            rect.height() - (alto_encabezado + alto_leyenda + margen + 24.0),
        )

        if area_grafico.height() < 50.0 or area_grafico.width() < 60.0:
            return

        # 1. Líneas guía horizontales punteadas del Eje Y
        lineas_y = 4
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

            # Etiqueta numérica del eje Y
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_lbl = QRectF(rect.left() + margen, y_pos - 8.0, 32.0, 16.0)
            painter.drawText(rect_lbl, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, formatear_entero(val_y))

        # 2. Barras apiladas por año
        n_anios = max(1, len(anios))
        paso_col = area_grafico.width() / float(n_anios)
        ancho_barra = min(36.0, paso_col * 0.55)

        self._rects_columnas = []
        fuente_total = QFont()
        fuente_total.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_total.setBold(True)

        fuente_anio = QFont()
        fuente_anio.setPointSize(estilo.TAMANO_AUXILIAR)

        for i, anio in enumerate(anios):
            x_centro = area_grafico.left() + (i + 0.5) * paso_col
            x_barra = x_centro - ancho_barra / 2.0

            # Guardar zona interactiva de columna para hover
            rect_col_interactiva = QRectF(x_centro - paso_col / 2.0, area_grafico.top(), paso_col, area_grafico.height() + 24.0)
            self._rects_columnas.append((anio, rect_col_interactiva))

            total_anio = totales_por_anio[anio]
            dict_anio = self._datos[anio]

            # Segmentos apilados
            y_base_seg = area_grafico.bottom()

            # Identificar cuál es el segmento más alto con valor > 0
            tipos_visibles = [t for t in TIPOLOGIAS_ORDEN if dict_anio.get(t, 0) > 0]
            tipo_mas_alto = tipos_visibles[-1] if tipos_visibles else None

            # Factor de animación
            prog = min(1.0, max(0.0, self._progreso_animacion))

            for tipo in TIPOLOGIAS_ORDEN:
                cant = dict_anio.get(tipo, 0)
                if cant <= 0:
                    continue

                fraccion = (float(cant) / float(max_redondo))
                alto_seg = fraccion * area_grafico.height() * prog
                rect_seg = QRectF(x_barra, y_base_seg - alto_seg, ancho_barra, alto_seg)

                color_base = QColor(COLORES_ORDEN[tipo])
                if tipo in self._series_atenuadas:
                    color_base.setAlpha(45)

                painter.setBrush(QBrush(color_base))
                painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.5))

                if tipo == tipo_mas_alto and alto_seg >= 4.0:
                    # Esquinas superiores redondeadas (radio 4 px)
                    path = QPainterPath()
                    path.moveTo(rect_seg.left(), rect_seg.bottom())
                    path.lineTo(rect_seg.left(), rect_seg.top() + 4.0)
                    path.quadTo(rect_seg.left(), rect_seg.top(), rect_seg.left() + 4.0, rect_seg.top())
                    path.lineTo(rect_seg.right() - 4.0, rect_seg.top())
                    path.quadTo(rect_seg.right(), rect_seg.top(), rect_seg.right(), rect_seg.top() + 4.0)
                    path.lineTo(rect_seg.right(), rect_seg.bottom())
                    path.closeSubpath()
                    painter.drawPath(path)
                else:
                    painter.drawRect(rect_seg)

                y_base_seg -= alto_seg

            # Total sobre la barra (10 pt negrita)
            if total_anio > 0 and prog >= 0.7:
                painter.setFont(fuente_total)
                painter.setPen(QPen(QColor(TEXTO)))
                rect_total = QRectF(x_centro - 24.0, y_base_seg - 18.0, 48.0, 16.0)
                painter.drawText(rect_total, Qt.AlignmentFlag.AlignCenter, formatear_entero(total_anio))

            # Etiqueta del año en el eje X
            painter.setFont(fuente_anio)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_x_lbl = QRectF(x_centro - 26.0, area_grafico.bottom() + 6.0, 52.0, 16.0)
            painter.drawText(rect_x_lbl, Qt.AlignmentFlag.AlignCenter, str(anio))

        # 3. Leyenda inferior con clic interactivo
        self._dibujar_leyenda(painter, rect, area_grafico.bottom() + 26.0)

        # 4. Tooltip flotante si hay columna en hover
        if self._tooltip_visible and self._columna_hover is not None and self._pos_cursor is not None:
            anio_h = self._columna_hover
            tot_h = totales_por_anio.get(anio_h, 0)
            dict_h = self._datos.get(anio_h, {})

            titulo_tt = f"{anio_h} · {tot_h} {'producto' if tot_h == 1 else 'productos'}"
            filas_tt: list[tuple[str, str, str | None]] = []
            for t in TIPOLOGIAS_ORDEN:
                c = dict_h.get(t, 0)
                filas_tt.append((t, str(c), COLORES_ORDEN[t]))

            self._dibujar_tooltip(painter, rect, self._pos_cursor, titulo_tt, filas_tt)

    def _dibujar_leyenda(self, painter: QPainter, rect: QRectF, y_leyenda: float) -> None:
        """Dibuja la leyenda inferior en dos columnas con indicadores de atenuación."""
        self._rect_leyenda_items = []
        fuente_ley = QFont()
        fuente_ley.setPointSize(estilo.TAMANO_AUXILIAR)
        painter.setFont(fuente_ley)

        # Disponer en 2 columnas equilibradas
        ancho_util = rect.width() - 32.0
        ancho_col = ancho_util / 2.0
        items_por_col = [
            [("GNC", NOMBRES_TIPOLOGIAS.get("GNC", "Generación de nuevo conocimiento")),
             ("DTI", NOMBRES_TIPOLOGIAS.get("DTI", "Desarrollo tecnológico e innovación"))],
            [("ASC", NOMBRES_TIPOLOGIAS.get("ASC", "Apropiación social del conocimiento")),
             ("FRH", NOMBRES_TIPOLOGIAS.get("FRH", "Formación de recurso humano"))],
        ]

        for col_idx, items in enumerate(items_por_col):
            x_col = rect.left() + 16.0 + col_idx * ancho_col
            for row_idx, (sigla, nombre) in enumerate(items):
                y_item = y_leyenda + row_idx * 18.0
                rect_click = QRectF(x_col, y_item, ancho_col - 10.0, 16.0)
                self._rect_leyenda_items.append((sigla, rect_click))

                esta_atenuada = sigla in self._series_atenuadas

                # Cuadrito indicador
                color_cuadro = QColor(COLORES_ORDEN[sigla])
                if esta_atenuada:
                    color_cuadro.setAlpha(60)

                painter.setBrush(QBrush(color_cuadro))
                painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else "{estilo.SUPERFICIE}"), 1))
                painter.drawRoundedRect(QRectF(x_col, y_item + 2.0, 11.0, 11.0), 3.0, 3.0)

                # Texto
                painter.setPen(QPen(QColor(LINEA_FUERTE if esta_atenuada else TEXTO)))
                texto_ley = f"{sigla}  {nombre}"
                rect_texto = QRectF(x_col + 16.0, y_item, ancho_col - 26.0, 16.0)
                painter.drawText(
                    rect_texto,
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    texto_ley,
                )


class GraficoBarrasApiladas(QWidget):
    """Componente completo de barras apiladas con botón de alternancia a tabla."""

    def __init__(
        self,
        titulo: str = "Producción anual por tipología",
        subtitulo: str = "Evolución histórica según el Modelo Minciencias",
        datos: dict[int, dict[str, int]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("grafico_barras_apiladas")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(6)

        # Barra superior de controles del gráfico
        barra_controles = QHBoxLayout()
        barra_controles.setContentsMargins(12, 8, 12, 0)

        self._lbl_titulo = QLabel(titulo)
        self._lbl_titulo.setStyleSheet("font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {estilo.TEXTO};")
        barra_controles.addWidget(self._lbl_titulo)
        barra_controles.addStretch()

        self._btn_alternar = QPushButton("Ver como tabla")
        self._btn_alternar.setObjectName("btn_alternar_tabla")
        self._btn_alternar.setAccessibleName("Alternar entre visualización gráfica y tabla de datos")
        self._btn_alternar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_alternar.setStyleSheet(
            "QPushButton { font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: 600; padding: 4px 10px; "
            "border: 1px solid {estilo.LINEA}; border-radius: 6px; background-color: {estilo.SUPERFICIE}; color: {estilo.PRIMARIO}; }"
            "QPushButton:hover { background-color: {estilo.FONDO_APP}; border-color: {estilo.ACENTO}; }"
        )
        self._btn_alternar.clicked.connect(self.alternar_vista_tabla)
        barra_controles.addWidget(self._btn_alternar)
        layout_principal.addLayout(barra_controles)

        # Contenedor apilador (Gráfico / Tabla)
        self._apilador = QStackedWidget(self)

        self._lienzo = _LienzoBarrasApiladas(titulo="", subtitulo=subtitulo, datos=datos, parent=self)
        self._apilador.addWidget(self._lienzo)

        # Tabla accesible
        self._tabla = QTableWidget(self)
        self._tabla.setObjectName("tabla_barras_apiladas")
        self._tabla.setAccessibleName("Tabla de producción anual por tipología")
        self._tabla.setColumnCount(6)
        self._tabla.setHorizontalHeaderLabels(["Año", "GNC", "DTI", "ASC", "FRH", "Total"])
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabla.setAlternatingRowColors(True)
        self._apilador.addWidget(self._tabla)

        layout_principal.addWidget(self._apilador)

        if datos:
            self._actualizar_tabla(datos)

    def esta_vacio(self) -> bool:
        return self._lienzo.esta_vacio()

    def establecer_datos(self, datos: dict[int, dict[str, int]]) -> None:
        self._lienzo.establecer_datos(datos)
        self._actualizar_tabla(datos)

    def _actualizar_tabla(self, datos: dict[int, dict[str, int]]) -> None:
        anios = sorted(datos.keys())
        self._tabla.setRowCount(len(anios))
        for fila, a in enumerate(anios):
            subdict = datos[a]
            gnc = subdict.get("GNC", 0)
            dti = subdict.get("DTI", 0)
            asc = subdict.get("ASC", 0)
            frh = subdict.get("FRH", 0)
            total = gnc + dti + asc + frh

            valores = [str(a), formatear_entero(gnc), formatear_entero(dti),
                       formatear_entero(asc), formatear_entero(frh), formatear_entero(total)]
            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col == 0 else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self._tabla.setItem(fila, col, item)

    def alternar_vista_tabla(self) -> None:
        """Alterna entre la vista gráfica nativa y la vista tabular accesible."""
        if self._apilador.currentIndex() == 0:
            self._apilador.setCurrentIndex(1)
            self._btn_alternar.setText("Ver gráfico")
        else:
            self._apilador.setCurrentIndex(0)
            self._btn_alternar.setText("Ver como tabla")

    def exportar_png(self, ruta: Path | str, ancho: int = 800, alto: int = 500, escala: float = 2.0) -> bool:
        """Exporta el gráfico a PNG de doble resolución."""
        # Se asegura que el título general esté presente en el lienzo al exportar
        tit_ant = self._lienzo.titulo
        self._lienzo.titulo = self._lbl_titulo.text()
        exito = self._lienzo.exportar_png(ruta, ancho=ancho, alto=alto, escala=escala)
        self._lienzo.titulo = tit_ant
        return exito
