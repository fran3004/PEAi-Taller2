"""Elemento gráfico de nodo (investigador) para QGraphicsScene.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Radio proporcional a la raíz cuadrada del grado: 8 + 2.5·√grado.
- Color según categoría Minciencias (sección 4.1) con degradado radial y contraste alto.
- Anillo de acento de 3 px cuando está seleccionado.
- Etiqueta «J. Apellido» visible en nodos principales, al acercar el zoom o al pasar el cursor.
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
    QRadialGradient,
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
    PRIMARIO,
    TEXTO,
    TEXTO_SECUNDARIO,
)

if TYPE_CHECKING:
    from pea.gui.red.arista import AristaGrafoItem
    from pea.gui.red.vista_red import VistaRed


def _capitalizar_palabra(palabra: str) -> str:
    if not palabra:
        return ""
    if palabra.islower() or palabra.isupper():
        return palabra[:1].upper() + palabra[1:].lower()
    return palabra


def normalizar_nombre_investigador(nombre: str | None) -> str:
    """Normaliza mayúsculas/minúsculas de un nombre completo de investigador."""
    if not nombre or not nombre.strip():
        return ""
    particulas = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos"}
    partes = [p for p in nombre.strip().split() if p]
    salida: list[str] = []
    for idx, p in enumerate(partes):
        if idx > 0 and p.lower() in particulas:
            salida.append(p.lower())
        else:
            salida.append(_capitalizar_palabra(p))
    return " ".join(salida)


def abreviar_nombre_investigador(nombre: str | None) -> str:
    """Abrevia un nombre de persona al formato reglamentario 'J. Apellido'."""
    if not nombre or not nombre.strip():
        return ""
    partes = [p for p in nombre.strip().split() if p]
    if len(partes) == 1:
        return _capitalizar_palabra(partes[0])
    inicial = partes[0][0].upper()
    apellido = _capitalizar_palabra(partes[-1])
    return f"{inicial}. {apellido}"


def _obtener_iniciales(nombre: str | None) -> str:
    if not nombre or not nombre.strip():
        return "--"
    partes = [p for p in nombre.strip().split() if len(p) > 1]
    if not partes:
        return nombre.strip()[:2].upper()
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


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
        self.nombre_legible: str = normalizar_nombre_investigador(self.nombre) or self.nombre
        self.categoria: str = str(self.datos.get("categoria", "Sin categoría"))
        self.grado: int = int(self.datos.get("grado", 0))
        self.intermediacion: float = float(self.datos.get("intermediacion", 0.0))
        self.grupo_principal: str = str(self.datos.get("grupo_principal", "Sin grupo"))
        self.es_externo: bool = bool(self.datos.get("es_externo", False))

        # Radio según especificación: 8 + 2.5 * math.sqrt(grado)
        self.radio = round(8.0 + 2.5 * math.sqrt(max(0, self.grado)), 1)
        self.etiqueta_abreviada = abreviar_nombre_investigador(self.nombre)
        self.iniciales = _obtener_iniciales(self.nombre)

        # Color cromático institucional por categoría (con alto contraste sobre lienzo claro)
        self.color_relleno = self._resolver_color_categoria(self.categoria)
        self.color_texto = QColor(estilo.SUPERFICIE)

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
        from PySide6.QtWidgets import QApplication
        if QApplication.instance() is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setZValue(2.0 if self.grado > 0 else 1.0)

        # Tooltip accesible y detallado
        rol_txt = " · Colaborador externo" if self.es_externo else ""
        cat_txt = "Emérito" if self.categoria.lower() == "emerito" else (
            "Sin categoría" if self.categoria.lower() == "sin categoria" else self.categoria
        )
        self.setToolTip(
            f"{self.nombre_legible}\n"
            f"Categoría: {cat_txt}{rol_txt}\n"
            f"Grupo: {self.grupo_principal}\n"
            f"Coautores directos: {self.grado}\n"
            f"Centralidad de intermediación: {self.intermediacion:.4f}\n"
            f"(Doble clic para ver ficha en Investigadores)"
        )

    @property
    def nombre_abreviado(self) -> str:
        return self.etiqueta_abreviada

    def _resolver_color_categoria(self, categoria: str) -> QColor:
        cat_baja = (categoria or "").strip().lower()
        if "emérito" in cat_baja or "emerito" in cat_baja or "(ie)" in cat_baja:
            return QColor(COLOR_CAT_EMERITO)
        if "senior" in cat_baja or "(is)" in cat_baja:
            return QColor(COLOR_CAT_SENIOR)
        if "asociado" in cat_baja or "(ia)" in cat_baja:
            return QColor(COLOR_CAT_ASOCIADO)
        if "junior" in cat_baja or "(ij)" in cat_baja:
            return QColor(COLOR_CAT_JUNIOR)
        if self.grado > 0:
            idx = sum(ord(c) for c in (self.codigo or self.nombre)) % len(estilo.PALETA_NODOS_RED)
            return QColor(estilo.PALETA_NODOS_RED[idx])
        return QColor(estilo.COLOR_NODO_AISLADO)

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
            self.setZValue(10.0 if seleccion else (2.0 if self.grado > 0 else 1.0))
            self.update()

    def establecer_resaltado(self, resaltado: bool) -> None:
        """Activa el resaltado de hover (nodo o vecino enfocado)."""
        if self._resaltado != resaltado:
            self._resaltado = resaltado
            self.setZValue(5.0 if resaltado else (10.0 if self._seleccionado else (2.0 if self.grado > 0 else 1.0)))
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
        self.setZValue(10.0 if self._seleccionado else (2.0 if self.grado > 0 else 1.0))
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
        r = self.radio + 8.0
        return QRectF(-r - 44.0, -r - 4.0, 2.0 * (r + 44.0), 2.0 * r + 28.0)

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

        # Control de opacidad
        if self._atenuado and not self._resaltado and not self._seleccionado:
            painter.setOpacity(0.24)
        elif self.grado == 0 and not self._resaltado and not self._seleccionado:
            painter.setOpacity(0.82)
        else:
            painter.setOpacity(1.0)

        r_dibujo = self.radio * 1.12 if (self._resaltado or self._seleccionado) else self.radio

        # 1. Halo / sombra de profundidad y anillo de selección (3 px ACENTO)
        if self._seleccionado or self._resaltado:
            halo_col = QColor(ACENTO if self._seleccionado else PRIMARIO)
            halo_col.setAlpha(48)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(halo_col))
            painter.drawEllipse(QPointF(0, 0), r_dibujo + 5.5, r_dibujo + 5.5)

            if self._seleccionado:
                pen_anillo = QPen(QColor(ACENTO), 3.0)
                painter.setPen(pen_anillo)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(0, 0), r_dibujo + 3.5, r_dibujo + 3.5)
        elif self.grado > 0:
            sombra_col = QColor(self.color_relleno)
            sombra_col.setAlpha(36)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(sombra_col))
            painter.drawEllipse(QPointF(0, 1.5), r_dibujo + 3.0, r_dibujo + 3.0)

        # 2. Círculo principal del nodo con degradado radial suave
        grad = QRadialGradient(QPointF(-r_dibujo * 0.3, -r_dibujo * 0.3), r_dibujo * 1.35)
        grad.setColorAt(0.0, self.color_relleno.lighter(125))
        grad.setColorAt(0.68, self.color_relleno)
        grad.setColorAt(1.0, self.color_relleno.darker(114))

        pen_borde = QPen(
            QColor(estilo.SUPERFICIE),
            2.2 if not self.es_externo else 1.8,
            Qt.PenStyle.SolidLine if not self.es_externo else Qt.PenStyle.DashLine,
        )
        painter.setPen(pen_borde)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(0, 0), r_dibujo, r_dibujo)

        # 3. Iniciales dentro del nodo
        if r_dibujo >= 8.0:
            tam_ini = 7 if r_dibujo < 12.0 else (8 if r_dibujo < 15.0 else estilo.TAMANO_AUXILIAR)
            fuente_ini = QFont(estilo.FAMILIA_FUENTE, tam_ini)
            fuente_ini.setBold(True)
            painter.setFont(fuente_ini)
            painter.setPen(QPen(self.color_texto))
            rect_circulo = QRectF(-r_dibujo, -r_dibujo, 2.0 * r_dibujo, 2.0 * r_dibujo)
            painter.drawText(rect_circulo, Qt.AlignmentFlag.AlignCenter, self.iniciales)

        # 4. Insignia numérica de grado en la esquina superior derecha para nodos conectados
        if self.grado > 0:
            r_badge = 7.0
            bx = r_dibujo * 0.72
            by = -r_dibujo * 0.72
            painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.3))
            painter.setBrush(QBrush(QColor(PRIMARIO if self._seleccionado else estilo.ENCABEZADO_INICIO)))
            painter.drawEllipse(QPointF(bx, by), r_badge, r_badge)

            f_b = QFont(estilo.FAMILIA_FUENTE, 6)
            f_b.setBold(True)
            painter.setFont(f_b)
            painter.setPen(QColor(estilo.SUPERFICIE))
            painter.drawText(
                QRectF(bx - r_badge, by - r_badge, r_badge * 2.0, r_badge * 2.0),
                Qt.AlignmentFlag.AlignCenter,
                str(self.grado),
            )

        # 5. Rótulo de texto («J. Apellido») dentro de píldora legible
        zoom_actual = self.vista.zoom_actual if self.vista is not None else 1.0
        debe_mostrar_etiqueta = (
            zoom_actual >= 0.8
            or self.mostrar_etiqueta_forzada
            or self._resaltado
            or self._seleccionado
        )

        if debe_mostrar_etiqueta and self.etiqueta_abreviada:
            fuente_lbl = QFont(estilo.FAMILIA_FUENTE, 9)
            fuente_lbl.setBold(self._seleccionado or self._resaltado or self.grado > 0)
            painter.setFont(fuente_lbl)

            fm = QFontMetrics(fuente_lbl)
            texto_dib = fm.elidedText(self.etiqueta_abreviada, Qt.TextElideMode.ElideRight, 100)
            ancho_txt = fm.horizontalAdvance(texto_dib)
            alto_txt = fm.height()

            rect_lbl = QRectF(-ancho_txt / 2.0 - 6.0, r_dibujo + 3.5, ancho_txt + 12.0, alto_txt + 3.0)

            fondo_pildora = QColor(estilo.SUPERFICIE_SELECCIONADA if self._seleccionado else estilo.SUPERFICIE)
            fondo_pildora.setAlpha(238)
            borde_pildora = QColor(ACENTO if self._seleccionado else estilo.LINEA)
            borde_pildora.setAlpha(185)
            painter.setPen(QPen(borde_pildora, 1.0))
            painter.setBrush(QBrush(fondo_pildora))
            painter.drawRoundedRect(rect_lbl, 5.0, 5.0)

            color_txt = (
                QColor(PRIMARIO)
                if self._seleccionado
                else (QColor(TEXTO) if self.grado > 0 else QColor(TEXTO_SECUNDARIO))
            )
            painter.setPen(QPen(color_txt))
            painter.drawText(rect_lbl, Qt.AlignmentFlag.AlignCenter, texto_dib)

        painter.restore()
