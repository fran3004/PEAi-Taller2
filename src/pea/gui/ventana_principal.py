"""Ventana principal institucional de PEA-i (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 5).
Estructura de cuatro zonas:
1. Barra superior de 88 px con degradado horizontal, átomo, eslogan,
   7 pestañas institucionales, botón Deshacer con popover de historial,
   avatar con iniciales, Cerrar sesión, enlace Acerca de y filete UPC de 3 px.
2. Franjas reactivas de aviso de revisión remota y modo sin conexión.
3. Zona central con QStackedWidget y 8 pantallas (enum Pantalla).
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
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
    QThreadPool,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontMetrics,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QPen,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractScrollArea,
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
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
        try:
            w = float(self.width())
            h = float(self.height())
            w1 = round(w / 3.0)
            w2 = round(w / 3.0)
            w3 = w - w1 - w2

            painter.fillRect(QRectF(0, 0, w1, h), QColor(UPC_VERDE_OSCURO))
            painter.fillRect(QRectF(w1, 0, w2, h), QColor(UPC_VERDE))
            painter.fillRect(QRectF(w1 + w2, 0, w3, h), QColor(UPC_VERDE_CLARO))
        finally:
            painter.end()


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
        ancho_inicial = self._calcular_ancho_completo()
        self.setMinimumWidth(ancho_inicial)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"Pestaña {texto}")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._pixmap_normal = cargar_pixmap(nombre_icono, 24, 24)

    def _calcular_ancho_completo(self) -> int:
        """Calcula el ancho necesario para el texto completo con QFontMetrics y margen de respiración."""
        fuente = QFont(self.font())
        fuente.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente.setBold(True)  # Se calcula sobre negrita (cuando la pestaña está activa/seleccionada)
        fm = QFontMetrics(fuente)
        ancho_texto = fm.horizontalAdvance(self._texto)
        # Margen horizontal simétrico (14 px por lado) para que el texto nunca roce los bordes
        margen_horizontal = 28
        return max(76, ancho_texto + margen_horizontal)

    def sizeHint(self) -> QSize:
        """Devuelve el tamaño preferido del botón según el modo activo."""
        if self._modo_compacto:
            return QSize(44, 64)
        return QSize(self._calcular_ancho_completo(), 64)

    def minimumSizeHint(self) -> QSize:
        """Garantiza que la barra no colapse el ancho requerido por el texto."""
        return self.sizeHint()

    def establecer_modo_compacto(self, compacto: bool) -> None:
        """Alterna entre mostrar solo ícono con tooltip o ícono con etiqueta completa."""
        if self._modo_compacto == compacto:
            return
        self._modo_compacto = compacto
        if compacto:
            self.setToolTip(self._texto)
            self.setFixedWidth(44)
        else:
            self.setToolTip("")
            self.setMaximumWidth(16777215)
            ancho_completo = self._calcular_ancho_completo()
            self.setMinimumWidth(ancho_completo)
        self.updateGeometry()
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
            painter.drawRoundedRect(
                rect.adjusted(2, 2, -2, -2),
                estilo.RADIO_PESTANA_ACTIVA,
                estilo.RADIO_PESTANA_ACTIVA,
            )
        elif es_hover:
            painter.setBrush(QColor(255, 255, 255, 20))  # 8%
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                rect.adjusted(2, 2, -2, -2),
                estilo.RADIO_PESTANA_ACTIVA,
                estilo.RADIO_PESTANA_ACTIVA,
            )

        # 2. Anillo de foco accesible
        if self.hasFocus() and es_activo:
            pen_foco = QPen(QColor(ACENTO), 2)
            painter.setPen(pen_foco)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(2, 2, -2, -2),
                estilo.RADIO_PESTANA_ACTIVA,
                estilo.RADIO_PESTANA_ACTIVA,
            )

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

            # 4. Etiqueta de texto completa
            fuente = QFont(self.font())
            fuente.setPointSize(estilo.TAMANO_AUXILIAR)
            fuente.setBold(es_activo)
            painter.setFont(fuente)

            color_txt = QColor(TEXTO_SOBRE_OSCURO if es_activo else TEXTO_SOBRE_OSCURO_SUAVE)
            painter.setPen(color_txt)

            rect_txt = QRectF(0, 38, float(rect.width()), 20)
            painter.drawText(rect_txt, Qt.AlignmentFlag.AlignCenter, self._texto)

        # 5. Barra inferior de acento (40% del ancho, centrado)
        if es_activo:
            ancho_barra = rect.width() * 0.40
            x_barra = (rect.width() - ancho_barra) / 2.0
            y_barra = rect.height() - 4.0
            rect_barra = QRectF(x_barra, y_barra, ancho_barra, 3.0)
            painter.fillRect(rect_barra, QColor(ACENTO))
        painter.end()


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
            f"QPushButton {{ background-color: {estilo.SUPERPOSICION_CLARA_12}; "
            f"border: 1px solid {estilo.SUPERPOSICION_CLARA_25}; border-radius: {estilo.RADIO_TARJETA}px; }} "
            f"QPushButton:hover {{ background-color: {estilo.SUPERPOSICION_CLARA_22}; }} "
            f"QPushButton:focus {{ border: 2px solid {ACENTO}; outline: none; }} "
            f"QPushButton:disabled {{ background-color: {estilo.SUPERPOSICION_CLARA_5}; border-color: {estilo.SUPERPOSICION_CLARA_10}; }}"
        )
        self.btn_accion.clicked.connect(self.deshacer_pulsado.emit)
        layout.addWidget(self.btn_accion)

        # Chevron para desplegar historial
        self.btn_chevron = QPushButton("v", self)
        self.btn_chevron.setFixedSize(22, 40)
        self.btn_chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chevron.setToolTip("Abrir historial de operaciones")
        self.btn_chevron.setAccessibleName("Abrir historial de operaciones")
        self.btn_chevron.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {TEXTO_SOBRE_OSCURO_SUAVE}; "
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; border: none; border-radius: {estilo.RADIO_BOTON}px; }} "
            f"QPushButton:hover {{ background-color: {estilo.SUPERPOSICION_CLARA_12}; color: {estilo.SUPERFICIE}; }} "
            f"QPushButton:focus {{ border: 1px solid {ACENTO}; outline: none; }}"
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
            f"QFrame {{ background-color: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; }}"
        )
        layout_ctx = QHBoxLayout(barra_contexto)
        layout_ctx.setContentsMargins(16, 8, 16, 8)
        layout_ctx.setSpacing(12)

        lbl_tit = QLabel(titulo, barra_contexto)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {TEXTO};")
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
        widget_central.setObjectName("fondo")
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
            try:
                grad = QLinearGradient(0, 0, barra.width(), 0)
                grad.setColorAt(0.0, QColor(ENCABEZADO_INICIO))
                grad.setColorAt(0.5, QColor(ENCABEZADO_MEDIO))
                grad.setColorAt(1.0, QColor(ENCABEZADO_FIN))
                painter.fillRect(barra.rect(), grad)
            finally:
                painter.end()

        barra.paintEvent = pintar_barra  # type: ignore[assignment]

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

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
        caja_textos_marca.setSpacing(2)

        fila_marca = QHBoxLayout()
        fila_marca.setContentsMargins(0, 0, 0, 0)
        fila_marca.setSpacing(8)
        self._fila_marca = fila_marca

        lbl_marca = QLabel("PEA-i", self._zona_marca)
        lbl_marca.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt; font-weight: 800; color: {estilo.SUPERFICIE};")
        fila_marca.addWidget(lbl_marca)

        # Píldora de datos de demostración compacta junto al logo
        self._pildora_demo = Pildora("Datos de demostración", variante="aviso", parent=self._zona_marca)
        self._pildora_demo.setVisible(False)
        fila_marca.addWidget(self._pildora_demo)
        fila_marca.addStretch()

        caja_textos_marca.addLayout(fila_marca)
        self._caja_textos_marca = caja_textos_marca

        self._lbl_eslogan = QLabel(f"{ESLOGAN_LINEA_1}\n{ESLOGAN_LINEA_2}", self._zona_marca)
        self._lbl_eslogan.setStyleSheet(
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SOBRE_OSCURO_SUAVE}; line-height: 1.1;"
        )
        caja_textos_marca.addWidget(self._lbl_eslogan)
        layout_marca.addLayout(caja_textos_marca)

        layout.addWidget(self._zona_marca)
        layout.addStretch(1)

        # --- Zona Centro: 7 Pestañas Principales ---
        self._pestanas = QButtonGroup(self)
        self._pestanas.setExclusive(True)

        self._contenedor_pestanas = QWidget(barra)
        layout_p = QHBoxLayout(self._contenedor_pestanas)
        layout_p.setContentsMargins(0, 0, 0, 0)
        layout_p.setSpacing(0)
        layout_p.addStretch(1)

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
            layout_p.addStretch(1)
            self._botones_pestanas.append(btn)
            if idx == 0:
                btn.setChecked(True)

        self._pestanas.idClicked.connect(self._al_clic_pestana)
        layout.addWidget(self._contenedor_pestanas, 1)

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
        col_sesion.setSpacing(3)
        col_sesion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_cerrar_sesion = QPushButton("Cerrar sesión", zona_der)
        self.btn_cerrar_sesion.setObjectName("btnCerrarSesion")
        self.btn_cerrar_sesion.setAccessibleName("Cerrar sesión")
        self.btn_cerrar_sesion.setIcon(cargar_icono("cerrar_sesion.svg", 14))
        self.btn_cerrar_sesion.setIconSize(QSize(14, 14))
        self.btn_cerrar_sesion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar_sesion.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_cerrar_sesion.setStyleSheet(
            f"QPushButton#btnCerrarSesion {{ "
            f"  background-color: transparent; "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"  font-size: {estilo.TAMANO_AUXILIAR}pt; "
            f"  font-weight: 600; "
            f"  border: 1px solid {estilo.SUPERPOSICION_CLARA_40}; "
            f"  border-radius: {RADIO_BOTON}px; "
            f"  padding: 4px 10px; "
            f"}} "
            f"QPushButton#btnCerrarSesion:hover {{ "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_14}; "
            f"  border: 1px solid {TEXTO_SOBRE_OSCURO}; "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"}} "
            f"QPushButton#btnCerrarSesion:focus {{ "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_10}; "
            f"  border: 2px solid {ACENTO}; "
            f"  padding: 3px 9px; "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"  outline: none; "
            f"}} "
            f"QPushButton#btnCerrarSesion:pressed {{ "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_22}; "
            f"  border: 1px solid {TEXTO_SOBRE_OSCURO}; "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"}}"
        )
        self.btn_cerrar_sesion.clicked.connect(self._al_clic_cerrar_sesion)
        col_sesion.addWidget(self.btn_cerrar_sesion)

        self.btn_acerca = QPushButton("ⓘ Acerca de", zona_der)
        self.btn_acerca.setObjectName("btnAcercaDe")
        self.btn_acerca.setAccessibleName("Acerca de PEA-i")
        self.btn_acerca.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_acerca.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_acerca.setStyleSheet(
            f"QPushButton#btnAcercaDe {{ "
            f"  background-color: transparent; "
            f"  color: {TEXTO_SOBRE_OSCURO_SUAVE}; "
            f"  font-size: {estilo.TAMANO_AUXILIAR}pt; "
            f"  font-weight: 500; "
            f"  border: 1px solid transparent; "
            f"  border-radius: {RADIO_BOTON}px; "
            f"  padding: 2px 6px; "
            f"  text-align: center; "
            f"}} "
            f"QPushButton#btnAcercaDe:hover {{ "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_8}; "
            f"  border: 1px solid {estilo.SUPERPOSICION_CLARA_20}; "
            f"  text-decoration: underline; "
            f"}} "
            f"QPushButton#btnAcercaDe:focus {{ "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_10}; "
            f"  border: 1px solid {ACENTO}; "
            f"  outline: none; "
            f"}} "
            f"QPushButton#btnAcercaDe:pressed {{ "
            f"  background-color: {estilo.SUPERPOSICION_CLARA_14}; "
            f"  color: {TEXTO_SOBRE_OSCURO}; "
            f"}}"
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
        self._lbl_texto_banner.setStyleSheet(f"color: {AVISO}; font-weight: bold; font-size: {estilo.TAMANO_CUERPO}pt;")
        layout.addWidget(self._lbl_texto_banner, 1)

        btn_recargar = QPushButton("Recargar ahora", banner)
        btn_recargar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recargar.setStyleSheet(
            f"QPushButton {{ background-color: {AVISO}; color: {estilo.SUPERFICIE}; padding: 5px 14px; "
            f"border-radius: {RADIO_BOTON}px; font-weight: bold; border: none; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.AVISO}; }}"
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
        lbl_txt.setStyleSheet(f"color: {ERROR}; font-weight: 600; font-size: {estilo.TAMANO_CUERPO}pt;")
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
        self._pantalla_inicio.datos_modificados.connect(self.actualizar_estado_global)

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
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._layout_pie = layout

        # Izquierda: Logo UPC en pastilla blanca + marca
        self._pastilla_logo = QFrame(pie)
        self._pastilla_logo.setFixedSize(52, 52)
        self._pastilla_logo.setStyleSheet(
            f"QFrame {{ background-color: {estilo.SUPERFICIE}; border-radius: {estilo.RADIO_PESTANA_ACTIVA}px; }}"
        )
        layout_logo = QHBoxLayout(self._pastilla_logo)
        layout_logo.setContentsMargins(4, 4, 4, 4)

        lbl_upc = QLabel(self._pastilla_logo)
        lbl_upc.setPixmap(cargar_pixmap("logo_upc.png", 42, 42))
        lbl_upc.setScaledContents(True)
        layout_logo.addWidget(lbl_upc)
        self._lbl_upc = lbl_upc
        layout.addWidget(self._pastilla_logo)

        lbl_pea_pie = QLabel("PEA-i", pie)
        lbl_pea_pie.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};")
        layout.addWidget(lbl_pea_pie)

        # Centro: Texto institucional en 2 líneas (adaptable según resolución)
        self._caja_texto_pie = QWidget(pie)
        layout_txt_pie = QVBoxLayout(self._caja_texto_pie)
        layout_txt_pie.setContentsMargins(10, 0, 10, 0)
        layout_txt_pie.setSpacing(1)
        layout_txt_pie.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        l1 = QLabel(
            "Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas",
            self._caja_texto_pie,
        )
        l1.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        l2 = QLabel(
            "Taller 2 de Estructura de Datos · Datos de SCIENTI (Minciencias) · Modelo de Medición 2024 (M601PR04G01)",
            self._caja_texto_pie,
        )
        l2.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        layout_txt_pie.addWidget(l1)
        layout_txt_pie.addWidget(l2)
        self._lbl_pie_l1 = l1
        self._lbl_pie_l2 = l2
        self._caja_texto_pie.setToolTip(
            "Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas\n"
            "Taller 2 de Estructura de Datos · Datos de SCIENTI (Minciencias) · Modelo de Medición 2024 (M601PR04G01)"
        )
        layout.addWidget(self._caja_texto_pie)

        layout.addStretch(1)

        # Derecha: Estado vivo (conexión, revisión, deshacer, cola)
        zona_vivo = QWidget(pie)
        self._zona_vivo_pie = zona_vivo
        layout_vivo = QHBoxLayout(zona_vivo)
        layout_vivo.setContentsMargins(0, 0, 0, 0)
        layout_vivo.setSpacing(10)
        layout_vivo.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._zona_vivo_layout = layout_vivo

        self._lbl_estado_conexion = QLabel("● Conectando…", zona_vivo)
        self._lbl_estado_conexion.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: 600; color: {TEXTO};")
        layout_vivo.addWidget(self._lbl_estado_conexion)

        self._chip_revision = QLabel("Revisión: -", zona_vivo)
        self._chip_revision.setStyleSheet(
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; background: {estilo.SUPERFICIE}; "
            f"border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; padding: 3px 8px;"
        )
        layout_vivo.addWidget(self._chip_revision)

        self._chip_deshacer = QLabel("Deshacer: 0", zona_vivo)
        self._chip_deshacer.setStyleSheet(
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; background: {estilo.SUPERFICIE}; "
            f"border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; padding: 3px 8px;"
        )
        layout_vivo.addWidget(self._chip_deshacer)

        self._chip_cola = QLabel("Cola: 0", zona_vivo)
        self._chip_cola.setStyleSheet(
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; background: {estilo.SUPERFICIE}; "
            f"border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; padding: 3px 8px;"
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

        self._cambiar_pantalla_estable(indice)

        pantalla_actual = self._apilador.currentWidget()
        if hasattr(pantalla_actual, "refrescar"):
            pantalla_actual.refrescar()

        self.actualizar_estado_global()

    def _cambiar_pantalla_estable(self, indice: int) -> None:
        """Cambia de página sin composición temporal ni efectos de opacidad."""
        widget_anterior = self._apilador.currentWidget()
        widget_nuevo = self._apilador.widget(indice)
        if widget_nuevo is None:
            return

        # Elimina cualquier efecto de opacidad heredado de versiones anteriores
        # antes de que cualquiera de las dos páginas vuelva a pintarse.
        if widget_anterior is not None:
            widget_anterior.setGraphicsEffect(None)  # type: ignore[arg-type]
        widget_nuevo.setGraphicsEffect(None)  # type: ignore[arg-type]
        self._apilador.setCurrentIndex(indice)

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
        dialogo = QMessageBox(self)
        dialogo.setIcon(QMessageBox.Icon.Question)
        dialogo.setWindowTitle("Cerrar sesión")
        dialogo.setText("¿Deseas cerrar la sesión activa y desconectar de la base de datos?")
        dialogo.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialogo.setStyleSheet(
            f"QMessageBox {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO}; }}"
            f"QMessageBox QLabel {{ color: {TEXTO}; background-color: transparent; }}"
            f"QMessageBox QPushButton {{ background-color: {estilo.FICHA}; color: {TEXTO}; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 16px; }}"
            f"QMessageBox QPushButton:hover {{ background-color: {estilo.SUPERFICIE_SELECCIONADA}; }}"
        )
        dialogo.button(QMessageBox.StandardButton.Yes).setText("Sí")
        dialogo.button(QMessageBox.StandardButton.No).setText("No")
        dialogo.setDefaultButton(QMessageBox.StandardButton.No)
        resp = dialogo.exec()
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
                self._lbl_estado_conexion.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {ERROR};")
            else:
                rev = estado.revision_local or 0
                self._lbl_estado_conexion.setText(f"● Conectado a Supabase · Revisión {rev}")
                self._lbl_estado_conexion.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {EXITO};")
        elif es_demo:
            self._lbl_estado_conexion.setText("● Datos de demostración")
            self._lbl_estado_conexion.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {AVISO};")
        else:
            self._lbl_estado_conexion.setText("● Desconectado")
            self._lbl_estado_conexion.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {TEXTO_SECUNDARIO};")

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
        modo_solo_icono = ancho < 1600
        ocultar_eslogan = ancho < 2000

        self._lbl_eslogan.setVisible(not ocultar_eslogan)
        self._ajustar_marca_compacta(ancho < 2000)

        if getattr(self, "_modo_pestanas_compacto_actual", None) != modo_solo_icono:
            for btn in self._botones_pestanas:
                btn.establecer_modo_compacto(modo_solo_icono)
            layout_pestanas = self._contenedor_pestanas.layout()
            if layout_pestanas is not None:
                layout_pestanas.invalidate()
                ancho_pestanas = layout_pestanas.minimumSize().width()
                self._contenedor_pestanas.setMinimumWidth(ancho_pestanas)
                layout_pestanas.activate()
            layout_barra = self._barra_superior.layout()
            if layout_barra is not None:
                layout_barra.invalidate()
                layout_barra.activate()
            self._modo_pestanas_compacto_actual = modo_solo_icono

        # Pie institucional responsivo (conserva texto institucional y estado vivo)
        modo_pie_compacto = alto < 760 or ancho < 1240
        if getattr(self, "_modo_pie_compacto_actual", None) != modo_pie_compacto:
            self._modo_pie_compacto_actual = modo_pie_compacto
            self._pie.setFixedHeight(44 if modo_pie_compacto else 72)
            if modo_pie_compacto:
                self._pastilla_logo.setFixedSize(34, 34)
                self._lbl_upc.setPixmap(cargar_pixmap("logo_upc.png", 26, 26))
                self._layout_pie.setContentsMargins(16, 4, 16, 4)
                self._layout_pie.setSpacing(10)
                self._zona_vivo_layout.setSpacing(6)
            else:
                self._pastilla_logo.setFixedSize(52, 52)
                self._lbl_upc.setPixmap(cargar_pixmap("logo_upc.png", 42, 42))
                self._layout_pie.setContentsMargins(20, 8, 20, 8)
                self._layout_pie.setSpacing(16)
                self._zona_vivo_layout.setSpacing(10)
            self._lbl_pie_l2.setVisible(not modo_pie_compacto)

        self._caja_texto_pie.setVisible(True)
        self._lbl_pie_l1.setVisible(True)

        texto_l1 = (
            "Universidad Popular del Cesar · Ingeniería de Sistemas"
            if ancho < 1240
            else "Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas"
        )
        if self._lbl_pie_l1.text() != texto_l1:
            self._lbl_pie_l1.setText(texto_l1)

    def _ajustar_marca_compacta(self, compacto: bool) -> None:
        """Ubica la insignia debajo de la marca cuando el ancho no admite una sola fila."""
        if getattr(self, "_marca_compacta_actual", None) == compacto:
            return
        if compacto:
            self._fila_marca.removeWidget(self._pildora_demo)
            self._caja_textos_marca.addWidget(self._pildora_demo)
            self._pildora_demo.establecer_margen_horizontal(8)
        else:
            self._caja_textos_marca.removeWidget(self._pildora_demo)
            self._fila_marca.insertWidget(1, self._pildora_demo)
            self._pildora_demo.establecer_margen_horizontal(10)
        self._marca_compacta_actual = compacto


# ---------------------------------------------------------------------------
# Autoprueba Automatizada y Capturas
# ---------------------------------------------------------------------------


def _nombre_widget(widget: QWidget) -> str:
    return widget.objectName() or widget.metaObject().className()


def _eje_alcanzable_con_scroll(
    inicio: int,
    tamano: int,
    inicio_visible: int,
    tamano_visible: int,
    valor_actual: int,
    valor_minimo: int,
    valor_maximo: int,
) -> bool:
    inicio_minimo = inicio + valor_actual - valor_maximo
    inicio_maximo = inicio + valor_actual - valor_minimo
    return inicio_minimo < inicio_visible + tamano_visible and inicio_maximo + tamano > inicio_visible


def _widget_alcanzable_con_scroll(widget: QWidget, ventana: QWidget) -> bool:
    padre = widget.parentWidget()
    while padre is not None and padre is not ventana:
        if isinstance(padre, QScrollArea):
            contenido = padre.widget()
            if contenido is not None and (contenido is widget or contenido.isAncestorOf(widget)):
                rect_contenido = QRect(widget.mapTo(contenido, QPoint(0, 0)), widget.size())
                if contenido.rect().contains(rect_contenido):
                    viewport = padre.viewport()
                    rect_visible = QRect(viewport.mapTo(ventana, QPoint(0, 0)), viewport.size())
                    rect_visible = rect_visible.intersected(ventana.rect())
                    ancestro = viewport.parentWidget()
                    while ancestro is not None and ancestro is not ventana and not rect_visible.isEmpty():
                        rect_ancestro = QRect(ancestro.mapTo(ventana, QPoint(0, 0)), ancestro.size())
                        rect_visible = rect_visible.intersected(rect_ancestro)
                        ancestro = ancestro.parentWidget()
                    if rect_visible.isEmpty():
                        padre = padre.parentWidget()
                        continue

                    clip_visible = QRect(
                        viewport.mapFrom(ventana, rect_visible.topLeft()),
                        rect_visible.size(),
                    )
                    rect_viewport = QRect(widget.mapTo(viewport, QPoint(0, 0)), widget.size())
                    barra_h = padre.horizontalScrollBar()
                    barra_v = padre.verticalScrollBar()
                    maximo_h = barra_h.maximum()
                    maximo_v = barra_v.maximum()
                    if padre.horizontalScrollBarPolicy() != Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
                        maximo_h = max(maximo_h, contenido.width() - viewport.width())
                    if padre.verticalScrollBarPolicy() != Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
                        maximo_v = max(maximo_v, contenido.height() - viewport.height())
                    if _eje_alcanzable_con_scroll(
                        rect_viewport.x(),
                        rect_viewport.width(),
                        clip_visible.x(),
                        clip_visible.width(),
                        barra_h.value(),
                        barra_h.minimum(),
                        maximo_h,
                    ) and _eje_alcanzable_con_scroll(
                        rect_viewport.y(),
                        rect_viewport.height(),
                        clip_visible.y(),
                        clip_visible.height(),
                        barra_v.value(),
                        barra_v.minimum(),
                        maximo_v,
                    ):
                        return True
        padre = padre.parentWidget()
    return False


def _widgets_fuera_de_ventana(ventana: QWidget) -> list[str]:
    rect_ventana = ventana.rect()
    fuera: list[str] = []
    for widget in ventana.findChildren(QWidget):
        if not widget.isVisibleTo(ventana) or widget.size().isEmpty():
            continue
        rect_widget = QRect(widget.mapTo(ventana, QPoint(0, 0)), widget.size())
        if not rect_ventana.contains(rect_widget) and not _widget_alcanzable_con_scroll(widget, ventana):
            fuera.append(_nombre_widget(widget))
    return fuera


def _etiqueta_elidida(etiqueta: QLabel) -> bool:
    texto = etiqueta.text().strip()
    if not texto:
        return False

    area = etiqueta.contentsRect()
    ancho_disponible = max(0, area.width() - 2 * etiqueta.margin())
    if etiqueta.textFormat() == Qt.TextFormat.RichText or texto.startswith("<"):
        documento = QTextDocument()
        documento.setDefaultFont(etiqueta.font())
        documento.setDocumentMargin(0)
        documento.setHtml(texto)
        if etiqueta.wordWrap():
            documento.setTextWidth(ancho_disponible)
            return documento.size().height() > area.height()
        return documento.idealWidth() > ancho_disponible

    if etiqueta.wordWrap():
        return etiqueta.hasHeightForWidth() and etiqueta.heightForWidth(etiqueta.width()) > etiqueta.height()

    metricas = QFontMetrics(etiqueta.font())
    lineas = texto.splitlines() or [texto]
    ancho_texto = max(metricas.horizontalAdvance(linea) for linea in lineas)
    alto_texto = metricas.height() * len(lineas)
    return ancho_texto > ancho_disponible or alto_texto > area.height()


def _textos_elididos_sin_tooltip(ventana: QWidget) -> list[str]:
    hallazgos: list[str] = []
    for widget in ventana.findChildren(QWidget):
        if not widget.isVisibleTo(ventana) or widget.toolTip().strip():
            continue
        if isinstance(widget, QLabel):
            texto = widget.text().strip()
            if texto and _etiqueta_elidida(widget):
                hallazgos.append(f"{_nombre_widget(widget)} «{texto[:36]}»")
        elif isinstance(widget, QAbstractButton):
            texto = widget.text().strip()
            medida = widget.sizeHint()
            if texto and (medida.width() > widget.width() or medida.height() > widget.height()):
                hallazgos.append(f"{_nombre_widget(widget)} «{texto[:36]}»")

    for encabezado in ventana.findChildren(QHeaderView):
        if (
            not encabezado.isVisibleTo(ventana)
            or encabezado.orientation() != Qt.Orientation.Horizontal
            or encabezado.model() is None
        ):
            continue
        modelo = encabezado.model()
        manejador_tooltip = "helpEvent" in type(encabezado).__dict__
        metricas = QFontMetrics(encabezado.font())
        for seccion in range(encabezado.count()):
            if encabezado.isSectionHidden(seccion):
                continue
            texto = str(
                modelo.headerData(seccion, encabezado.orientation(), Qt.ItemDataRole.DisplayRole) or ""
            ).strip()
            if not texto or metricas.horizontalAdvance(texto) <= max(0, encabezado.sectionSize(seccion) - 16):
                continue
            tooltip = modelo.headerData(
                seccion,
                encabezado.orientation(),
                Qt.ItemDataRole.ToolTipRole,
            )
            if not tooltip and not encabezado.toolTip() and not manejador_tooltip:
                hallazgos.append(f"{_nombre_widget(encabezado)} «{texto[:36]}»")
    return hallazgos


def ejecutar_autoprueba(app: QApplication, ventana: VentanaPrincipal) -> int:
    """Ejecuta el recorrido visual, valida geometrías y genera capturas oficiales."""
    import os

    prev_sin_anim = os.environ.get("PEA_SIN_ANIMACIONES")
    os.environ["PEA_SIN_ANIMACIONES"] = "1"
    if not fuente_inter_cargada():
        if prev_sin_anim is None:
            os.environ.pop("PEA_SIN_ANIMACIONES", None)
        else:
            os.environ["PEA_SIN_ANIMACIONES"] = prev_sin_anim
        print("[AUTOPRUEBA] ERROR: la fuente Inter no está cargada; no se generan capturas.")
        return 2
    print("[AUTOPRUEBA] Iniciando autoprueba de ventana principal PEA-i (PEA_SIN_ANIMACIONES=1)...")
    salida_dir = Path("datos/capturas/oficiales")
    salida_dir.mkdir(parents=True, exist_ok=True)

    # Cargar demostración
    ventana._servicio.cargar_demostracion()
    ventana.actualizar_estado_global()
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

    resumen: list[tuple[str, str, int, int, int, str]] = []
    errores_barras = 0
    errores_fuera = 0
    errores_texto = 0

    for p_enum, nombre_pantalla in pantallas_recorrido:
        ventana.seleccionar_pantalla(p_enum)
        app.processEvents()
        QThreadPool.globalInstance().waitForDone(3000)
        app.processEvents()
        app.processEvents()

        for ancho, alto, etiqueta in tamanos:
            ventana.resize(ancho, alto)
            app.processEvents()
            app.processEvents()

            barras = [
                widget.objectName() or widget.metaObject().className()
                for widget in ventana.findChildren(QAbstractScrollArea)
                if widget.isVisible() and widget.horizontalScrollBar().isVisible()
            ]
            fuera = _widgets_fuera_de_ventana(ventana)
            textos_elididos = _textos_elididos_sin_tooltip(ventana)

            pix = ventana.grab()
            ruta = salida_dir / f"pantalla_{nombre_pantalla}_{etiqueta}.png"
            pix.save(str(ruta), "PNG")
            print(f"[AUTOPRUEBA] Captura guardada en {ruta}")
            if barras:
                errores_barras += len(barras)
                print(
                    f"[AUTOPRUEBA] FALLA {nombre_pantalla} {etiqueta}: "
                    f"barras horizontales visibles: {', '.join(barras)}"
                )
            if fuera:
                errores_fuera += len(fuera)
                print(
                    f"[AUTOPRUEBA] FALLA {nombre_pantalla} {etiqueta}: "
                    f"{len(fuera)} widgets fuera de la ventana: {', '.join(fuera)}"
                )
            if textos_elididos:
                errores_texto += len(textos_elididos)
                print(
                    f"[AUTOPRUEBA] FALLA {nombre_pantalla} {etiqueta}: "
                    f"{len(textos_elididos)} textos elididos sin tooltip: "
                    f"{', '.join(textos_elididos)}"
                )
            resumen.append(
                (nombre_pantalla, etiqueta, len(barras), len(fuera), len(textos_elididos), str(ruta))
            )

    # Restaurar a Inicio y cerrar ventana de autoprueba para no interferir con pruebas posteriores
    ventana.seleccionar_pantalla(Pantalla.INICIO)
    if hasattr(ventana, "_timer_revision"):
        ventana._timer_revision.stop()
    ventana.close()
    ventana.deleteLater()
    app.processEvents()
    if prev_sin_anim is None:
        os.environ.pop("PEA_SIN_ANIMACIONES", None)
    else:
        os.environ["PEA_SIN_ANIMACIONES"] = prev_sin_anim

    print("\n[AUTOPRUEBA] Resumen")
    print(f"{'Pantalla':<22} {'Tamaño':<10} {'Barras':>7} {'Fuera':>7} {'Elididos':>9}  Captura")
    print("-" * 100)
    for nombre, etiqueta, barras, fuera, elididos, ruta in resumen:
        print(f"{nombre:<22} {etiqueta:<10} {barras:>7} {fuera:>7} {elididos:>9}  {ruta}")

    hallazgos_totales = errores_barras + errores_fuera + errores_texto
    if hallazgos_totales:
        print(
            f"[AUTOPRUEBA] FALLA: {hallazgos_totales} hallazgos visuales "
            f"(barras: {errores_barras}, widgets inaccesibles: {errores_fuera}, "
            f"textos elididos sin tooltip: {errores_texto})."
        )
        return 3
    print(f"[AUTOPRUEBA] Cero hallazgos en las {len(resumen)} combinaciones de pantalla y resolución.")
    return 0
