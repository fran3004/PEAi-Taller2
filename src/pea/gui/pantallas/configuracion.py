"""Pantalla de configuración y verificación del sistema (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.7).
- Selector segmentado con dos secciones:
  1. «Conexión»: tarjeta de estado grande (modo, servidor, usuario, revisión local/remota,
     motivo de bloqueo) y formulario de parámetros HTTPS a Supabase.
  2. «Verificación cruzada»: paridad funcional Python / C++ (ADR-0011), tabla de pasos
     con píldoras de resultado y visores comparativos monoespaciados lado a lado.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.pildora import Pildora
from pea.gui.componentes.selector_segmentado import SelectorSegmentado
from pea.gui.componentes.tabla import TablaEstilizada
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    ERROR,
    ERROR_FONDO,
    EXITO,
    EXITO_FONDO,
    FICHA,
    LINEA,
    RADIO_BOTON,
    SUPERFICIE,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_verificacion_cruzada import ResultadoVerificacionCruzada
from pea.servicios.vistas import EstadoAplicacion, FiltroAnios, ModoConexion, TablaDatos


class PantallaConfiguracion(QWidget):
    """Pantalla oficial de configuración y verificación cruzada (Sección 6.7)."""

    estado_actualizado = Signal(object)  # Emite EstadoAplicacion
    datos_modificados = Signal()
    solicitar_navegacion = Signal(object)

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaConfiguracion")
        self.servicio = servicio
        self.ejecutor = ejecutor
        self._resultado_cruzada: ResultadoVerificacionCruzada | None = None
        self._filtro_actual: FiltroAnios | None = None

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 20, 24, 20)
        layout_principal.setSpacing(18)

        # -------------------------------------------------------------------
        # 1. Cabecera con título y selector segmentado
        # -------------------------------------------------------------------
        fila_cabecera = QHBoxLayout()
        fila_cabecera.setContentsMargins(0, 0, 0, 0)
        fila_cabecera.setSpacing(16)

        caja_titulo = QVBoxLayout()
        caja_titulo.setContentsMargins(0, 0, 0, 0)
        caja_titulo.setSpacing(4)

        lbl_titulo = QLabel("Configuración del Sistema", self)
        lbl_titulo.setObjectName("tituloPantalla")
        lbl_titulo.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {TEXTO};")
        caja_titulo.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Administre el acceso seguro a Supabase por HTTPS y verifique la paridad "
            "funcional entre los componentes Python y C++.",
            self,
        )
        lbl_desc.setObjectName("ayuda")
        lbl_desc.setStyleSheet(f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        lbl_desc.setWordWrap(True)
        caja_titulo.addWidget(lbl_desc)

        fila_cabecera.addLayout(caja_titulo, 1)

        # Selector segmentado de sección
        self.selector_seccion = SelectorSegmentado(
            opciones=[
                ("conexion", "Conexión"),
                ("cruzada", "Verificación cruzada"),
            ],
            parent=self,
        )
        self.selector_seccion.opcion_cambiada.connect(self._al_cambiar_seccion)
        fila_cabecera.addWidget(self.selector_seccion, 0, Qt.AlignmentFlag.AlignVCenter)

        layout_principal.addLayout(fila_cabecera)

        # -------------------------------------------------------------------
        # 2. Apilador de vistas (Conexión / Verificación cruzada)
        # -------------------------------------------------------------------
        self._apilador_secciones = QStackedWidget(self)
        layout_principal.addWidget(self._apilador_secciones, 1)

        # Página 0: Conexión
        self._widget_conexion = self._crear_seccion_conexion()
        self._apilador_secciones.addWidget(self._widget_conexion)

        # Página 1: Verificación cruzada
        self._widget_cruzada = self._crear_seccion_cruzada()
        self._apilador_secciones.addWidget(self._widget_cruzada)

    # =======================================================================
    # SECCIÓN 1: CONEXIÓN
    # =======================================================================

    def _crear_seccion_conexion(self) -> QWidget:
        contenedor = QWidget(self)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # --- Tarjeta de Estado Grande ---
        self.tarjeta_estado = Tarjeta(titulo="Estado de la Conexión", parent=contenedor)
        layout_grid_estado = QGridLayout()
        layout_grid_estado.setContentsMargins(0, 0, 0, 0)
        layout_grid_estado.setSpacing(12)

        # Fila 1: Modo e indicador
        lbl_modo_rot = QLabel("Modo de operación:", self.tarjeta_estado)
        lbl_modo_rot.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(lbl_modo_rot, 0, 0)

        fila_modo = QHBoxLayout()
        fila_modo.setSpacing(8)
        self.pildora_modo = Pildora("Desconectado", variante="error", parent=self.tarjeta_estado)
        fila_modo.addWidget(self.pildora_modo)

        self.lbl_estado_resumen = QLabel("No hay conexión activa.", self.tarjeta_estado)
        self.lbl_estado_resumen.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {TAMANO_CUERPO}pt;")
        fila_modo.addWidget(self.lbl_estado_resumen, 1)
        layout_grid_estado.addLayout(fila_modo, 0, 1)

        # Fila 2: Servidor
        lbl_srv_rot = QLabel("Servidor Supabase:", self.tarjeta_estado)
        lbl_srv_rot.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(lbl_srv_rot, 1, 0)

        self.lbl_servidor = QLabel("—", self.tarjeta_estado)
        self.lbl_servidor.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(self.lbl_servidor, 1, 1)

        # Fila 3: Usuario
        lbl_usr_rot = QLabel("Usuario autenticado:", self.tarjeta_estado)
        lbl_usr_rot.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(lbl_usr_rot, 2, 0)

        self.lbl_usuario = QLabel("—", self.tarjeta_estado)
        self.lbl_usuario.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(self.lbl_usuario, 2, 1)

        # Fila 4: Revisiones
        lbl_rev_rot = QLabel("Revisión del esquema:", self.tarjeta_estado)
        lbl_rev_rot.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(lbl_rev_rot, 3, 0)

        self.lbl_revisiones = QLabel("Local: — | Remota: —", self.tarjeta_estado)
        self.lbl_revisiones.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {TAMANO_CUERPO}pt;")
        layout_grid_estado.addWidget(self.lbl_revisiones, 3, 1)

        # Fila 5: Motivo de bloqueo (si existe)
        self.lbl_bloqueo = QLabel("", self.tarjeta_estado)
        self.lbl_bloqueo.setStyleSheet(
            f"background-color: {AVISO_FONDO}; color: {AVISO}; "
            f"border: 1px solid {AVISO}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; font-weight: bold;"
        )
        self.lbl_bloqueo.setVisible(False)
        layout_grid_estado.addWidget(self.lbl_bloqueo, 4, 0, 1, 2)

        self.tarjeta_estado.layout_contenido.addLayout(layout_grid_estado)
        layout.addWidget(self.tarjeta_estado)

        # --- Tarjeta de Formulario de Parámetros ---
        self.tarjeta_form = Tarjeta(titulo="Parámetros de Acceso a Supabase (HTTPS)", parent=contenedor)
        layout_form = QFormLayout()
        layout_form.setContentsMargins(0, 0, 0, 0)
        layout_form.setSpacing(12)

        cfg = self.servicio.configuracion_entorno()

        self.txt_url = QLineEdit(cfg.get("url", ""), self.tarjeta_form)
        self.txt_url.setPlaceholderText("https://xxxxxxxxxxxx.supabase.co")
        layout_form.addRow("URL de Supabase (HTTPS):", self.txt_url)

        self.txt_clave = QLineEdit(cfg.get("clave_publicable", ""), self.tarjeta_form)
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_clave.setPlaceholderText("Clave publicable (sb_publishable_... o anon JWT)")
        layout_form.addRow("Clave publicable:", self.txt_clave)

        self.txt_correo = QLineEdit(cfg.get("correo", ""), self.tarjeta_form)
        self.txt_correo.setPlaceholderText("usuario@unicesar.edu.co (opcional para Auth)")
        layout_form.addRow("Correo de usuario:", self.txt_correo)

        self.txt_pass = QLineEdit(self.tarjeta_form)
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setPlaceholderText("Contraseña del usuario")
        layout_form.addRow("Contraseña:", self.txt_pass)

        self.chk_entorno = QCheckBox("Tomar contraseña de la variable PEA_USUARIO_CLAVE si existe", self.tarjeta_form)
        self.chk_entorno.setChecked(cfg.get("hay_clave_usuario_en_entorno", False))
        layout_form.addRow("", self.chk_entorno)

        self.tarjeta_form.layout_contenido.addLayout(layout_form)

        # Banner de aviso informativo
        self.lbl_aviso = QLabel("", self.tarjeta_form)
        self.lbl_aviso.setWordWrap(True)
        self.lbl_aviso.setVisible(False)
        self.tarjeta_form.agregar_widget(self.lbl_aviso)

        # Botonera de acciones
        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)

        self.btn_conectar = QPushButton("Conectar con Supabase", self.tarjeta_form)
        self.btn_conectar.setObjectName("primario")
        self.btn_conectar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_conectar.clicked.connect(self._al_conectar)
        fila_botones.addWidget(self.btn_conectar)

        self.btn_demo = QPushButton("Cargar datos de demostración", self.tarjeta_form)
        self.btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_demo.clicked.connect(self._al_cargar_demostracion)
        fila_botones.addWidget(self.btn_demo)

        self.btn_desconectar = QPushButton("Cerrar sesión / Desconectar", self.tarjeta_form)
        self.btn_desconectar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_desconectar.clicked.connect(self._al_desconectar)
        fila_botones.addWidget(self.btn_desconectar)

        fila_botones.addStretch()
        self.tarjeta_form.layout_contenido.addLayout(fila_botones)

        layout.addWidget(self.tarjeta_form)
        layout.addStretch(1)

        return contenedor

    # =======================================================================
    # SECCIÓN 2: VERIFICACIÓN CRUZADA
    # =======================================================================

    def _crear_seccion_cruzada(self) -> QWidget:
        contenedor = QWidget(self)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Tarjeta superior con banner y botón
        self.tarjeta_cruzada = Tarjeta(
            titulo="Verificación Cruzada Python / C++ (Paridad Funcional)",
            parent=contenedor,
        )

        lbl_desc_cruzada = QLabel(
            "Valida el Principio de Equivalencia Observacional (ADR-0011 e Interoperabilidad.md). "
            "Ejecuta simultáneamente la CLI de Python y el ejecutable C++ con los mismos comandos, "
            "comparando byte a byte el JSON canónico y la ejecución de mutaciones en memoria.",
            self.tarjeta_cruzada,
        )
        lbl_desc_cruzada.setWordWrap(True)
        lbl_desc_cruzada.setStyleSheet(f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        self.tarjeta_cruzada.agregar_widget(lbl_desc_cruzada)

        self.btn_ejecutar = QPushButton("▶ Ejecutar Verificación Cruzada", self.tarjeta_cruzada)
        self.btn_ejecutar.setObjectName("primario")
        self.btn_ejecutar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ejecutar.clicked.connect(self._al_ejecutar_cruzada)
        self.tarjeta_cruzada.agregar_accion(self.btn_ejecutar)

        # Banner de resultado
        self.frame_resultado = QFrame(self.tarjeta_cruzada)
        self.frame_resultado.setObjectName("panelResultadoCruzada")
        self.frame_resultado.setStyleSheet(
            f"QFrame#panelResultadoCruzada {{"
            f"  background-color: {FICHA};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"  padding: 8px 14px;"
            f"}}"
        )
        layout_res = QVBoxLayout(self.frame_resultado)
        layout_res.setContentsMargins(10, 8, 10, 8)
        self.lbl_estado = QLabel("Presione '▶ Ejecutar Verificación Cruzada' para iniciar la prueba.", self.frame_resultado)
        self.lbl_estado.setStyleSheet(f"font-weight: bold; font-size: {TAMANO_CUERPO}pt; color: {TEXTO};")
        layout_res.addWidget(self.lbl_estado)
        self.tarjeta_cruzada.agregar_widget(self.frame_resultado)

        layout.addWidget(self.tarjeta_cruzada)

        # Splitter vertical: Tabla de pasos arriba, Visores monoespaciados abajo
        splitter = QSplitter(Qt.Orientation.Vertical, contenedor)

        # 1. Tabla de Pasos
        self.tabla_pasos = TablaEstilizada(splitter)
        self.modelo_pasos = ModeloTabla(parent=self.tabla_pasos.vista)
        self.tabla_pasos.establecer_modelo(self.modelo_pasos)

        # Columna 3 es "Resultado" ("✔ COINCIDEN", "✖ DIFIEREN")
        self.tabla_pasos.vista.setItemDelegateForColumn(3, self.tabla_pasos.delegado_pildora)
        self.tabla_pasos.fila_seleccionada.connect(self._al_seleccionar_paso_cruzada)
        splitter.addWidget(self.tabla_pasos)

        # 2. Visores Comparativos Monoespaciados
        frame_visores = QFrame(splitter)
        frame_visores.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"}}"
        )
        layout_vis = QHBoxLayout(frame_visores)
        layout_vis.setContentsMargins(12, 10, 12, 10)
        layout_vis.setSpacing(14)

        # Columna Python
        col_py = QVBoxLayout()
        col_py.setSpacing(4)
        lbl_py = QLabel("Salida CLI Python:", frame_visores)
        lbl_py.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_AUXILIAR}pt;")
        col_py.addWidget(lbl_py)

        self.txt_out_py = QPlainTextEdit(frame_visores)
        self.txt_out_py.setReadOnly(True)
        self.txt_out_py.setStyleSheet(
            f"QPlainTextEdit {{"
            f"  background-color: {FICHA};"
            f"  color: {TEXTO};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: 4px;"
            f"  font-family: Consolas, monospace;"
            f"  font-size: 10pt;"
            f"}}"
        )
        col_py.addWidget(self.txt_out_py)
        layout_vis.addLayout(col_py)

        # Columna C++
        col_cpp = QVBoxLayout()
        col_cpp.setSpacing(4)
        lbl_cpp = QLabel("Salida CLI C++:", frame_visores)
        lbl_cpp.setStyleSheet(f"font-weight: bold; color: {TEXTO}; font-size: {TAMANO_AUXILIAR}pt;")
        col_cpp.addWidget(lbl_cpp)

        self.txt_out_cpp = QPlainTextEdit(frame_visores)
        self.txt_out_cpp.setReadOnly(True)
        self.txt_out_cpp.setStyleSheet(
            f"QPlainTextEdit {{"
            f"  background-color: {FICHA};"
            f"  color: {TEXTO};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: 4px;"
            f"  font-family: Consolas, monospace;"
            f"  font-size: 10pt;"
            f"}}"
        )
        col_cpp.addWidget(self.txt_out_cpp)
        layout_vis.addLayout(col_cpp)

        splitter.addWidget(frame_visores)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        return contenedor

    # -----------------------------------------------------------------------
    # Navegación entre Secciones
    # -----------------------------------------------------------------------

    def _al_cambiar_seccion(self, clave: str) -> None:
        if clave == "conexion":
            self._apilador_secciones.setCurrentIndex(0)
        elif clave == "cruzada":
            self._apilador_secciones.setCurrentIndex(1)

    # -----------------------------------------------------------------------
    # Acciones de Conexión
    # -----------------------------------------------------------------------

    def _mostrar_mensaje(self, texto: str, error: bool = False) -> None:
        self.lbl_aviso.setText(texto)
        if error:
            self.lbl_aviso.setStyleSheet(
                f"background-color: {ERROR_FONDO}; color: {ERROR}; "
                f"border: 1px solid {ERROR}; padding: 8px 12px; border-radius: {RADIO_BOTON}px;"
            )
        else:
            self.lbl_aviso.setStyleSheet(
                f"background-color: {EXITO_FONDO}; color: {EXITO}; "
                f"border: 1px solid {EXITO}; padding: 8px 12px; border-radius: {RADIO_BOTON}px;"
            )
        self.lbl_aviso.setVisible(bool(texto))

    def _al_conectar(self) -> None:
        url = self.txt_url.text().strip()
        clave_pub = self.txt_clave.text().strip()
        correo = self.txt_correo.text().strip()
        clave = self.txt_pass.text()
        usar_entorno = self.chk_entorno.isChecked()

        self._mostrar_mensaje("Estableciendo conexión HTTPS con Supabase...", error=False)
        self.btn_conectar.setEnabled(False)
        self.btn_demo.setEnabled(False)

        def trabajo() -> EstadoAplicacion:
            return self.servicio.conectar(
                url=url,
                clave_publicable=clave_pub,
                correo=correo,
                clave=clave,
                usar_clave_entorno=usar_entorno,
            )

        def exito(est: EstadoAplicacion) -> None:
            self.btn_conectar.setEnabled(True)
            self.btn_demo.setEnabled(True)
            self.txt_pass.clear()
            self._mostrar_mensaje(f"Conexión exitosa. Revisión inicial: {est.revision_local}", error=False)
            self.refrescar()
            self.estado_actualizado.emit(est)
            self.datos_modificados.emit()

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_conectar.setEnabled(True)
            self.btn_demo.setEnabled(True)
            self._mostrar_mensaje(f"Error de conexión: {err}", error=True)
            self.refrescar()

        if self.ejecutor is not None:
            self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)
        else:
            try:
                est = trabajo()
                exito(est)
            except Exception as err:
                fallo(err, str(err))

    def _al_cargar_demostracion(self) -> None:
        try:
            est = self.servicio.cargar_demostracion()
            self._mostrar_mensaje("Datos de demostración cargados en memoria.", error=False)
            self.refrescar()
            self.estado_actualizado.emit(est)
            self.datos_modificados.emit()
        except Exception as err:
            self._mostrar_mensaje(f"Error al cargar demostración: {err}", error=True)

    def _al_desconectar(self) -> None:
        est = self.servicio.desconectar()
        self._mostrar_mensaje("Sesión cerrada. Memoria limpiada.", error=False)
        self.refrescar()
        self.estado_actualizado.emit(est)
        self.datos_modificados.emit()

    # -----------------------------------------------------------------------
    # Acciones de Verificación Cruzada
    # -----------------------------------------------------------------------

    def _al_ejecutar_cruzada(self) -> None:
        self.btn_ejecutar.setEnabled(False)
        self.lbl_estado.setText("Ejecutando verificaciones cruzadas en segundo plano...")
        self.frame_resultado.setStyleSheet(
            f"background-color: #E3ECF8; border: 1px solid #0D47A1; border-radius: {RADIO_BOTON}px; padding: 8px 14px;"
        )

        def trabajo() -> ResultadoVerificacionCruzada:
            return self.servicio.ejecutar_verificacion_cruzada(usar_base=False)

        def exito(res: ResultadoVerificacionCruzada) -> None:
            self.btn_ejecutar.setEnabled(True)
            self._resultado_cruzada = res
            self._mostrar_resultado_cruzada(res)

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_ejecutar.setEnabled(True)
            self.lbl_estado.setText(f"Error durante la verificación: {err}")
            self.frame_resultado.setStyleSheet(
                f"background-color: {ERROR_FONDO}; border: 1px solid {ERROR}; "
                f"border-radius: {RADIO_BOTON}px; padding: 8px 14px;"
            )

        if self.ejecutor is not None:
            self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)
        else:
            try:
                res = trabajo()
                exito(res)
            except Exception as err:
                fallo(err, str(err))

    def _mostrar_resultado_cruzada(self, res: ResultadoVerificacionCruzada) -> None:
        if res.exito:
            self.lbl_estado.setText(f"✔ VERIFICACIÓN CRUZADA EXITOSA: {res.mensaje}")
            self.frame_resultado.setStyleSheet(
                f"background-color: {EXITO_FONDO}; border: 1px solid {EXITO}; "
                f"border-radius: {RADIO_BOTON}px; padding: 8px 14px;"
            )
        else:
            self.lbl_estado.setText(f"✖ FALLO O ADVERTENCIA: {res.mensaje}")
            self.frame_resultado.setStyleSheet(
                f"background-color: {AVISO_FONDO}; border: 1px solid {AVISO}; "
                f"border-radius: {RADIO_BOTON}px; padding: 8px 14px;"
            )

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
        self.tabla_pasos.actualizar_pie()
        if filas:
            self.tabla_pasos.vista.selectRow(0)
            self._al_seleccionar_paso_cruzada(0)

    def _al_seleccionar_paso_cruzada(self, fila: int) -> None:
        if not self._resultado_cruzada or not self._resultado_cruzada.pasos:
            return
        if 0 <= fila < len(self._resultado_cruzada.pasos):
            paso = self._resultado_cruzada.pasos[fila]
            self.txt_out_py.setPlainText(paso.salida_python)
            self.txt_out_cpp.setPlainText(paso.salida_cpp)

    # -----------------------------------------------------------------------
    # API Pública Requerida
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Actualiza el estado de conexión mostrado en pantalla."""
        est = self.servicio.estado()

        # Actualizar píldora de modo y resumen
        if est.modo == ModoConexion.SUPABASE:
            self.pildora_modo.establecer_texto("Supabase")
            self.pildora_modo.establecer_variante("exito")
        elif est.modo == ModoConexion.DEMOSTRACION:
            self.pildora_modo.establecer_texto("Demostración")
            self.pildora_modo.establecer_variante("aviso")
        else:
            self.pildora_modo.establecer_texto("Desconectado")
            self.pildora_modo.establecer_variante("error")

        self.lbl_estado_resumen.setText(est.descripcion_modo)
        self.lbl_servidor.setText(est.base_url or "Ninguno")
        self.lbl_usuario.setText(est.correo or "Sin usuario autenticado")

        rev_local = str(est.revision_local) if est.revision_local is not None else "—"
        rev_remota = str(est.revision_remota) if est.revision_remota is not None else "—"
        self.lbl_revisiones.setText(f"Local: {rev_local}  |  Remota: {rev_remota}")

        if est.motivo_bloqueo:
            self.lbl_bloqueo.setText(f"Bloqueo activo: {est.motivo_bloqueo}")
            self.lbl_bloqueo.setVisible(True)
        else:
            self.lbl_bloqueo.setVisible(False)

        self.btn_desconectar.setEnabled(est.modo != ModoConexion.DESCONECTADO)

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Conserva la API uniforme entre todas las pantallas."""
        self._filtro_actual = filtro
