"""Ventana principal de la aplicación PEA-i (PySide6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import HOJA_ESTILOS_GLOBAL
from pea.gui.pantallas.pantalla_acerca import PantallaAcerca
from pea.gui.pantallas.pantalla_conectar import PantallaConectar
from pea.gui.pantallas.pantalla_cruzada import PantallaCruzada
from pea.gui.pantallas.pantalla_gestion import PantallaGestion
from pea.gui.pantallas.pantalla_grupo import PantallaGrupo
from pea.gui.pantallas.pantalla_importar import PantallaImportar
from pea.gui.pantallas.pantalla_investigador import PantallaInvestigador
from pea.gui.pantallas.pantalla_producto import PantallaProducto
from pea.gui.pantallas.pantalla_resumen import PantallaResumen
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import ModoConexion


class VentanaPrincipal(QMainWindow):
    """Ventana principal con diseño de cuatro zonas para PEA-i."""

    def __init__(self, servicio: ServicioAplicacion | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PEA-i · Programa Estadístico de Análisis de Investigación")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self._servicio = servicio or ServicioAplicacion()
        self._ejecutor = EjecutorHilos.instancia()

        self._configurar_ui()
        self._configurar_atajos()
        self._configurar_temporizador_revision()
        self.actualizar_estado_global()

    def _configurar_ui(self) -> None:
        self.setStyleSheet(HOJA_ESTILOS_GLOBAL)

        widget_central = QWidget()
        disposicion_principal = QVBoxLayout(widget_central)
        disposicion_principal.setContentsMargins(0, 0, 0, 0)
        disposicion_principal.setSpacing(0)

        # 1. Barra superior
        self._barra_superior = self._crear_barra_superior()
        disposicion_principal.addWidget(self._barra_superior)

        # Banner de advertencia de revisión
        self._banner_revision = self._crear_banner_revision()
        disposicion_principal.addWidget(self._banner_revision)
        self._banner_revision.setVisible(False)

        # Zona central: Navegación lateral + Pantallas apiladas
        zona_medio = QWidget()
        disp_medio = QHBoxLayout(zona_medio)
        disp_medio.setContentsMargins(0, 0, 0, 0)
        disp_medio.setSpacing(0)

        # 2. Navegación lateral
        self._navegacion = self._crear_navegacion_lateral()
        disp_medio.addWidget(self._navegacion)

        # 3. Pantallas apiladas
        self._apilador = QStackedWidget()
        self._inicializar_pantallas()
        disp_medio.addWidget(self._apilador, 1)

        disposicion_principal.addWidget(zona_medio, 1)
        self.setCentralWidget(widget_central)

        # 4. Barra de estado inferior
        self._barra_estado = QStatusBar()
        self.setStatusBar(self._barra_estado)
        self._lbl_estado_conexion = QLabel("Desconectado")
        self._lbl_estado_revision = QLabel("Revisión: -")
        self._lbl_estado_deshacer = QLabel("Deshacer: 0")
        self._lbl_estado_cola = QLabel("Cola: 0")

        self._barra_estado.addWidget(self._lbl_estado_conexion)
        self._barra_estado.addPermanentWidget(self._lbl_estado_revision)
        self._barra_estado.addPermanentWidget(self._lbl_estado_deshacer)
        self._barra_estado.addPermanentWidget(self._lbl_estado_cola)

    def _crear_barra_superior(self) -> QWidget:
        barra = QFrame()
        barra.setObjectName("barraSuperior")
        barra.setStyleSheet(
            "QFrame#barraSuperior { background-color: #003366; color: white; padding: 6px 16px; border-bottom: 2px solid #002244; }"
        )
        disp = QHBoxLayout(barra)
        disp.setContentsMargins(12, 8, 12, 8)
        disp.setSpacing(16)

        lbl_logo = QLabel("PEA-i")
        lbl_logo.setStyleSheet("font-size: 15pt; font-weight: bold; color: #FFFFFF;")
        disp.addWidget(lbl_logo)

        lbl_separador = QLabel("│")
        lbl_separador.setStyleSheet("color: #64B5F6; font-size: 12pt;")
        disp.addWidget(lbl_separador)

        lbl_subtitulo = QLabel("Universidad Popular del Cesar · Análisis Estadístico MinCiencias")
        lbl_subtitulo.setStyleSheet("font-size: 10pt; color: #E0E0E0;")
        disp.addWidget(lbl_subtitulo)

        disp.addStretch(1)

        # Indicador de modo de conexión
        self._punto_conexion = QLabel("●")
        self._punto_conexion.setStyleSheet("color: #9CA3AF; font-size: 14pt;")
        disp.addWidget(self._punto_conexion)

        self._texto_conexion = QLabel("Sin conexión")
        self._texto_conexion.setStyleSheet("color: #F3F4F6; font-weight: 500;")
        disp.addWidget(self._texto_conexion)

        # Botón Deshacer
        self._btn_deshacer = QPushButton("Deshacer (Ctrl+Z)")
        self._btn_deshacer.setStyleSheet(
            "QPushButton { background-color: #1E3A8A; color: white; border: 1px solid #3B82F6; padding: 6px 12px; border-radius: 4px; font-weight: 500; }"
            "QPushButton:hover { background-color: #2563EB; }"
            "QPushButton:disabled { background-color: #374151; color: #9CA3AF; border: 1px solid #4B5563; }"
        )
        self._btn_deshacer.setEnabled(False)
        self._btn_deshacer.clicked.connect(self._al_clic_deshacer)
        disp.addWidget(self._btn_deshacer)

        return barra

    def _crear_banner_revision(self) -> QWidget:
        banner = QFrame()
        banner.setObjectName("bannerRevision")
        banner.setStyleSheet(
            "QFrame#bannerRevision { background-color: #FEF3C7; border-bottom: 1px solid #F59E0B; padding: 6px 16px; }"
        )
        disp = QHBoxLayout(banner)
        disp.setContentsMargins(16, 6, 16, 6)
        disp.setSpacing(12)

        lbl_icono = QLabel("⚠️")
        disp.addWidget(lbl_icono)

        self._lbl_texto_banner = QLabel("La base de datos cambió en el servidor. Existen modificaciones externas.")
        self._lbl_texto_banner.setStyleSheet("color: #92400E; font-weight: 600;")
        disp.addWidget(self._lbl_texto_banner, 1)

        btn_recargar = QPushButton("Recargar ahora")
        btn_recargar.setStyleSheet(
            "QPushButton { background-color: #D97706; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; border: none; }"
            "QPushButton:hover { background-color: #B45309; }"
        )
        btn_recargar.clicked.connect(self._al_clic_recargar_revision)
        disp.addWidget(btn_recargar)

        return banner

    def _crear_navegacion_lateral(self) -> QListWidget:
        lista = QListWidget()
        lista.setFixedWidth(220)
        lista.setStyleSheet(
            "QListWidget { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; padding: 8px 0; outline: none; }"
            "QListWidget::item { padding: 10px 16px; border-left: 4px solid transparent; color: #1E293B; font-size: 10pt; font-weight: 500; }"
            "QListWidget::item:hover { background-color: #EDF2F7; }"
            "QListWidget::item:selected { background-color: #E2E8F0; border-left: 4px solid #006633; color: #006633; font-weight: bold; }"
        )

        pantallas = [
            "Conectar con PEA-i",
            "Resumen general",
            "Por grupo",
            "Por investigador",
            "Por producto",
            "Gestión de datos",
            "Importar",
            "Verificación cruzada",
            "Acerca del proyecto",
        ]

        for nombre in pantallas:
            item = QListWidgetItem(nombre)
            item.setSizeHint(QSize(200, 42))
            lista.addItem(item)

        lista.currentRowChanged.connect(self._al_cambiar_pantalla)
        return lista

    def _inicializar_pantallas(self) -> None:
        self._pantalla_conectar = PantallaConectar(self._servicio, self._ejecutor)
        self._pantalla_resumen = PantallaResumen(self._servicio)
        self._pantalla_grupo = PantallaGrupo(self._servicio)
        self._pantalla_investigador = PantallaInvestigador(self._servicio)
        self._pantalla_producto = PantallaProducto(self._servicio)
        self._pantalla_gestion = PantallaGestion(self._servicio)
        self._pantalla_importar = PantallaImportar(self._servicio, self._ejecutor)
        self._pantalla_cruzada = PantallaCruzada(self._servicio, self._ejecutor)
        self._pantalla_acerca = PantallaAcerca(self._servicio)


        self._pantallas_lista = [
            self._pantalla_conectar,
            self._pantalla_resumen,
            self._pantalla_grupo,
            self._pantalla_investigador,
            self._pantalla_producto,
            self._pantalla_gestion,
            self._pantalla_importar,
            self._pantalla_cruzada,
            self._pantalla_acerca,
        ]

        for p in self._pantallas_lista:
            self._apilador.addWidget(p)

        # Conectar señales de cambio de estado / datos
        self._pantalla_conectar.estado_actualizado.connect(self._al_cambiar_conexion)
        self._pantalla_gestion.datos_modificados.connect(self.actualizar_estado_global)


    def _configurar_atajos(self) -> None:
        accion_deshacer = QAction(self)
        accion_deshacer.setShortcut(QKeySequence("Ctrl+Z"))
        accion_deshacer.triggered.connect(self._al_clic_deshacer)
        self.addAction(accion_deshacer)

    def _configurar_temporizador_revision(self) -> None:
        self._timer_revision = QTimer(self)
        self._timer_revision.setInterval(10000)  # Cada 10 segundos
        self._timer_revision.timeout.connect(self._verificar_revision_en_segundo_plano)
        self._timer_revision.start()

    def _al_cambiar_pantalla(self, indice: int) -> None:
        if 0 <= indice < self._apilador.count():
            self._apilador.setCurrentIndex(indice)
            pantalla_actual = self._apilador.currentWidget()
            if hasattr(pantalla_actual, "refrescar"):
                pantalla_actual.refrescar()
            self.actualizar_estado_global()

    def _al_cambiar_conexion(self) -> None:
        self.actualizar_estado_global()
        # Si acabamos de conectar exitosamente o cargar datos de demostración, actualizar pantalla actual
        pantalla_actual = self._apilador.currentWidget()
        if hasattr(pantalla_actual, "refrescar"):
            pantalla_actual.refrescar()

    def _al_clic_deshacer(self) -> None:
        try:
            desc = self._servicio.deshacer()
            self._barra_estado.showMessage(f"Acción revertida: {desc}", 5000)
            self.actualizar_estado_global()
            pantalla_actual = self._apilador.currentWidget()
            if hasattr(pantalla_actual, "refrescar"):
                pantalla_actual.refrescar()
        except Exception as err:
            QMessageBox.warning(self, "Deshacer", str(err))


    def _al_clic_recargar_revision(self) -> None:
        def tarea():
            return self._servicio.recargar()

        def exito(_):
            self._banner_revision.setVisible(False)
            self.actualizar_estado_global()
            pantalla_actual = self._apilador.currentWidget()
            if hasattr(pantalla_actual, "refrescar"):
                pantalla_actual.refrescar()
            self._barra_estado.showMessage("Datos recargados y sincronizados con el servidor.", 4000)


        def fallo(err, _):
            QMessageBox.warning(self, "Recarga", f"No fue posible recargar: {err}")

        self._ejecutor.ejecutar(tarea, al_terminar=exito, al_fallar=fallo)

    def _verificar_revision_en_segundo_plano(self) -> None:
        estado = self._servicio.estado()
        if estado.modo != ModoConexion.SUPABASE:
            return

        def tarea():
            return self._servicio.verificar_cambios_remotos()

        def exito(est_nuevo):
            self._banner_revision.setVisible(est_nuevo.cambio_remoto)

        self._ejecutor.ejecutar(tarea, al_terminar=exito)

    def actualizar_estado_global(self) -> None:
        estado = self._servicio.estado()

        # Actualizar indicador superior
        if estado.modo == ModoConexion.SUPABASE:
            if estado.sin_conexion:
                self._punto_conexion.setStyleSheet("color: #EF4444; font-size: 14pt;")
                self._texto_conexion.setText("Sin conexión")
                self._lbl_estado_conexion.setText("Sin conexión (Supabase bloqueado)")
            else:
                self._punto_conexion.setStyleSheet("color: #10B981; font-size: 14pt;")
                self._texto_conexion.setText("Conectado a Supabase")
                self._lbl_estado_conexion.setText("En línea (HTTPS/Supabase)")
        elif estado.modo == ModoConexion.DEMOSTRACION:
            self._punto_conexion.setStyleSheet("color: #F59E0B; font-size: 14pt;")
            self._texto_conexion.setText("Modo Demostración")
            self._lbl_estado_conexion.setText("Demostración (datos ficticios)")
        else:
            self._punto_conexion.setStyleSheet("color: #9CA3AF; font-size: 14pt;")
            self._texto_conexion.setText("Desconectado")
            self._lbl_estado_conexion.setText("Desconectado")

        # Botón deshacer
        puede_deshacer = estado.operaciones_deshacer > 0
        self._btn_deshacer.setEnabled(puede_deshacer)
        self._btn_deshacer.setText(f"Deshacer ({estado.operaciones_deshacer})")

        # Barra de estado inferior
        rev_txt = f"Revisión: {estado.revision_local}" if estado.revision_local is not None else "Revisión: N/A"
        self._lbl_estado_revision.setText(rev_txt)
        self._lbl_estado_deshacer.setText(f"Deshacer: {estado.operaciones_deshacer}")
        self._lbl_estado_cola.setText(f"Cola: {estado.tareas_pendientes}")

    def seleccionar_pantalla(self, indice: int) -> None:
        """Cambia programáticamente la pantalla seleccionada."""
        self._navegacion.setCurrentRow(indice)


def ejecutar_autoprueba(app: QApplication, ventana: VentanaPrincipal) -> int:
    """Ejecuta el recorrido automatizado de todas las pantallas y toma capturas.

    Retorna 0 si todas las pantallas fueron renderizadas sin error.
    """
    print("[AUTOPRUEBA] Iniciando autoprueba de la interfaz PEA-i...")
    directorio_capturas = Path("datos/capturas")
    directorio_capturas.mkdir(parents=True, exist_ok=True)

    # Aseguramos carga de demostración
    ventana._servicio.cargar_demostracion()


    ventana.show()
    app.processEvents()

    nombres_pantallas = [
        "01_conectar",
        "02_resumen",
        "03_grupo",
        "04_investigador",
        "05_producto",
        "06_gestion",
        "07_importar",
        "08_cruzada",
        "09_acerca",
    ]

    for idx, nombre in enumerate(nombres_pantallas):
        ventana.seleccionar_pantalla(idx)
        app.processEvents()

        # Renderizar la ventana en un pixmap
        pixmap = ventana.grab()
        ruta_captura = directorio_capturas / f"pantalla_{nombre}.png"
        pixmap.save(str(ruta_captura), "PNG")
        print(f"[AUTOPRUEBA] Pantalla {idx + 1}/9 ({nombre}) capturada en: {ruta_captura}")

    print("[AUTOPRUEBA] Todas las 9 pantallas recorridas y capturadas exitosamente.")
    return 0
