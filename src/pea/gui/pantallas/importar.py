"""Pantalla de importación e ingesta de fuentes (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.6).
- Tres tarjetas de fuente en fila: CSV (con combo de tipo), PDF y URL de SCIENTI.
- Zonas de arrastrar y soltar (Drag and Drop) para archivos locales.
- Tarjeta inferior con la cola FIFO propia de importación.
- Tabla estilizada con píldoras de estado (Pendiente, En proceso, Completada, Falló).
- Procesamiento asíncrono en segundo plano, barra de progreso indeterminada
  y avisos tipo toast al completar cada tarea.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.tabla import TablaEstilizada
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.toast import GestorAvisos, Toast
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    ACENTO,
    FICHA,
    LINEA_FUERTE,
    PRIMARIO,
    RADIO_BOTON,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios


class ZonaSoltarArchivo(QFrame):
    """Zona visual interactiva para arrastrar y soltar archivos o seleccionarlos mediante diálogo."""

    archivo_seleccionado = Signal(str)

    def __init__(
        self,
        extensiones: tuple[str, ...] = (".csv",),
        filtro: str = "Archivos (*.*)",
        placeholder: str = "Arrastre el archivo aquí o examine en su equipo",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("zonaSoltarArchivo")
        self.setAcceptDrops(True)
        self._extensiones = tuple(ext.lower() for ext in extensiones)
        self._filtro = filtro
        self._placeholder = placeholder
        self._ruta_archivo: str = ""

        self._construir_ui()
        self._establecer_estilo(arrastrando=False)

    def _construir_ui(self) -> None:
        self.setFixedHeight(88)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Ícono decorativo
        self._lbl_icono = QLabel("📁", self)
        self._lbl_icono.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt;")
        layout.addWidget(self._lbl_icono)

        # Columna de texto (nombre de archivo o ayuda)
        col_textos = QVBoxLayout()
        col_textos.setContentsMargins(0, 0, 0, 0)
        col_textos.setSpacing(2)

        self._lbl_principal = QLabel(self._placeholder, self)
        self._lbl_principal.setStyleSheet(
            f"font-size: {TAMANO_CUERPO}pt; font-weight: 500; color: {TEXTO};"
        )
        self._lbl_principal.setWordWrap(True)
        col_textos.addWidget(self._lbl_principal)

        self._lbl_subtexto = QLabel(f"Formatos aceptados: {', '.join(self._extensiones).upper()}", self)
        self._lbl_subtexto.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};"
        )
        col_textos.addWidget(self._lbl_subtexto)

        layout.addLayout(col_textos, 1)

        # Botón examinar
        self.btn_examinar = QPushButton("Examinar...", self)
        self.btn_examinar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_examinar.clicked.connect(self._al_examinar)
        layout.addWidget(self.btn_examinar)

        # Botón limpiar (inicialmente oculto)
        self.btn_limpiar = QPushButton("✕", self)
        self.btn_limpiar.setToolTip("Quitar archivo")
        self.btn_limpiar.setFixedWidth(28)
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.setVisible(False)
        self.btn_limpiar.clicked.connect(self.limpiar)
        layout.addWidget(self.btn_limpiar)

    def _establecer_estilo(self, arrastrando: bool) -> None:
        if arrastrando:
            borde = f"2px dashed {ACENTO}"
            fondo = "{estilo.INFO_FONDO}"
        else:
            borde = f"2px dashed {LINEA_FUERTE}"
            fondo = FICHA

        self.setStyleSheet(
            f"QFrame#zonaSoltarArchivo {{"
            f"  background-color: {fondo};"
            f"  border: {borde};"
            f"  border-radius: {RADIO_BOTON + 2}px;"
            f"}}"
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ruta = urls[0].toLocalFile()
                if not self._extensiones or any(ruta.lower().endswith(ext) for ext in self._extensiones):
                    event.acceptProposedAction()
                    self._establecer_estilo(arrastrando=True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._establecer_estilo(arrastrando=False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._establecer_estilo(arrastrando=False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                ruta = urls[0].toLocalFile()
                if not self._extensiones or any(ruta.lower().endswith(ext) for ext in self._extensiones):
                    self.establecer_ruta(ruta)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def _al_examinar(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", self._filtro)
        if ruta:
            self.establecer_ruta(ruta)

    def establecer_ruta(self, ruta: str) -> None:
        self._ruta_archivo = ruta.strip()
        if self._ruta_archivo:
            nombre = Path(self._ruta_archivo).name
            self._lbl_principal.setText(nombre)
            self._lbl_principal.setStyleSheet(
                f"font-size: {TAMANO_CUERPO}pt; font-weight: bold; color: {PRIMARIO};"
            )
            self.btn_limpiar.setVisible(True)
            self.archivo_seleccionado.emit(self._ruta_archivo)
        else:
            self.limpiar()

    def ruta(self) -> str:
        return self._ruta_archivo

    def limpiar(self) -> None:
        self._ruta_archivo = ""
        self._lbl_principal.setText(self._placeholder)
        self._lbl_principal.setStyleSheet(
            f"font-size: {TAMANO_CUERPO}pt; font-weight: 500; color: {TEXTO};"
        )
        self.btn_limpiar.setVisible(False)
        self.archivo_seleccionado.emit("")


class PantallaImportar(QWidget):
    """Pantalla oficial de importación e ingesta de fuentes (Sección 6.6)."""

    datos_modificados = Signal()
    solicitar_navegacion = Signal(object)

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaImportar")
        self.servicio = servicio
        self.ejecutor = ejecutor
        self._filtro_actual: FiltroAnios | None = None

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 20, 24, 20)
        layout_principal.setSpacing(18)

        # -------------------------------------------------------------------
        # 1. Cabecera de la pantalla
        # -------------------------------------------------------------------
        caja_titulo = QVBoxLayout()
        caja_titulo.setContentsMargins(0, 0, 0, 0)
        caja_titulo.setSpacing(4)

        lbl_titulo = QLabel("Importación e Ingesta de Fuentes", self)
        lbl_titulo.setObjectName("tituloPantalla")
        lbl_titulo.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt; font-weight: 800; color: {TEXTO};")
        caja_titulo.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Encole archivos tabulares CSV, documentos PDF del modelo normativo o enlaces web de "
            "GrupLAC y CvLAC. Las tareas se procesan en la cola propia en memoria sin congelar la interfaz.",
            self,
        )
        lbl_desc.setObjectName("ayuda")
        lbl_desc.setStyleSheet(f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        lbl_desc.setWordWrap(True)
        caja_titulo.addWidget(lbl_desc)

        layout_principal.addLayout(caja_titulo)

        # -------------------------------------------------------------------
        # 2. Tres Tarjetas de Fuente en Fila (CSV, PDF, URL)
        # -------------------------------------------------------------------
        layout_fuentes = QHBoxLayout()
        layout_fuentes.setContentsMargins(0, 0, 0, 0)
        layout_fuentes.setSpacing(14)

        # --- Tarjeta 1: CSV ---
        self.tarjeta_csv = Tarjeta(titulo="Archivo Tabular CSV", parent=self)
        lbl_desc_csv = QLabel(
            "Importe datos masivos en formato CSV para grupos, investigadores o productos.",
            self.tarjeta_csv,
        )
        lbl_desc_csv.setWordWrap(True)
        lbl_desc_csv.setStyleSheet(f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        self.tarjeta_csv.agregar_widget(lbl_desc_csv)

        self.zona_csv = ZonaSoltarArchivo(
            extensiones=(".csv",),
            filtro="Archivos CSV (*.csv);;Todos (*.*)",
            placeholder="Arrastre su archivo .csv aquí",
            parent=self.tarjeta_csv,
        )
        self.tarjeta_csv.agregar_widget(self.zona_csv)

        # Campo de compatibilidad directa
        self.txt_ruta_csv = QLineEdit(self.tarjeta_csv)
        self.txt_ruta_csv.setPlaceholderText("Ruta del archivo CSV...")
        self.txt_ruta_csv.setVisible(False)
        self.zona_csv.archivo_seleccionado.connect(self.txt_ruta_csv.setText)

        fila_csv_opts = QHBoxLayout()
        fila_csv_opts.setSpacing(8)

        lbl_tipo = QLabel("Tipo:", self.tarjeta_csv)
        lbl_tipo.setStyleSheet(f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        fila_csv_opts.addWidget(lbl_tipo)

        self.combo_tipo_csv = QComboBox(self.tarjeta_csv)
        self.combo_tipo_csv.addItem("Detección automática", None)
        self.combo_tipo_csv.addItem("Grupos", "grupos")
        self.combo_tipo_csv.addItem("Investigadores", "investigadores")
        self.combo_tipo_csv.addItem("Productos", "productos")
        self.combo_tipo_csv.addItem("Autores / Relaciones", "autores")
        fila_csv_opts.addWidget(self.combo_tipo_csv, 1)

        self.btn_encolar_csv = QPushButton("Encolar CSV", self.tarjeta_csv)
        self.btn_encolar_csv.setObjectName("primario")
        self.btn_encolar_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_encolar_csv.clicked.connect(self._al_encolar_csv)
        fila_csv_opts.addWidget(self.btn_encolar_csv)

        self.tarjeta_csv.layout_contenido.addLayout(fila_csv_opts)
        layout_fuentes.addWidget(self.tarjeta_csv, 1)

        # --- Tarjeta 2: PDF ---
        self.tarjeta_pdf = Tarjeta(titulo="Documento Oficial PDF", parent=self)
        lbl_desc_pdf = QLabel(
            "Documentos oficiales del Modelo de Medición 2024 o normativas de MinCiencias.",
            self.tarjeta_pdf,
        )
        lbl_desc_pdf.setWordWrap(True)
        lbl_desc_pdf.setStyleSheet(f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        self.tarjeta_pdf.agregar_widget(lbl_desc_pdf)

        self.zona_pdf = ZonaSoltarArchivo(
            extensiones=(".pdf",),
            filtro="Documentos PDF (*.pdf);;Todos (*.*)",
            placeholder="Arrastre su archivo .pdf aquí",
            parent=self.tarjeta_pdf,
        )
        self.tarjeta_pdf.agregar_widget(self.zona_pdf)

        # Campo de compatibilidad directa
        self.txt_ruta_pdf = QLineEdit(self.tarjeta_pdf)
        self.txt_ruta_pdf.setPlaceholderText("Ruta del archivo PDF...")
        self.txt_ruta_pdf.setVisible(False)
        self.zona_pdf.archivo_seleccionado.connect(self.txt_ruta_pdf.setText)

        fila_pdf_opts = QHBoxLayout()
        fila_pdf_opts.addStretch()
        self.btn_encolar_pdf = QPushButton("Encolar PDF", self.tarjeta_pdf)
        self.btn_encolar_pdf.setObjectName("primario")
        self.btn_encolar_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_encolar_pdf.clicked.connect(self._al_encolar_pdf)
        fila_pdf_opts.addWidget(self.btn_encolar_pdf)

        self.tarjeta_pdf.layout_contenido.addLayout(fila_pdf_opts)
        layout_fuentes.addWidget(self.tarjeta_pdf, 1)

        # --- Tarjeta 3: URL SCIENTI ---
        self.tarjeta_url = Tarjeta(titulo="Enlace Web SCIENTI", parent=self)
        lbl_desc_url = QLabel(
            "Descarga responsable de páginas públicas de GrupLAC o CvLAC por protocolo HTTPS.",
            self.tarjeta_url,
        )
        lbl_desc_url.setWordWrap(True)
        lbl_desc_url.setStyleSheet(f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        self.tarjeta_url.agregar_widget(lbl_desc_url)

        self.txt_url = QLineEdit(self.tarjeta_url)
        self.txt_url.setPlaceholderText("https://scienti.minciencias.gov.co/gruplac/...")
        self.tarjeta_url.agregar_widget(self.txt_url)

        fila_url_opts = QHBoxLayout()
        fila_url_opts.addStretch()
        self.btn_encolar_url = QPushButton("Encolar URL SCIENTI", self.tarjeta_url)
        self.btn_encolar_url.setObjectName("primario")
        self.btn_encolar_url.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_encolar_url.clicked.connect(self._al_encolar_url)
        fila_url_opts.addWidget(self.btn_encolar_url)

        self.tarjeta_url.layout_contenido.addLayout(fila_url_opts)
        layout_fuentes.addWidget(self.tarjeta_url, 1)

        layout_principal.addLayout(layout_fuentes)

        # -------------------------------------------------------------------
        # 3. Tarjeta Inferior: Cola de Importación
        # -------------------------------------------------------------------
        self.tarjeta_cola = Tarjeta(titulo="Cola de Importación", parent=self)

        # Barra superior de control de la cola (acciones de tarjeta)
        self.lbl_estado_cola = QLabel("Tareas pendientes: 0", self.tarjeta_cola)
        self.lbl_estado_cola.setStyleSheet(f"font-weight: bold; color: {PRIMARIO}; font-size: {estilo.TAMANO_CUERPO}pt;")
        self.tarjeta_cola.agregar_accion(self.lbl_estado_cola)

        self.btn_procesar_siguiente = QPushButton("Procesar siguiente", self.tarjeta_cola)
        self.btn_procesar_siguiente.setObjectName("primario")
        self.btn_procesar_siguiente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_procesar_siguiente.clicked.connect(self._al_procesar_siguiente)
        self.tarjeta_cola.agregar_accion(self.btn_procesar_siguiente)

        self.btn_procesar_todas = QPushButton("Procesar todas", self.tarjeta_cola)
        self.btn_procesar_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_procesar_todas.clicked.connect(self._al_procesar_todas)
        self.tarjeta_cola.agregar_accion(self.btn_procesar_todas)

        # Barra de progreso indeterminada durante procesamiento
        self.barra_progreso = QProgressBar(self.tarjeta_cola)
        self.barra_progreso.setRange(0, 0)
        self.barra_progreso.setFixedHeight(4)
        self.barra_progreso.setTextVisible(False)
        self.barra_progreso.setVisible(False)
        self.barra_progreso.setStyleSheet(
            f"QProgressBar {{ background-color: {FICHA}; border: none; border-radius: 2px; }}"
            f"QProgressBar::chunk {{ background-color: {ACENTO}; border-radius: 2px; }}"
        )
        self.tarjeta_cola.agregar_widget(self.barra_progreso)

        # Tabla estilizada de la cola
        self.tabla_cola = TablaEstilizada(self.tarjeta_cola)
        self.modelo_cola = ModeloTabla(parent=self.tabla_cola.vista)
        self.tabla_cola.establecer_modelo(self.modelo_cola)

        # La columna 3 corresponde al Estado de la tarea ("Pendiente", "En proceso", "Completada", "Falló")
        self.tabla_cola.vista.setItemDelegateForColumn(3, self.tabla_cola.delegado_pildora)

        self.tarjeta_cola.agregar_widget(self.tabla_cola)
        layout_principal.addWidget(self.tarjeta_cola, 1)

    # -----------------------------------------------------------------------
    # Métodos de Encolamiento
    # -----------------------------------------------------------------------

    def _al_encolar_csv(self) -> None:
        ruta = self.zona_csv.ruta() or self.txt_ruta_csv.text().strip()
        if not ruta:
            self._notificar_aviso("Indique o arrastre un archivo tabular CSV.", titulo="Ruta requerida", exito=False)
            return

        tipo = self.combo_tipo_csv.currentData()
        try:
            msg = self.servicio.encolar_csv(ruta, tipo=tipo)
            self.zona_csv.limpiar()
            self.txt_ruta_csv.clear()
            self._notificar_aviso(msg, titulo="Tarea Encolada", exito=True)
            self.refrescar()
            self.datos_modificados.emit()
        except Exception as err:
            self._notificar_aviso(str(err), titulo="Error al encolar CSV", exito=False)

    def _al_encolar_pdf(self) -> None:
        ruta = self.zona_pdf.ruta() or self.txt_ruta_pdf.text().strip()
        if not ruta:
            self._notificar_aviso("Indique o arrastre un documento PDF oficial.", titulo="Ruta requerida", exito=False)
            return

        try:
            msg = self.servicio.encolar_pdf(ruta)
            self.zona_pdf.limpiar()
            self.txt_ruta_pdf.clear()
            self._notificar_aviso(msg, titulo="Tarea Encolada", exito=True)
            self.refrescar()
            self.datos_modificados.emit()
        except Exception as err:
            self._notificar_aviso(str(err), titulo="Error al encolar PDF", exito=False)

    def _al_encolar_url(self) -> None:
        url = self.txt_url.text().strip()
        if not url:
            self._notificar_aviso("Indique la URL oficial de GrupLAC o CvLAC.", titulo="URL requerida", exito=False)
            return

        try:
            msg = self.servicio.encolar_url(url)
            self.txt_url.clear()
            self._notificar_aviso(msg, titulo="Tarea Encolada", exito=True)
            self.refrescar()
            self.datos_modificados.emit()
        except Exception as err:
            self._notificar_aviso(str(err), titulo="Error al encolar URL", exito=False)

    # -----------------------------------------------------------------------
    # Métodos de Procesamiento
    # -----------------------------------------------------------------------

    def _establecer_estado_procesando(self, procesando: bool) -> None:
        self.btn_procesar_siguiente.setEnabled(not procesando)
        self.btn_procesar_todas.setEnabled(not procesando)
        self.btn_encolar_csv.setEnabled(not procesando)
        self.btn_encolar_pdf.setEnabled(not procesando)
        self.btn_encolar_url.setEnabled(not procesando)
        self.barra_progreso.setVisible(procesando)

    def _al_procesar_siguiente(self) -> None:
        if self.servicio.tareas_pendientes() == 0:
            self._notificar_aviso("No hay tareas pendientes en la cola de importación.", titulo="Cola vacía", exito=False)
            return

        self._establecer_estado_procesando(True)

        def trabajo() -> dict[str, Any] | None:
            return self.servicio.procesar_siguiente_tarea()

        def al_terminar(res: dict[str, Any] | None) -> None:
            self._establecer_estado_procesando(False)
            self.refrescar()
            self.datos_modificados.emit()

            if res:
                if res.get("exito"):
                    msg = (
                        f"Procesada con éxito.\n"
                        f"Grupos: {res.get('grupos', 0)} · "
                        f"Investigadores: {res.get('investigadores', 0)} · "
                        f"Productos: {res.get('productos', 0)}"
                    )
                    self._notificar_aviso(msg, titulo="Tarea Completada", exito=True)
                else:
                    err_msg = str(res.get("mensaje") or "Fallo al procesar la tarea")
                    self._notificar_aviso(err_msg, titulo="Fallo en Tarea", exito=False)

        def al_fallar(err: Exception, detalle: str) -> None:
            self._establecer_estado_procesando(False)
            self.refrescar()
            self.datos_modificados.emit()
            self._notificar_aviso(f"Fallo al procesar tarea: {err}", titulo="Error de Ingesta", exito=False)

        if self.ejecutor is not None:
            self.ejecutor.ejecutar(trabajo, al_terminar=al_terminar, al_fallar=al_fallar)
        else:
            try:
                res = trabajo()
                al_terminar(res)
            except Exception as err:
                al_fallar(err, str(err))

    def _al_procesar_todas(self) -> None:
        pendientes = self.servicio.tareas_pendientes()
        if pendientes == 0:
            self._notificar_aviso("No hay tareas pendientes en la cola de importación.", titulo="Cola vacía", exito=False)
            return

        self._establecer_estado_procesando(True)

        def trabajo() -> tuple[int, int, int, int]:
            procesadas = 0
            grupos = 0
            investigadores = 0
            productos = 0
            while self.servicio.tareas_pendientes() > 0:
                res = self.servicio.procesar_siguiente_tarea()
                procesadas += 1
                if res:
                    grupos += int(res.get("grupos", 0))
                    investigadores += int(res.get("investigadores", 0))
                    productos += int(res.get("productos", 0))
            return procesadas, grupos, investigadores, productos

        def al_terminar(datos: tuple[int, int, int, int]) -> None:
            self._establecer_estado_procesando(False)
            self.refrescar()
            self.datos_modificados.emit()
            procesadas, grupos, investigadores, productos = datos
            msg = (
                f"Se procesaron {procesadas} tareas.\n"
                f"Grupos: {grupos} · Investigadores: {investigadores} · Productos: {productos}"
            )
            self._notificar_aviso(msg, titulo="Cola Procesada", exito=True)

        def al_fallar(err: Exception, detalle: str) -> None:
            self._establecer_estado_procesando(False)
            self.refrescar()
            self.datos_modificados.emit()
            self._notificar_aviso(f"Ocurrió un error en la cola: {err}", titulo="Error en Procesamiento", exito=False)

        if self.ejecutor is not None:
            self.ejecutor.ejecutar(trabajo, al_terminar=al_terminar, al_fallar=al_fallar)
        else:
            try:
                datos = trabajo()
                al_terminar(datos)
            except Exception as err:
                al_fallar(err, str(err))

    def _notificar_aviso(self, mensaje: str, titulo: str = "Aviso", exito: bool = True) -> None:
        """Muestra un toast flotante en la ventana principal si está disponible."""
        win = self.window() if self.window() is not None else self
        gestor = getattr(win, "_gestor_toasts", None) or getattr(win, "_gestor_avisos", None)
        if isinstance(gestor, GestorAvisos):
            if exito:
                gestor.mostrar_exito(mensaje, titulo=titulo)
            else:
                gestor.mostrar_error(mensaje, titulo=titulo)
        else:
            try:
                tipo = "exito" if exito else "error"
                toast = Toast(mensaje, titulo=titulo, tipo=tipo, parent=win)
                toast.show()
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # API Pública Requerida
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Actualiza la vista con las tareas pendientes y el historial de la cola."""
        pendientes = self.servicio.tareas_pendientes()
        self.lbl_estado_cola.setText(f"Tareas pendientes: {pendientes}")
        self.btn_procesar_siguiente.setEnabled(pendientes > 0)
        self.btn_procesar_todas.setEnabled(pendientes > 0)

        tabla_datos = self.servicio.tabla_cola()
        self.modelo_cola.establecer_tabla(tabla_datos)
        self.tabla_cola.actualizar_pie()

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Conserva la API uniforme entre todas las pantallas."""
        self._filtro_actual = filtro
