"""Pantalla 1: Conectar con PEA-i (Supabase HTTPS / Modo demostración)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pea.gui.ejecutor import EjecutorAsincrono
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import EstadoAplicacion, ModoConexion


class PantallaConectar(QWidget):
    """Permite autenticarse con Supabase o activar el modo demostración local."""

    estado_actualizado = Signal(object)  # emite EstadoAplicacion

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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Encabezado
        lbl_titulo = QLabel("Conectar con PEA-i", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Configure el acceso a la base de datos PostgreSQL alojada en Supabase mediante HTTPS "
            "o active el conjunto de datos de demostración en memoria.",
            self,
        )
        lbl_desc.setObjectName("ayuda")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Tarjeta de estado actual
        self.frame_estado = QFrame(self)
        self.frame_estado.setObjectName("panel")
        layout_estado = QVBoxLayout(self.frame_estado)
        self.lbl_estado_resumen = QLabel("Estado: Desconectado", self.frame_estado)
        self.lbl_estado_resumen.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_estado_detalle = QLabel("No hay conexión activa.", self.frame_estado)
        self.lbl_estado_detalle.setStyleSheet("color: #5F6368;")
        layout_estado.addWidget(self.lbl_estado_resumen)
        layout_estado.addWidget(self.lbl_estado_detalle)
        layout.addWidget(self.frame_estado)

        # Formulario de parámetros de conexión
        frame_form = QFrame(self)
        frame_form.setObjectName("panel")
        layout_form = QFormLayout(frame_form)
        layout_form.setContentsMargins(16, 16, 16, 16)
        layout_form.setSpacing(12)

        cfg = self.servicio.configuracion_entorno()

        self.txt_url = QLineEdit(cfg.get("url", ""), frame_form)
        self.txt_url.setPlaceholderText("https://xxxxxxxxxxxx.supabase.co")
        layout_form.addRow("URL de Supabase (HTTPS):", self.txt_url)

        self.txt_clave = QLineEdit(cfg.get("clave_publicable", ""), frame_form)
        self.txt_clave.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_clave.setPlaceholderText("Clave publicable (sb_publishable_... o anon JWT)")
        layout_form.addRow("Clave publicable:", self.txt_clave)

        self.txt_correo = QLineEdit(cfg.get("correo", ""), frame_form)
        self.txt_correo.setPlaceholderText("usuario@unicesar.edu.co (opcional para Auth)")
        layout_form.addRow("Correo de usuario:", self.txt_correo)

        self.txt_pass = QLineEdit(frame_form)
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setPlaceholderText("Contraseña del usuario")
        layout_form.addRow("Contraseña:", self.txt_pass)

        self.chk_entorno = QCheckBox("Tomar contraseña de la variable PEA_USUARIO_CLAVE si existe", frame_form)
        self.chk_entorno.setChecked(cfg.get("hay_clave_usuario_en_entorno", False))
        layout_form.addRow("", self.chk_entorno)

        layout.addWidget(frame_form)

        # Mensajes de aviso / error
        self.lbl_aviso = QLabel("", self)
        self.lbl_aviso.setWordWrap(True)
        self.lbl_aviso.setVisible(False)
        layout.addWidget(self.lbl_aviso)

        # Botonera de acciones
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(12)

        self.btn_conectar = QPushButton("Conectar con Supabase", self)
        self.btn_conectar.setObjectName("primario")
        self.btn_conectar.clicked.connect(self._al_conectar)
        layout_botones.addWidget(self.btn_conectar)

        self.btn_demo = QPushButton("Cargar datos de demostración", self)
        self.btn_demo.clicked.connect(self._al_cargar_demostracion)
        layout_botones.addWidget(self.btn_demo)

        self.btn_desconectar = QPushButton("Cerrar sesión / Desconectar", self)
        self.btn_desconectar.clicked.connect(self._al_desconectar)
        layout_botones.addWidget(self.btn_desconectar)

        layout_botones.addStretch()
        layout.addLayout(layout_botones)
        layout.addStretch()

    def _mostrar_mensaje(self, texto: str, error: bool = False) -> None:
        self.lbl_aviso.setText(texto)
        if error:
            self.lbl_aviso.setStyleSheet("background-color: #FDECEA; color: #D32F2F; border: 1px solid #D32F2F; padding: 8px; border-radius: 4px;")
        else:
            self.lbl_aviso.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; border: 1px solid #2E7D32; padding: 8px; border-radius: 4px;")
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

        def fallo(err: Exception, detalle: str) -> None:
            self.btn_conectar.setEnabled(True)
            self.btn_demo.setEnabled(True)
            self._mostrar_mensaje(f"Error de conexión: {err}", error=True)
            self.refrescar()

        self.ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)

    def _al_cargar_demostracion(self) -> None:
        try:
            est = self.servicio.cargar_demostracion()
            self._mostrar_mensaje("Datos de demostración cargados en memoria.", error=False)
            self.refrescar()
            self.estado_actualizado.emit(est)
        except Exception as err:
            self._mostrar_mensaje(f"Error al cargar demostración: {err}", error=True)

    def _al_desconectar(self) -> None:
        est = self.servicio.desconectar()
        self._mostrar_mensaje("Sesión cerrada. Memoria limpiada.", error=False)
        self.refrescar()
        self.estado_actualizado.emit(est)

    def refrescar(self) -> None:
        est = self.servicio.estado()
        self.lbl_estado_resumen.setText(f"Modo actual: {est.descripcion_modo}")
        detalles = []
        if est.base_url:
            detalles.append(f"Servidor: {est.base_url}")
        if est.correo:
            detalles.append(f"Usuario: {est.correo}")
        if est.revision_local is not None:
            detalles.append(f"Revisión local: {est.revision_local}")
        if est.revision_remota is not None:
            detalles.append(f"Revisión remota: {est.revision_remota}")
        if est.motivo_bloqueo:
            detalles.append(f"Bloqueo: {est.motivo_bloqueo}")
        self.lbl_estado_detalle.setText(" | ".join(detalles) if detalles else "Sin conexión activa.")
        self.btn_desconectar.setEnabled(est.modo != ModoConexion.DESCONECTADO)

