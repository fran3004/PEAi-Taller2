"""Ventana principal institucional de PEA-i (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 5).
Estructura de cuatro zonas:
1. Barra superior de 88 px con degradado horizontal, átomo, eslogan,
   7 pestañas institucionales, botón Deshacer con popover de historial,
   avatar con iniciales, Cerrar sesión, enlace Acerca de y filete UPC de 3 px.
2. Franjas reactivas de aviso de revisión remota y modo sin conexión.
3. Zona central con QStackedWidget animado (200 ms) y 8 pantallas (enum Pantalla).
4. Pie institucional con logo de la UPC en pastilla blanca, texto institucional
   y estado vivo (conexión, revisión, deshacer y cola).
"""

from __future__ import annotations

import sys
from enum import IntEnum
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QEvent,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.animacion import animaciones_habilitadas, animar_desvanecimiento
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.estado_vacio import EstadoVacio
from pea.gui.componentes.filtro_anios import ChipVentana
from pea.gui.componentes.pildora import Pildora
from pea.gui.componentes.popover_historial import PopoverHistorial
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    ACENTO,
    AVISO,
    AVISO_FONDO,
    ENCABEZADO_FIN,
    ENCABEZADO_INICIO,
    ENCABEZADO_MEDIO,
    ERROR,
    ERROR_FONDO,
    EXITO,
    FONDO_APP,
    HOJA_ESTILOS_GLOBAL,
    LINEA,
    PIE,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
    TEXTO_SOBRE_OSCURO_SUAVE,
    UPC_VERDE,
    UPC_VERDE_CLARO,
    UPC_VERDE_OSCURO,
)
from pea.gui.pantallas.acerca import PantallaAcerca
from pea.gui.pantallas.configuracion import PantallaConfiguracion
from pea.gui.pantallas.grupos import PantallaGrupos
from pea.gui.pantallas.importar import PantallaImportar
from pea.gui.pantallas.inicio import PantallaInicio
from pea.gui.pantallas.investigadores import PantallaInvestigadores
from pea.gui.pantallas.productos import PantallaProductos
from pea.gui.pantallas.redes import PantallaRedes
from pea.gui.recursos.cargador import cargar_icono, cargar_pixmap, fuente_inter_cargada
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoConexion, ModoFiltroAnios
from pea.version import ESLOGAN_LINEA_1, ESLOGAN_LINEA_2, NOMBRE_COMPLETO


class Pantalla(IntEnum):
    """Índices oficiales de pantallas en la vista apilada."""

    INICIO = 0
    INVESTIGADORES = 1
    GRUPOS = 2
    PRODUCTOS = 3
    REDES = 4
    IMPORTAR = 5
    CONFIGURACION = 6
    ACERCA = 7


# ---------------------------------------------------------------------------
# Componentes auxiliares de la barra superior y pie
# ---------------------------------------------------------------------------


