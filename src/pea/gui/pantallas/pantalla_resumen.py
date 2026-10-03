"""Pantalla 2: Resumen general institucional (Panel principal y estadísticas OLAP)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.filtro_anios import BarraFiltroAnios
from pea.gui.componentes.graficos import GraficoBarras, GraficoSeries, GraficoTorta
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.tarjeta_kpi import TarjetaKPI
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, TablaDatos


class PantallaResumen(QWidget):
    """Panel general con métricas agregadas del Hipercubo, gráficos y tablas de clasificación."""

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self._filtro_actual = FiltroAnios()
        self._datos_actuales: dict[str, Any] = {}

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Encabezado
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Resumen General Institucional", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        self.btn_exportar_csv = QPushButton("Exportar tablas (CSV)", self)
        self.btn_exportar_csv.clicked.connect(self._al_exportar_csv)
        layout_cabecera.addWidget(self.btn_exportar_csv)

        self.btn_exportar_png = QPushButton("Exportar gráficos (PNG)", self)
        self.btn_exportar_png.clicked.connect(self._al_exportar_png)
        layout_cabecera.addWidget(self.btn_exportar_png)

        layout_principal.addLayout(layout_cabecera)

        # Barra de filtros temporales
        self.barra_filtro = BarraFiltroAnios(self)
        self.barra_filtro.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout_principal.addWidget(self.barra_filtro)

        # Aviso cuando no hay datos
        self.lbl_sin_datos = QLabel("Sin datos: Conéctese o cargue el catálogo para ver estadísticas.", self)
        self.lbl_sin_datos.setObjectName("sinDatos")
        self.lbl_sin_datos.setStyleSheet("padding: 24px; text-align: center; color: #5F6368;")
        self.lbl_sin_datos.setVisible(False)
        layout_principal.addWidget(self.lbl_sin_datos)

        # Área con desplazamiento para todo el contenido analítico
        self.area_desplazamiento = QScrollArea(self)
        self.area_desplazamiento.setWidgetResizable(True)
        self.area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)

        widget_contenido = QWidget()
        layout_contenido = QVBoxLayout(widget_contenido)
        layout_contenido.setContentsMargins(0, 0, 0, 0)
        layout_contenido.setSpacing(16)

        # Cuatro tarjetas KPI
        layout_kpis = QGridLayout()
        layout_kpis.setSpacing(12)

        self.kpi_productos = TarjetaKPI("Total Productos", "0", "En ventana seleccionada", widget_contenido)
        layout_kpis.addWidget(self.kpi_productos, 0, 0)

        self.kpi_grupos = TarjetaKPI("Grupos Activos", "0", "Con producción académica", widget_contenido)
        layout_kpis.addWidget(self.kpi_grupos, 0, 1)

        self.kpi_investigadores = TarjetaKPI("Investigadores", "0", "Autores vinculados", widget_contenido)
        layout_kpis.addWidget(self.kpi_investigadores, 0, 2)

        self.kpi_promedio = TarjetaKPI("Promedio por Autor", "0.00", "Productos / Investigador", widget_contenido)
        layout_kpis.addWidget(self.kpi_promedio, 0, 3)

        layout_contenido.addLayout(layout_kpis)

        # Gráficos en dos columnas
        layout_graficos = QHBoxLayout()
        layout_graficos.setSpacing(12)

        self.grafico_categorias = GraficoBarras("Distribución por Tipología (Minciencias)", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_categorias)

        self.grafico_validacion = GraficoTorta("Estado de Validación Institucional", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_validacion)

        layout_contenido.addLayout(layout_graficos)

        # Serie temporal de productos por año
        self.grafico_series = GraficoSeries("Evolución Cronológica de Productos por Año", parent=widget_contenido)
        self.grafico_series.setMinimumHeight(240)
        layout_contenido.addWidget(self.grafico_series)

        # Tablas de clasificación Top 5
        frame_tablas = QFrame(widget_contenido)
        frame_tablas.setObjectName("panel")
        layout_split_tablas = QHBoxLayout(frame_tablas)
        layout_split_tablas.setContentsMargins(12, 12, 12, 12)
        layout_split_tablas.setSpacing(16)

        # Columna Top 5 Investigadores
        col_inv = QVBoxLayout()
        lbl_top_inv = QLabel("Top 5 Investigadores con Mayor Producción", frame_tablas)
        lbl_top_inv.setStyleSheet("font-weight: bold; color: #003366;")
        col_inv.addWidget(lbl_top_inv)

        self.tabla_top_inv = QTableView(frame_tablas)
        self.modelo_top_inv = ModeloTabla(parent=self.tabla_top_inv)
        self.tabla_top_inv.setModel(self.modelo_top_inv)
        self.tabla_top_inv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_top_inv.setMaximumHeight(180)
        col_inv.addWidget(self.tabla_top_inv)
        layout_split_tablas.addLayout(col_inv)

        # Columna Top 5 Grupos
        col_grp = QVBoxLayout()
        lbl_top_grp = QLabel("Top 5 Grupos con Mayor Producción", frame_tablas)
        lbl_top_grp.setStyleSheet("font-weight: bold; color: #003366;")
        col_grp.addWidget(lbl_top_grp)

        self.tabla_top_grp = QTableView(frame_tablas)
        self.modelo_top_grp = ModeloTabla(parent=self.tabla_top_grp)
        self.tabla_top_grp.setModel(self.modelo_top_grp)
        self.tabla_top_grp.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_top_grp.setMaximumHeight(180)
        col_grp.addWidget(self.tabla_top_grp)
        layout_split_tablas.addLayout(col_grp)

        layout_contenido.addWidget(frame_tablas)

        self.area_desplazamiento.setWidget(widget_contenido)
        layout_principal.addWidget(self.area_desplazamiento)

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.refrescar()

    def refrescar(self) -> None:
        self._datos_actuales = self.servicio.resumen_general(self._filtro_actual)
        hay_datos = self._datos_actuales.get("hay_datos", False)

        self.lbl_sin_datos.setVisible(not hay_datos)
        self.area_desplazamiento.setVisible(hay_datos)

        if not hay_datos:
            return

        total_prods = self._datos_actuales["total_productos"]
        grupos_activos = self._datos_actuales["grupos_activos"]
        grupos_totales = self._datos_actuales["grupos_totales"]
        invs_activos = self._datos_actuales["investigadores_activos"]
        invs_totales = self._datos_actuales["investigadores_totales"]
        promedio = self._datos_actuales["promedio_por_investigador"]

        self.kpi_productos.actualizar(str(total_prods), f"Filtro: {self._datos_actuales['filtro']}")
        self.kpi_grupos.actualizar(str(grupos_activos), f"De {grupos_totales} registrados")
        self.kpi_investigadores.actualizar(str(invs_activos), f"De {invs_totales} registrados")
        self.kpi_promedio.actualizar(f"{promedio:.2f}", "Promedio ponderado")

        self.grafico_categorias.establecer_datos(self._datos_actuales["productos_por_categoria"])
        self.grafico_validacion.establecer_datos(self._datos_actuales["productos_por_validacion"])
        self.grafico_series.establecer_datos(self._datos_actuales["productos_por_anio"])

        self.modelo_top_inv.establecer_tabla(self._datos_actuales["top_investigadores"])
        self.modelo_top_grp.establecer_tabla(self._datos_actuales["top_grupos"])

    def _al_exportar_csv(self) -> None:
        if not self._datos_actuales:
            return
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportación CSV")
        if not directorio:
            return
        p_dir = Path(directorio)
        ruta_inv = p_dir / "resumen_top_investigadores.csv"
        ruta_grp = p_dir / "resumen_top_grupos.csv"
        self.servicio.exportar_tabla_csv(self._datos_actuales["top_investigadores"], ruta_inv)
        self.servicio.exportar_tabla_csv(self._datos_actuales["top_grupos"], ruta_grp)
        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Tablas exportadas en:\n • {ruta_inv.name}\n • {ruta_grp.name}",
        )

    def _al_exportar_png(self) -> None:
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportación de gráficos")
        if not directorio:
            return
        p_dir = Path(directorio)
        self.grafico_categorias.exportar_png(p_dir / "grafico_categorias.png")
        self.grafico_validacion.exportar_png(p_dir / "grafico_validacion.png")
        self.grafico_series.exportar_png(p_dir / "grafico_series_temporales.png")
        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Gráficos PNG guardados en {p_dir.resolve()}",
        )

