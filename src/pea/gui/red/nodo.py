"""Elemento gráfico de nodo (investigador) para QGraphicsScene.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Radio proporcional a la raíz cuadrada del grado: 8 + 2.5·√grado.
- Color según categoría Minciencias (sección 4.1).
- Anillo de acento de 3 px cuando está seleccionado.
- Etiqueta «J. Apellido» (10 pt) visible si zoom >= 0.8, top 10 o hover.
- Hover resalta nodo y vecinos; resto al 25% de opacidad.
- Doble clic solicita abrir la ficha del investigador.
- Arrastre fija el nodo en su nueva posición.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from pea.gui import estilo
from pea.gui.estilo import (
    ACENTO,
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_CAT_SIN_CATEGORIA_FONDO,
    COLOR_CAT_SIN_CATEGORIA_TEXTO,
    TEXTO,
)

if TYPE_CHECKING:
    from pea.gui.red.arista import AristaGrafoItem
    from pea.gui.red.vista_red import VistaRed


def abreviar_nombre_investigador(nombre: str | None) -> str:
    """Abrevia un nombre de persona al formato reglamentario 'J. Apellido'."""
    if not nombre or not nombre.strip():
        return ""
    partes = [p for p in nombre.strip().split() if p]
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0][0]}. {partes[-1]}"


class NodoGrafoItem(QGraphicsItem):
    """Representa a un investigador en el lienzo interactivo de la red."""

    def __init__(
        self,
        datos: dict[str, Any] | None = None,
        vista: VistaRed | None = None,
        parent: QGraphicsItem | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self.datos = dict(datos or {})
        self.datos.update(kwargs)
        self.vista = vista

        self.codigo: str = str(self.datos.get("codigo") or self.datos.get("id") or "")
        self.nombre: str = str(self.datos.get("nombre", self.codigo))
        self.categoria: str = str(self.datos.get("categoria", "Sin categoría"))
        self.grado: int = int(self.datos.get("grado", 0))
        self.intermediacion: float = float(self.datos.get("intermediacion", 0.0))
        self.grupo_principal: str = str(self.datos.get("grupo_principal", "Sin grupo"))
        self.es_externo: bool = bool(self.datos.get("es_externo", False))

        # Radio según especificación: 8 + 2.5 * math.sqrt(grado)
        self.radio = round(8.0 + 2.5 * math.sqrt(max(0, self.grado)), 1)
        self.etiqueta_abreviada = abreviar_nombre_investigador(self.nombre)

        # Color cromático institucional por categoría
        self.color_relleno = self._resolver_color_categoria(self.categoria)
        self.color_texto = QColor(estilo.SUPERFICIE) if self.categoria != "Sin categoría" else QColor(COLOR_CAT_SIN_CATEGORIA_TEXTO)

        self.aristas: list[AristaGrafoItem] = []
        self._seleccionado = False
        self._resaltado = False
        self._atenuado = False
        self.fijado = False
        self.mostrar_etiqueta_forzada = False

        self.setAcceptHoverEvents(True)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setZValue(1.0)

        # Tooltip accesible y detallado
        rol_txt = " · Colaborador externo" if self.es_externo else ""
        self.setToolTip(
            f"{self.nombre}\n"
            f"Categoría: {self.categoria}{rol_txt}\n"
            f"Grupo: {self.grupo_principal}\n"
            f"Coautores directos: {self.grado}\n"
            f"Centralidad de intermediación: {self.intermediacion:.4f}\n"
            f"(Doble clic para ver ficha en Investigadores)"
        )

    @property
    def nombre_abreviado(self) -> str:
        return self.etiqueta_abreviada

    def _resolver_color_categoria(self, categoria: str) -> QColor:
        cat_limpia = categoria.strip()
        if cat_limpia == "Emérito":
            return QColor(COLOR_CAT_EMERITO)
        if cat_limpia == "Senior":
            return QColor(COLOR_CAT_SENIOR)
        if cat_limpia == "Asociado":
            return QColor(COLOR_CAT_ASOCIADO)
        if cat_limpia == "Junior":
            return QColor(COLOR_CAT_JUNIOR)
        return QColor(COLOR_CAT_SIN_CATEGORIA_FONDO)

    def agregar_arista(self, arista: AristaGrafoItem) -> None:
        if arista not in self.aristas:
            self.aristas.append(arista)

    def vecinos(self) -> set[NodoGrafoItem]:
        """Devuelve el conjunto de nodos conectados directamente a este nodo."""
        res: set[NodoGrafoItem] = set()
        for a in self.aristas:
            if a.origen is not self:
                res.add(a.origen)
            if a.destino is not self:
                res.add(a.destino)
        return res

    def establecer_seleccion(self, seleccion: bool) -> None:
        """Marca el nodo como seleccionado con anillo de acento de 3 px."""
        if self._seleccionado != seleccion:
            self._seleccionado = seleccion
            self.setZValue(10.0 if seleccion else 1.0)
            self.update()

    def establecer_resaltado(self, resaltado: bool) -> None:
        """Activa el resaltado de hover (nodo o vecino enfocado)."""
        if self._resaltado != resaltado:
            self._resaltado = resaltado
            self.setZValue(5.0 if resaltado else (10.0 if self._seleccionado else 1.0))
            self.update()

    def establecer_atenuado(self, atenuado: bool) -> None:
        """Atenúa el nodo al 25% de opacidad cuando no es relevante en el hover."""
        if self._atenuado != atenuado:
            self._atenuado = atenuado
            self.update()

    def restablecer_estado(self) -> None:
        """Restablece los estados temporales de hover y opacidad."""
        self._resaltado = False
        self._atenuado = False
        self.setZValue(10.0 if self._seleccionado else 1.0)
        self.update()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.fijado = True
            for a in self.aristas:
                a.actualizar_geometria()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self.vista is not None:
            self.vista.notificar_hover_nodo(self)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        if self.vista is not None:
            self.vista.notificar_fin_hover()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.vista is not None:
                self.vista.seleccionar_nodo(self)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.vista is not None:
                self.vista.abrir_investigador_solicitado.emit(self.codigo)
        super().mouseDoubleClickEvent(event)

    def boundingRect(self) -> QRectF:
        r = self.radio + 8.0  # Espacio para anillo de selección y borde
        # Espacio adicional inferior para etiqueta
        return QRectF(-r - 40.0, -r, 2.0 * (r + 40.0), 2.0 * r + 24.0)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Control de opacidad
        if self._atenuado and not self._resaltado and not self._seleccionado:
            painter.setOpacity(0.25)
        else:
            painter.setOpacity(1.0)

        # 1. Anillo de selección destacado (3 px ACENTO)
        if self._seleccionado:
            pen_anillo = QPen(QColor(ACENTO), 3.5)
            painter.setPen(pen_anillo)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_anillo = self.radio + 4.0
            painter.drawEllipse(QPointF(0, 0), r_anillo, r_anillo)

        # 2. Círculo principal del nodo
        pen_borde = QPen(
            QColor(estilo.SUPERFICIE),
            2.0 if not self.es_externo else 1.8,
            Qt.PenStyle.SolidLine if not self.es_externo else Qt.PenStyle.DashLine,
        )
        painter.setPen(pen_borde)
        painter.setBrush(QBrush(self.color_relleno))
        painter.drawEllipse(QPointF(0, 0), self.radio, self.radio)

        # 3. Iniciales en nodos con suficiente radio (radio >= 14)
        if self.radio >= 14.0:
            fuente_ini = QFont()
            fuente_ini.setPointSize(estilo.TAMANO_AUXILIAR)
            fuente_ini.setBold(True)
            painter.setFont(fuente_ini)
            painter.setPen(QPen(self.color_texto))
            iniciales = (
                self.etiqueta_abreviada[:2].upper()
                if self.etiqueta_abreviada
                else "--"
            )
            rect_circulo = QRectF(-self.radio, -self.radio, 2.0 * self.radio, 2.0 * self.radio)
            painter.drawText(rect_circulo, Qt.AlignmentFlag.AlignCenter, iniciales)

        # 4. Rótulo de texto («J. Apellido»)
        # Se muestra si: zoom >= 0.8, o está forzado (top 10), o está resaltado/seleccionado
        zoom_actual = self.vista.zoom_actual if self.vista is not None else 1.0
        debe_mostrar_etiqueta = (
            zoom_actual >= 0.8
            or self.mostrar_etiqueta_forzada
            or self._resaltado
            or self._seleccionado
        )

        if debe_mostrar_etiqueta and self.etiqueta_abreviada:
            fuente_lbl = QFont()
            fuente_lbl.setPointSize(estilo.TAMANO_AUXILIAR)
            fuente_lbl.setBold(self._seleccionado or self._resaltado)
            painter.setFont(fuente_lbl)

            fm = QFontMetrics(fuente_lbl)
            ancho_txt = fm.horizontalAdvance(self.etiqueta_abreviada)
            alto_txt = fm.height()

            rect_lbl = QRectF(-ancho_txt / 2.0 - 4.0, self.radio + 3.0, ancho_txt + 8.0, alto_txt + 2.0)

            # Fondo suave semitransparente para legibilidad sobre aristas
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 230))
            painter.drawRoundedRect(rect_lbl, 4.0, 4.0)

            # Texto del nombre abreviado
            color_txt = QColor(ACENTO) if self._seleccionado else QColor(TEXTO)
            painter.setPen(QPen(color_txt))
            painter.drawText(rect_lbl, Qt.AlignmentFlag.AlignCenter, self.etiqueta_abreviada)

        painter.restore()