class FileteInstitucionalUPC(QWidget):
    """Filete inferior institucional de 3 px dividido en 3 tramos de color UPC."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(3)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        w = float(self.width())
        h = float(self.height())
        w1 = round(w / 3.0)
        w2 = round(w / 3.0)
        w3 = w - w1 - w2

        painter.fillRect(QRectF(0, 0, w1, h), QColor(UPC_VERDE_OSCURO))
        painter.fillRect(QRectF(w1, 0, w2, h), QColor(UPC_VERDE))
        painter.fillRect(QRectF(w1 + w2, 0, w3, h), QColor(UPC_VERDE_CLARO))


class BotonPestanaSuperior(QPushButton):
    """Botón de pestaña institucional con ícono vertical, rótulo y barra de acento."""

    def __init__(
        self,
        texto: str,
        nombre_icono: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._texto = texto
        self._nombre_icono = nombre_icono
        self._modo_compacto = False

        self.setCheckable(True)
        self.setFixedHeight(64)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"Pestaña {texto}")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._pixmap_normal = cargar_pixmap(nombre_icono, 24, 24)

    def establecer_modo_compacto(self, compacto: bool) -> None:
        """Alterna entre mostrar solo ícono con tooltip o ícono con etiqueta."""
        self._modo_compacto = compacto
        if compacto:
            self.setToolTip(self._texto)
            self.setFixedWidth(54)
        else:
            self.setToolTip("")
            self.setMinimumWidth(80)
            self.setMaximumWidth(130)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        es_activo = self.isChecked()
        es_hover = self.underMouse()

        # 1. Fondo según estado
        if es_activo:
            painter.setBrush(QColor(255, 255, 255, 36))  # 14%
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)
        elif es_hover:
            painter.setBrush(QColor(255, 255, 255, 20))  # 8%
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

        # 2. Anillo de foco accesible
        if self.hasFocus():
            pen_foco = QPen(QColor(ACENTO), 2)
            painter.setPen(pen_foco)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

        # 3. Ícono
        ancho_icono = self._pixmap_normal.width()
        alto_icono = self._pixmap_normal.height()

        if self._modo_compacto:
            x_ico = (rect.width() - ancho_icono) / 2.0
            y_ico = (rect.height() - alto_icono) / 2.0
            painter.drawPixmap(int(x_ico), int(y_ico), self._pixmap_normal)
        else:
            x_ico = (rect.width() - ancho_icono) / 2.0
            y_ico = 10.0
            painter.drawPixmap(int(x_ico), int(y_ico), self._pixmap_normal)

            # 4. Etiqueta de texto
            fuente = QFont()
            fuente.setPointSize(10)
            fuente.setBold(es_activo)
            painter.setFont(fuente)

            color_txt = QColor(TEXTO_SOBRE_OSCURO if es_activo else TEXTO_SOBRE_OSCURO_SUAVE)
            painter.setPen(color_txt)

            rect_txt = QRectF(4, 38, rect.width() - 8, 20)
            painter.drawText(rect_txt, Qt.AlignmentFlag.AlignCenter, self._texto)

        # 5. Barra inferior de acento (40% del ancho, centrado)
        if es_activo:
            ancho_barra = rect.width() * 0.40
            x_barra = (rect.width() - ancho_barra) / 2.0
            y_barra = rect.height() - 4.0
            rect_barra = QRectF(x_barra, y_barra, ancho_barra, 3.0)
            painter.fillRect(rect_barra, QColor(ACENTO))


class BotonDeshacerSuperior(QWidget):
    """Botón circular de Deshacer (40 px) con insignia numérica y disparador de popover."""

    deshacer_pulsado = Signal()
    popover_solicitado = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(68, 44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Botón circular principal
        self.btn_accion = QPushButton(self)
        self.btn_accion.setFixedSize(40, 40)
        self.btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_accion.setAccessibleName("Deshacer última operación (Ctrl+Z)")
        self.btn_accion.setIcon(cargar_icono("deshacer.svg", 18))
        self.btn_accion.setIconSize(QSize(18, 18))
        self.btn_accion.setStyleSheet(
            "QPushButton { background-color: rgba(255, 255, 255, 0.12); "
            "border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 20px; }"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.22); }"
            "QPushButton:disabled { background-color: rgba(255, 255, 255, 0.05); border-color: rgba(255, 255, 255, 0.1); }"
        )
        self.btn_accion.clicked.connect(self.deshacer_pulsado.emit)
        layout.addWidget(self.btn_accion)

        # Chevron para desplegar historial
        self.btn_chevron = QPushButton("▾", self)
        self.btn_chevron.setFixedSize(22, 40)
        self.btn_chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chevron.setAccessibleName("Abrir historial de operaciones")
        self.btn_chevron.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXTO_SOBRE_OSCURO_SUAVE}; "
            f"font-size: 11pt; border: none; border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.12); color: #FFFFFF; }}"
        )
        self.btn_chevron.clicked.connect(self.popover_solicitado.emit)
        layout.addWidget(self.btn_chevron)

        self._contador = 0
        self.actualizar_contador(0)

    def actualizar_contador(self, contador: int) -> None:
        self._contador = contador
        puede_deshacer = contador > 0
        self.btn_accion.setEnabled(puede_deshacer)
        self.btn_accion.setToolTip(f"Deshacer (Ctrl+Z) · {contador} disponibles" if puede_deshacer else "Nada que deshacer")
        self.btn_chevron.setEnabled(puede_deshacer)
        self.update()

    def setEnabled(self, habilitado: bool) -> None:
        super().setEnabled(habilitado)
        self.btn_accion.setEnabled(habilitado)
        self.btn_chevron.setEnabled(habilitado)

    def setText(self, texto: str) -> None:
        # Retrocompatibilidad con la API previa de _btn_deshacer.setText()
        self.btn_accion.setToolTip(texto)


# ---------------------------------------------------------------------------
# Marcador de Pantalla Temporal
# ---------------------------------------------------------------------------


class MarcadorPantalla(QWidget):
    """Pantalla contenedora con barra de contexto y estado vacío accesible."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        icono: str,
        filtro_global: FiltroAnios,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._filtro_actual = filtro_global

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(16)

        # 1. Barra de contexto (alto 56 px)
        barra_contexto = QFrame(self)
        barra_contexto.setFixedHeight(56)
        barra_contexto.setStyleSheet(
            f"QFrame {{ background-color: #FFFFFF; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; }}"
        )
        layout_ctx = QHBoxLayout(barra_contexto)
        layout_ctx.setContentsMargins(16, 8, 16, 8)
        layout_ctx.setSpacing(12)

        lbl_tit = QLabel(titulo, barra_contexto)
        lbl_tit.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {TEXTO};")
        layout_ctx.addWidget(lbl_tit)
        layout_ctx.addStretch()

        # Chip de ventana global temporal
        self.chip_filtro = ChipVentana(self._filtro_actual, barra_contexto)
        layout_ctx.addWidget(self.chip_filtro)

        layout.addWidget(barra_contexto)

        # 2. Contenido central con Tarjeta y EstadoVacio
        tarjeta_central = Tarjeta(parent=self)
        self._estado_vacio = EstadoVacio(
            titulo=f"Módulo de {titulo}",
            mensaje=f"{descripcion}\nEste módulo se integra reactivamente con los servicios de PEA-i.",
            texto_principal="Conectar con Supabase",
            texto_secundario="Cargar datos de demostración",
            parent=tarjeta_central,
        )
        tarjeta_central.agregar_widget(self._estado_vacio)
        layout.addWidget(tarjeta_central, stretch=1)

    def refrescar(self) -> None:
        pass

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.chip_filtro.establecer_filtro(filtro)


# ---------------------------------------------------------------------------
# Ventana Principal
# ---------------------------------------------------------------------------


