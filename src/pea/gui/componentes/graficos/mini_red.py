"""Mini vista previa del grafo de coautoría para el panel de Inicio con QPainter.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 9.5).
- Muestra hasta 18 nodos de mayor grado.
- Sin etiquetas saturadas: solo los 6 primeros llevan rótulo textual en píldora legible.
- Aristas en gris azulado ({estilo.COLOR_RED_ARISTAS}) con resaltado dinámico.
- Hover en nodo resalta vecinos y muestra tooltip oscuro institucional.
- Al hacer clic abre la pantalla completa de Análisis de redes (señal abrir_analisis_completo).
"""

from __future__ import annotations

import math
from typing import Any

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
    QFontMetricsF,
    QMouseEvent,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.gui.componentes.graficos.base import GraficoBase
from pea.gui.estilo import (
    ACENTO,
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_DTI,
    PRIMARIO,
    SUPERFICIE,
    TEXTO,
)
from pea.gui.red.nodo import (
    abreviar_nombre_investigador,
    normalizar_nombre_investigador,
)


def _resolver_color_mini_nodo(categoria: str, grado: int, idx: int) -> str:
    cat_baja = (categoria or "").strip().lower()
    if "emérito" in cat_baja or "emerito" in cat_baja:
        return COLOR_CAT_EMERITO
    if "senior" in cat_baja:
        return COLOR_CAT_SENIOR
    if "asociado" in cat_baja:
        return COLOR_CAT_ASOCIADO
    if "junior" in cat_baja:
        return COLOR_CAT_JUNIOR
    if grado > 0:
        return estilo.PALETA_NODOS_RED[idx % len(estilo.PALETA_NODOS_RED)]
    return estilo.COLOR_NODO_AISLADO


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
        color_hex: str = estilo.COLOR_NODO_SIN_CATEGORIA,
    ) -> None:
        self.codigo = codigo
        self.nombre = nombre
        self.nombre_legible = normalizar_nombre_investigador(nombre) or nombre
        self.etiqueta = abreviar_nombre_investigador(nombre) or nombre
        self.categoria = categoria
        self.grado = grado
        self.pos = pos
        self.radio = radio
        self.mostrar_etiqueta = mostrar_etiqueta
        self.color_hex = color_hex


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

        self._nodos_seleccionados = nodos_ordenados
        r = QRectF(self.rect())
        self._calcular_posiciones(r if r.width() > 10 else QRectF(0, 0, 400, 300))

    def _calcular_posiciones(self, rect_lienzo: QRectF) -> None:
        """Distribuye armónicamente los nodos en dos órbitas concéntricas."""
        if not hasattr(self, "_nodos_seleccionados") or not self._nodos_seleccionados:
            self._nodos_geom = []
            return

        cx = rect_lienzo.center().x()
        cy = rect_lienzo.center().y() - 2.0
        rx = max(36.0, (rect_lienzo.width() - 56.0) / 2.0)
        ry = max(32.0, (rect_lienzo.height() - 48.0) / 2.0)

        total_n = len(self._nodos_seleccionados)
        self._nodos_geom = []

        if total_n == 1:
            n0 = self._nodos_seleccionados[0]
            grado0 = int(n0.get("grado", 0))
            cat0 = str(n0.get("categoria", "Sin categoría"))
            self._nodos_geom.append(
                _NodoMiniRed(
                    codigo=n0["codigo"],
                    nombre=n0["nombre"],
                    categoria=cat0,
                    grado=grado0,
                    pos=QPointF(cx, cy),
                    radio=14.0,
                    mostrar_etiqueta=True,
                    color_hex=_resolver_color_mini_nodo(cat0, grado0, 0),
                )
            )
            return

        # Distribución en 2 anillos alrededor del nodo central (índice 0):
        # - Anillo primario (índices 1..5, etiquetados): radio 55% para que sus etiquetas nunca se corten.
        # - Anillo secundario (índices 6..17): radio 92% en el perímetro exterior.
        n_anillo1 = min(5, max(0, total_n - 1))
        n_anillo2 = max(0, total_n - 1 - n_anillo1)

        for i, n in enumerate(self._nodos_seleccionados):
            grado = int(n.get("grado", 0))
            cat = str(n.get("categoria", "Sin categoría"))
            radio = min(14.0, max(7.5, 8.0 + math.sqrt(max(0, grado)) * 2.0))
            es_top6 = i < 6

            if i == 0:
                px = cx
                py = cy
            elif i <= n_anillo1:
                idx_1 = i - 1
                angulo = -math.pi / 2.0 + (2.0 * math.pi * idx_1) / max(1, n_anillo1)
                r_factor = 0.56 if n_anillo2 > 0 else 0.78
                px = cx + rx * r_factor * math.cos(angulo)
                py = cy + ry * r_factor * math.sin(angulo)
            else:
                idx_2 = i - 1 - n_anillo1
                angulo = (math.pi / 10.0) + (2.0 * math.pi * idx_2) / max(1, n_anillo2)
                px = cx + rx * 0.92 * math.cos(angulo)
                py = cy + ry * 0.90 * math.sin(angulo)

            self._nodos_geom.append(
                _NodoMiniRed(
                    codigo=n["codigo"],
                    nombre=n["nombre"],
                    categoria=cat,
                    grado=grado,
                    pos=QPointF(px, py),
                    radio=radio,
                    mostrar_etiqueta=es_top6,
                    color_hex=_resolver_color_mini_nodo(cat, grado, i),
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
            if (dx * dx + dy * dy) <= (n.radio + 5.0) ** 2:
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
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))
        alto_encabezado = self.dibujar_encabezado(painter, rect)
        margen = 14.0

        if self.esta_vacio():
            rect_vacio = rect.adjusted(margen, alto_encabezado + 10, -margen, -margen)
            self.dibujar_estado_vacio(painter, rect_vacio, "Sin red de coautoría", "Prueba con otro grupo o filtro")
            return

        area_red = QRectF(
            rect.left() + margen,
            rect.top() + alto_encabezado + 6.0,
            rect.width() - 2 * margen,
            rect.height() - (alto_encabezado + margen + 24.0),
        )

        # Halo elíptico suave de fondo para dar estructura visual
        painter.save()
        grad_fondo = QRadialGradient(area_red.center(), max(area_red.width(), area_red.height()) * 0.48)
        c_in = QColor(estilo.SUPERFICIE_SELECCIONADA)
        c_in.setAlpha(115)
        c_out = QColor(estilo.SUPERFICIE)
        c_out.setAlpha(0)
        grad_fondo.setColorAt(0.0, c_in)
        grad_fondo.setColorAt(1.0, c_out)
        painter.setPen(QPen(QColor(estilo.LINEA), 1.0, Qt.PenStyle.DotLine))
        painter.setBrush(QBrush(grad_fondo))
        painter.drawEllipse(area_red.center(), area_red.width() * 0.42, area_red.height() * 0.42)
        painter.restore()

        self._calcular_posiciones(area_red)

        prog = min(1.0, max(0.0, self._progreso_animacion))

        # 1. Dibujar aristas
        for u_idx, v_idx, peso in self._aristas_indices:
            if u_idx >= len(self._nodos_geom) or v_idx >= len(self._nodos_geom):
                continue
            nu = self._nodos_geom[u_idx]
            nv = self._nodos_geom[v_idx]

            es_conectada_a_hover = (
                self._nodo_hover is not None
                and (self._nodo_hover.codigo == nu.codigo or self._nodo_hover.codigo == nv.codigo)
            )

            color_arista = QColor(ACENTO if es_conectada_a_hover else estilo.COLOR_RED_ARISTA_ACTIVA)
            color_arista.setAlpha(240 if es_conectada_a_hover else 155)
            grosor = 2.4 if es_conectada_a_hover else min(2.6, 1.2 + peso * 0.4)

            painter.setPen(QPen(color_arista, grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(nu.pos, nv.pos)

        # 2. Dibujar nodos (primero círculos, luego etiquetas del top 6 encima para que nunca queden tapadas)
        for n in self._nodos_geom:
            es_hover = self._nodo_hover is not None and self._nodo_hover.codigo == n.codigo
            r_actual = (n.radio + (3.0 if es_hover else 0.0)) * prog

            color_nodo = QColor(n.color_hex)
            if es_hover:
                halo = QColor(ACENTO)
                halo.setAlpha(55)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(halo))
                painter.drawEllipse(n.pos, r_actual + 4.5, r_actual + 4.5)

            grad_n = QRadialGradient(
                QPointF(n.pos.x() - r_actual * 0.3, n.pos.y() - r_actual * 0.3),
                r_actual * 1.35,
            )
            grad_n.setColorAt(0.0, color_nodo.lighter(124))
            grad_n.setColorAt(0.7, color_nodo)
            grad_n.setColorAt(1.0, color_nodo.darker(112))

            painter.setBrush(QBrush(grad_n))
            painter.setPen(QPen(QColor(ACENTO if es_hover else SUPERFICIE), 2.0))
            painter.drawEllipse(n.pos, r_actual, r_actual)

        # 2b. Rótulos en píldora legible para los 6 primeros nodos
        fuente_eti = QFont()
        fuente_eti.setPointSize(estilo.TAMANO_MICRO)
        fuente_eti.setBold(True)
        painter.setFont(fuente_eti)
        fm = QFontMetricsF(fuente_eti)

        for n in self._nodos_geom:
            if n.mostrar_etiqueta and prog >= 0.7:
                es_hover = self._nodo_hover is not None and self._nodo_hover.codigo == n.codigo
                r_actual = (n.radio + (3.0 if es_hover else 0.0)) * prog
                etiqueta = fm.elidedText(n.etiqueta, Qt.TextElideMode.ElideRight, 92.0)
                ancho_p = fm.horizontalAdvance(etiqueta) + 10.0
                alto_p = max(14.0, fm.height() + 2.0)

                x_p = max(
                    rect.left() + 6.0,
                    min(rect.right() - ancho_p - 6.0, n.pos.x() - ancho_p / 2.0),
                )
                y_p = min(area_red.bottom() - alto_p, n.pos.y() + r_actual + 2.5)
                rect_eti = QRectF(x_p, y_p, ancho_p, alto_p)

                fondo_p = QColor(estilo.SUPERFICIE_SELECCIONADA if es_hover else SUPERFICIE)
                fondo_p.setAlpha(238)
                painter.setPen(QPen(QColor(ACENTO if es_hover else estilo.LINEA), 1.0))
                painter.setBrush(QBrush(fondo_p))
                painter.drawRoundedRect(rect_eti, 4.0, 4.0)

                painter.setPen(QPen(QColor(PRIMARIO if es_hover else TEXTO)))
                painter.drawText(rect_eti, Qt.AlignmentFlag.AlignCenter, etiqueta)

        # 3. Pie interactivo «Ver análisis completo →»
        fuente_pie = QFont()
        fuente_pie.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_pie.setBold(True)
        painter.setFont(fuente_pie)
        painter.setPen(QPen(QColor(COLOR_DTI)))
        rect_pie = QRectF(rect.left() + margen, rect.bottom() - 20.0, rect.width() - 2 * margen, 16.0)
        painter.drawText(
            rect_pie,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "Ver análisis completo ->",
        )

        # 4. Tooltip al pasar sobre un nodo
        if self._tooltip_visible and self._nodo_hover is not None and self._pos_cursor is not None:
            nh = self._nodo_hover
            filas_tt = [
                ("Categoría", nh.categoria, nh.color_hex),
                ("Coautorías", str(nh.grado), None),
            ]
            self._dibujar_tooltip(painter, rect, self._pos_cursor, nh.nombre_legible, filas_tt)
