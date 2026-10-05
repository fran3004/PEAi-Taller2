"""Elemento gráfico de arista (vínculo de coautoría) para QGraphicsScene.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Conecta los centros de dos nodos investigadores.
- Grosor proporcional a los productos compartidos: min(4.0, 1.0 + log2(peso)).
- Color base: {estilo.COLOR_RED_ARISTAS} (gris azulado).
- Resaltado y atenuación interactiva según el foco del usuario.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

from pea.gui.estilo import ACENTO, COLOR_RED_ARISTAS

if TYPE_CHECKING:
    from pea.gui.red.nodo import NodoGrafoItem


class AristaGrafoItem(QGraphicsItem):
    """Representa una arista de coautoría entre dos investigadores."""

    def __init__(
        self,
        origen: NodoGrafoItem | None = None,
        destino: NodoGrafoItem | None = None,
        productos_compartidos: int | None = None,
        parent: QGraphicsItem | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        nodo_orig = origen or kwargs.get("nodo_origen")
        nodo_dest = destino or kwargs.get("nodo_destino")
        if nodo_orig is None or nodo_dest is None:
            raise ValueError("Se requieren nodos de origen y destino")
        self.origen = nodo_orig
        self.destino = nodo_dest

        peso_val = productos_compartidos if productos_compartidos is not None else kwargs.get("peso", 1)
        self.productos_compartidos = max(1, int(peso_val))

        # Grosor según especificación: 1 + log2(peso), máximo 4 px
        self.grosor = min(4.0, max(1.0, 1.0 + math.log2(self.productos_compartidos)))

        self._atenuada = False
        self._resaltada = False

        # Z-Value por debajo de los nodos para que no se superpongan
        self.setZValue(-1.0)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self.origen.agregar_arista(self)
        self.destino.agregar_arista(self)

        self._linea = QLineF()
        self.actualizar_geometria()

    def actualizar_geometria(self) -> None:
        """Actualiza los puntos de la línea según las posiciones actuales de los nodos."""
        self.prepareGeometryChange()
        p1 = self.origen.pos()
        p2 = self.destino.pos()
        self._linea = QLineF(p1, p2)

    def establecer_resaltado(self, resaltada: bool) -> None:
        """Activa el resaltado directo cuando uno de sus nodos tiene foco."""
        if self._resaltada != resaltada:
            self._resaltada = resaltada
            self.setZValue(0.0 if resaltada else -1.0)
            self.update()

    def establecer_atenuado(self, atenuada: bool) -> None:
        """Atenúa la arista al 25% de opacidad cuando no es relevante para el hover."""
        if self._atenuada != atenuada:
            self._atenuada = atenuada
            self.update()

    def restablecer_estado(self) -> None:
        """Restaura los valores predeterminados de visualización."""
        self._atenuada = False
        self._resaltada = False
        self.setZValue(-1.0)
        self.update()

    def boundingRect(self) -> QRectF:
        ancho_extra = (self.grosor + 4.0) / 2.0
        return (
            QRectF(self._linea.p1(), self._linea.p2())
            .normalized()
            .adjusted(-ancho_extra, -ancho_extra, ancho_extra, ancho_extra)
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._resaltada:
            color = QColor(ACENTO)
            grosor = self.grosor + 1.2
            painter.setOpacity(1.0)
        elif self._atenuada:
            color = QColor(COLOR_RED_ARISTAS)
            grosor = self.grosor
            painter.setOpacity(0.25)
        else:
            color = QColor(COLOR_RED_ARISTAS)
            grosor = self.grosor
            painter.setOpacity(0.85)

        pen = QPen(color, grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self._linea)

        painter.restore()
