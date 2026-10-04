"""Contenedor de tarjeta estilizada con barra de acento y zona de acciones."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from pea.gui.estilo import (
    COLOR_DTI,
    RELLENO_TARJETA,
    SEPARACION_TARJETAS,
    SOMBRA_TARJETA_COLOR,
    SOMBRA_TARJETA_DESENFOQUE,
    SOMBRA_TARJETA_DESPLAZAMIENTO,
    SOMBRA_TARJETA_OPACIDAD,
    TAMANO_TITULO_TARJETA,
    TEXTO,
)


class Tarjeta(QFrame):
    """Tarjeta de contenido institucional con sombra suave, encabezado y barra de acento."""

    def __init__(
        self,
        titulo: str | None = None,
        con_sombra: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._titulo = titulo
        self._layout_principal = QVBoxLayout(self)
        self._layout_principal.setContentsMargins(
            RELLENO_TARJETA, RELLENO_TARJETA, RELLENO_TARJETA, RELLENO_TARJETA
        )
        self._layout_principal.setSpacing(SEPARACION_TARJETAS)

        # Contenedor de encabezado (barra acento + título + acciones)
        self._cabecera = QWidget(self)
        self._layout_cabecera = QHBoxLayout(self._cabecera)
        self._layout_cabecera.setContentsMargins(0, 0, 0, 0)
        self._layout_cabecera.setSpacing(10)

        # Barra vertical de acento de 3 px
        self._barra_acento = QFrame(self._cabecera)
        self._barra_acento.setObjectName("tarjetaBarraAcento")
        self._barra_acento.setFixedWidth(3)
        self._barra_acento.setFixedHeight(20)
        self._barra_acento.setStyleSheet(f"background-color: {COLOR_DTI}; border-radius: 1px;")
        self._layout_cabecera.addWidget(self._barra_acento)

        # Etiqueta de título
        self._lbl_titulo = QLabel(titulo or "", self._cabecera)
        self._lbl_titulo.setObjectName("tarjetaTitulo")
        self._lbl_titulo.setStyleSheet(
            f"font-size: {TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {TEXTO};"
        )
        self._layout_cabecera.addWidget(self._lbl_titulo)

        self._layout_cabecera.addStretch()

        # Layout horizontal para botones de acción a la derecha
        self._layout_acciones = QHBoxLayout()
        self._layout_acciones.setContentsMargins(0, 0, 0, 0)
        self._layout_acciones.setSpacing(8)
        self._layout_cabecera.addLayout(self._layout_acciones)

        self._layout_principal.addWidget(self._cabecera)

        # Si no hay título inicialmente, ocultar encabezado
        if not titulo:
            self._cabecera.setVisible(False)

        # Layout de contenido principal de la tarjeta
        self._layout_contenido = QVBoxLayout()
        self._layout_contenido.setContentsMargins(0, 0, 0, 0)
        self._layout_contenido.setSpacing(10)
        self._layout_principal.addLayout(self._layout_contenido)

        if con_sombra:
            sombra = QGraphicsDropShadowEffect(self)
            sombra.setBlurRadius(SOMBRA_TARJETA_DESENFOQUE)
            sombra.setOffset(*SOMBRA_TARJETA_DESPLAZAMIENTO)
            color_sombra = QColor(SOMBRA_TARJETA_COLOR)
            color_sombra.setAlphaF(SOMBRA_TARJETA_OPACIDAD)
            sombra.setColor(color_sombra)
            self.setGraphicsEffect(sombra)

        self._actualizar_accesibilidad()

    @property
    def layout_contenido(self) -> QVBoxLayout:
        """Devuelve el layout donde se insertan los controles del cuerpo de la tarjeta."""
        return self._layout_contenido

    def agregar_widget(self, widget: QWidget) -> None:
        """Agrega un widget al cuerpo de la tarjeta."""
        self._layout_contenido.addWidget(widget)

    def agregar_accion(self, widget: QWidget) -> None:
        """Agrega un botón u opción en la zona de acciones a la derecha del título."""
        self._cabecera.setVisible(True)
        self._layout_acciones.addWidget(widget)

    def establecer_titulo(self, titulo: str | None) -> None:
        """Configura o actualiza el título superior de la tarjeta."""
        self._titulo = titulo
        if titulo:
            self._lbl_titulo.setText(titulo)
            self._cabecera.setVisible(True)
        else:
            self._lbl_titulo.setText("")
            if self._layout_acciones.count() == 0:
                self._cabecera.setVisible(False)
        self._actualizar_accesibilidad()

    def _actualizar_accesibilidad(self) -> None:
        nombre = f"Tarjeta {self._titulo}" if self._titulo else "Tarjeta de contenido"
        self.setAccessibleName(nombre)
