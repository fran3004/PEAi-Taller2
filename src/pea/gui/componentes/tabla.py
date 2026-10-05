"""Tabla de datos institucional estilizada con delegados visuales de PEA-i.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 8 y 6.2).
- Filas de 48 px con espaciado amplio y legible (11 pt).
- Selección institucional con barra de acento (3 px en {estilo.ACENTO}).
- Estados hover ({estilo.SUPERFICIE_GRAFICO}) y selección ({estilo.SUPERFICIE_SELECCIONADA}).
- Encabezado institucional en color FICHA ({estilo.FICHA}) de 10 pt negrita.
- Ordenamiento y filtrado mediante QSortFilterProxyModel.
- Pie descriptivo «Mostrando N de M».
- Delegados:
  * PildoraDelegate: renderiza valores como píldoras semánticas y de datos.
  * AvatarNombreDelegate: círculo de 28 px con iniciales + nombre en negrita.
  * EnlaceDelegate: enlace copiable al portapapeles con cursor de mano.
  * NumeroDelegate: formateo numérico es_CO alineado a la derecha.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import (
    QEvent,
    QModelIndex,
    QRectF,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QHelpEvent,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.avatar import PALETA_DEGRADADOS
from pea.gui.componentes.pildora import resolver_estilo_pildora
from pea.gui.estilo import (
    ACENTO,
    ENLACE,
    FICHA,
    LINEA,
    RADIO_BOTON,
    RADIO_PILDORA,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
)
from pea.gui.formato import formatear_decimal, formatear_entero, iniciales_nombre

# ---------------------------------------------------------------------------
# Rol de modelo para estado activo/inactivo (60% opacidad en delegados)
# ---------------------------------------------------------------------------
ROL_ACTIVO = int(Qt.ItemDataRole.UserRole) + 10


# ---------------------------------------------------------------------------
# Delegados
# ---------------------------------------------------------------------------


class TextoDelegate(QStyledItemDelegate):
    """Renderiza texto en celdas normales con soporte para selección, hover y opacidad de inactivos."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        texto = str(index.data(Qt.ItemDataRole.DisplayRole) or "")

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_SELECCIONADA))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_GRAFICO))
        else:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE))

        if index.column() == 0 and (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(QRectF(option.rect.left(), option.rect.top(), 3.0, option.rect.height()), QColor(ACENTO))

        if index.data(ROL_ACTIVO) is False:
            painter.setOpacity(0.60)

        fuente = QFont()
        fuente.setPointSize(estilo.TAMANO_CUERPO)
        painter.setFont(fuente)
        painter.setPen(QPen(QColor(TEXTO)))

        rect_txt = option.rect.adjusted(12, 0, -12, 0)
        texto_visible = painter.fontMetrics().elidedText(
            texto,
            Qt.TextElideMode.ElideRight,
            max(0, rect_txt.width()),
        )
        painter.drawText(rect_txt, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto_visible)

        painter.restore()

    def helpEvent(self, event: QHelpEvent, view: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        texto = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        if texto:
            QToolTip.showText(event.globalPos(), texto, view)
            return True
        return super().helpEvent(event, view, option, index)


class PildoraDelegate(QStyledItemDelegate):
    """Renderiza el contenido de la celda como una píldora redondeada estilizada."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        valor = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()
        if not valor or valor == "—":
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo de selección si aplica
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_SELECCIONADA))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_GRAFICO))
        else:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE))

        # Barra de acento si es primera columna y seleccionada
        if index.column() == 0 and (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(QRectF(option.rect.left(), option.rect.top(), 3.0, option.rect.height()), QColor(ACENTO))

        if index.data(ROL_ACTIVO) is False:
            painter.setOpacity(0.60)

        fondo_hex, texto_hex = resolver_estilo_pildora(valor)

        # Calcular tamaño de la píldora
        fuente = QFont()
        fuente.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente.setBold(True)
        painter.setFont(fuente)

        fm = painter.fontMetrics()
        ancho_disponible = max(0, option.rect.width() - 20)
        texto_visible = fm.elidedText(valor, Qt.TextElideMode.ElideRight, max(0, ancho_disponible - 16))
        ancho_txt = fm.horizontalAdvance(texto_visible)
        ancho_pildora = min(ancho_txt + 16.0, ancho_disponible)
        alto_pildora = 22.0

        x_pildora = option.rect.left() + 10.0
        y_pildora = option.rect.center().y() - alto_pildora / 2.0
        rect_pildora = QRectF(x_pildora, y_pildora, ancho_pildora, alto_pildora)

        painter.setBrush(QBrush(QColor(fondo_hex)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect_pildora, RADIO_PILDORA, RADIO_PILDORA)

        painter.setPen(QPen(QColor(texto_hex)))
        painter.drawText(rect_pildora, Qt.AlignmentFlag.AlignCenter, texto_visible)

        painter.restore()


class AvatarNombreDelegate(QStyledItemDelegate):
    """Renderiza avatar circular de 28 px con iniciales junto al nombre en negrita."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        nombre = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo de selección / hover
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_SELECCIONADA))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_GRAFICO))
        else:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE))

        if index.column() == 0 and (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(QRectF(option.rect.left(), option.rect.top(), 3.0, option.rect.height()), QColor(ACENTO))

        if index.data(ROL_ACTIVO) is False:
            painter.setOpacity(0.60)

        if not nombre:
            painter.restore()
            return

        diametro = 28.0
        x_avatar = option.rect.left() + 12.0
        y_avatar = option.rect.center().y() - diametro / 2.0
        rect_avatar = QRectF(x_avatar, y_avatar, diametro, diametro)

        # Degradado estable según hash del nombre
        h = int(hashlib.md5(nombre.encode("utf-8")).hexdigest(), 16)
        c_ini_hex, c_fin_hex = PALETA_DEGRADADOS[h % len(PALETA_DEGRADADOS)]

        grad = QLinearGradient(rect_avatar.topLeft(), rect_avatar.bottomRight())
        grad.setColorAt(0.0, QColor(c_ini_hex))
        grad.setColorAt(1.0, QColor(c_fin_hex))

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(estilo.SUPERFICIE), 1.0))
        painter.drawEllipse(rect_avatar)

        # Iniciales en blanco
        fuente_ini = QFont()
        fuente_ini.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_ini.setBold(True)
        painter.setFont(fuente_ini)
        painter.setPen(QPen(QColor(TEXTO_SOBRE_OSCURO)))
        painter.drawText(rect_avatar, Qt.AlignmentFlag.AlignCenter, iniciales_nombre(nombre))

        # Nombre en 11 pt negrita
        fuente_nom = QFont()
        fuente_nom.setPointSize(estilo.TAMANO_CUERPO)
        fuente_nom.setBold(True)
        painter.setFont(fuente_nom)
        painter.setPen(QPen(QColor(TEXTO)))

        x_nom = rect_avatar.right() + 12.0
        rect_nom = QRectF(x_nom, option.rect.top(), option.rect.right() - x_nom - 8.0, option.rect.height())
        painter.drawText(rect_nom, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)

        painter.restore()


