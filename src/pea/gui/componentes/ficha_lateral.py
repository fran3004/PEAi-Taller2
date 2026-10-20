"""Componente base de ficha lateral de 360 px para detalles y acciones.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 8, 6.2, 6.3 y 6.4).
- Ancho estándar de 360 px con bordes redondeados y sombra.
- Cabecera: avatar circular grande (72-96 px), nombre principal (16 pt) y subtítulo.
- Zona KPI: cuadrícula flexible (habitualmente 2×2 de FichaKPI).
- Zona de contenido: espacio para minigráficos, listas de coautores o badges.
- Zona de acciones: botones Editar, Activar/Desactivar, Eliminar… y acciones secundarias.
- Estado vacío cuando no hay fila seleccionada.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.pildora import Pildora
from pea.gui.estilo import (
    ERROR,
    FICHA,
    LINEA,
    PRIMARIO,
    RADIO_BOTON,
    RADIO_TARJETA,
    TEXTO,
    TEXTO_SECUNDARIO,
)


class FichaLateral(QFrame):
    """Ficha lateral institucional de 360 px para visualización detallada y acciones."""

    ANCHO_MINIMO_KPI = 180

    editar_solicitado = Signal()
    cambiar_estado_solicitado = Signal()
    eliminar_solicitado = Signal()
    ver_completa_solicitado = Signal()
    ver_productos_solicitado = Signal()
    accion_extra_solicitada = Signal(str)

    def __init__(self, parent: QWidget | None = None, diametro_avatar: int = 80) -> None:
        super().__init__(parent)
        self.setObjectName("fichaLateral")
        self.setMinimumWidth(320)
        self.setMaximumWidth(440)
        self.ajustar_ancho_ficha(self.window().width())
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QFrame#fichaLateral {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_TARJETA}px;"
            f"}}"
        )

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(16, 16, 16, 16)
        layout_raiz.setSpacing(12)

        # -------------------------------------------------------------------
        # Contenedor con scroll para contenido extenso
        # -------------------------------------------------------------------
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("background: transparent;")
        self._scroll.viewport().installEventFilter(self)

        self._cuerpo = QWidget(self._scroll)
        self._cuerpo.setStyleSheet("background: transparent;")
        self._cuerpo.setMinimumWidth(0)
        self._cuerpo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._layout_cuerpo = QVBoxLayout(self._cuerpo)
        self._layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        self._layout_cuerpo.setSpacing(14)

        # 1. Cabecera (Avatar + Nombre + Subtítulo + Píldora de estado)
        self._contenedor_cabecera = QWidget(self._cuerpo)
        layout_cab = QVBoxLayout(self._contenedor_cabecera)
        layout_cab.setContentsMargins(0, 0, 0, 0)
        layout_cab.setSpacing(6)
        layout_cab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._avatar = Avatar(diametro=diametro_avatar, nombre="", con_anillo=True, parent=self._contenedor_cabecera)
        layout_cab.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        self._lbl_nombre = QLabel("Nombre de entidad", self._contenedor_cabecera)
        self._lbl_nombre.setObjectName("fichaLateralNombre")
        self._lbl_nombre.setMinimumWidth(0)
        self._lbl_nombre.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._lbl_nombre.setWordWrap(True)
        self._lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_nombre.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt; font-weight: bold; color: {TEXTO};")
        layout_cab.addWidget(self._lbl_nombre)

        self._lbl_subtitulo = QLabel("", self._contenedor_cabecera)
        self._lbl_subtitulo.setObjectName("fichaLateralSubtitulo")
        self._lbl_subtitulo.setMinimumWidth(0)
        self._lbl_subtitulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._lbl_subtitulo.setWordWrap(True)
        self._lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_subtitulo.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        layout_cab.addWidget(self._lbl_subtitulo)

        self._contenedor_pildoras = QWidget(self._contenedor_cabecera)
        self._layout_pildoras = QHBoxLayout(self._contenedor_pildoras)
        self._layout_pildoras.setContentsMargins(0, 4, 0, 0)
        self._layout_pildoras.setSpacing(6)
        self._layout_pildoras.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_cab.addWidget(self._contenedor_pildoras)

        self._layout_cuerpo.addWidget(self._contenedor_cabecera)

        # 2. Zona KPI (cuadrícula 2×2)
        self._contenedor_kpi = QWidget(self._cuerpo)
        self._layout_kpi = QGridLayout(self._contenedor_kpi)
        self._layout_kpi.setContentsMargins(0, 0, 0, 0)
        self._layout_kpi.setSpacing(8)
        self._posiciones_kpi: list[tuple[QWidget, int, int]] = []
        self._columnas_kpi = 0
        self._layout_cuerpo.addWidget(self._contenedor_kpi)

        # 3. Zona de Contenido libre (Gráficos, listas, notas)
        self._contenedor_contenido = QWidget(self._cuerpo)
        self._layout_contenido = QVBoxLayout(self._contenedor_contenido)
        self._layout_contenido.setContentsMargins(0, 0, 0, 0)
        self._layout_contenido.setSpacing(10)
        self._layout_cuerpo.addWidget(self._contenedor_contenido)

        self._layout_cuerpo.addStretch()
        self._scroll.setWidget(self._cuerpo)
        layout_raiz.addWidget(self._scroll)

        # 4. Zona de Acciones fijas al pie
        self._contenedor_acciones = QWidget(self)
        self._contenedor_acciones.installEventFilter(self)
        self._layout_acciones = QVBoxLayout(self._contenedor_acciones)
        self._layout_acciones.setContentsMargins(0, 6, 0, 0)
        self._layout_acciones.setSpacing(6)

        # Fila principal de botones (Editar / Estado / Eliminar)
        fila_btn_primarios = QGridLayout()
        fila_btn_primarios.setContentsMargins(0, 0, 0, 0)
        fila_btn_primarios.setHorizontalSpacing(6)
        fila_btn_primarios.setVerticalSpacing(6)
        self._layout_botones_primarios = fila_btn_primarios

        self.btn_editar = QPushButton("Editar", self._contenedor_acciones)
        self.btn_editar.setAccessibleName("Editar datos de la entidad seleccionada")
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.setStyleSheet(
            f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {estilo.SUPERFICIE_DESHABILITADA_SUAVE}; }}"
        )
        self.btn_editar.clicked.connect(self.editar_solicitado.emit)

        self.btn_estado = QPushButton("Desactivar", self._contenedor_acciones)
        self.btn_estado.setAccessibleName("Activar o desactivar entidad")
        self.btn_estado.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_estado.setStyleSheet(
            f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {estilo.SUPERFICIE_DESHABILITADA_SUAVE}; }}"
        )
        self.btn_estado.clicked.connect(self.cambiar_estado_solicitado.emit)

        self.btn_eliminar = QPushButton("Eliminar…", self._contenedor_acciones)
        self.btn_eliminar.setAccessibleName("Eliminar entidad permanentemente")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE_ERROR}; color: {ERROR}; font-weight: 600; "
            f"border: 1px solid {estilo.BORDE_ERROR_SUAVE}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {estilo.SUPERFICIE_DESHABILITADA_ERROR}; border-color: {ERROR}; }}"
        )
        self.btn_eliminar.clicked.connect(self.eliminar_solicitado.emit)

        self._layout_acciones.addLayout(fila_btn_primarios)

        # Botón secundario completo («Ver ficha completa»)
        self.btn_ver_completa = QPushButton("Ver ficha completa", self._contenedor_acciones)
        self.btn_ver_completa.setAccessibleName("Abrir diálogo con todos los datos y pestañas")
        self.btn_ver_completa.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_completa.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {PRIMARIO}; border-radius: {RADIO_BOTON}px; padding: 6px 6px; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self.btn_ver_completa.clicked.connect(self.ver_completa_solicitado.emit)
        self._layout_acciones.addWidget(self.btn_ver_completa)

        # Botón para navegar a catálogo de productos («Ver productos»)
        self.btn_ver_productos = QPushButton("Ver productos", self._contenedor_acciones)
        self.btn_ver_productos.setAccessibleName("Abrir catálogo de productos de esta entidad")
        self.btn_ver_productos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_productos.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; border-color: {PRIMARIO}; }}"
        )
        self.btn_ver_productos.clicked.connect(self.ver_productos_solicitado.emit)
        self._layout_acciones.addWidget(self.btn_ver_productos)
        self._botones_primarios = [self.btn_editar, self.btn_estado, self.btn_eliminar]
        self._columnas_acciones_primarias = 0
        self._ajustar_disposicion_acciones_primarias()

        layout_raiz.addWidget(self._contenedor_acciones)

        # -------------------------------------------------------------------
        # Estado Vacío inicial
        # -------------------------------------------------------------------
        self._lbl_vacio = QLabel("Selecciona un elemento para ver su detalle", self)
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_vacio.setWordWrap(True)
        self._lbl_vacio.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO}; padding: 32px;")
        layout_raiz.addWidget(self._lbl_vacio)

        self.mostrar_vacio()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._ajustar_ancho_cuerpo()
        self._ajustar_disposicion_acciones_primarias()
        if self.parent() is None and self.window() is not self:
            self.ajustar_ancho_ficha(self.window().width())

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        if watched is self._scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._ajustar_ancho_cuerpo()
        elif getattr(self, "_contenedor_acciones", None) is watched and event.type() == QEvent.Type.Resize:
            self._ajustar_disposicion_acciones_primarias()
        return super().eventFilter(watched, event)

    def _ajustar_ancho_cuerpo(self) -> None:
        ancho = self._scroll.viewport().width()
        if ancho > 0:
            self._cuerpo.setFixedWidth(ancho)
            if hasattr(self, "_layout_kpi"):
                self._ajustar_columnas_kpi(ancho)

    def _ajustar_columnas_kpi(self, ancho_disponible: int, forzar: bool = False) -> None:
        ancho_dos_columnas = self.ANCHO_MINIMO_KPI * 2 + self._layout_kpi.spacing()
        columnas = 2 if ancho_disponible >= ancho_dos_columnas else 1
        if columnas == self._columnas_kpi and not forzar:
            return

        posiciones = sorted(self._posiciones_kpi, key=lambda item: (item[1], item[2]))
        while self._layout_kpi.count():
            self._layout_kpi.takeAt(0)

        for indice, (widget, fila, columna) in enumerate(posiciones):
            if columnas == 1:
                self._layout_kpi.addWidget(widget, indice, 0)
            else:
                self._layout_kpi.addWidget(widget, fila, columna)

        self._layout_kpi.setColumnStretch(0, 1)
        self._layout_kpi.setColumnStretch(1, 1 if columnas == 2 else 0)
        self._columnas_kpi = columnas

    def _ajustar_disposicion_acciones_primarias(self) -> None:
        if not hasattr(self, "_botones_primarios"):
            return

        ancho_disponible = self._contenedor_acciones.contentsRect().width()
        ancho_dos_columnas = (
            self.btn_editar.sizeHint().width()
            + self.btn_estado.sizeHint().width()
            + self._layout_botones_primarios.horizontalSpacing()
        )
        columnas = 2 if ancho_disponible >= ancho_dos_columnas else 1
        if columnas == self._columnas_acciones_primarias:
            return

        while self._layout_botones_primarios.count():
            self._layout_botones_primarios.takeAt(0)

        if columnas == 1:
            for fila, boton in enumerate(self._botones_primarios):
                self._layout_botones_primarios.addWidget(boton, fila, 0)
        else:
            self._layout_botones_primarios.addWidget(self.btn_editar, 0, 0)
            self._layout_botones_primarios.addWidget(self.btn_estado, 0, 1)
            self._layout_botones_primarios.addWidget(self.btn_eliminar, 1, 0, 1, 2)

        self._layout_botones_primarios.setColumnStretch(0, 1)
        self._layout_botones_primarios.setColumnStretch(1, 1 if columnas == 2 else 0)
        self._columnas_acciones_primarias = columnas

    def ajustar_ancho_ficha(self, ancho_ventana: int) -> None:
        """Ajusta el ancho lateral a la ventana sin habilitar desplazamiento horizontal."""
        if ancho_ventana < 1240:
            ancho = 320
        elif ancho_ventana < 1500:
            ancho = 380
        else:
            ancho = 440
        self.setMinimumWidth(ancho)
        self.setMaximumWidth(ancho)
        self.resize(ancho, self.height())

    def _asegurar_texto_envuelve(self, widget: QWidget) -> None:
        for etiqueta in widget.findChildren(QLabel):
            etiqueta.setWordWrap(True)

    # -----------------------------------------------------------------------
    # Métodos de configuración y gestión de estados
    # -----------------------------------------------------------------------

    def mostrar_vacio(self, mensaje: str = "Selecciona un elemento para ver su detalle") -> None:
        """Oculta las secciones activas y muestra el mensaje neutro de selección."""
        self._scroll.setVisible(False)
        self._contenedor_acciones.setVisible(False)
        self._lbl_vacio.setText(mensaje)
        self._lbl_vacio.setVisible(True)

    def mostrar_contenido(self) -> None:
        """Activa las zonas de cabecera, KPI, contenido y acciones."""
        self._ajustar_ancho_cuerpo()
        self._lbl_vacio.setVisible(False)
        self._scroll.setVisible(True)
        self._contenedor_acciones.setVisible(True)

    def establecer_cabecera(
        self,
        nombre: str,
        subtitulo: str = "",
        iniciales: str = "",
        pildoras: list[tuple[str, str | None]] | None = None,
    ) -> None:
        """Configura el encabezado visual superior."""
        self.mostrar_contenido()
        self._lbl_nombre.setText(nombre)
        self._lbl_subtitulo.setText(subtitulo)
        self._lbl_subtitulo.setVisible(bool(subtitulo))
        self._lbl_nombre.updateGeometry()
        self._lbl_subtitulo.updateGeometry()

        # Recrear avatar
        self._avatar.establecer_nombre(nombre)

        # Limpiar y regenerar píldoras
        while self._layout_pildoras.count() > 0:
            item = self._layout_pildoras.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if pildoras:
            for texto_pildora, variante in pildoras:
                p = Pildora(texto=texto_pildora, variante=variante, parent=self._contenedor_pildoras)
                self._layout_pildoras.addWidget(p)

    def agregar_kpi(self, widget: QWidget, fila: int, columna: int) -> None:
        """Agrega un widget a la cuadrícula KPI."""
        self._posiciones_kpi.append((widget, fila, columna))
        self._ajustar_columnas_kpi(self._scroll.viewport().width(), forzar=True)

    def agregar_contenido(self, widget: QWidget) -> None:
        """Inserta un widget en la zona de contenido libre."""
        self._layout_contenido.addWidget(widget)
        self._asegurar_texto_envuelve(widget)

    def configurar_estado_activo(self, activo: bool) -> None:
        """Ajusta el texto y estilo del botón de activación/desactivación."""
        if activo:
            self.btn_estado.setText("Desactivar")
            self.btn_estado.setStyleSheet(
                f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
                f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
                f"QPushButton:hover {{ background-color: {estilo.SUPERFICIE_DESHABILITADA_SUAVE}; }}"
            )
        else:
            self.btn_estado.setText("Activar")
            self.btn_estado.setStyleSheet(
                f"QPushButton {{ background-color: {estilo.SUPERFICIE_EXITO}; color: {estilo.EXITO}; font-weight: 600; "
                f"border: 1px solid {estilo.EXITO_BORDE_SUAVE}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
                f"QPushButton:hover {{ background-color: {estilo.SUPERFICIE_EXITO_HOVER}; }}"
            )
