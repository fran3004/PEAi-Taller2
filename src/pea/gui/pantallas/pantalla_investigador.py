"""Pantalla 4: Análisis por Investigador (Ficha analítica y autoría multilista)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.filtro_anios import BarraFiltroAnios
from pea.gui.componentes.graficos import GraficoBarras, GraficoSeries
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.tarjeta_kpi import TarjetaKPI
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios


class PantallaInvestigador(QWidget):
    """Ficha analítica individual de autoría y contribución a grupos."""

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self._filtro_actual = FiltroAnios()
        self._datos_inv: dict[str, Any] = {}

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Barra superior con selector de investigador
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Análisis por Investigador", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        lbl_sel = QLabel("Investigador:", self)
        lbl_sel.setStyleSheet("font-weight: bold;")
        layout_cabecera.addWidget(lbl_sel)

        self.combo_inv = QComboBox(self)
        self.combo_inv.setMinimumWidth(300)
        self.combo_inv.currentIndexChanged.connect(self._al_cambiar_inv)
        layout_cabecera.addWidget(self.combo_inv)

        self.btn_exportar = QPushButton("Exportar investigador (CSV)", self)
        self.btn_exportar.clicked.connect(self._al_exportar_csv)
        layout_cabecera.addWidget(self.btn_exportar)

        layout_principal.addLayout(layout_cabecera)

        # Barra de filtros temporales
        self.barra_filtro = BarraFiltroAnios(self)
        self.barra_filtro.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout_principal.addWidget(self.barra_filtro)

        # Aviso sin datos
        self.lbl_sin_datos = QLabel("No hay investigadores registrados o seleccionados.", self)
        self.lbl_sin_datos.setObjectName("sinDatos")
        self.lbl_sin_datos.setStyleSheet("padding: 24px; text-align: center; color: #5F6368;")
        self.lbl_sin_datos.setVisible(False)
        layout_principal.addWidget(self.lbl_sin_datos)

        # Área desplazable
        self.area_desplazamiento = QScrollArea(self)
        self.area_desplazamiento.setWidgetResizable(True)
        self.area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)

        widget_contenido = QWidget()
        layout_contenido = QVBoxLayout(widget_contenido)
        layout_contenido.setContentsMargins(0, 0, 0, 0)
        layout_contenido.setSpacing(14)

        # Ficha del investigador
        self.frame_ficha = QFrame(widget_contenido)
        self.frame_ficha.setObjectName("panel")
        layout_ficha = QHBoxLayout(self.frame_ficha)
        layout_ficha.setContentsMargins(16, 12, 16, 12)

        col_izq = QVBoxLayout()
        self.lbl_nombre = QLabel("Nombre del Investigador", self.frame_ficha)
        self.lbl_nombre.setStyleSheet("font-size: 16px; font-weight: bold; color: #003366;")
        self.lbl_formacion = QLabel("Formación: —", self.frame_ficha)
        col_izq.addWidget(self.lbl_nombre)
        col_izq.addWidget(self.lbl_formacion)
        layout_ficha.addLayout(col_izq)

        layout_ficha.addStretch()

        col_der = QVBoxLayout()
        self.lbl_categoria = QLabel("Categoría: —", self.frame_ficha)
        self.lbl_categoria.setStyleSheet("font-weight: bold;")
        self.lbl_estado = QLabel("Estado: Activo", self.frame_ficha)
        col_der.addWidget(self.lbl_categoria)
        col_der.addWidget(self.lbl_estado)
        layout_ficha.addLayout(col_der)

        layout_contenido.addWidget(self.frame_ficha)

        # Tarjetas KPI
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(12)

        self.kpi_total = TarjetaKPI("Total Productos", "0", "Autorados", widget_contenido)
        layout_kpis.addWidget(self.kpi_total)

        layout_contenido.addLayout(layout_kpis)

        # Gráficos
        layout_graficos = QHBoxLayout()
        layout_graficos.setSpacing(12)

        self.grafico_categorias = GraficoBarras("Tipología del Investigador", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_categorias)

        self.grafico_series = GraficoSeries("Producción Anual", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_series)

        layout_contenido.addLayout(layout_graficos)

        # Pestañas con tablas: Aportes a grupos, Membresías y Productos
        self.pestanas = QTabWidget(widget_contenido)

        # Pestaña Aportes
        self.tabla_aportes = QTableView(self.pestanas)
        self.modelo_aportes = ModeloTabla(parent=self.tabla_aportes)
        self.tabla_aportes.setModel(self.modelo_aportes)
        self.tabla_aportes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pestanas.addTab(self.tabla_aportes, "Aporte a Grupos de Investigación")

        # Pestaña Membresías
        self.tabla_membresias = QTableView(self.pestanas)
        self.modelo_membresias = ModeloTabla(parent=self.tabla_membresias)
        self.tabla_membresias.setModel(self.modelo_membresias)
        self.tabla_membresias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pestanas.addTab(self.tabla_membresias, "Membresías Registradas")

        # Pestaña Productos
        self.tabla_productos = QTableView(self.pestanas)
        self.modelo_productos = ModeloTabla(parent=self.tabla_productos)
        self.tabla_productos.setModel(self.modelo_productos)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.pestanas.addTab(self.tabla_productos, "Productos Autorados en Multilista")

        layout_contenido.addWidget(self.pestanas)

        self.area_desplazamiento.setWidget(widget_contenido)
        layout_principal.addWidget(self.area_desplazamiento)

    def _al_cambiar_inv(self) -> None:
        self.cargar_inv_actual()

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.cargar_inv_actual()

    def refrescar(self) -> None:
        codigo_previo = self.combo_inv.currentData()
        self.combo_inv.blockSignals(True)
        self.combo_inv.clear()
        opciones = self.servicio.opciones_investigadores()
        for cod, nom in opciones:
            self.combo_inv.addItem(f"{nom} ({cod})", cod)
        self.combo_inv.blockSignals(False)

        if opciones:
            idx = self.combo_inv.findData(codigo_previo)
            self.combo_inv.setCurrentIndex(max(0, idx))
            self.cargar_inv_actual()
        else:
            self.lbl_sin_datos.setVisible(True)
    def cargar_inv_actual(self) -> None:
        codigo = self.combo_inv.currentData()

        if not codigo:
            self.lbl_sin_datos.setVisible(True)
            self.area_desplazamiento.setVisible(False)
            return

        try:
            self._datos_inv = self.servicio.vista_investigador(codigo, self._filtro_actual)
            self.lbl_sin_datos.setVisible(False)
            self.area_desplazamiento.setVisible(True)
        except Exception:
            self.lbl_sin_datos.setVisible(True)
            self.area_desplazamiento.setVisible(False)
            return

        self.lbl_nombre.setText(f"{self._datos_inv['nombre']} ({self._datos_inv['codigo']})")
        self.lbl_formacion.setText(f"Formación académica: {self._datos_inv['formacion']}")
        self.lbl_categoria.setText(f"Categoría: {self._datos_inv['categoria']}")
        self.lbl_estado.setText(f"Estado: {'Activo' if self._datos_inv['activo'] else 'Inactivo'}")

        self.kpi_total.actualizar(str(self._datos_inv["total_productos"]), f"Filtro: {self._datos_inv['filtro']}")

        self.grafico_categorias.establecer_datos(self._datos_inv["productos_por_categoria"])
        self.grafico_series.establecer_datos(self._datos_inv["productos_por_anio"])

        self.modelo_aportes.establecer_tabla(self._datos_inv["aportes"])
        self.modelo_membresias.establecer_tabla(self._datos_inv["membresias"])
        self.modelo_productos.establecer_tabla(self._datos_inv["productos"])

    def _al_exportar_csv(self) -> None:
        if not self._datos_inv:
            return
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportación CSV")
        if not directorio:
            return
        cod = self._datos_inv["codigo"]
        p_dir = Path(directorio)
        ruta_ap = p_dir / f"investigador_{cod}_aportes.csv"
        ruta_prd = p_dir / f"investigador_{cod}_productos.csv"
        self.servicio.exportar_tabla_csv(self._datos_inv["aportes"], ruta_ap)
        self.servicio.exportar_tabla_csv(self._datos_inv["productos"], ruta_prd)
        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Archivos guardados:\n • {ruta_ap.name}\n • {ruta_prd.name}",
        )
