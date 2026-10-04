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

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

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

    editar_solicitado = Signal()
    cambiar_estado_solicitado = Signal()
    eliminar_solicitado = Signal()
    ver_completa_solicitado = Signal()
    accion_extra_solicitada = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fichaLateral")
        self.setFixedWidth(360)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QFrame#fichaLateral {{"
            f"  background-color: #FFFFFF;"
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

        self._cuerpo = QWidget(self._scroll)
        self._cuerpo.setStyleSheet("background: transparent;")
        self._layout_cuerpo = QVBoxLayout(self._cuerpo)
        self._layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        self._layout_cuerpo.setSpacing(14)

        # 1. Cabecera (Avatar + Nombre + Subtítulo + Píldora de estado)
        self._contenedor_cabecera = QWidget(self._cuerpo)
        layout_cab = QVBoxLayout(self._contenedor_cabecera)
        layout_cab.setContentsMargins(0, 0, 0, 0)
        layout_cab.setSpacing(6)
        layout_cab.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._avatar = Avatar(diametro=80, nombre="", con_anillo=True, parent=self._contenedor_cabecera)
        layout_cab.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        self._lbl_nombre = QLabel("Nombre de entidad", self._contenedor_cabecera)
        self._lbl_nombre.setObjectName("fichaLateralNombre")
        self._lbl_nombre.setWordWrap(True)
        self._lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_nombre.setStyleSheet(f"font-size: 15pt; font-weight: bold; color: {TEXTO};")
        layout_cab.addWidget(self._lbl_nombre)

        self._lbl_subtitulo = QLabel("", self._contenedor_cabecera)
        self._lbl_subtitulo.setObjectName("fichaLateralSubtitulo")
        self._lbl_subtitulo.setWordWrap(True)
        self._lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_subtitulo.setStyleSheet(f"font-size: 11pt; color: {TEXTO_SECUNDARIO};")
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
        self._layout_acciones = QVBoxLayout(self._contenedor_acciones)
        self._layout_acciones.setContentsMargins(0, 6, 0, 0)
        self._layout_acciones.setSpacing(6)

        # Fila principal de botones (Editar / Estado / Eliminar)
        fila_btn_primarios = QHBoxLayout()
        fila_btn_primarios.setSpacing(6)

        self.btn_editar = QPushButton("Editar", self._contenedor_acciones)
        self.btn_editar.setAccessibleName("Editar datos de la entidad seleccionada")
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.setStyleSheet(
            f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: #DDE5F0; }}"
        )
        self.btn_editar.clicked.connect(self.editar_solicitado.emit)
        fila_btn_primarios.addWidget(self.btn_editar)

        self.btn_estado = QPushButton("Desactivar", self._contenedor_acciones)
        self.btn_estado.setAccessibleName("Activar o desactivar entidad")
        self.btn_estado.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_estado.setStyleSheet(
            f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: #DDE5F0; }}"
        )
        self.btn_estado.clicked.connect(self.cambiar_estado_solicitado.emit)
        fila_btn_primarios.addWidget(self.btn_estado)

        self.btn_eliminar = QPushButton("Eliminar…", self._contenedor_acciones)
        self.btn_eliminar.setAccessibleName("Eliminar entidad permanentemente")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setStyleSheet(
            f"QPushButton {{ background-color: #FFF0F0; color: {ERROR}; font-weight: 600; "
            f"border: 1px solid #F5C6C6; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: #FDE8E8; border-color: {ERROR}; }}"
        )
        self.btn_eliminar.clicked.connect(self.eliminar_solicitado.emit)
        fila_btn_primarios.addWidget(self.btn_eliminar)

        self._layout_acciones.addLayout(fila_btn_primarios)

        # Botón secundario completo («Ver ficha completa»)
        self.btn_ver_completa = QPushButton("Ver ficha completa", self._contenedor_acciones)
        self.btn_ver_completa.setAccessibleName("Abrir diálogo con todos los datos y pestañas")
        self.btn_ver_completa.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_completa.setStyleSheet(
            f"QPushButton {{ background-color: #FFFFFF; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {PRIMARIO}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
            f"QPushButton:hover {{ background-color: #F1F5F9; }}"
        )
        self.btn_ver_completa.clicked.connect(self.ver_completa_solicitado.emit)
        self._layout_acciones.addWidget(self.btn_ver_completa)

        layout_raiz.addWidget(self._contenedor_acciones)

        # -------------------------------------------------------------------
        # Estado Vacío inicial
        # -------------------------------------------------------------------
        self._lbl_vacio = QLabel("Selecciona un elemento para ver su detalle", self)
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_vacio.setWordWrap(True)
        self._lbl_vacio.setStyleSheet(f"font-size: 11pt; color: {TEXTO_SECUNDARIO}; padding: 32px;")
        layout_raiz.addWidget(self._lbl_vacio)

        self.mostrar_vacio()

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

        # Recrear avatar
        self._avatar.establecer_nombre(nombre)

        # Limpiar y regenerar píldoras
        while self._layout_pildoras.count() > 0:
            item = self._layout_pildoras.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if pildoras:
            for texto_pildora, variante in pildoras:
                p = Pildora(texto=texto_pildora, variante=variante, parent=self._contenedor_pildoras)
                self._layout_pildoras.addWidget(p)

    def limpiar_kpis(self) -> None:
        """Limpia los widgets de la cuadrícula KPI."""
        while self._layout_kpi.count() > 0:
            item = self._layout_kpi.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def agregar_kpi(self, widget: QWidget, fila: int, columna: int) -> None:
        """Agrega un widget a la cuadrícula KPI."""
        self._layout_kpi.addWidget(widget, fila, columna)

    def limpiar_contenido(self) -> None:
        """Limpia los widgets de la zona de contenido libre."""
        while self._layout_contenido.count() > 0:
            item = self._layout_contenido.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def agregar_contenido(self, widget: QWidget) -> None:
        """Inserta un widget en la zona de contenido libre."""
        self._layout_contenido.addWidget(widget)

    def configurar_estado_activo(self, activo: bool) -> None:
        """Ajusta el texto y estilo del botón de activación/desactivación."""
        if activo:
            self.btn_estado.setText("Desactivar")
            self.btn_estado.setStyleSheet(
                f"QPushButton {{ background-color: {FICHA}; color: {TEXTO}; font-weight: 600; "
                f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
                f"QPushButton:hover {{ background-color: #DDE5F0; }}"
            )
        else:
            self.btn_estado.setText("Activar")
            self.btn_estado.setStyleSheet(
                f"QPushButton {{ background-color: #E6F4EC; color: #1B6E3F; font-weight: 600; "
                f"border: 1px solid #B8E2CB; border-radius: {RADIO_BOTON}px; padding: 6px 12px; }}"
                f"QPushButton:hover {{ background-color: #D7EFE0; }}"
            )