class EnlaceDelegate(QStyledItemDelegate):
    """Renderiza enlaces clicables (código CvLAC / GrupLAC) y copia al portapapeles al pulsar."""

    copiado = Signal(str)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        texto = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_SELECCIONADA))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_GRAFICO))
        else:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE))

        if index.column() == 0 and (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(QRectF(option.rect.left(), option.rect.top(), 3.0, option.rect.height()), QColor(ACENTO))

        if index.data(ROL_ACTIVO) is False:
            painter.setOpacity(0.60)

        if not texto or texto == "—":
            painter.restore()
            super().paint(painter, option, index)
            return

        fuente = QFont()
        fuente.setPointSize(estilo.TAMANO_CUERPO)
        fuente.setUnderline(bool(option.state & QStyle.StateFlag.State_MouseOver))
        painter.setFont(fuente)
        painter.setPen(QPen(QColor(ENLACE)))

        rect_txt = option.rect.adjusted(12, 0, -12, 0)
        texto_visible = painter.fontMetrics().elidedText(
            texto,
            Qt.TextElideMode.ElideRight,
            max(0, rect_txt.width()),
        )
        painter.drawText(rect_txt, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto_visible)

        painter.restore()

    def helpEvent(self, event: QHelpEvent, view: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        texto = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        if texto:
            QToolTip.showText(event.globalPos(), texto, view)
            return True
        return super().helpEvent(event, view, option, index)

    def editorEvent(
        self,
        event: QEvent,
        model: Any,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        if event.type() == QEvent.Type.MouseButtonRelease:
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                val = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()
                if val and val != "—":
                    clipboard = QApplication.clipboard()
                    if clipboard is not None:
                        clipboard.setText(val)
                    self.copiado.emit(val)
                    return True
        return super().editorEvent(event, model, option, index)


class NumeroDelegate(QStyledItemDelegate):
    """Alinea a la derecha y formatea enteros o decimales con separador de miles colombiano."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        val = index.data(Qt.ItemDataRole.DisplayRole)

        painter.save()
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_SELECCIONADA))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE_GRAFICO))
        else:
            painter.fillRect(option.rect, QColor(estilo.SUPERFICIE))

        if index.column() == 0 and (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(QRectF(option.rect.left(), option.rect.top(), 3.0, option.rect.height()), QColor(ACENTO))

        if index.data(ROL_ACTIVO) is False:
            painter.setOpacity(0.60)

        if val is None or val == "—":
            texto_formateado = "—"
        elif isinstance(val, int):
            texto_formateado = formatear_entero(val)
        elif isinstance(val, float):
            texto_formateado = formatear_decimal(val)
        else:
            texto_formateado = str(val)

        fuente = QFont()
        fuente.setPointSize(estilo.TAMANO_CUERPO)
        painter.setFont(fuente)
        painter.setPen(QPen(QColor(TEXTO)))

        rect_txt = option.rect.adjusted(6, 0, -8, 0)
        painter.drawText(rect_txt, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, texto_formateado)

        painter.restore()


# ---------------------------------------------------------------------------
# Vista y Contenedor Principal
# ---------------------------------------------------------------------------


class _VistaTablaEstilizada(QTableView):
    """Vista interna de tabla con filas de 48 px y estilos institucionales."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("vistaTablaEstilizada")
        self.setMouseTracking(True)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(True)
        self.setSortingEnabled(True)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(48)

        encabezado_h = self.horizontalHeader()
        encabezado_h.setStretchLastSection(False)
        encabezado_h.setHighlightSections(False)
        encabezado_h.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        encabezado_h.setFixedHeight(38)
        encabezado_h.setDefaultSectionSize(120)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._especificaciones: list[ColumnSpecification] = []
        self._columnas_ocultas: set[int] = set()

        self.setStyleSheet(
            f"QTableView#vistaTablaEstilizada {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"  gridline-color: {estilo.FONDO_APP};"
            f"  selection-background-color: {estilo.SUPERFICIE_SELECCIONADA};"
            f"  selection-color: {TEXTO};"
            f"  font-size: {estilo.TAMANO_CUERPO}pt;"
            f"}}"
            f"QTableView#vistaTablaEstilizada::item {{"
            f"  height: 48px;"
            f"  padding: 4px 8px;"
            f"  border-bottom: 1px solid {estilo.FONDO_APP};"
            f"}}"
            f"QTableView#vistaTablaEstilizada::item:hover {{"
            f"  background-color: {estilo.SUPERFICIE_GRAFICO};"
            f"}}"
            f"QTableView#vistaTablaEstilizada::item:selected {{"
            f"  background-color: {estilo.SUPERFICIE_SELECCIONADA};"
            f"  color: {TEXTO};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {FICHA};"
            f"  color: {TEXTO};"
            f"  font-size: {estilo.TAMANO_AUXILIAR}pt;"
            f"  font-weight: bold;"
            f"  padding: 6px 12px;"
            f"  border: none;"
            f"  border-bottom: 2px solid {LINEA};"
            f"}}"
        )

    def configurar_columnas(self, especificaciones: list[ColumnSpecification]) -> None:
        self._especificaciones = especificaciones
        self._aplicar_columnas()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._aplicar_columnas()

    def _aplicar_columnas(self) -> None:
        if self.model() is None or not self._especificaciones:
            return
        cantidad = self.model().columnCount()
        specs = self._especificaciones[:cantidad]
        if len(specs) < cantidad:
            specs += [ColumnSpecification("contenido", 120, 3)] * (cantidad - len(specs))
        disponibles = max(0, self.viewport().width())
        visibles = set(range(cantidad))
        while sum(specs[i].ancho_minimo for i in visibles) > disponibles:
            candidatos = [i for i in visibles if specs[i].prioridad > 1]
            if not candidatos:
                break
            visibles.remove(max(candidatos, key=lambda i: specs[i].prioridad))
        for indice in range(cantidad):
            visible = indice in visibles
            self.setColumnHidden(indice, not visible)
            if visible:
                spec = specs[indice]
                modo = {
                    "estirar": self.horizontalHeader().ResizeMode.Stretch,
                    "contenido": self.horizontalHeader().ResizeMode.ResizeToContents,
                    "fijo": self.horizontalHeader().ResizeMode.Fixed,
                }[spec.modo]
                self.horizontalHeader().setSectionResizeMode(indice, modo)
                if spec.modo == "fijo":
                    self.setColumnWidth(indice, spec.ancho_minimo)
                elif spec.modo != "estirar":
                    self.setColumnWidth(indice, max(spec.ancho_minimo, self.columnWidth(indice)))


@dataclass(frozen=True)
class ColumnSpecification:
    """Regla responsive para una columna de tabla."""

    modo: str
    ancho_minimo: int
    prioridad: int = 2

    def __post_init__(self) -> None:
        if self.modo not in {"estirar", "contenido", "fijo"}:
            raise ValueError(f"Modo de columna no válido: {self.modo}")
        if self.ancho_minimo < 0:
            raise ValueError("El ancho mínimo de una columna no puede ser negativo")
        if self.prioridad not in {1, 2, 3}:
            raise ValueError("La prioridad de una columna debe ser 1, 2 o 3")


class TablaEstilizada(QWidget):
    """Componente completo de tabla institucional con proxy de ordenamiento y pie."""

    fila_seleccionada = Signal(int)
    clave_seleccionada = Signal(str)
    fila_doble_clic = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tablaEstilizada")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._vista = _VistaTablaEstilizada(self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._vista.setModel(self._proxy)

        # Delegados predeterminados disponibles
        self.delegado_texto = TextoDelegate(self)
        self.delegado_pildora = PildoraDelegate(self)
        self.delegado_avatar = AvatarNombreDelegate(self)
        self.delegado_enlace = EnlaceDelegate(self)
        self.delegado_numero = NumeroDelegate(self)

        layout.addWidget(self._vista)

        # Pie con conteo
        self._lbl_pie = QLabel("Mostrando 0 de 0", self)
        self._lbl_pie.setObjectName("tablaPie")
        self._lbl_pie.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; padding: 2px 4px;")
        layout.addWidget(self._lbl_pie)

        # Conectar señales
        self._vista.clicked.connect(self._al_hacer_clic)
        self._vista.doubleClicked.connect(self._al_doble_clic)
        sm = self._vista.selectionModel()
        if sm is not None:
            sm.selectionChanged.connect(self._al_cambiar_seleccion)

    @property
    def vista(self) -> QTableView:
        """Acceso a la vista QTableView subyacente para configurar delegados y cabeceras."""
        return self._vista

    @property
    def proxy(self) -> QSortFilterProxyModel:
        """Acceso al QSortFilterProxyModel para configurar filtros de texto o columnas."""
        return self._proxy

    def model(self) -> Any:
        """Devuelve el modelo activo (proxy) para compatibilidad directa con QTableView."""
        return self._proxy

    def establecer_modelo(self, modelo: Any) -> None:
        """Asigna el modelo de datos de origen al proxy y actualiza el pie."""
        self._proxy.setSourceModel(modelo)
        self.actualizar_pie()
        # Conectar cambios de modelo para actualizar el pie automáticamente
        if modelo is not None:
            modelo.modelReset.connect(self.actualizar_pie)
            modelo.rowsInserted.connect(lambda *_: self.actualizar_pie())
            modelo.rowsRemoved.connect(lambda *_: self.actualizar_pie())
            sm = self._vista.selectionModel()
            if sm is not None:
                sm.selectionChanged.connect(self._al_cambiar_seleccion)

    def establecer_proxy(self, proxy: QSortFilterProxyModel) -> None:
        """Asigna un proxy personalizado para ordenamiento y filtrado avanzado."""
        self._proxy = proxy
        self._vista.setModel(proxy)
        self.actualizar_pie()
        sm = self._vista.selectionModel()
        if sm is not None:
            sm.selectionChanged.connect(self._al_cambiar_seleccion)

    def establecer_delegado_columna(self, columna: int, delegado: QStyledItemDelegate) -> None:
        """Asigna un delegado visual a una columna específica."""
        self._vista.setItemDelegateForColumn(columna, delegado)

    def configurar_columnas(self, especificaciones: list[ColumnSpecification]) -> None:
        """Configura modos, mínimos y prioridades responsive de las columnas."""
        self._vista.configurar_columnas(especificaciones)

    def actualizar_pie(self, mostrados: int | None = None, total: int | None = None) -> None:
        """Actualiza el texto del pie con las filas visibles y el total."""
        if mostrados is None:
            mostrados = self._proxy.rowCount()
        if total is None:
            src = self._proxy.sourceModel()
            total = src.rowCount() if src is not None else mostrados

        self._lbl_pie.setText(f"Mostrando {mostrados} de {total}")

    def _al_cambiar_seleccion(self, *_: Any) -> None:
        sm = self._vista.selectionModel()
        if sm is None:
            return
        filas_sel = sm.selectedRows()
        if not filas_sel:
            return
        idx_origen = self._proxy.mapToSource(filas_sel[0])
        if not idx_origen.isValid():
            return
        fila = idx_origen.row()
        self.fila_seleccionada.emit(fila)

        src = self._proxy.sourceModel()
        if src is not None and hasattr(src, "obtener_clave_fila"):
            clave = src.obtener_clave_fila(fila)
            if clave:
                self.clave_seleccionada.emit(str(clave))

    def _al_hacer_clic(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        # Si el clic no cambió la fila (ya estaba seleccionada), aseguramos la emisión
        idx_origen = self._proxy.mapToSource(index)
        fila = idx_origen.row()
        src = self._proxy.sourceModel()
        if src is not None and hasattr(src, "obtener_clave_fila"):
            clave = src.obtener_clave_fila(fila)
            if clave:
                self.clave_seleccionada.emit(str(clave))

    def _al_doble_clic(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        idx_origen = self._proxy.mapToSource(index)
        self.fila_doble_clic.emit(idx_origen.row())

    def fila_seleccionada_actual(self) -> int | None:
        """Devuelve el índice de la fila seleccionada en el modelo de origen."""
        sel = self._vista.selectionModel().selectedRows()
        if not sel:
            return None
        idx_origen = self._proxy.mapToSource(sel[0])
        return idx_origen.row()

    def seleccionar_fila(self, fila_origen: int) -> None:
        """Selecciona programáticamente una fila del modelo de origen."""
        src = self._proxy.sourceModel()
        if src is None:
            return
        idx_src = src.index(fila_origen, 0)
        idx_proxy = self._proxy.mapFromSource(idx_src)
        if idx_proxy.isValid():
            self._vista.selectRow(idx_proxy.row())

    def ajustar_columnas(self, anchos: dict[int, int] | None = None) -> None:
        """Ajusta anchos de columna personalizados o automáticos según contenido."""
        if anchos:
            for col, ancho in anchos.items():
                self._vista.setColumnWidth(col, ancho)
        else:
            self._vista.resizeColumnsToContents()
