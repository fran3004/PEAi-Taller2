"""Selector segmentado con pastillas excluyentes para cambios de ámbito o modo."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from pea.gui import estilo
from pea.gui.estilo import (
    FICHA,
    LINEA,
    PRIMARIO,
    RADIO_BOTON,
    SUPERFICIE,
    TAMANO_CUERPO,
    TEXTO_SECUNDARIO,
)


class SelectorSegmentado(QFrame):
    """Control de selección entre pastillas continuas excluyentes."""

    opcion_cambiada = Signal(str)  # Emite la clave de la opción elegida

    def __init__(
        self,
        opciones: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("selectorSegmentado")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QFrame#selectorSegmentado {{"
            f"  background-color: {FICHA};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON + 2}px;"
            f"}}"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(3, 3, 3, 3)
        self._layout.setSpacing(2)

        self._grupo_botones = QButtonGroup(self)
        self._grupo_botones.setExclusive(True)
        self._botones: dict[str, QPushButton] = {}
        self._clave_activa: str = ""

        if opciones:
            for clave, etiqueta in opciones:
                self.agregar_opcion(clave, etiqueta)
            if opciones:
                self.seleccionar(opciones[0][0])

    def agregar_opcion(self, clave: str, etiqueta: str) -> None:
        """Añade una opción con su clave identificadora y texto legible."""
        btn = QPushButton(etiqueta, self)
        btn.setObjectName(f"segmento_{clave}")
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {TEXTO_SECUNDARIO};"
            f"  border: none;"
            f"  border-radius: {RADIO_BOTON}px;"
            f"  padding: 6px 18px;"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"  font-weight: 500;"
            f"}}"
            f"QPushButton:hover:!checked {{"
            f"  background-color: {estilo.SUPERPOSICION_CLARA_45};"
            f"  color: {PRIMARIO};"
            f"}}"
            f"QPushButton:checked {{"
            f"  background-color: {SUPERFICIE};"
            f"  color: {PRIMARIO};"
            f"  font-weight: bold;"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"}}"
        )

        btn.clicked.connect(lambda: self._al_pulsar_boton(clave))

        self._botones[clave] = btn
        self._grupo_botones.addButton(btn)
        self._layout.addWidget(btn)

        if not self._clave_activa:
            self.seleccionar(clave)

    def seleccionar(self, clave: str, emitir_senal: bool = True) -> None:
        """Selecciona el segmento correspondiente a la clave y emite señal si cambió."""
        if clave not in self._botones:
            return
        cambio = self._clave_activa != clave
        self._clave_activa = clave
        self._botones[clave].setChecked(True)
        self._actualizar_accesibilidad()
        if emitir_senal and cambio:
            self.opcion_cambiada.emit(clave)

    def clave_seleccionada(self) -> str:
        """Devuelve la clave de la opción actualmente activa."""
        return self._clave_activa

    def texto_seleccionado(self) -> str:
        """Devuelve el texto de la opción activa."""
        if self._clave_activa in self._botones:
            return self._botones[self._clave_activa].text()
        return ""

    def _al_pulsar_boton(self, clave: str) -> None:
        self._clave_activa = clave
        self._actualizar_accesibilidad()
        self.opcion_cambiada.emit(clave)

    def _actualizar_accesibilidad(self) -> None:
        self.setAccessibleName(f"Selector segmentado: {self.texto_seleccionado()}")
