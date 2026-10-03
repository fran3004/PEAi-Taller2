"""Pantalla 5: Catálogo y detalle por Producto de Investigación."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QItemSelection, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.filtro_anios import BarraFiltroAnios
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios


class PantallaProducto(QWidget):
    """Catálogo general de productos de investigación con buscador y ficha de detalle."""

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self._filtro_actual = FiltroAnios()
        self._producto_seleccionado: dict[str, Any] | None = None

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(12)

        # Encabezado
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Catálogo por Producto Científico", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        self.btn_exportar = QPushButton("Exportar catálogo (CSV)", self)
        self.btn_exportar.clicked.connect(self._al_exportar_csv)
        layout_cabecera.addWidget(self.btn_exportar)

        layout_principal.addLayout(layout_cabecera)

        # Barra de filtros temporales
        self.barra_filtro = BarraFiltroAnios(self)
        self.barra_filtro.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout_principal.addWidget(self.barra_filtro)

        # Barra de búsqueda y filtros adicionales
        frame_filtros = QFrame(self)
        frame_filtros.setObjectName("panel")
        layout_filtros = QHBoxLayout(frame_filtros)
        layout_filtros.setContentsMargins(12, 8, 12, 8)
        layout_filtros.setSpacing(10)

        self.txt_buscar = QLineEdit(frame_filtros)
        self.txt_buscar.setPlaceholderText("Buscar por título, código o autor...")
        self.txt_buscar.textChanged.connect(self._al_buscar)
        layout_filtros.addWidget(self.txt_buscar)

        # Combo tipología
        self.combo_tipo = QComboBox(frame_filtros)
        self.combo_tipo.addItem("Todas las tipologías", None)
        self.combo_tipo.addItem("GNC (Nuevo Conocimiento)", "GNC")
        self.combo_tipo.addItem("DTI (Tecnología e Innovación)", "DTI")
        self.combo_tipo.addItem("ASC (Apropiación Social)", "ASC")
        self.combo_tipo.addItem("FRH (Formación RH)", "FRH")
        self.combo_tipo.currentIndexChanged.connect(self._al_buscar)
        layout_filtros.addWidget(self.combo_tipo)

        # Combo validación
        self.combo_val = QComboBox(frame_filtros)
        self.combo_val.addItem("Todas las validaciones", None)
        self.combo_val.addItem("Avalado", "Avalado")
        self.combo_val.addItem("Con soporte", "Con soporte")
        self.combo_val.addItem("No avalado", "No avalado")
        self.combo_val.currentIndexChanged.connect(self._al_buscar)
        layout_filtros.addWidget(self.combo_val)

        layout_principal.addWidget(frame_filtros)

        # Zona central dividida: Tabla de productos a la izquierda, Ficha a la derecha
        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Tabla
        self.tabla = QTableView(splitter)
        self.modelo = ModeloTabla(parent=self.tabla)
        self.tabla.setModel(self.modelo)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tabla.selectionModel().selectionChanged.connect(self._al_seleccionar_fila)
        splitter.addWidget(self.tabla)

        # Ficha lateral de detalle
        self.frame_detalle = QFrame(splitter)
        self.frame_detalle.setObjectName("panel")
        self.frame_detalle.setMinimumWidth(320)
        layout_det = QVBoxLayout(self.frame_detalle)
        layout_det.setContentsMargins(16, 16, 16, 16)
        layout_det.setSpacing(10)

        lbl_det_titulo = QLabel("Ficha Técnica del Producto", self.frame_detalle)
        lbl_det_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #003366;")
        layout_det.addWidget(lbl_det_titulo)

        self.lbl_det_codigo = QLabel("Código: —", self.frame_detalle)
        self.lbl_det_codigo.setStyleSheet("font-weight: bold;")
        layout_det.addWidget(self.lbl_det_codigo)

        self.lbl_det_nombre = QLabel("Seleccione un producto de la tabla.", self.frame_detalle)
        self.lbl_det_nombre.setWordWrap(True)
        layout_det.addWidget(self.lbl_det_nombre)

        self.lbl_det_tipo = QLabel("Tipología: —", self.frame_detalle)
        layout_det.addWidget(self.lbl_det_tipo)

        self.lbl_det_subtipo = QLabel("Subtipo: —", self.frame_detalle)
        layout_det.addWidget(self.lbl_det_subtipo)

        self.lbl_det_ano = QLabel("Año: —", self.frame_detalle)
        layout_det.addWidget(self.lbl_det_ano)

        self.lbl_det_validacion = QLabel("Validación: —", self.frame_detalle)
        layout_det.addWidget(self.lbl_det_validacion)

        self.lbl_det_grupo = QLabel("Grupo asociado: —", self.frame_detalle)
        self.lbl_det_grupo.setWordWrap(True)
        layout_det.addWidget(self.lbl_det_grupo)

        self.lbl_det_autores = QLabel("Coautores:\n —", self.frame_detalle)
        self.lbl_det_autores.setWordWrap(True)
        layout_det.addWidget(self.lbl_det_autores)

        # Badge indicador Modelo 2024
        self.lbl_badge_modelo = QLabel("Vigencia Modelo 2024", self.frame_detalle)
        self.lbl_badge_modelo.setStyleSheet(
            "padding: 6px; border-radius: 4px; font-weight: bold; background-color: #E8F5E9; color: #2E7D32;"
        )
        layout_det.addWidget(self.lbl_badge_modelo)

        layout_det.addStretch()
        splitter.addWidget(self.frame_detalle)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout_principal.addWidget(splitter)

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.refrescar()

    def _al_buscar(self) -> None:
        self.refrescar()

    def refrescar(self) -> None:
        texto = self.txt_buscar.text()
        tipo = self.combo_tipo.currentData()
        val = self.combo_val.currentData()

        tabla_datos = self.servicio.tabla_productos(
            filtro=self._filtro_actual,
            texto=texto,
            tipo_mayor=tipo,
            validacion=val,
        )
        self.modelo.establecer_tabla(tabla_datos)

        # Limpiar detalle si la selección ya no existe
        if tabla_datos.vacia:
            self.lbl_det_codigo.setText("Código: —")
            self.lbl_det_nombre.setText("No hay productos coincidentes con los filtros.")
            self.lbl_det_tipo.setText("Tipología: —")
            self.lbl_det_subtipo.setText("Subtipo: —")
            self.lbl_det_ano.setText("Año: —")
            self.lbl_det_validacion.setText("Validación: —")
            self.lbl_det_grupo.setText("Grupo: —")
            self.lbl_det_autores.setText("Coautores:\n —")
            self.lbl_badge_modelo.setVisible(False)

    def _al_seleccionar_fila(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        indexes = self.tabla.selectionModel().selectedRows()
        if not indexes:
            return
        fila = indexes[0].row()
        cod = self.modelo.obtener_clave_fila(fila)
        if not cod:
            return

        try:
            det = self.servicio.detalle_producto(cod)
            self.lbl_det_codigo.setText(f"Código: {det['codigo']}")
            self.lbl_det_nombre.setText(f"Título: {det['titulo']}")
            self.lbl_det_tipo.setText(f"Tipología mayor: {det['tipo_mayor']}")
            self.lbl_det_subtipo.setText(f"Subtipo: {det['subtipo']}")
            self.lbl_det_ano.setText(f"Año: {det['ano']}")
            self.lbl_det_validacion.setText(f"Validación: {det['validacion']}")
            self.lbl_det_grupo.setText(f"Grupo asociado: {det['grupo']}")
            autores_texto = "\n • " + "\n • ".join(det["autores"]) if det["autores"] else " —"
            self.lbl_det_autores.setText(f"Coautores vinculados:{autores_texto}")

            en_ventana = det["en_ventana_modelo_2024"]
            self.lbl_badge_modelo.setVisible(True)
            if en_ventana:
                self.lbl_badge_modelo.setText("✔ Dentro de la Ventana del Modelo 2024")
                self.lbl_badge_modelo.setStyleSheet(
                    "padding: 6px; border-radius: 4px; font-weight: bold; background-color: #E8F5E9; color: #2E7D32;"
                )
            else:
                self.lbl_badge_modelo.setText("✖ Fuera de la Ventana del Modelo 2024")
                self.lbl_badge_modelo.setStyleSheet(
                    "padding: 6px; border-radius: 4px; font-weight: bold; background-color: #FFF4E5; color: #ED6C02;"
                )
        except Exception:
            pass

    def _al_exportar_csv(self) -> None:
        tabla = self.modelo.tabla_actual
        if tabla.vacia:
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar catálogo a CSV", "productos.csv", "Archivos CSV (*.csv)")
        if not ruta:
            return
        self.servicio.exportar_tabla_csv(tabla, ruta)
        QMessageBox.information(self, "Exportación exitosa", f"Catálogo guardado en {Path(ruta).name}")

