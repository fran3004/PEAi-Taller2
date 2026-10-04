"""Pantalla 3: Análisis por Grupo de Investigación (Ficha analítica y multilista)."""

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


class PantallaGrupo(QWidget):
    """Ficha técnica y métricas OLAP de un grupo de investigación seleccionado."""

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self._filtro_actual = FiltroAnios()
        self._datos_grupo: dict[str, Any] = {}

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Barra superior con selector de grupo
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Análisis por Grupo de Investigación", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        lbl_sel = QLabel("Grupo:", self)
        lbl_sel.setStyleSheet("font-weight: bold;")
        layout_cabecera.addWidget(lbl_sel)

        self.combo_grupo = QComboBox(self)
        self.combo_grupo.setMinimumWidth(280)
        self.combo_grupo.currentIndexChanged.connect(self._al_cambiar_grupo)
        layout_cabecera.addWidget(self.combo_grupo)

        self.btn_exportar = QPushButton("Exportar grupo (CSV)", self)
        self.btn_exportar.clicked.connect(self._al_exportar_csv)
        layout_cabecera.addWidget(self.btn_exportar)

        layout_principal.addLayout(layout_cabecera)

        # Barra de filtros temporales
        self.barra_filtro = BarraFiltroAnios(self)
        self.barra_filtro.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout_principal.addWidget(self.barra_filtro)

        # Aviso sin datos
        self.lbl_sin_datos = QLabel("No hay grupos registrados o seleccionados.", self)
        self.lbl_sin_datos.setObjectName("sinDatos")
        self.lbl_sin_datos.setStyleSheet("padding: 24px; text-align: center; color: #5F6368;")
        self.lbl_sin_datos.setVisible(False)
        layout_principal.addWidget(self.lbl_sin_datos)

        # Área con desplazamiento
        self.area_desplazamiento = QScrollArea(self)
        self.area_desplazamiento.setWidgetResizable(True)
        self.area_desplazamiento.setFrameShape(QFrame.Shape.NoFrame)

        widget_contenido = QWidget()
        layout_contenido = QVBoxLayout(widget_contenido)
        layout_contenido.setContentsMargins(0, 0, 0, 0)
        layout_contenido.setSpacing(14)

        # Ficha del grupo
        self.frame_ficha = QFrame(widget_contenido)
        self.frame_ficha.setObjectName("panel")
        layout_ficha = QHBoxLayout(self.frame_ficha)
        layout_ficha.setContentsMargins(16, 12, 16, 12)

        col_izq = QVBoxLayout()
        self.lbl_nombre_grupo = QLabel("Nombre del Grupo", self.frame_ficha)
        self.lbl_nombre_grupo.setStyleSheet("font-size: 16px; font-weight: bold; color: #003366;")
        self.lbl_lider_grupo = QLabel("Líder: —", self.frame_ficha)
        col_izq.addWidget(self.lbl_nombre_grupo)
        col_izq.addWidget(self.lbl_lider_grupo)
        layout_ficha.addLayout(col_izq)

        layout_ficha.addStretch()

        col_der = QVBoxLayout()
        self.lbl_categoria_grupo = QLabel("Categoría: —", self.frame_ficha)
        self.lbl_categoria_grupo.setStyleSheet("font-weight: bold;")
        self.lbl_estado_grupo = QLabel("Estado: Activo", self.frame_ficha)
        col_der.addWidget(self.lbl_categoria_grupo)
        col_der.addWidget(self.lbl_estado_grupo)
        layout_ficha.addLayout(col_der)

        layout_contenido.addWidget(self.frame_ficha)

        # Tarjetas KPI
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(12)

        self.kpi_total = TarjetaKPI("Total Productos", "0", "En el grupo", widget_contenido)
        layout_kpis.addWidget(self.kpi_total)

        self.kpi_porcentaje = TarjetaKPI("Aporte Institucional", "0.0%", "Sobre la universidad", widget_contenido)
        layout_kpis.addWidget(self.kpi_porcentaje)

        self.kpi_promedio = TarjetaKPI("Promedio por Autor", "0.00", "Productos / Investigador", widget_contenido)
        layout_kpis.addWidget(self.kpi_promedio)

        layout_contenido.addLayout(layout_kpis)

        # Gráficos
        layout_graficos = QHBoxLayout()
        layout_graficos.setSpacing(12)

        self.grafico_categorias = GraficoBarras("Tipología del Grupo", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_categorias)

        self.grafico_series = GraficoSeries("Producción Anual del Grupo", parent=widget_contenido)
        layout_graficos.addWidget(self.grafico_series)

        layout_contenido.addLayout(layout_graficos)

        # Pestañas con tablas: Integrantes y Productos
        self.pestanas = QTabWidget(widget_contenido)

        # Pestaña Integrantes
        self.tabla_integrantes = QTableView(self.pestanas)
        self.modelo_integrantes = ModeloTabla(parent=self.tabla_integrantes)
        self.tabla_integrantes.setModel(self.modelo_integrantes)
        self.tabla_integrantes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pestanas.addTab(self.tabla_integrantes, "Integrantes y Coautores")

        # Pestaña Productos
        self.tabla_productos = QTableView(self.pestanas)
        self.modelo_productos = ModeloTabla(parent=self.tabla_productos)
        self.tabla_productos.setModel(self.modelo_productos)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.pestanas.addTab(self.tabla_productos, "Productos Enlazados en Multilista")

        layout_contenido.addWidget(self.pestanas)

        self.area_desplazamiento.setWidget(widget_contenido)
        layout_principal.addWidget(self.area_desplazamiento)

    def _al_cambiar_grupo(self) -> None:
        self.cargar_grupo_actual()

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.cargar_grupo_actual()

    def refrescar(self) -> None:
        codigo_previo = self.combo_grupo.currentData()
        self.combo_grupo.blockSignals(True)
        self.combo_grupo.clear()
        opciones = self.servicio.opciones_grupos()
        for cod, nom in opciones:
            self.combo_grupo.addItem(f"{nom} ({cod})", cod)
        self.combo_grupo.blockSignals(False)

        if opciones:
            idx = self.combo_grupo.findData(codigo_previo)
            self.combo_grupo.setCurrentIndex(max(0, idx))
            self.cargar_grupo_actual()
        else:
            self.lbl_sin_datos.setVisible(True)
            self.area_desplazamiento.setVisible(False)

    def cargar_grupo_actual(self) -> None:
        codigo = self.combo_grupo.currentData()
        if not codigo:
            self.lbl_sin_datos.setVisible(True)
            self.area_desplazamiento.setVisible(False)
            return

        try:
            self._datos_grupo = self.servicio.vista_grupo(codigo, self._filtro_actual)
            self.lbl_sin_datos.setVisible(False)
            self.area_desplazamiento.setVisible(True)
        except Exception:
            self.lbl_sin_datos.setVisible(True)
            self.area_desplazamiento.setVisible(False)
            return

        self.lbl_nombre_grupo.setText(f"{self._datos_grupo['nombre']} ({self._datos_grupo['codigo']})")
        self.lbl_lider_grupo.setText(f"Líder: {self._datos_grupo['lider']}")
        self.lbl_categoria_grupo.setText(f"Categoría: {self._datos_grupo['categoria']}")
        self.lbl_estado_grupo.setText(f"Estado: {'Activo' if self._datos_grupo['activo'] else 'Inactivo'}")

        self.kpi_total.actualizar(str(self._datos_grupo["total_productos"]), f"Filtro: {self._datos_grupo['filtro']}")
        self.kpi_porcentaje.actualizar(f"{self._datos_grupo['porcentaje_sobre_institucion']:.2f} %", "Sobre producción total")
        self.kpi_promedio.actualizar(f"{self._datos_grupo['promedio_por_investigador']:.2f}", "Productos / Integrante")

        self.grafico_categorias.establecer_datos(self._datos_grupo["productos_por_categoria"])
        self.grafico_series.establecer_datos(self._datos_grupo["productos_por_anio"])

        self.modelo_integrantes.establecer_tabla(self._datos_grupo["integrantes"])
        self.modelo_productos.establecer_tabla(self._datos_grupo["productos"])

    def _al_exportar_csv(self) -> None:
        if not self._datos_grupo:
            return
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportación CSV")
        if not directorio:
            return
        cod = self._datos_grupo["codigo"]
        p_dir = Path(directorio)
        ruta_int = p_dir / f"grupo_{cod}_integrantes.csv"
        ruta_prd = p_dir / f"grupo_{cod}_productos.csv"
        self.servicio.exportar_tabla_csv(self._datos_grupo["integrantes"], ruta_int)
        self.servicio.exportar_tabla_csv(self._datos_grupo["productos"], ruta_prd)
        QMessageBox.information(
            self,
            "Exportación exitosa",
            f"Archivos guardados:\n • {ruta_int.name}\n • {ruta_prd.name}",
        )

