"""Histograma nativo con rangos, conteos, tooltip y alternancia a tabla."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPen
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
from pea.gui.estilo import COLOR_DTI, LINEA, TEXTO, TEXTO_SECUNDARIO
from pea.gui.formato import formatear_entero


class _LienzoHistograma(GraficoBase):
    """Lienzo que dibuja bins con QPainter y resalta el rango bajo el cursor."""

    def __init__(
        self,
        subtitulo: str,
        datos: dict[str, int],
        unidad: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(subtitulo=subtitulo, parent=parent)
        if any(cantidad < 0 for cantidad in datos.values()):
            raise ValueError("Los conteos del histograma no pueden ser negativos.")
        self._datos = dict(datos)
        self._unidad = unidad
        self._bin_hover: str | None = None
        self._rects_bins: list[tuple[str, QRectF]] = []

    def esta_vacio(self) -> bool:
        return not self._datos or not any(self._datos.values())

    def establecer_datos(self, datos: dict[str, int]) -> None:
        if any(cantidad < 0 for cantidad in datos.values()):
            raise ValueError("Los conteos del histograma no pueden ser negativos.")
        self._datos = dict(datos)
        self._bin_hover = None
        self._iniciar_animacion(duracion_ms=350)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._pos_cursor = event.position()
        anterior = self._bin_hover
        self._bin_hover = next(
            (etiqueta for etiqueta, rect in self._rects_bins if rect.contains(self._pos_cursor)),
            None,
        )
        if anterior != self._bin_hover:
            self._tooltip_visible = self._bin_hover is not None
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._bin_hover = None
        self._tooltip_visible = False
        self._pos_cursor = None
        self.update()
        super().leaveEvent(event)

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))
        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 16.0
        if self.esta_vacio():
            self.dibujar_estado_vacio(
                painter,
                rect.adjusted(margen, alto_encabezado + 10.0, -margen, -margen),
            )
            return

        area = QRectF(
            rect.left() + margen + 38.0,
            rect.top() + alto_encabezado + 14.0,
            rect.width() - (2 * margen + 46.0),
            rect.height() - alto_encabezado - 68.0,
        )
        if area.width() < 60.0 or area.height() < 50.0:
            return

        maximo = max(self._datos.values(), default=0)
        divisiones = min(4, maximo)
        if divisiones == 0:
            return

        fuente_eje = QFont()
        fuente_eje.setPointSize(estilo.TAMANO_AUXILIAR)
        painter.setFont(fuente_eje)
        pen_guia = QPen(QColor(estilo.SUPERFICIE_GRAFICO_GUIA), 1, Qt.PenStyle.DashLine)
        pen_eje = QPen(QColor(LINEA), 1)
        for indice in range(divisiones + 1):
            valor = round(maximo * indice / divisiones)
            y = area.bottom() - valor / maximo * area.height()
            painter.setPen(pen_eje if indice == 0 else pen_guia)
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            painter.drawText(
                QRectF(rect.left() + margen, y - 8.0, 32.0, 16.0),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                formatear_entero(valor),
            )

        bins = list(self._datos.items())
        paso = area.width() / len(bins)
        ancho_barra = min(40.0, paso * 0.56)
        progreso = min(1.0, max(0.0, self._progreso_animacion))
        fuente_conteo = QFont()
        fuente_conteo.setPointSize(estilo.TAMANO_MICRO if paso < 25.0 else estilo.TAMANO_AUXILIAR)
        fuente_conteo.setBold(True)
        fuente_etiqueta = QFont()
        fuente_etiqueta.setPointSize(estilo.TAMANO_MICRO if paso < 40.0 else estilo.TAMANO_AUXILIAR)
        metricas_etiqueta = QFontMetrics(fuente_etiqueta)

        self._rects_bins = []
        for indice, (etiqueta, cantidad) in enumerate(bins):
            x_centro = area.left() + (indice + 0.5) * paso
            rect_interactivo = QRectF(
                x_centro - paso / 2.0,
                area.top(),
                paso,
                area.height() + 42.0,
            )
            self._rects_bins.append((etiqueta, rect_interactivo))

            if self._bin_hover == etiqueta:
                painter.fillRect(
                    QRectF(x_centro - paso * 0.44, area.top(), paso * 0.88, area.height()),
                    QColor(estilo.SUPERFICIE_GRAFICO_HOVER),
                )

            alto = cantidad / maximo * area.height() * progreso
            rect_barra = QRectF(
                x_centro - ancho_barra / 2.0,
                area.bottom() - alto,
                ancho_barra,
                alto,
            )
            painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.0))
            painter.setBrush(QColor(COLOR_DTI))
            painter.drawRoundedRect(rect_barra, 4.0, 4.0)

            if progreso >= 0.7:
                painter.setFont(fuente_conteo)
                painter.setPen(QPen(QColor(TEXTO)))
                painter.drawText(
                    QRectF(x_centro - paso / 2.0, rect_barra.top() - 17.0, paso, 15.0),
                    Qt.AlignmentFlag.AlignCenter,
                    formatear_entero(cantidad),
                )

            painter.setFont(fuente_etiqueta)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            ancho_texto = metricas_etiqueta.horizontalAdvance(etiqueta) + 4.0
            if ancho_texto <= paso:
                painter.drawText(
                    QRectF(x_centro - paso / 2.0, area.bottom() + 5.0, paso, 18.0),
                    Qt.AlignmentFlag.AlignCenter,
                    etiqueta,
                )
            else:
                painter.save()
                painter.translate(x_centro, area.bottom() + 7.0)
                painter.rotate(-45.0)
                painter.drawText(
                    QRectF(0.0, -8.0, ancho_texto, 16.0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    etiqueta,
                )
                painter.restore()

        if self._tooltip_visible and self._bin_hover is not None and self._pos_cursor is not None:
            cantidad = self._datos[self._bin_hover]
            unidad = {
                "investigador": "investigador" if cantidad == 1 else "investigadores",
                "producto": "producto" if cantidad == 1 else "productos",
            }.get(self._unidad, self._unidad)
            self._dibujar_tooltip(
                painter,
                rect,
                self._pos_cursor,
                self._bin_hover,
                [(unidad.capitalize(), formatear_entero(cantidad), None)],
            )


class GraficoHistograma(QWidget):
    """Histograma con vista tabular accesible para distribuciones estadísticas."""

    def __init__(
        self,
        titulo: str,
        subtitulo: str,
        unidad: str,
        datos: dict[str, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("grafico_histograma")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        barra = QHBoxLayout()
        barra.setContentsMargins(12, 8, 12, 0)
        self._lbl_titulo = QLabel(titulo, self)
        self._lbl_titulo.setStyleSheet(
            f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {estilo.TEXTO};"
        )
        barra.addWidget(self._lbl_titulo)
        barra.addStretch()

        self._btn_alternar = QPushButton("Ver como tabla", self)
        self._btn_alternar.setObjectName("btn_alternar_histograma")
        self._btn_alternar.setAccessibleName("Alternar entre histograma y tabla de datos")
        self._btn_alternar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_alternar.setStyleSheet(
            f"QPushButton {{ font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: 600; padding: 4px 10px; "
            f"border: 1px solid {estilo.LINEA}; border-radius: 6px; background-color: {estilo.SUPERFICIE}; "
            f"color: {estilo.PRIMARIO}; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; border-color: {estilo.ACENTO}; }}"
        )
        self._btn_alternar.clicked.connect(self.alternar_vista_tabla)
        barra.addWidget(self._btn_alternar)
        layout.addLayout(barra)

        self._apilador = QStackedWidget(self)
        self._lienzo = _LienzoHistograma(subtitulo, datos or {}, unidad, self)
        self._apilador.addWidget(self._lienzo)

        self._tabla = QTableWidget(self)
        self._tabla.setObjectName("tabla_histograma")
        self._tabla.setAccessibleName("Tabla de datos del histograma")
        self._tabla.setColumnCount(2)
        self._tabla.setHorizontalHeaderLabels(["Rango", "Cantidad"])
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tabla.setAlternatingRowColors(True)
        self._apilador.addWidget(self._tabla)
        layout.addWidget(self._apilador)

        self._actualizar_tabla(datos or {})

    def esta_vacio(self) -> bool:
        return self._lienzo.esta_vacio()

    def establecer_datos(self, datos: dict[str, int]) -> None:
        self._lienzo.establecer_datos(datos)
        self._actualizar_tabla(datos)

    def _actualizar_tabla(self, datos: dict[str, int]) -> None:
        self._tabla.setRowCount(len(datos))
        for fila, (etiqueta, cantidad) in enumerate(datos.items()):
            self._tabla.setItem(fila, 0, QTableWidgetItem(etiqueta))
            item_cantidad = QTableWidgetItem(formatear_entero(cantidad))
            item_cantidad.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._tabla.setItem(fila, 1, item_cantidad)
        if self._apilador.currentWidget() is self._tabla:
            self._ajustar_alto_tabla()

    def _ajustar_alto_tabla(self) -> None:
        alto_encabezado = max(
            self._tabla.horizontalHeader().height(),
            self._tabla.horizontalHeader().sizeHint().height(),
        )
        alto_filas = sum(self._tabla.rowHeight(fila) for fila in range(self._tabla.rowCount()))
        self._tabla.setFixedHeight(alto_encabezado + alto_filas + 2 * self._tabla.frameWidth())

    def alternar_vista_tabla(self) -> None:
        if self._apilador.currentWidget() is self._lienzo:
            self._ajustar_alto_tabla()
            self._apilador.setCurrentWidget(self._tabla)
            self._btn_alternar.setText("Ver gráfico")
        else:
            self._tabla.setMinimumHeight(0)
            self._tabla.setMaximumHeight(16777215)
            self._apilador.setCurrentWidget(self._lienzo)
            self._btn_alternar.setText("Ver como tabla")

    def exportar_png(
        self,
        ruta: Path | str,
        ancho: int = 800,
        alto: int = 500,
        escala: float = 2.0,
    ) -> bool:
        titulo_anterior = self._lienzo.titulo
        self._lienzo.titulo = self._lbl_titulo.text()
        try:
            return self._lienzo.exportar_png(ruta, ancho=ancho, alto=alto, escala=escala)
        finally:
            self._lienzo.titulo = titulo_anterior
