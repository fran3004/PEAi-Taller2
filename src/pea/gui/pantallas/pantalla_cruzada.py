"""Pantalla 8: Verificación cruzada entre Python y C++ (Paridad Funcional)."""

from __future__ import annotations

from PySide6.QtCore import QItemSelection, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.ejecutor import EjecutorAsincrono
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_verificacion_cruzada import ResultadoVerificacionCruzada
from pea.servicios.vistas import TablaDatos


class PantallaCruzada(QWidget):
    """Ejecuta de manera cruzada las dos CLI y valida la equivalencia observacional byte a byte."""

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorAsincrono,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.servicio = servicio
        self.ejecutor = ejecutor
        self._resultado: ResultadoVerificacionCruzada | None = None

        self._construir_ui()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Encabezado
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Verificación Cruzada Python / C++", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        self.btn_ejecutar = QPushButton("▶ Ejecutar Verificación Cruzada", self)
        self.btn_ejecutar.setObjectName("primario")
        self.btn_ejecutar.clicked.connect(self._al_ejecutar)
        layout_cabecera.addWidget(self.btn_ejecutar)

        layout_principal.addLayout(layout_cabecera)

        lbl_desc = QLabel(
            "Valida el Principio de Equivalencia Observacional (ADR-0011 e Interoperabilidad.md). "
            "Ejecuta simultáneamente la CLI de Python y el ejecutable C++ con los mismos comandos, "
            "comparando byte a byte el JSON canónico y la ejecución del escenario de mutaciones.",
            self,
        )
        lbl_desc.setObjectName("ayuda")
        lbl_desc.setWordWrap(True)
        layout_principal.addWidget(lbl_desc)

        # Banner de estado global
        self.frame_resultado = QFrame(self)
        self.frame_resultado.setObjectName("panel")
        layout_res = QVBoxLayout(self.frame_resultado)
        self.lbl_estado = QLabel("Presione 'Ejecutar Verificación Cruzada' para iniciar la prueba.", self.frame_resultado)
        self.lbl_estado.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout_res.addWidget(self.lbl_estado)
        layout_principal.addWidget(self.frame_resultado)

        # Splitter: Tabla de pasos a la izquierda, Comparador de salida a la derecha
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        self.tabla_pasos = QTableView(splitter)
        self.modelo_pasos = ModeloTabla(parent=self.tabla_pasos)
        self.tabla_pasos.setModel(self.modelo_pasos)
        self.tabla_pasos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_pasos.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tabla_pasos.selectionModel().selectionChanged.connect(self._al_seleccionar_paso)
        splitter.addWidget(self.tabla_pasos)

        # Visor de salidas comparadas
        frame_visores = QFrame(splitter)
        layout_vis = QHBoxLayout(frame_visores)
        layout_vis.setContentsMargins(0, 8, 0, 0)
        layout_vis.setSpacing(12)

        # Salida Python
        col_py = QVBoxLayout()
        col_py.addWidget(QLabel("Salida CLI Python:", frame_visores))
        self.txt_out_py = QPlainTextEdit(frame_visores)
        self.txt_out_py.setReadOnly(True)
        self.txt_out_py.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        col_py.addWidget(self.txt_out_py)
        layout_vis.addLayout(col_py)

        # Salida C++
        col_cpp = QVBoxLayout()
        col_cpp.addWidget(QLabel("Salida CLI C++:", frame_visores))
        self.txt_out_cpp = QPlainTextEdit(frame_visores)
        self.txt_out_cpp.setReadOnly(True)
        self.txt_out_cpp.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        col_cpp.addWidget(self.txt_out_cpp)
        layout_vis.addLayout(col_cpp)

        splitter.addWidget(frame_visores)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout_principal.addWidget(splitter)

    def _al_ejecutar(self) -> None:
        self.btn_ejecutar.setEnabled(False)
        self.lbl_estado.setText("Ejecutando verificaciones en segundo plano...")
        self.frame_resultado.setStyleSheet("background-color: #E3ECF8; border: 1px solid #0D47A1;")

        def trabajo() -> ResultadoVerificacionCruzada:
            return self.servicio.ejecutar_verificacion_cruzada(usar_base=False)

        def exito(res: ResultadoVerificacionCruzada) -> None:
            self.btn_ejecutar.setEnabled(True)
            self._resultado = res
            self._mostrar_resultado(res)

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_ejecutar.setEnabled(True)
            self.lbl_estado.setText(f"Error durante la verificación: {err}")
            self.frame_resultado.setStyleSheet("background-color: #FDECEA; border: 1px solid #D32F2F;")

        self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)

    def _mostrar_resultado(self, res: ResultadoVerificacionCruzada) -> None:
        if res.exito:
            self.lbl_estado.setText(f"✔ VERIFICACIÓN CRUZADA EXITOSA: {res.mensaje}")
            self.frame_resultado.setStyleSheet("background-color: #E8F5E9; border: 1px solid #2E7D32;")
        else:
            self.lbl_estado.setText(f"✖ FALLO O ADVERTENCIA: {res.mensaje}")
            self.frame_resultado.setStyleSheet("background-color: #FFF4E5; border: 1px solid #ED6C02;")

        filas = []
        for p in res.pasos:
            filas.append(
                (
                    p.nombre,
                    p.comando,
                    f"Py: {p.codigo_python} | C++: {p.codigo_cpp}",
                    "✔ COINCIDEN" if p.coincide else "✖ DIFIEREN",
                    p.detalle,
                )
            )

        tabla = TablaDatos(
            columnas=("Paso de Verificación", "Argumentos", "Códigos Salida", "Resultado", "Detalle"),
            filas=tuple(filas),
            claves=tuple(str(i) for i in range(len(filas))),
        )
        self.modelo_pasos.establecer_tabla(tabla)
        if filas:
            self.tabla_pasos.selectRow(0)

    def _al_seleccionar_paso(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if not self._resultado or not self._resultado.pasos:
            return
        indexes = self.tabla_pasos.selectionModel().selectedRows()
        if not indexes:
            return
        idx = indexes[0].row()
        if 0 <= idx < len(self._resultado.pasos):
            paso = self._resultado.pasos[idx]
            self.txt_out_py.setPlainText(paso.salida_python)
            self.txt_out_cpp.setPlainText(paso.salida_cpp)

