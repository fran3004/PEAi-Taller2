"""Pantalla 7: Importación de fuentes y gestión de la cola FIFO propia."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.ejecutor import EjecutorAsincrono
from pea.servicios.servicio_aplicacion import ServicioAplicacion


class PantallaImportar(QWidget):
    """Encolamiento y procesamiento asíncrono de fuentes CSV, PDF y URLs SCIENTI."""

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorAsincrono,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.ejecutor = ejecutor

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Encabezado
        lbl_titulo = QLabel("Importación e Ingesta de Fuentes", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_principal.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Encole archivos tabulares CSV, documentos normativos PDF o enlaces web de GrupLAC/CvLAC. "
            "Las tareas se procesan de forma asíncrona mediante la cola propia enlazada en memoria.",
            self,
        )
        lbl_desc.setObjectName("ayuda")
        lbl_desc.setWordWrap(True)
        layout_principal.addWidget(lbl_desc)

        # Paneles de encolamiento en cuadrícula
        grid_fuentes = QGridLayout()
        grid_fuentes.setSpacing(12)

        # 1. Encolar CSV
        box_csv = QGroupBox("Importar Archivo Tabular CSV", self)
        layout_csv = QVBoxLayout(box_csv)
        self.txt_ruta_csv = QLineEdit(box_csv)
        self.txt_ruta_csv.setPlaceholderText("Ruta del archivo CSV...")
        layout_csv.addWidget(self.txt_ruta_csv)

        row_csv_opts = QHBoxLayout()
        btn_sel_csv = QPushButton("Examinar...", box_csv)
        btn_sel_csv.clicked.connect(self._al_examinar_csv)
        row_csv_opts.addWidget(btn_sel_csv)

        self.combo_tipo_csv = QComboBox(box_csv)
        self.combo_tipo_csv.addItem("Detección automática", None)
        self.combo_tipo_csv.addItem("Grupos", "grupos")
        self.combo_tipo_csv.addItem("Investigadores", "investigadores")
        self.combo_tipo_csv.addItem("Productos", "productos")
        self.combo_tipo_csv.addItem("Autores / Relaciones", "autores")
        row_csv_opts.addWidget(self.combo_tipo_csv)

        btn_encolar_csv = QPushButton("Encolar CSV", box_csv)
        btn_encolar_csv.setObjectName("primario")
        btn_encolar_csv.clicked.connect(self._al_encolar_csv)
        row_csv_opts.addWidget(btn_encolar_csv)

        layout_csv.addLayout(row_csv_opts)
        grid_fuentes.addWidget(box_csv, 0, 0)

        # 2. Encolar PDF
        box_pdf = QGroupBox("Importar Documento PDF", self)
        layout_pdf = QVBoxLayout(box_pdf)
        self.txt_ruta_pdf = QLineEdit(box_pdf)
        self.txt_ruta_pdf.setPlaceholderText("Ruta del documento PDF oficial...")
        layout_pdf.addWidget(self.txt_ruta_pdf)

        row_pdf_opts = QHBoxLayout()
        btn_sel_pdf = QPushButton("Examinar...", box_pdf)
        btn_sel_pdf.clicked.connect(self._al_examinar_pdf)
        row_pdf_opts.addWidget(btn_sel_pdf)

        btn_encolar_pdf = QPushButton("Encolar PDF", box_pdf)
        btn_encolar_pdf.setObjectName("primario")
        btn_encolar_pdf.clicked.connect(self._al_encolar_pdf)
        row_pdf_opts.addWidget(btn_encolar_pdf)

        layout_pdf.addLayout(row_pdf_opts)
        grid_fuentes.addWidget(box_pdf, 0, 1)

        # 3. Encolar URL (SCIENTI GrupLAC / CvLAC)
        box_url = QGroupBox("Importar Enlace Web SCIENTI (GrupLAC / CvLAC)", self)
        layout_url = QVBoxLayout(box_url)
        self.txt_url = QLineEdit(box_url)
        self.txt_url.setPlaceholderText("https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=...")
        layout_url.addWidget(self.txt_url)

        row_url_opts = QHBoxLayout()
        row_url_opts.addStretch()
        btn_encolar_url = QPushButton("Encolar URL SCIENTI", box_url)
        btn_encolar_url.setObjectName("primario")
        btn_encolar_url.clicked.connect(self._al_encolar_url)
        row_url_opts.addWidget(btn_encolar_url)
        layout_url.addLayout(row_url_opts)

        grid_fuentes.addWidget(box_url, 1, 0, 1, 2)

        layout_principal.addLayout(grid_fuentes)

        # Barra de control de la cola
        frame_controles_cola = QFrame(self)
        frame_controles_cola.setObjectName("panel")
        layout_ctrl = QHBoxLayout(frame_controles_cola)
        layout_ctrl.setContentsMargins(12, 8, 12, 8)

        self.lbl_estado_cola = QLabel("Tareas en cola: 0", frame_controles_cola)
        self.lbl_estado_cola.setStyleSheet("font-weight: bold; color: #003366;")
        layout_ctrl.addWidget(self.lbl_estado_cola)
        layout_ctrl.addStretch()

        self.btn_procesar_siguiente = QPushButton("Procesar siguiente tarea", frame_controles_cola)
        self.btn_procesar_siguiente.setObjectName("primario")
        self.btn_procesar_siguiente.clicked.connect(self._al_procesar_siguiente)
        layout_ctrl.addWidget(self.btn_procesar_siguiente)

        self.btn_procesar_todas = QPushButton("Procesar todas las tareas", frame_controles_cola)
        self.btn_procesar_todas.clicked.connect(self._al_procesar_todas)
        layout_ctrl.addWidget(self.btn_procesar_todas)

        layout_principal.addWidget(frame_controles_cola)

        # Tabla de tareas
        self.tabla_cola = QTableView(self)
        self.modelo_cola = ModeloTabla(parent=self.tabla_cola)
        self.tabla_cola.setModel(self.modelo_cola)
        self.tabla_cola.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout_principal.addWidget(self.tabla_cola)

    def _al_examinar_csv(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo CSV", "", "Archivos CSV (*.csv);;Todos (*.*)")
        if ruta:
            self.txt_ruta_csv.setText(ruta)

    def _al_examinar_pdf(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar documento PDF", "", "Documentos PDF (*.pdf);;Todos (*.*)")
        if ruta:
            self.txt_ruta_pdf.setText(ruta)

    def _al_encolar_csv(self) -> None:
        ruta = self.txt_ruta_csv.text().strip()
        if not ruta:
            QMessageBox.warning(self, "Ruta requerida", "Indique la ruta al archivo CSV.")
            return
        tipo = self.combo_tipo_csv.currentData()
        try:
            msg = self.servicio.encolar_csv(ruta, tipo=tipo)
            self.txt_ruta_csv.clear()
            QMessageBox.information(self, "Tarea Encolada", msg)
            self.refrescar()
        except Exception as err:
            QMessageBox.warning(self, "Error al encolar CSV", str(err))

    def _al_encolar_pdf(self) -> None:
        ruta = self.txt_ruta_pdf.text().strip()
        if not ruta:
            QMessageBox.warning(self, "Ruta requerida", "Indique la ruta al archivo PDF.")
            return
        try:
            msg = self.servicio.encolar_pdf(ruta)
            self.txt_ruta_pdf.clear()
            QMessageBox.information(self, "Tarea Encolada", msg)
            self.refrescar()
        except Exception as err:
            QMessageBox.warning(self, "Error al encolar PDF", str(err))

    def _al_encolar_url(self) -> None:
        url = self.txt_url.text().strip()
        if not url:
            QMessageBox.warning(self, "URL requerida", "Indique la URL oficial de GrupLAC o CvLAC.")
            return
        try:
            msg = self.servicio.encolar_url(url)
            self.txt_url.clear()
            QMessageBox.information(self, "Tarea Encolada", msg)
            self.refrescar()
        except Exception as err:
            QMessageBox.warning(self, "Error al encolar URL", str(err))

    def _al_procesar_siguiente(self) -> None:
        if self.servicio.tareas_pendientes() == 0:
            QMessageBox.information(self, "Cola vacía", "No hay tareas pendientes en la cola.")
            return

        self.btn_procesar_siguiente.setEnabled(False)
        self.btn_procesar_todas.setEnabled(False)

        def trabajo() -> dict[str, Any] | None:
            return self.servicio.procesar_siguiente_tarea()

        def exito(res: dict[str, Any] | None) -> None:
            self.btn_procesar_siguiente.setEnabled(True)
            self.btn_procesar_todas.setEnabled(True)
            self.refrescar()
            if res:
                if res.get("exito"):
                    QMessageBox.information(
                        self,
                        "Tarea Completada",
                        f"Procesada con éxito.\n"
                        f" • Grupos: {res.get('grupos', 0)}\n"
                        f" • Investigadores: {res.get('investigadores', 0)}\n"
                        f" • Productos: {res.get('productos', 0)}",
                    )
                else:
                    QMessageBox.warning(self, "Fallo en Tarea", f"Error: {res.get('mensaje')}")

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_procesar_siguiente.setEnabled(True)
            self.btn_procesar_todas.setEnabled(True)
            self.refrescar()
            QMessageBox.critical(self, "Error de Ingesta", f"Fallo al procesar tarea: {err}")

        self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)

    def _al_procesar_todas(self) -> None:
        pendientes = self.servicio.tareas_pendientes()
        if pendientes == 0:
            QMessageBox.information(self, "Cola vacía", "No hay tareas pendientes en la cola.")
            return

        self.btn_procesar_siguiente.setEnabled(False)
        self.btn_procesar_todas.setEnabled(False)

        def trabajo() -> int:
            procesadas = 0
            while self.servicio.tareas_pendientes() > 0:
                self.servicio.procesar_siguiente_tarea()
                procesadas += 1
            return procesadas

        def exito(conteo: int) -> None:
            self.btn_procesar_siguiente.setEnabled(True)
            self.btn_procesar_todas.setEnabled(True)
            self.refrescar()
            QMessageBox.information(self, "Cola Procesada", f"Se procesaron {conteo} tareas en su totalidad.")

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_procesar_siguiente.setEnabled(True)
            self.btn_procesar_todas.setEnabled(True)
            self.refrescar()
            QMessageBox.critical(self, "Error en Procesamiento", f"Ocurrió un error: {err}")

        self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)

    def refrescar(self) -> None:
        pendientes = self.servicio.tareas_pendientes()
        self.lbl_estado_cola.setText(f"Tareas pendientes en cola: {pendientes}")
        self.btn_procesar_siguiente.setEnabled(pendientes > 0)
        self.btn_procesar_todas.setEnabled(pendientes > 0)
        self.modelo_cola.establecer_tabla(self.servicio.tabla_cola())