class VentanaPrincipal(QMainWindow):
    """Ventana principal de PEA-i con diseño institucional de cuatro zonas."""

    def __init__(self, servicio: ServicioAplicacion | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"PEA-i · {NOMBRE_COMPLETO}")
        self.setMinimumSize(1100, 700)
        self.resize(1360, 820)

        self._servicio = servicio or ServicioAplicacion()
        self._ejecutor = EjecutorHilos.instancia()
        self._filtro_global = FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)

        self._gestor_toasts = GestorAvisos(self)
        self._configurar_barra_titulo_windows()

        self._construir_ui()
        self._configurar_atajos()
        self._configurar_temporizador_revision()
        self.actualizar_estado_global()

        # Centrar ventana en pantalla disponible
        self._centrar_en_pantalla()

    def _configurar_barra_titulo_windows(self) -> None:
        """Activa la barra de título oscura inmersiva en Windows si está soportada."""
        if sys.platform == "win32":
            try:
                import ctypes

                hwnd = int(self.winId())
                dwmwa_use_immersive_dark_mode = 20
                valor = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    dwmwa_use_immersive_dark_mode,
                    ctypes.byref(valor),
                    ctypes.sizeof(valor),
                )
            except Exception:
                pass

    def _centrar_en_pantalla(self) -> None:
        pantalla = self.screen()
        if pantalla:
            geo_disp = pantalla.availableGeometry()
            x = geo_disp.x() + max(0, (geo_disp.width() - self.width()) // 2)
            y = geo_disp.y() + max(0, (geo_disp.height() - self.height()) // 2)
            self.move(x, y)

    def _construir_ui(self) -> None:
        self.setStyleSheet(HOJA_ESTILOS_GLOBAL)

        widget_central = QWidget(self)
        widget_central.setStyleSheet(f"background-color: {FONDO_APP};")
        layout_raiz = QVBoxLayout(widget_central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        # 1. Barra superior institucional (88 px)
        self._barra_superior = self._crear_barra_superior()
        layout_raiz.addWidget(self._barra_superior)

        # Filete de 3 px UPC
        self._filete_upc = FileteInstitucionalUPC(self)
        layout_raiz.addWidget(self._filete_upc)

        # 2. Franjas reactivas de estado
        self._banner_revision = self._crear_banner_revision()
        layout_raiz.addWidget(self._banner_revision)
        self._banner_revision.setVisible(False)

        self._franja_sin_conexion = self._crear_franja_sin_conexion()
        layout_raiz.addWidget(self._franja_sin_conexion)
        self._franja_sin_conexion.setVisible(False)

        # 3. Zona de contenido apilado
        self._apilador = QStackedWidget(self)
        self._inicializar_pantallas()
        layout_raiz.addWidget(self._apilador, 1)

        # 4. Pie institucional
        self._pie = self._crear_pie_institucional()
        layout_raiz.addWidget(self._pie)

        self.setCentralWidget(widget_central)

        # Popover de historial
        self._popover_historial = PopoverHistorial(self)
        self._popover_historial.deshacer_solicitado.connect(self._al_clic_deshacer)

    # -----------------------------------------------------------------------
    # 1. Barra Superior (88 px)
    # -----------------------------------------------------------------------

    def _crear_barra_superior(self) -> QFrame:
        barra = QFrame(self)
        barra.setObjectName("barraSuperior")
        barra.setFixedHeight(88)

        # Degradado horizontal institucional
        def pintar_barra(event: QPaintEvent) -> None:
            painter = QPainter(barra)
            grad = QLinearGradient(0, 0, barra.width(), 0)
            grad.setColorAt(0.0, QColor(ENCABEZADO_INICIO))
            grad.setColorAt(0.5, QColor(ENCABEZADO_MEDIO))
            grad.setColorAt(1.0, QColor(ENCABEZADO_FIN))
            painter.fillRect(barra.rect(), grad)

        barra.paintEvent = pintar_barra  # type: ignore[assignment]

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(14)

        # --- Zona Izquierda: Marca y Eslogan ---
        self._zona_marca = QWidget(barra)
        layout_marca = QHBoxLayout(self._zona_marca)
        layout_marca.setContentsMargins(0, 0, 0, 0)
        layout_marca.setSpacing(10)

        # Átomo blanco (44 px)
        lbl_atomo = QLabel(self._zona_marca)
        lbl_atomo.setFixedSize(44, 44)
        lbl_atomo.setPixmap(cargar_pixmap("logo_pea.svg", 44, 44))
        lbl_atomo.setScaledContents(True)
        layout_marca.addWidget(lbl_atomo)

        # Textos de marca
        caja_textos_marca = QVBoxLayout()
        caja_textos_marca.setContentsMargins(0, 0, 0, 0)
        caja_textos_marca.setSpacing(1)

        lbl_marca = QLabel("PEA-i", self._zona_marca)
        lbl_marca.setStyleSheet("font-size: 16pt; font-weight: 800; color: #FFFFFF;")
        caja_textos_marca.addWidget(lbl_marca)

        self._lbl_eslogan = QLabel(f"{ESLOGAN_LINEA_1}\n{ESLOGAN_LINEA_2}", self._zona_marca)
        self._lbl_eslogan.setStyleSheet(
            f"font-size: 8.5pt; color: {TEXTO_SOBRE_OSCURO_SUAVE}; line-height: 1.1;"
        )
        caja_textos_marca.addWidget(self._lbl_eslogan)
        layout_marca.addLayout(caja_textos_marca)

        # Píldora de datos de demostración
        self._pildora_demo = Pildora("Datos de demostración", variante="aviso", parent=self._zona_marca)
        self._pildora_demo.setVisible(False)
        layout_marca.addWidget(self._pildora_demo)

        layout.addWidget(self._zona_marca)
        layout.addStretch(1)

        # --- Zona Centro: 7 Pestañas Principales ---
        self._pestanas = QButtonGroup(self)
        self._pestanas.setExclusive(True)

        self._contenedor_pestanas = QWidget(barra)
        layout_p = QHBoxLayout(self._contenedor_pestanas)
        layout_p.setContentsMargins(0, 0, 0, 0)
        layout_p.setSpacing(4)

        datos_pestanas = [
            ("Inicio", "inicio.svg", Pantalla.INICIO),
            ("Investigadores", "investigadores.svg", Pantalla.INVESTIGADORES),
            ("Grupos", "grupos.svg", Pantalla.GRUPOS),
            ("Productos", "productos.svg", Pantalla.PRODUCTOS),
            ("Análisis de redes", "redes.svg", Pantalla.REDES),
            ("Importar", "importar.svg", Pantalla.IMPORTAR),
            ("Configuración", "configuracion.svg", Pantalla.CONFIGURACION),
        ]

        self._botones_pestanas: list[BotonPestanaSuperior] = []
        for idx, (nombre, icono, pantalla_enum) in enumerate(datos_pestanas):
            btn = BotonPestanaSuperior(nombre, icono, self._contenedor_pestanas)
            self._pestanas.addButton(btn, int(pantalla_enum))
            layout_p.addWidget(btn)
            self._botones_pestanas.append(btn)
            if idx == 0:
                btn.setChecked(True)

        self._pestanas.idClicked.connect(self._al_clic_pestana)
        layout.addWidget(self._contenedor_pestanas)
        layout.addStretch(1)

        # --- Zona Derecha: Deshacer, Avatar, Sesión, Acerca de ---
        zona_der = QWidget(barra)
        layout_der = QHBoxLayout(zona_der)
        layout_der.setContentsMargins(0, 0, 0, 0)
        layout_der.setSpacing(12)

        # Botón Deshacer
        self._btn_deshacer = BotonDeshacerSuperior(zona_der)
        self._btn_deshacer.deshacer_pulsado.connect(self._al_clic_deshacer)
        self._btn_deshacer.popover_solicitado.connect(self._abrir_popover_historial)
        layout_der.addWidget(self._btn_deshacer)

        # Avatar con iniciales
        self._avatar_usuario = Avatar(diametro=42, nombre="Administrador", parent=zona_der)
        layout_der.addWidget(self._avatar_usuario)

        # Columna: Cerrar sesión + Acerca de
        col_sesion = QVBoxLayout()
        col_sesion.setContentsMargins(0, 0, 0, 0)
        col_sesion.setSpacing(2)

        self.btn_cerrar_sesion = QPushButton("Cerrar sesión", zona_der)
        self.btn_cerrar_sesion.setIcon(cargar_icono("cerrar_sesion.svg", 14))
        self.btn_cerrar_sesion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar_sesion.setStyleSheet(
            "QPushButton { background-color: transparent; color: #FFFFFF; font-size: 9.5pt; "
            "border: 1px solid rgba(255, 255, 255, 0.4); border-radius: 8px; padding: 4px 10px; }"
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); }"
        )
        self.btn_cerrar_sesion.clicked.connect(self._al_clic_cerrar_sesion)
        col_sesion.addWidget(self.btn_cerrar_sesion)

        self.btn_acerca = QPushButton("ⓘ Acerca de", zona_der)
        self.btn_acerca.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_acerca.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXTO_SOBRE_OSCURO_SUAVE}; "
            f"font-size: 8.5pt; border: none; padding: 0; text-align: center; }}"
            f"QPushButton:hover {{ color: #FFFFFF; text-decoration: underline; }}"
        )
        self.btn_acerca.clicked.connect(lambda: self.seleccionar_pantalla(Pantalla.ACERCA))
        col_sesion.addWidget(self.btn_acerca)

        layout_der.addLayout(col_sesion)
        layout.addWidget(zona_der)

        return barra

    # -----------------------------------------------------------------------
    # 2. Franjas de Estado
    # -----------------------------------------------------------------------

    def _crear_banner_revision(self) -> QFrame:
        banner = QFrame(self)
        banner.setObjectName("bannerRevision")
        banner.setStyleSheet(
            f"QFrame#bannerRevision {{ background-color: {AVISO_FONDO}; "
            f"border-bottom: 1px solid {AVISO}; padding: 6px 16px; }}"
        )
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(12)

        lbl_ico = QLabel("⚠️", banner)
        layout.addWidget(lbl_ico)

        self._lbl_texto_banner = QLabel(
            "La base de datos cambió en el servidor. Existen modificaciones externas.", banner
        )
        self._lbl_texto_banner.setStyleSheet(f"color: {AVISO}; font-weight: bold; font-size: 10.5pt;")
        layout.addWidget(self._lbl_texto_banner, 1)

        btn_recargar = QPushButton("Recargar ahora", banner)
        btn_recargar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recargar.setStyleSheet(
            f"QPushButton {{ background-color: {AVISO}; color: #FFFFFF; padding: 5px 14px; "
            f"border-radius: {RADIO_BOTON}px; font-weight: bold; border: none; font-size: 10pt; }}"
            f"QPushButton:hover {{ background-color: #703D00; }}"
        )
        btn_recargar.clicked.connect(self._al_clic_recargar_revision)
        layout.addWidget(btn_recargar)

        return banner

    def _crear_franja_sin_conexion(self) -> QFrame:
        franja = QFrame(self)
        franja.setObjectName("franjaSinConexion")
        franja.setStyleSheet(
            f"QFrame#franjaSinConexion {{ background-color: {ERROR_FONDO}; "
            f"border-bottom: 1px solid {ERROR}; padding: 6px 16px; }}"
        )
        layout = QHBoxLayout(franja)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(12)

        lbl_ico = QLabel("🔴", franja)
        layout.addWidget(lbl_ico)

        lbl_txt = QLabel(
            "Sin conexión con Supabase. Los datos en pantalla pueden no ser actuales y las escrituras están bloqueadas.",
            franja,
        )
        lbl_txt.setStyleSheet(f"color: {ERROR}; font-weight: 600; font-size: 10.5pt;")
        layout.addWidget(lbl_txt, 1)

        return franja

    # -----------------------------------------------------------------------
    # 3. Inicialización de Pantallas
    # -----------------------------------------------------------------------

    def _inicializar_pantallas(self) -> None:
        # Pantallas existentes y marcadores modulares
        self._pantalla_inicio = PantallaInicio(
            servicio=self._servicio,
            ejecutor=self._ejecutor,
            filtro_global=self._filtro_global,
            parent=self._apilador,
        )
        self._pantalla_inicio.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_inicio.filtro_cambiado.connect(self._al_cambiar_filtro_global)

        self._pantalla_investigadores_modulo = PantallaInvestigadores(
            servicio=self._servicio,
            ejecutor=self._ejecutor,
            filtro_global=self._filtro_global,
            parent=self._apilador,
        )
        self._pantalla_investigadores_modulo.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_investigadores_modulo.filtro_cambiado.connect(self._al_cambiar_filtro_global)
        self._pantalla_investigadores_modulo.datos_modificados.connect(self.actualizar_estado_global)

        self._pantalla_grupos_modulo = PantallaGrupos(
            servicio=self._servicio,
            ejecutor=self._ejecutor,
            filtro_global=self._filtro_global,
            parent=self._apilador,
        )
        self._pantalla_grupos_modulo.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_grupos_modulo.filtro_cambiado.connect(self._al_cambiar_filtro_global)
        self._pantalla_grupos_modulo.datos_modificados.connect(self.actualizar_estado_global)

        self._pantalla_productos_modulo = PantallaProductos(
            servicio=self._servicio,
            ejecutor=self._ejecutor,
            filtro_global=self._filtro_global,
            parent=self._apilador,
        )
        self._pantalla_productos_modulo.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_productos_modulo.filtro_cambiado.connect(self._al_cambiar_filtro_global)
        self._pantalla_productos_modulo.datos_modificados.connect(self.actualizar_estado_global)
        self._pantalla_productos_modulo.abrir_investigador_solicitado.connect(self._al_solicitar_abrir_investigador)

        # Conectar navegación cruzada de pantallas previas hacia Productos
        self._pantalla_investigadores_modulo.ver_productos_solicitado.connect(self._al_solicitar_ver_productos)
        self._pantalla_grupos_modulo.ver_productos_solicitado.connect(self._al_solicitar_ver_productos)

        # Conectar navegación de inicio a redes
        self._pantalla_inicio.ver_red_nodo_solicitado.connect(self._al_solicitar_ver_nodo_red)

        self._pantalla_redes_modulo = PantallaRedes(
            servicio=self._servicio,
            ejecutor=self._ejecutor,
            filtro_global=self._filtro_global,
            parent=self._apilador,
        )
        self._pantalla_redes_modulo.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_redes_modulo.filtro_cambiado.connect(self._al_cambiar_filtro_global)
        self._pantalla_redes_modulo.abrir_investigador_solicitado.connect(self._al_solicitar_abrir_investigador)

        # Módulos oficiales rediseñados (Secciones 6.6, 6.7 y 6.8)
        self._pantalla_importar = PantallaImportar(self._servicio, self._ejecutor, parent=self._apilador)
        self._pantalla_importar.datos_modificados.connect(self.actualizar_estado_global)
        self._pantalla_importar.solicitar_navegacion.connect(self.seleccionar_pantalla)

        self._pantalla_configuracion_modulo = PantallaConfiguracion(
            self._servicio, self._ejecutor, parent=self._apilador
        )
        self._pantalla_configuracion_modulo.estado_actualizado.connect(self.actualizar_estado_global)
        self._pantalla_configuracion_modulo.datos_modificados.connect(self.actualizar_estado_global)
        self._pantalla_configuracion_modulo.solicitar_navegacion.connect(self.seleccionar_pantalla)
        self._pantalla_conectar = self._pantalla_configuracion_modulo  # alias retrocompatible

        self._pantalla_acerca = PantallaAcerca(self._servicio, parent=self._apilador)
        self._pantalla_acerca.volver_solicitado.connect(lambda: self.seleccionar_pantalla(Pantalla.INICIO))
        self._pantalla_acerca.solicitar_navegacion.connect(self.seleccionar_pantalla)

        self._pantallas_apiladas: list[QWidget] = [
            self._pantalla_inicio,  # 0: INICIO
            self._pantalla_investigadores_modulo,  # 1: INVESTIGADORES
            self._pantalla_grupos_modulo,  # 2: GRUPOS
            self._pantalla_productos_modulo,  # 3: PRODUCTOS
            self._pantalla_redes_modulo,  # 4: REDES
            self._pantalla_importar,  # 5: IMPORTAR
            self._pantalla_configuracion_modulo,  # 6: CONFIGURACION
            self._pantalla_acerca,  # 7: ACERCA
        ]

        for p in self._pantallas_apiladas:
            self._apilador.addWidget(p)

    # -----------------------------------------------------------------------
    # 4. Pie Institucional (72 px / 44 px)
    # -----------------------------------------------------------------------

    def _crear_pie_institucional(self) -> QFrame:
        pie = QFrame(self)
        pie.setObjectName("pieInstitucional")
        pie.setFixedHeight(72)
        pie.setStyleSheet(
            f"QFrame#pieInstitucional {{ background-color: {PIE}; "
            f"border-top: 1px solid {LINEA}; padding: 0 16px; }}"
        )

        layout = QHBoxLayout(pie)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(16)

        # Izquierda: Logo UPC en pastilla blanca + marca
        self._pastilla_logo = QFrame(pie)
        self._pastilla_logo.setFixedSize(52, 52)
        self._pastilla_logo.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 12px; }"
        )
        layout_logo = QHBoxLayout(self._pastilla_logo)
        layout_logo.setContentsMargins(4, 4, 4, 4)

        lbl_upc = QLabel(self._pastilla_logo)
        lbl_upc.setPixmap(cargar_pixmap("logo_upc.png", 42, 42))
        lbl_upc.setScaledContents(True)
        layout_logo.addWidget(lbl_upc)
        layout.addWidget(self._pastilla_logo)

        lbl_pea_pie = QLabel("PEA-i", pie)
        lbl_pea_pie.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {TEXTO};")
        layout.addWidget(lbl_pea_pie)

        # Centro: Texto institucional en 2 líneas
        self._caja_texto_pie = QWidget(pie)
        layout_txt_pie = QVBoxLayout(self._caja_texto_pie)
        layout_txt_pie.setContentsMargins(10, 0, 10, 0)
        layout_txt_pie.setSpacing(1)

        l1 = QLabel(
            "Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas",
            self._caja_texto_pie,
        )
        l1.setStyleSheet(f"font-size: 8.5pt; color: {TEXTO_SECUNDARIO};")
        l2 = QLabel(
            "Taller 2 de Estructura de Datos · Datos de SCIENTI (Minciencias) · Modelo de Medición 2024 (M601PR04G01)",
            self._caja_texto_pie,
        )
        l2.setStyleSheet(f"font-size: 8.5pt; color: {TEXTO_SECUNDARIO};")
        layout_txt_pie.addWidget(l1)
        layout_txt_pie.addWidget(l2)
        layout.addWidget(self._caja_texto_pie)

        layout.addStretch(1)

        # Derecha: Estado vivo (conexión, revisión, deshacer, cola)
        zona_vivo = QWidget(pie)
        layout_vivo = QHBoxLayout(zona_vivo)
        layout_vivo.setContentsMargins(0, 0, 0, 0)
        layout_vivo.setSpacing(10)

        self._lbl_estado_conexion = QLabel("● Conectando…", zona_vivo)
        self._lbl_estado_conexion.setStyleSheet(f"font-size: 9.5pt; font-weight: 600; color: {TEXTO};")
        layout_vivo.addWidget(self._lbl_estado_conexion)

        self._chip_revision = QLabel("Revisión: -", zona_vivo)
        self._chip_revision.setStyleSheet(
            f"font-size: 9pt; color: {TEXTO_SECUNDARIO}; background: #FFFFFF; "
            f"border: 1px solid {LINEA}; border-radius: 6px; padding: 3px 8px;"
        )
        layout_vivo.addWidget(self._chip_revision)

        self._chip_deshacer = QLabel("Deshacer: 0", zona_vivo)
        self._chip_deshacer.setStyleSheet(
            f"font-size: 9pt; color: {TEXTO_SECUNDARIO}; background: #FFFFFF; "
            f"border: 1px solid {LINEA}; border-radius: 6px; padding: 3px 8px;"
        )
        layout_vivo.addWidget(self._chip_deshacer)

        self._chip_cola = QLabel("Cola: 0", zona_vivo)
        self._chip_cola.setStyleSheet(
            f"font-size: 9pt; color: {TEXTO_SECUNDARIO}; background: #FFFFFF; "
            f"border: 1px solid {LINEA}; border-radius: 6px; padding: 3px 8px;"
        )
        layout_vivo.addWidget(self._chip_cola)

        layout.addWidget(zona_vivo)

        return pie

    # -----------------------------------------------------------------------
    # Atajos de Teclado y Temporizador
    # -----------------------------------------------------------------------

    def _configurar_atajos(self) -> None:
        # Ctrl+1 a Ctrl+7: Selección de pestañas
        for num in range(1, 8):
            accion = QAction(self)
            accion.setShortcut(QKeySequence(f"Ctrl+{num}"))
            pantalla_destino = Pantalla(num - 1)
            accion.triggered.connect(lambda _, p=pantalla_destino: self.seleccionar_pantalla(p))
            self.addAction(accion)

        # Ctrl+Z: Deshacer
        accion_deshacer = QAction(self)
        accion_deshacer.setShortcut(QKeySequence("Ctrl+Z"))
        accion_deshacer.triggered.connect(self._al_clic_deshacer)
        self.addAction(accion_deshacer)

        # Ctrl+F: Enfocar búsqueda
        accion_buscar = QAction(self)
        accion_buscar.setShortcut(QKeySequence("Ctrl+F"))
        accion_buscar.triggered.connect(self._al_atajo_buscar)
        self.addAction(accion_buscar)

        # F5: Recargar
        accion_f5 = QAction(self)
        accion_f5.setShortcut(QKeySequence("F5"))
        accion_f5.triggered.connect(self._al_atajo_recargar)
        self.addAction(accion_f5)

        # Ctrl+S: Exportar tabla
        accion_exportar = QAction(self)
        accion_exportar.setShortcut(QKeySequence("Ctrl+S"))
        accion_exportar.triggered.connect(self._al_atajo_exportar)
        self.addAction(accion_exportar)

        # Alt+Left: Volver desde Acerca de
        accion_volver = QAction(self)
        accion_volver.setShortcut(QKeySequence("Alt+Left"))
        accion_volver.triggered.connect(self._al_atajo_volver)
        self.addAction(accion_volver)

        # Esc: Cerrar popovers
        accion_esc = QAction(self)
        accion_esc.setShortcut(QKeySequence("Escape"))
        accion_esc.triggered.connect(self._popover_historial.close)
        self.addAction(accion_esc)

    def _configurar_temporizador_revision(self) -> None:
        self._timer_revision = QTimer(self)
        self._timer_revision.setInterval(10000)
        self._timer_revision.timeout.connect(self._verificar_revision_en_segundo_plano)
        self._timer_revision.start()

    def _al_cambiar_filtro_global(self, filtro: FiltroAnios) -> None:
        """Propaga el filtro temporal a todas las pantallas apiladas."""
        self._filtro_global = filtro
        for p in self._pantallas_apiladas:
            if hasattr(p, "establecer_filtro"):
                p.establecer_filtro(filtro)

    # -----------------------------------------------------------------------
    # Navegación y Transición de Pantallas
    # -----------------------------------------------------------------------

    def seleccionar_pantalla(self, pantalla: Pantalla | int) -> None:
        """Cambia a la pantalla indicada con actualización de botón activo."""
        indice = int(pantalla)
        if not (0 <= indice < self._apilador.count()):
            return

        # Actualizar botón de la barra si es una de las 7 pestañas
        if indice <= 6:
            self._pestanas.setExclusive(True)
            btn = self._pestanas.button(indice)
            if btn and not btn.isChecked():
                btn.setChecked(True)
        else:
            # Desmarcar todas si se abre "Acerca de"
            self._pestanas.setExclusive(False)
            for b in self._botones_pestanas:
                b.setChecked(False)
            self._pestanas.setExclusive(True)

        # Transición animada o directa
        if animaciones_habilitadas():
            self._animar_cambio_pantalla(indice)
        else:
            self._apilador.setCurrentIndex(indice)

        pantalla_actual = self._apilador.currentWidget()
        if hasattr(pantalla_actual, "refrescar"):
            pantalla_actual.refrescar()

        self.actualizar_estado_global()

    def _animar_cambio_pantalla(self, indice: int) -> None:
        """Aplica una transición suave de desvanecimiento entre pantallas."""
        widget_nuevo = self._apilador.widget(indice)
        if widget_nuevo is None:
            self._apilador.setCurrentIndex(indice)
            return

        self._apilador.setCurrentIndex(indice)
        animar_desvanecimiento(widget_nuevo, inicio=0.2, fin=1.0, duracion_ms=200)

    def _al_clic_pestana(self, id_btn: int) -> None:
        self.seleccionar_pantalla(Pantalla(id_btn))

    def _al_solicitar_abrir_investigador(self, clave_o_nombre: str) -> None:
        self.seleccionar_pantalla(Pantalla.INVESTIGADORES)
        if hasattr(self._pantalla_investigadores_modulo, "seleccionar_investigador"):
            self._pantalla_investigadores_modulo.seleccionar_investigador(clave_o_nombre)

    def _al_solicitar_ver_productos(self, filtro_texto: str) -> None:
        self.seleccionar_pantalla(Pantalla.PRODUCTOS)
        if hasattr(self._pantalla_productos_modulo, "filtrar_por_texto"):
            self._pantalla_productos_modulo.filtrar_por_texto(filtro_texto)

    def _al_solicitar_ver_investigadores_grupo(self, cod_o_nombre_grupo: str) -> None:
        self.seleccionar_pantalla(Pantalla.INVESTIGADORES)
        if hasattr(self._pantalla_investigadores_modulo, "filtrar_por_grupo"):
            self._pantalla_investigadores_modulo.filtrar_por_grupo(cod_o_nombre_grupo)

    def _al_solicitar_ver_nodo_red(self, codigo_investigador: str) -> None:
        self.seleccionar_pantalla(Pantalla.REDES)
        if hasattr(self._pantalla_redes_modulo, "seleccionar_nodo"):
            self._pantalla_redes_modulo.seleccionar_nodo(codigo_investigador)

    def _abrir_popover_historial(self) -> None:
        self._popover_historial.mostrar_bajo(self._btn_deshacer)

    # -----------------------------------------------------------------------
    # Atajos y Acciones
    # -----------------------------------------------------------------------

    def _al_atajo_buscar(self) -> None:
        pantalla_actual = self._apilador.currentWidget()
        if hasattr(pantalla_actual, "enfocar_busqueda"):
            pantalla_actual.enfocar_busqueda()

    def _al_atajo_recargar(self) -> None:
        self._al_clic_recargar_revision()

    def _al_atajo_exportar(self) -> None:
        pantalla_actual = self._apilador.currentWidget()
        if hasattr(pantalla_actual, "exportar_csv"):
            pantalla_actual.exportar_csv()

    def _al_atajo_volver(self) -> None:
        if self._apilador.currentIndex() == int(Pantalla.ACERCA):
            self.seleccionar_pantalla(Pantalla.INICIO)

    def _al_clic_deshacer(self) -> None:
        try:
            desc = self._servicio.deshacer()
            self._gestor_toasts.mostrar_exito(f"Acción revertida: {desc}", titulo="Deshacer")
            self.actualizar_estado_global()
            pantalla_actual = self._apilador.currentWidget()
            if hasattr(pantalla_actual, "refrescar"):
                pantalla_actual.refrescar()
        except Exception as err:
            self._gestor_toasts.mostrar_error(str(err), titulo="Deshacer")

    def _al_clic_cerrar_sesion(self) -> None:
        resp = QMessageBox.question(
            self,
            "Cerrar sesión",
            "¿Deseas cerrar la sesión activa y desconectar de la base de datos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._servicio.desconectar()
            self._gestor_toasts.mostrar_info("Sesión cerrada correctamente", titulo="Sesión")
            self.actualizar_estado_global()
            self.seleccionar_pantalla(Pantalla.INICIO)

    def _al_clic_recargar_revision(self) -> None:
        def tarea() -> Any:
            return self._servicio.recargar()

        def exito(_: Any) -> None:
            self._banner_revision.setVisible(False)
            self.actualizar_estado_global()
            pantalla_actual = self._apilador.currentWidget()
            if hasattr(pantalla_actual, "refrescar"):
                pantalla_actual.refrescar()
            self._gestor_toasts.mostrar_exito(
                "Datos recargados y sincronizados con el servidor.", titulo="Sincronización"
            )

        def fallo(err: Exception, _: str) -> None:
            self._gestor_toasts.mostrar_error(f"No fue posible recargar: {err}", titulo="Error de recarga")

        self._ejecutor.ejecutar(tarea, al_terminar=exito, al_fallar=fallo)

    def _verificar_revision_en_segundo_plano(self) -> None:
        estado = self._servicio.estado()
        if estado.modo != ModoConexion.SUPABASE:
            return

        def tarea() -> Any:
            return self._servicio.verificar_cambios_remotos()

        def exito(est_nuevo: Any) -> None:
            self._banner_revision.setVisible(getattr(est_nuevo, "cambio_remoto", False))

        self._ejecutor.ejecutar(tarea, al_terminar=exito)

    def mostrar_aviso_revision(self, rev_local: int, rev_remota: int) -> None:
        """Muestra la franja reactiva de aviso cuando la revisión remota difiere de la local."""
        self._lbl_texto_banner.setText(
            f"La base de datos cambió en el servidor (local: {rev_local}, remota: {rev_remota}). "
            f"Existen modificaciones externas."
        )
        self._banner_revision.setVisible(True)

    # -----------------------------------------------------------------------
    # Estado Global Vivo
    # -----------------------------------------------------------------------

    def actualizar_estado_global(self) -> None:
        """Sincroniza todos los indicadores visuales con ServicioAplicacion.estado()."""
        estado = self._servicio.estado()

        # 1. Píldora de demostración y avatar
        es_demo = estado.modo == ModoConexion.DEMOSTRACION
        self._pildora_demo.setVisible(es_demo)

        if estado.correo:
            self._avatar_usuario.establecer_nombre(estado.correo)
        elif es_demo:
            self._avatar_usuario.establecer_nombre("Demostración")
        else:
            self._avatar_usuario.establecer_nombre("—")

        # 2. Deshacer
        self._btn_deshacer.actualizar_contador(estado.operaciones_deshacer)
        historial = getattr(estado, "historial_deshacer", [])
        self._popover_historial.actualizar_operaciones(historial)

        # 3. Franja sin conexión y banner de revisión
        self._franja_sin_conexion.setVisible(bool(estado.sin_conexion))
        if getattr(estado, "cambio_remoto", False):
            self._banner_revision.setVisible(True)

        # 4. Pie Institucional
        if estado.modo == ModoConexion.SUPABASE:
            if estado.sin_conexion:
                self._lbl_estado_conexion.setText("● Sin conexión")
                self._lbl_estado_conexion.setStyleSheet(f"font-size: 9.5pt; font-weight: bold; color: {ERROR};")
            else:
                rev = estado.revision_local or 0
                self._lbl_estado_conexion.setText(f"● Conectado a Supabase · Revisión {rev}")
                self._lbl_estado_conexion.setStyleSheet(f"font-size: 9.5pt; font-weight: bold; color: {EXITO};")
        elif es_demo:
            self._lbl_estado_conexion.setText("● Datos de demostración")
            self._lbl_estado_conexion.setStyleSheet(f"font-size: 9.5pt; font-weight: bold; color: {AVISO};")
        else:
            self._lbl_estado_conexion.setText("● Desconectado")
            self._lbl_estado_conexion.setStyleSheet(f"font-size: 9.5pt; font-weight: bold; color: {TEXTO_SECUNDARIO};")

        rev_txt = f"Revisión: {estado.revision_local}" if estado.revision_local is not None else "Revisión: N/A"
        self._chip_revision.setText(rev_txt)
        self._chip_deshacer.setText(f"Deshacer: {estado.operaciones_deshacer}")
        self._chip_cola.setText(f"Cola: {estado.tareas_pendientes}")

    # -----------------------------------------------------------------------
    # Responsividad (Sección 11)
    # -----------------------------------------------------------------------

    def resizeEvent(self, event: QEvent) -> None:
        super().resizeEvent(event)
        ancho = self.width()
        alto = self.height()

        # Barra superior según ancho
        modo_solo_icono = ancho < 1120
        ocultar_eslogan = ancho < 1240

        self._lbl_eslogan.setVisible(not ocultar_eslogan)

        for btn in self._botones_pestanas:
            btn.establecer_modo_compacto(modo_solo_icono)

        # Pie institucional según alto
        modo_pie_compacto = alto < 760
        self._caja_texto_pie.setVisible(not modo_pie_compacto)
        self._pie.setFixedHeight(44 if modo_pie_compacto else 72)


# ---------------------------------------------------------------------------
# Autoprueba Automatizada y Capturas
# ---------------------------------------------------------------------------


def ejecutar_autoprueba(app: QApplication, ventana: VentanaPrincipal) -> int:
    """Ejecuta el recorrido de verificación y genera capturas en los 3 tamaños oficiales."""
    import os

    os.environ["PEA_SIN_ANIMACIONES"] = "1"
    if not fuente_inter_cargada():
        print("[AUTOPRUEBA] ERROR: la fuente Inter no está cargada; no se generan capturas.")
        return 2
    print("[AUTOPRUEBA] Iniciando autoprueba de ventana principal PEA-i (PEA_SIN_ANIMACIONES=1)...")
    salida_dir = Path("datos/capturas")
    salida_dir.mkdir(parents=True, exist_ok=True)

    # Cargar demostración
    ventana._servicio.cargar_demostracion()
    ventana.actualizar_estado_global()
    if hasattr(ventana._pantalla_inicio, "refrescar"):
        ventana._pantalla_inicio.refrescar()
    ventana.show()
    app.processEvents()

    # Recorrido de las 3 resoluciones oficiales (1100x700, 1366x768, 1920x1080)
    tamanos = [
        (1100, 700, "1100x700"),
        (1366, 768, "1366x768"),
        (1920, 1080, "1920x1080"),
    ]

    pantallas_recorrido: list[tuple[Pantalla, str]] = [
        (Pantalla.INICIO, "00_inicio"),
        (Pantalla.INVESTIGADORES, "01_investigadores"),
        (Pantalla.GRUPOS, "02_grupos"),
        (Pantalla.PRODUCTOS, "03_productos"),
        (Pantalla.REDES, "04_redes"),
        (Pantalla.IMPORTAR, "05_importar"),
        (Pantalla.CONFIGURACION, "06_configuracion"),
        (Pantalla.ACERCA, "07_acerca"),
    ]

    for p_enum, nombre_pantalla in pantallas_recorrido:
        ventana.seleccionar_pantalla(p_enum)
        app.processEvents()
        p_widget = ventana._apilador.currentWidget()
        if hasattr(p_widget, "refrescar"):
            p_widget.refrescar()
        app.processEvents()

        for ancho, alto, etiqueta in tamanos:
            ventana.resize(ancho, alto)
            app.processEvents()
            pix = ventana.grab()
            ruta = salida_dir / f"pantalla_{nombre_pantalla}_{etiqueta}.png"
            pix.save(str(ruta), "PNG")
            print(f"[AUTOPRUEBA] Captura guardada en {ruta}")

    # Restaurar a Inicio
    ventana.seleccionar_pantalla(Pantalla.INICIO)
    app.processEvents()

    print("[AUTOPRUEBA] Autoprueba completada exitosamente.")
    return 0
