"""Chip de ventana temporal con popover emergente y barra retrocompatible de filtro de años."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pea.gui.estilo import (
    ACENTO,
    COLOR_DTI,
    LINEA,
    LINEA_FUERTE,
    RADIO_BOTON,
    RADIO_TARJETA,
    SOMBRA_TARJETA_COLOR,
    SOMBRA_TARJETA_DESENFOQUE,
    SOMBRA_TARJETA_DESPLAZAMIENTO,
    SOMBRA_TARJETA_OPACIDAD,
    SUPERFICIE,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


def texto_resumen_filtro(filtro: FiltroAnios) -> str:
    """Genera una descripción corta para mostrar en el chip."""
    if filtro.modo == ModoFiltroAnios.TODOS:
        return "Todos los años"
    if filtro.modo == ModoFiltroAnios.ULTIMOS:
        return f"Últimos {filtro.ultimos_n or 5} años"
    if filtro.modo == ModoFiltroAnios.RANGO:
        d = filtro.desde or 2015
        h = filtro.hasta or 2024
        return f"{d} – {h}"
    if filtro.modo == ModoFiltroAnios.MODELO_2024:
        return "Modelo 2024"
    return "Todos los años"


class PopoverFiltroAnios(QFrame):
    """Menú emergente tipo popover para configurar la ventana temporal global."""

    filtro_cambiado = Signal(object)  # Emite FiltroAnios

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("popoverFiltroAnios")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(360)

        self.setStyleSheet(
            f"QFrame#popoverFiltroAnios {{"
            f"  background-color: {SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_TARJETA}px;"
            f"}}"
            f"QLabel#tituloPopover {{"
            f"  font-weight: bold;"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"  color: {TEXTO};"
            f"}}"
            f"QLabel#ayudaPopover {{"
            f"  font-size: {TAMANO_AUXILIAR}pt;"
            f"  color: {TEXTO_SECUNDARIO};"
            f"}}"
            f"QRadioButton {{"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"  color: {TEXTO};"
            f"  spacing: 8px;"
            f"}}"
        )

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(SOMBRA_TARJETA_DESENFOQUE)
        sombra.setOffset(*SOMBRA_TARJETA_DESPLAZAMIENTO)
        c_sombra = QColor(SOMBRA_TARJETA_COLOR)
        c_sombra.setAlphaF(SOMBRA_TARJETA_OPACIDAD)
        sombra.setColor(c_sombra)
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        lbl_titulo = QLabel("Ventana temporal de análisis", self)
        lbl_titulo.setObjectName("tituloPopover")
        layout.addWidget(lbl_titulo)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)

        # 1. Todos los años
        self.rb_todos = QRadioButton("Todos los años (histórico completo)", self)
        self._grupo.addButton(self.rb_todos)
        layout.addWidget(self.rb_todos)

        # 2. Últimos N años
        fila_ultimos = QHBoxLayout()
        fila_ultimos.setSpacing(8)
        self.rb_ultimos = QRadioButton("Últimos N años:", self)
        self._grupo.addButton(self.rb_ultimos)
        fila_ultimos.addWidget(self.rb_ultimos)

        self.spin_ultimos = QSpinBox(self)
        self.spin_ultimos.setRange(1, 30)
        self.spin_ultimos.setValue(5)
        self.spin_ultimos.setFixedWidth(65)
        fila_ultimos.addWidget(self.spin_ultimos)
        fila_ultimos.addStretch()
        layout.addLayout(fila_ultimos)

        # 3. Rango específico
        fila_rango = QHBoxLayout()
        fila_rango.setSpacing(8)
        self.rb_rango = QRadioButton("Rango:", self)
        self._grupo.addButton(self.rb_rango)
        fila_rango.addWidget(self.rb_rango)

        self.spin_desde = QSpinBox(self)
        self.spin_desde.setRange(1950, 2030)
        self.spin_desde.setValue(2015)
        self.spin_desde.setFixedWidth(70)
        fila_rango.addWidget(self.spin_desde)

        lbl_a = QLabel("a", self)
        fila_rango.addWidget(lbl_a)

        self.spin_hasta = QSpinBox(self)
        self.spin_hasta.setRange(1950, 2030)
        self.spin_hasta.setValue(2024)
        self.spin_hasta.setFixedWidth(70)
        fila_rango.addWidget(self.spin_hasta)
        fila_rango.addStretch()
        layout.addLayout(fila_rango)

        # 4. Modelo 2024
        self.rb_modelo = QRadioButton("Modelo 2024 (Convocatoria Minciencias)", self)
        self._grupo.addButton(self.rb_modelo)
        layout.addWidget(self.rb_modelo)

        self.lbl_detalle = QLabel(
            "Ventana oficial: 5 años para artículos/software/ASC/FRH; "
            "10 años para libros/patentes (corte 2023).",
            self,
        )
        self.lbl_detalle.setObjectName("ayudaPopover")
        self.lbl_detalle.setWordWrap(True)
        self.lbl_detalle.setStyleSheet(f"color: {COLOR_DTI}; font-size: {TAMANO_AUXILIAR}pt; margin-left: 24px;")
        layout.addWidget(self.lbl_detalle)

        # Conectar cambios
        self.rb_todos.toggled.connect(self._al_cambiar)
        self.rb_ultimos.toggled.connect(self._al_cambiar)
        self.rb_rango.toggled.connect(self._al_cambiar)
        self.rb_modelo.toggled.connect(self._al_cambiar)
        self.spin_ultimos.valueChanged.connect(self._al_cambiar)
        self.spin_desde.valueChanged.connect(self._al_cambiar)
        self.spin_hasta.valueChanged.connect(self._al_cambiar)

        self.rb_modelo.setChecked(True)

    def obtener_filtro(self) -> FiltroAnios:
        if self.rb_todos.isChecked():
            modo = ModoFiltroAnios.TODOS
        elif self.rb_ultimos.isChecked():
            modo = ModoFiltroAnios.ULTIMOS
        elif self.rb_rango.isChecked():
            modo = ModoFiltroAnios.RANGO
        else:
            modo = ModoFiltroAnios.MODELO_2024

        return FiltroAnios(
            modo=modo,
            ultimos_n=self.spin_ultimos.value(),
            desde=self.spin_desde.value(),
            hasta=self.spin_hasta.value(),
        )

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        self.blockSignals(True)
        if filtro.modo == ModoFiltroAnios.TODOS:
            self.rb_todos.setChecked(True)
        elif filtro.modo == ModoFiltroAnios.ULTIMOS:
            self.rb_ultimos.setChecked(True)
        elif filtro.modo == ModoFiltroAnios.RANGO:
            self.rb_rango.setChecked(True)
        else:
            self.rb_modelo.setChecked(True)

        if filtro.ultimos_n:
            self.spin_ultimos.setValue(filtro.ultimos_n)
        if filtro.desde:
            self.spin_desde.setValue(filtro.desde)
        if filtro.hasta:
            self.spin_hasta.setValue(filtro.hasta)
        self.blockSignals(False)

    def _al_cambiar(self) -> None:
        self.filtro_cambiado.emit(self.obtener_filtro())


class ChipVentana(QPushButton):
    """Botón con aspecto de chip que muestra la ventana temporal y despliega el popover al pulsar."""

    filtro_cambiado = Signal(object)  # Emite FiltroAnios

    def __init__(
        self,
        filtro_inicial: FiltroAnios | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("chipVentana")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setStyleSheet(
            f"QPushButton#chipVentana {{"
            f"  background-color: {SUPERFICIE};"
            f"  color: {TEXTO};"
            f"  border: 1px solid {LINEA_FUERTE};"
            f"  border-radius: {RADIO_BOTON + 4}px;"
            f"  padding: 6px 14px;"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"  font-weight: 500;"
            f"}}"
            f"QPushButton#chipVentana:hover {{"
            f"  background-color: #EEF3FA;"
            f"  border-color: {ACENTO};"
            f"}}"
            f"QPushButton#chipVentana:focus {{"
            f"  border: 2px solid {ACENTO};"
            f"  padding: 5px 13px;"
            f"}}"
        )

        self._filtro = filtro_inicial or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)
        self._popover = PopoverFiltroAnios(self)
        self._popover.establecer_filtro(self._filtro)
        self._popover.filtro_cambiado.connect(self._al_cambiar_desde_popover)

        self.clicked.connect(self._abrir_popover)
        self._actualizar_etiqueta()

    @property
    def filtro(self) -> FiltroAnios:
        return self._filtro

    def obtener_filtro(self) -> FiltroAnios:
        return self._filtro

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro = filtro
        self._popover.establecer_filtro(filtro)
        self._actualizar_etiqueta()

    def _al_cambiar_desde_popover(self, filtro: FiltroAnios) -> None:
        self._filtro = filtro
        self._actualizar_etiqueta()
        self.filtro_cambiado.emit(filtro)

    def _actualizar_etiqueta(self) -> None:
        desc = texto_resumen_filtro(self._filtro)
        self.setText(f"Ventana: {desc}  ▾")
        self.setAccessibleName(f"Filtro de ventana temporal: {desc}")

    def _abrir_popover(self) -> None:
        pos_global = self.mapToGlobal(QPoint(0, self.height() + 4))
        self._popover.move(pos_global)
        self._popover.show()


__all__ = ["ChipVentana", "PopoverFiltroAnios", "texto_resumen_filtro"]
