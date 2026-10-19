"""Elemento gráfico de arista (vínculo de coautoría) para QGraphicsScene.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Conecta los centros de dos nodos investigadores.
- Grosor proporcional a los productos compartidos: min(4.0, 1.0 + log2(peso)).
- Color base: {estilo.COLOR_RED_ARISTAS} con insignia de peso en mitad del enlace.
- Resaltado y atenuación interactiva según el foco del usuario.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

from pea.gui import estilo
from pea.gui.estilo import ACENTO, COLOR_RED_ARISTAS, PRIMARIO, SUPERFICIE

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

        sufijo = "producto compartido" if self.productos_compartidos == 1 else "productos compartidos"
        nom_o = getattr(self.origen, "nombre_legible", getattr(self.origen, "nombre", ""))
        nom_d = getattr(self.destino, "nombre_legible", getattr(self.destino, "nombre", ""))
        self.setToolTip(f"{nom_o} ↔ {nom_d}\n{self.productos_compartidos} {sufijo}")

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
            self.setZValue(0.5 if resaltada else -1.0)
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
        ancho_extra = max((self.grosor + 4.0) / 2.0, 12.0)
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
        del option, widget
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        if self._resaltada:
            color = QColor(ACENTO)
            grosor = self.grosor + 1.4
            painter.setOpacity(0.96)
        elif self._atenuada:
            color = QColor(COLOR_RED_ARISTAS)
            grosor = self.grosor
            painter.setOpacity(0.18)
        else:
            color = QColor(estilo.COLOR_RED_ARISTA_ACTIVA if self.productos_compartidos >= 3 else COLOR_RED_ARISTAS)
            grosor = self.grosor + 0.3
            painter.setOpacity(0.82)

        pen = QPen(color, grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self._linea)

        # Insignia con la cantidad de coautorías en el punto medio del enlace
        if (self._resaltada or not self._atenuada) and self._linea.length() >= 52.0:
            mx = (self._linea.p1().x() + self._linea.p2().x()) / 2.0
            my = (self._linea.p1().y() + self._linea.p2().y()) / 2.0
            r_b = 8.0 if self._resaltada else 7.2
            rect_b = QRectF(mx - r_b, my - r_b, r_b * 2.0, r_b * 2.0)

            painter.setPen(QPen(QColor(SUPERFICIE if self._resaltada else ACENTO), 1.2))
            painter.setBrush(QBrush(QColor(PRIMARIO if self._resaltada else SUPERFICIE)))
            painter.drawEllipse(rect_b)

            f_b = QFont(estilo.FAMILIA_FUENTE, 7)
            f_b.setBold(True)
            painter.setFont(f_b)
            painter.setPen(QColor(SUPERFICIE if self._resaltada else PRIMARIO))
            painter.drawText(rect_b, Qt.AlignmentFlag.AlignCenter, str(self.productos_compartidos))

        painter.restore()
