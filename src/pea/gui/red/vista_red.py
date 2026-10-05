"""Visor interactivo de red de coautoría con QGraphicsView.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Lienzo QGraphicsView con fondo blanco y cuadrícula tenue de puntos.
- Zoom suave con rueda del ratón, paneo mediante arrastre del fondo.
- Resaltado reactivo de vecinos en hover y atenuación del resto al 25%.
- Selección de nodo que alimenta el panel de métricas de centralidad.
- Doble clic que emite la señal para abrir la ficha en Investigadores.
- Leyenda cromática institucional en la esquina inferior izquierda.
"""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.estilo import (
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_CAT_SIN_CATEGORIA_FONDO,
    LINEA,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.red.arista import AristaGrafoItem
from pea.gui.red.disposicion import calcular_disposicion_fuerzas
from pea.gui.red.nodo import NodoGrafoItem


class LeyendaRed(QFrame):
    """Leyenda flotante institucional ubicada en la esquina inferior izquierda del lienzo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("leyendaRed")
        self.setStyleSheet(
            f"QFrame#leyendaRed {{"
            f"  background-color: {estilo.SUPERPOSICION_CLARA_94};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: 8px;"
            f"  padding: 6px 12px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Fila de categorías con puntos de color
        fila_cats = QHBoxLayout()
        fila_cats.setContentsMargins(0, 0, 0, 0)
        fila_cats.setSpacing(10)

        categorias = [
            ("Emérito", COLOR_CAT_EMERITO),
            ("Senior", COLOR_CAT_SENIOR),
            ("Asociado", COLOR_CAT_ASOCIADO),
            ("Junior", COLOR_CAT_JUNIOR),
            ("Sin cat.", COLOR_CAT_SIN_CATEGORIA_FONDO),
        ]

        for nombre_cat, color_hex in categorias:
            item_c = QHBoxLayout()
            item_c.setSpacing(4)

            punto = QLabel("●", self)
            punto.setStyleSheet(f"color: {color_hex}; font-size: {estilo.TAMANO_CUERPO}pt;")
            lbl = QLabel(nombre_cat, self)
            lbl.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO}; font-weight: 500;")

            item_c.addWidget(punto)
            item_c.addWidget(lbl)
            fila_cats.addLayout(item_c)

        layout.addLayout(fila_cats)

        # Rótulo de escala
        lbl_escala = QLabel("Tamaño del nodo = coautores  ·  Grosor de línea = productos compartidos", self)
        lbl_escala.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        layout.addWidget(lbl_escala)


class VistaRed(QGraphicsView):
    """Visor interactivo con QGraphicsView para la red de coautorías académicas."""

    nodo_seleccionado = Signal(dict)
    nodo_deseleccionado = Signal()
    abrir_investigador_solicitado = Signal(str)
    limite_nodos_alcanzado = Signal(int, int)  # total_original, mostrados

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("vistaRed")

        self._escena = QGraphicsScene(self)
        self._escena.setSceneRect(-2000, -2000, 4000, 4000)
        self.setScene(self._escena)

        self._items_nodos: dict[str, NodoGrafoItem] = {}
        self._items_aristas: list[AristaGrafoItem] = []
        self._nodo_seleccionado: NodoGrafoItem | None = None
        self._nodo_hover: NodoGrafoItem | None = None
        self._zoom_actual = 1.0
        self._temporizador_reencuadre: QTimer | None = None

        # Configuración de rendimiento y calidad gráfica
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background-color: {estilo.SUPERFICIE};")

        # Leyenda flotante
        self._leyenda = LeyendaRed(self)
        self._estado_vacio = QLabel("No hay datos de red para los filtros seleccionados.", self)
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setWordWrap(True)
        self._estado_vacio.setStyleSheet(
            f"color: {TEXTO_SECUNDARIO}; font-size: {estilo.TAMANO_CUERPO}pt; "
            f"background: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; "
            f"border-radius: {estilo.RADIO_BOTON}px; padding: 12px;"
        )
        self._estado_vacio.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        self._estado_vacio.show()
        self._actualizar_posicion_leyenda()
        self._actualizar_estado_vacio()

    @property
    def zoom_actual(self) -> float:
        return self._zoom_actual

    @property
    def items_nodos(self) -> dict[str, NodoGrafoItem]:
        return self._items_nodos

    @property
    def items_aristas(self) -> list[AristaGrafoItem]:
        return self._items_aristas

    @property
    def leyenda(self) -> LeyendaRed:
        return self._leyenda

    # -----------------------------------------------------------------------
    # Fondo con Cuadrícula Tenue de Puntos
    # -----------------------------------------------------------------------

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.save()
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))

        # Cuadrícula suave de puntos cada 36 px
        paso = 36.0
        left = math.floor(rect.left() / paso) * paso
        top = math.floor(rect.top() / paso) * paso

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(estilo.SUPERFICIE_GRAFICO_GUIA))

        r_punto = 1.2
        x = left
        while x < rect.right():
            y = top
            while y < rect.bottom():
                painter.drawEllipse(QPointF(x, y), r_punto, r_punto)
                y += paso
            x += paso

        painter.restore()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._actualizar_posicion_leyenda()
        self._actualizar_estado_vacio()
        if self._items_nodos:
            self._programar_reencuadre()

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.ajustar_vista)

    def _actualizar_estado_vacio(self) -> None:
        if not hasattr(self, "_estado_vacio"):
            return
        self._estado_vacio.setVisible(not self._items_nodos)
        if self._items_nodos:
            return
        self._estado_vacio.adjustSize()
        x = max(0, (self.width() - self._estado_vacio.width()) // 2)
        y = max(0, (self.height() - self._estado_vacio.height()) // 2)
        self._estado_vacio.move(x, y)

    def _actualizar_posicion_leyenda(self) -> None:
        if hasattr(self, "_leyenda") and self._leyenda:
            self._leyenda.adjustSize()
            margen_x = 16
            margen_y = 16
            y = self.height() - self._leyenda.height() - margen_y
            self._leyenda.move(margen_x, max(10, y))

    # -----------------------------------------------------------------------
    # Carga y Actualización del Grafo
    # -----------------------------------------------------------------------

    def cargar_red(
        self,
        nodos_data: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        aristas_data: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        posiciones: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        """Puebla la escena con los nodos y aristas calculados."""
        self._escena.clear()
        self._items_nodos.clear()
        self._items_aristas.clear()
        self._nodo_seleccionado = None
        self._nodo_hover = None
        self._actualizar_estado_vacio()

        total_original = len(nodos_data)

        # Regla de rendimiento: Tope de 400 nodos con mayor grado
        nodos_filtrados = list(nodos_data)
        if len(nodos_filtrados) > 400:
            nodos_filtrados.sort(key=lambda d: (-int(d.get("grado", 0)), str(d.get("codigo", ""))))
            nodos_filtrados = nodos_filtrados[:400]
            self.limite_nodos_alcanzado.emit(total_original, 400)
        else:
            self.limite_nodos_alcanzado.emit(total_original, total_original)

        codigos_visibles = {str(nd.get("codigo", "")) for nd in nodos_filtrados}

        aristas_filtradas = [
            a
            for a in aristas_data
            if str(a.get("origen", "")) in codigos_visibles
            and str(a.get("destino", "")) in codigos_visibles
        ]

        if not nodos_filtrados:
            self._actualizar_estado_vacio()
            return

        # Calcular posiciones si no fueron proporcionadas
        if not posiciones:
            ancho_vista = max(900.0, float(self.viewport().width() or 1000.0))
            alto_vista = max(650.0, float(self.viewport().height() or 700.0))
            posiciones = calcular_disposicion_fuerzas(
                nodos=nodos_filtrados,
                aristas=aristas_filtradas,
                ancho=ancho_vista,
                alto=alto_vista,
            )

        # Determinar los 10 nodos de mayor grado para mostrar sus etiquetas forzadas
        nodos_ordenados_grado = sorted(
            nodos_filtrados, key=lambda d: -int(d.get("grado", 0))
        )
        codigos_top_10 = {
            str(d.get("codigo", "")) for d in nodos_ordenados_grado[:10]
        }

        # 1. Crear nodos en escena
        for nd in nodos_filtrados:
            cod = str(nd.get("codigo", ""))
            item_nodo = NodoGrafoItem(datos=nd, vista=self)
            if cod in codigos_top_10:
                item_nodo.mostrar_etiqueta_forzada = True

            pos = posiciones.get(cod, (0.0, 0.0))
            item_nodo.setPos(pos[0], pos[1])

            self._escena.addItem(item_nodo)
            self._items_nodos[cod] = item_nodo

        # 2. Crear aristas en escena
        for ar in aristas_filtradas:
            u_cod = str(ar.get("origen", ""))
            v_cod = str(ar.get("destino", ""))
            if u_cod in self._items_nodos and v_cod in self._items_nodos:
                u_item = self._items_nodos[u_cod]
                v_item = self._items_nodos[v_cod]
                peso = int(ar.get("productos_compartidos", 1))

                item_arista = AristaGrafoItem(
                    origen=u_item,
                    destino=v_item,
                    productos_compartidos=peso,
                )
                self._escena.addItem(item_arista)
                self._items_aristas.append(item_arista)

        self._actualizar_estado_vacio()
        QTimer.singleShot(0, self.ajustar_vista)

    # -----------------------------------------------------------------------
    # Interacción: Hover y Resaltado de Vecinos
    # -----------------------------------------------------------------------

    def notificar_hover_nodo(self, nodo: NodoGrafoItem) -> None:
        """Resalta el nodo bajo el cursor y sus vecinos; atenúa el resto."""
        self._nodo_hover = nodo
        vecinos = nodo.vecinos()
        grupo_enfocado = vecinos | {nodo}

        # Nodos
        for item in self._items_nodos.values():
            if item in grupo_enfocado:
                item.establecer_resaltado(True)
                item.establecer_atenuado(False)
            else:
                item.establecer_resaltado(False)
                item.establecer_atenuado(True)

        # Aristas
        for ar in self._items_aristas:
            if (ar.origen in grupo_enfocado) and (ar.destino in grupo_enfocado):
                ar.establecer_resaltado(True)
                ar.establecer_atenuado(False)
            else:
                ar.establecer_resaltado(False)
                ar.establecer_atenuado(True)

    def notificar_fin_hover(self) -> None:
        """Restaura la opacidad y estilo cuando el cursor sale del nodo."""
        self._nodo_hover = None
        for item in self._items_nodos.values():
            item.restablecer_estado()
        for ar in self._items_aristas:
            ar.restablecer_estado()

    # -----------------------------------------------------------------------
    # Selección
    # -----------------------------------------------------------------------

    def seleccionar_nodo(self, nodo_o_cod: NodoGrafoItem | str | None) -> None:
        """Selecciona un nodo, actualiza su anillo de acento y emite la señal."""
        target: NodoGrafoItem | None = None
        if isinstance(nodo_o_cod, NodoGrafoItem):
            target = nodo_o_cod
        elif isinstance(nodo_o_cod, str) and nodo_o_cod in self._items_nodos:
            target = self._items_nodos[nodo_o_cod]

        if self._nodo_seleccionado is not None and self._nodo_seleccionado is not target:
            self._nodo_seleccionado.establecer_seleccion(False)

        self._nodo_seleccionado = target
        if target is not None:
            target.establecer_seleccion(True)
            self.centerOn(target)
            self.nodo_seleccionado.emit(target.datos)
        else:
            self.nodo_deseleccionado.emit()

    def deseleccionar(self) -> None:
        self.seleccionar_nodo(None)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Clic en fondo despejado deselecciona
        item = self.itemAt(event.pos())
        if item is None or isinstance(item, AristaGrafoItem):
            self.deseleccionar()
        super().mousePressEvent(event)

    # -----------------------------------------------------------------------
    # Navegación y Zoom
    # -----------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta > 0:
            self.acercar()
        elif delta < 0:
            self.alejar()
        event.accept()

    def acercar(self) -> None:
        factor = 1.18
        if self._zoom_actual * factor <= 5.0:
            self.scale(factor, factor)
            self._zoom_actual *= factor
            self._actualizar_etiquetas_zoom()

    def _programar_reencuadre(self) -> None:
        if self._temporizador_reencuadre is None:
            self._temporizador_reencuadre = QTimer(self)
            self._temporizador_reencuadre.setSingleShot(True)
            self._temporizador_reencuadre.timeout.connect(self.ajustar_vista)
        self._temporizador_reencuadre.start(80)

    def alejar(self) -> None:
        factor = 1.0 / 1.18
        if self._zoom_actual * factor >= 0.2:
            self.scale(factor, factor)
            self._zoom_actual *= factor
            self._actualizar_etiquetas_zoom()

    def ajustar_vista(self) -> None:
        """Ajusta el zoom para que todo el grafo quede visible con margen."""
        rect_items = self._escena.itemsBoundingRect()
        if not rect_items.isEmpty():
            self.fitInView(rect_items.adjusted(-50, -50, 50, 50), Qt.AspectRatioMode.KeepAspectRatio)
            # Calcular zoom efectivo resultante
            matriz = self.transform()
            self._zoom_actual = matriz.m11()
            self._actualizar_etiquetas_zoom()

    def _actualizar_etiquetas_zoom(self) -> None:
        for item in self._items_nodos.values():
            item.update()
