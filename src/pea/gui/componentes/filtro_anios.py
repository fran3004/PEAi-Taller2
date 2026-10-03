"""Barra de control y selector de filtros temporales por años."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


class BarraFiltroAnios(QFrame):
    """Control de usuario para configurar la ventana temporal de análisis."""

    filtro_cambiado = Signal(object)  # emite FiltroAnios

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        lbl_icono = QLabel("Ventana temporal:", self)
        lbl_icono.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_icono)

        self.combo_modo = QComboBox(self)
        self.combo_modo.addItem("Todos los años", ModoFiltroAnios.TODOS)
        self.combo_modo.addItem("Últimos N años", ModoFiltroAnios.ULTIMOS)
        self.combo_modo.addItem("Rango específico", ModoFiltroAnios.RANGO)
        self.combo_modo.addItem("Modelo 2024 (Convocatoria Minciencias)", ModoFiltroAnios.MODELO_2024)
        layout.addWidget(self.combo_modo)

        # Controles para últimos N años
        self.lbl_ultimos = QLabel("Años:", self)
        self.spin_ultimos = QSpinBox(self)
        self.spin_ultimos.setRange(1, 30)
        self.spin_ultimos.setValue(5)
        layout.addWidget(self.lbl_ultimos)
        layout.addWidget(self.spin_ultimos)

        # Controles para rango específico
        self.lbl_desde = QLabel("Desde:", self)
        self.spin_desde = QSpinBox(self)
        self.spin_desde.setRange(1950, 2030)
        self.spin_desde.setValue(2015)
        self.lbl_hasta = QLabel("Hasta:", self)
        self.spin_hasta = QSpinBox(self)
        self.spin_hasta.setRange(1950, 2030)
        self.spin_hasta.setValue(2024)
        layout.addWidget(self.lbl_desde)
        layout.addWidget(self.spin_desde)
        layout.addWidget(self.lbl_hasta)
        layout.addWidget(self.spin_hasta)

        # Explicación del modelo
        self.lbl_detalle = QLabel(
            "Ventana del Modelo 2024: 5 años para artículos/software/ASC/FRH; 10 años para libros/patentes (corte 2023).",
            self,
        )
        self.lbl_detalle.setStyleSheet("color: #0D47A1; font-style: italic; font-size: 11px;")
        layout.addWidget(self.lbl_detalle)

        layout.addStretch()

        # Conectar señales
        self.combo_modo.currentIndexChanged.connect(self._al_cambiar_modo)
        self.spin_ultimos.valueChanged.connect(self._emitir_cambio)
        self.spin_desde.valueChanged.connect(self._emitir_cambio)
        self.spin_hasta.valueChanged.connect(self._emitir_cambio)

        self._actualizar_visibilidad()

    def _al_cambiar_modo(self) -> None:
        self._actualizar_visibilidad()
        self._emitir_cambio()

    def _actualizar_visibilidad(self) -> None:
        modo = self.combo_modo.currentData()
        es_ultimos = modo == ModoFiltroAnios.ULTIMOS
        es_rango = modo == ModoFiltroAnios.RANGO
        es_modelo = modo == ModoFiltroAnios.MODELO_2024

        self.lbl_ultimos.setVisible(es_ultimos)
        self.spin_ultimos.setVisible(es_ultimos)

        self.lbl_desde.setVisible(es_rango)
        self.spin_desde.setVisible(es_rango)
        self.lbl_hasta.setVisible(es_rango)
        self.spin_hasta.setVisible(es_rango)

        self.lbl_detalle.setVisible(es_modelo)

    def obtener_filtro(self) -> FiltroAnios:
        modo = self.combo_modo.currentData() or ModoFiltroAnios.TODOS
        return FiltroAnios(
            modo=modo,
            ultimos_n=self.spin_ultimos.value(),
            desde=self.spin_desde.value(),
            hasta=self.spin_hasta.value(),
        )

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        idx = self.combo_modo.findData(filtro.modo)
        if idx >= 0:
            self.combo_modo.setCurrentIndex(idx)
        if filtro.ultimos_n:
            self.spin_ultimos.setValue(filtro.ultimos_n)
        if filtro.desde:
            self.spin_desde.setValue(filtro.desde)
        if filtro.hasta:
            self.spin_hasta.setValue(filtro.hasta)
        self._actualizar_visibilidad()

    def _emitir_cambio(self) -> None:
        self.filtro_cambiado.emit(self.obtener_filtro())

