"""Mini vista previa del grafo de coautoría para el panel de Inicio con QPainter.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.5).
- Muestra hasta 18 nodos de mayor grado.
- Sin etiquetas saturadas: solo los 6 primeros llevan rótulo textual.
- Aristas en gris azulado (#9DB5C9).
- Hover en nodo resalta vecinos y muestra tooltip oscuro institucional.
- Al hacer clic abre la pantalla completa de Análisis de redes (señal abrir_analisis_completo).
"""

from __future__ import annotations

import math
from typing import Any, Final

from PySide6.QtCore import (
    QEvent,
    QPointF,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget

from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.estilo import (
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_CAT_SIN_CATEGORIA_FONDO,
    COLOR_CAT_SIN_CATEGORIA_TEXTO,
    COLOR_DTI,
    COLOR_RED_ARISTAS,
    TEXTO,
)

COLORES_CATEGORIAS_MAP: Final[dict[str, str]] = {
    "Emérito": COLOR_CAT_EMERITO,
    "Senior": COLOR_CAT_SENIOR,
    "Asociado": COLOR_CAT_ASOCIADO,
    "Junior": COLOR_CAT_JUNIOR,
    "Sin categoría": COLOR_CAT_SIN_CATEGORIA_FONDO,
}


class _NodoMiniRed:
    def __init__(
        self,
        codigo: str,
        nombre: str,
        categoria: str,
        grado: int,
        pos: QPointF,
        radio: float,
        mostrar_etiqueta: bool,
    ) -> None:
        self.codigo = codigo
        self.nombre = nombre
        self.categoria = categoria
        self.grado = grado
        self.pos = pos
        self.radio = radio
        self.mostrar_etiqueta = mostrar_etiqueta


class MiniRed(GraficoBase):
    """Componente de vista previa compacta de la red de coautoría."""

    abrir_analisis_completo = Signal()
    nodo_pulsado = Signal(str)

    def __init__(
        self,
        titulo: str = "Red de colaboración",
        subtitulo: str = "Principales coautorías entre investigadores",
        nodos: list[dict[str, Any]] | None = None,
        aristas: list[dict[str, Any]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)
        self.setObjectName("mini_red")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._datos_nodos: list[dict[str, Any]] = list(nodos or [])
        self._datos_aristas: list[dict[str, Any]] = list(aristas or [])
        self._nodos_geom: list[_NodoMiniRed] = []
        self._aristas_indices: list[tuple[int, int, int]] = []
        self._nodo_hover: _NodoMiniRed | None = None

        if self._datos_nodos:
            self._preparar_grafo()

    def esta_vacio(self) -> bool:
        return len(self._datos_nodos) == 0

    def establecer_datos(
        self,
        nodos: list[dict[str, Any]],
        aristas: list[dict[str, Any]],
    ) -> None:
        """Configura los nodos y aristas de la mini red con animación."""
        self._datos_nodos = list(nodos)
        self._datos_aristas = list(aristas)
        self._nodo_hover = None
        self._preparar_grafo()
        self._iniciar_animacion(duracion_ms=450)

    def _preparar_grafo(self) -> None:
        """Filtra hasta 18 nodos de mayor grado y calcula sus posiciones canónicas."""
        if not self._datos_nodos:
            self._nodos_geom = []
            self._aristas_indices = []
            return

        # Ordenar por grado descendente y tomar hasta 18
        nodos_ordenados = sorted(
            self._datos_nodos,
            key=lambda n: (n.get("grado", 0), n.get("nombre", "")),
            reverse=True,
        )[:18]

        codigos_presentes = {n["codigo"]: idx for idx, n in enumerate(nodos_ordenados)}

        # Calcular aristas entre los nodos presentes
        self._aristas_indices = []
        for a in self._datos_aristas:
            u = a.get("origen")
            v = a.get("destino")
            peso = a.get("peso", a.get("productos_compartidos", 1))
            if u in codigos_presentes and v in codigos_presentes:
                idx_u = codigos_presentes[u]
                idx_v = codigos_presentes[v]
                if idx_u != idx_v:
                    self._aristas_indices.append((idx_u, idx_v, int(peso)))

        # Guardar lista temporal de nodos para posicionamiento en resize / paint
        self._nodos_seleccionados = nodos_ordenados
        r = QRectF(self.rect())
        self._calcular_posiciones(r if r.width() > 10 else QRectF(0, 0, 400, 300))

    def _calcular_posiciones(self, rect_lienzo: QRectF) -> None:
        """Distribuye armónicamente los nodos en el área disponible."""
        if not hasattr(self, "_nodos_seleccionados") or not self._nodos_seleccionados:
            self._nodos_geom = []
            return

        cx = rect_lienzo.center().x()
        cy = rect_lienzo.center().y() + 4.0
        rx = max(30.0, (rect_lienzo.width() - 40.0) / 2.0)
        ry = max(30.0, (rect_lienzo.height() - 40.0) / 2.0)

        total_n = len(self._nodos_seleccionados)
        self._nodos_geom = []

        if total_n == 1:
            n0 = self._nodos_seleccionados[0]
            self._nodos_geom.append(
                _NodoMiniRed(
                    codigo=n0["codigo"],
                    nombre=n0["nombre"],
                    categoria=n0.get("categoria", "Sin categoría"),
                    grado=int(n0.get("grado", 0)),
                    pos=QPointF(cx, cy),
                    radio=14.0,
                    mostrar_etiqueta=True,
                )
            )
            return

        # Si hay más nodos: el primer nodo (más conectado) o primeros 2 van en órbita interna,
        # los demás en órbita elíptica externa para máxima claridad visual.
        n_internos = 1 if total_n > 4 else 0
        n_externos = total_n - n_internos

        for i, n in enumerate(self._nodos_seleccionados):
            grado = int(n.get("grado", 0))
            # Escala de radio según grado: de 7 px a 13 px
            radio = min(13.0, max(7.0, 7.0 + grado * 0.8))
            es_top6 = i < 6

            if i < n_internos:
                px = cx
                py = cy
            else:
                idx_ext = i - n_internos
                # Disposición angular regular en elipse
                angulo = (2.0 * math.pi * idx_ext) / max(1, n_externos)
                # Pequeña rotación para que no sea estrictamente cardinal
                angulo += math.pi / 6.0
                px = cx + rx * math.cos(angulo)
                py = cy + ry * math.sin(angulo)

            self._nodos_geom.append(
                _NodoMiniRed(
                    codigo=n["codigo"],
                    nombre=n["nombre"],
                    categoria=n.get("categoria", "Sin categoría"),
                    grado=grado,
                    pos=QPointF(px, py),
                    radio=radio,
                    mostrar_etiqueta=es_top6,
                )
            )

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position()
        self._pos_cursor = pos
        previo = self._nodo_hover
        self._nodo_hover = None

        for n in self._nodos_geom:
            dx = pos.x() - n.pos.x()
            dy = pos.y() - n.pos.y()
            if (dx * dx + dy * dy) <= (n.radio + 4.0) ** 2:
                self._nodo_hover = n
                break

        if self._nodo_hover != previo:
            self._tooltip_visible = self._nodo_hover is not None
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._nodo_hover = None
        self._tooltip_visible = False
        self._pos_cursor = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._nodo_hover is not None:
                self.nodo_pulsado.emit(self._nodo_hover.codigo)
            self.abrir_analisis_completo.emit()
        super().mousePressEvent(event)

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#FFFFFF"))
        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 16.0

        if self.esta_vacio():
            rect_vacio = rect.adjusted(margen, alto_encabezado + 10, -margen, -margen)
            self.dibujar_estado_vacio(painter, rect_vacio, "Sin red de coautoría", "Prueba con otro grupo o filtro")
            return

        area_red = QRectF(
            rect.left() + margen,
            rect.top() + alto_encabezado + 10.0,
            rect.width() - 2 * margen,
            rect.height() - (alto_encabezado + margen + 24.0),
        )

        self._calcular_posiciones(area_red)

        prog = min(1.0, max(0.0, self._progreso_animacion))

        # 1. Dibujar aristas
        for u_idx, v_idx, peso in self._aristas_indices:
            if u_idx >= len(self._nodos_geom) or v_idx >= len(self._nodos_geom):
                continue
            nu = self._nodos_geom[u_idx]
            nv = self._nodos_geom[v_idx]

            es_conectada_a_hover = (
                self._nodo_hover is not None and
                (self._nodo_hover.codigo == nu.codigo or self._nodo_hover.codigo == nv.codigo)
            )

            color_arista = QColor(COLOR_DTI if es_conectada_a_hover else COLOR_RED_ARISTAS)
            color_arista.setAlpha(240 if es_conectada_a_hover else 140)
            grosor = 2.0 if es_conectada_a_hover else min(2.5, 1.0 + peso * 0.4)

            painter.setPen(QPen(color_arista, grosor))
            painter.drawLine(nu.pos, nv.pos)

        # 2. Dibujar nodos
        fuente_eti = QFont()
        fuente_eti.setPointSize(8)
        painter.setFont(fuente_eti)

        for n in self._nodos_geom:
            es_hover = (self._nodo_hover is not None and self._nodo_hover.codigo == n.codigo)
            r_actual = (n.radio + (3.0 if es_hover else 0.0)) * prog

            col_hex = COLORES_CATEGORIAS_MAP.get(n.categoria, COLOR_CAT_SIN_CATEGORIA_FONDO)
            color_nodo = QColor(col_hex)

            painter.setBrush(QBrush(color_nodo))
            painter.setPen(QPen(QColor("#FFFFFF"), 1.75))
            painter.drawEllipse(n.pos, r_actual, r_actual)

            # Rótulo visible solo para los 6 primeros nodos
            if n.mostrar_etiqueta and prog >= 0.7:
                partes = n.nombre.split()
                primer_nombre = partes[0] if partes else n.nombre
                primer_apellido = partes[1] if len(partes) > 1 else ""
                etiqueta = f"{primer_nombre} {primer_apellido}".strip()

                painter.setPen(QPen(QColor(TEXTO)))
                rect_eti = QRectF(n.pos.x() - 40.0, n.pos.y() + r_actual + 2.0, 80.0, 14.0)
                painter.drawText(rect_eti, Qt.AlignmentFlag.AlignCenter, etiqueta)

        # 3. Pie interactivo «Ver análisis completo →»
        fuente_pie = QFont()
        fuente_pie.setPointSize(9)
        fuente_pie.setBold(True)
        painter.setFont(fuente_pie)
        painter.setPen(QPen(QColor(COLOR_DTI)))
        rect_pie = QRectF(rect.left() + margen, rect.bottom() - 20.0, rect.width() - 2 * margen, 16.0)
        painter.drawText(rect_pie, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Ver análisis completo →")

        # 4. Tooltip al pasar sobre un nodo
        if self._tooltip_visible and self._nodo_hover is not None and self._pos_cursor is not None:
            nh = self._nodo_hover
            col_cat = COLORES_CATEGORIAS_MAP.get(nh.categoria, COLOR_CAT_SIN_CATEGORIA_TEXTO)
            filas_tt = [
                ("Categoría", nh.categoria, col_cat),
                ("Coautorías", str(nh.grado), None),
            ]
            self._dibujar_tooltip(painter, rect, self._pos_cursor, nh.nombre, filas_tt)
