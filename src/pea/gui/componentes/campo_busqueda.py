"""Campo de búsqueda con icono de lupa, botón de limpieza y retardo de emisión (debounce)."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLineEdit, QWidget

from pea.gui.estilo import ACENTO, LINEA_FUERTE, RADIO_CAMPO, SUPERFICIE, TAMANO_CUERPO, TEXTO
from pea.gui.recursos import cargar_icono


class CampoBusqueda(QLineEdit):
    """Campo de texto con lupa, limpieza instantánea y señal con retardo de 250 ms."""

    texto_cambiado = Signal(str)      # Emite texto tras 250 ms de inactividad
    busqueda_ejecutada = Signal(str)  # Emite texto inmediatamente al presionar Enter

    def __init__(
        self,
        placeholder: str = "Buscar...",
        retardo_ms: int = 250,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("campoBusqueda")
        self.setPlaceholderText(placeholder)
        self.setAccessibleName("Campo de búsqueda")

        self.setStyleSheet(
            f"QLineEdit#campoBusqueda {{"
            f"  background-color: {SUPERFICIE};"
            f"  color: {TEXTO};"
            f"  border: 1px solid {LINEA_FUERTE};"
            f"  border-radius: {RADIO_CAMPO}px;"
            f"  padding: 6px 32px 6px 32px;"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"}}"
            f"QLineEdit#campoBusqueda:focus {{"
            f"  border: 2px solid {ACENTO};"
            f"  padding: 5px 31px 5px 31px;"
            f"}}"
        )

        # Icono de lupa en la posición izquierda (leading)
        try:
            icono_buscar = cargar_icono("buscar", 16)
        except Exception:
            icono_buscar = QIcon()
        self.accion_buscar = self.addAction(icono_buscar, QLineEdit.ActionPosition.LeadingPosition)

        # Botón/acción de limpiar a la derecha (trailing)
        try:
            icono_limpiar = cargar_icono("limpiar", 16)
        except Exception:
            icono_limpiar = QIcon()
        self.accion_limpiar = self.addAction(icono_limpiar, QLineEdit.ActionPosition.TrailingPosition)
        self.accion_limpiar.setVisible(False)
        self.accion_limpiar.triggered.connect(self.limpiar)

        # Temporizador de debounce
        self._retardo_ms = retardo_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(retardo_ms)
        self._timer.timeout.connect(self._emitir_texto_debounced)

        self.textChanged.connect(self._al_cambiar_texto)
        self.returnPressed.connect(self._al_presionar_enter)

    def _al_cambiar_texto(self, texto: str) -> None:
        self.accion_limpiar.setVisible(bool(texto))
        self._timer.start()

    def _emitir_texto_debounced(self) -> None:
        self.texto_cambiado.emit(self.text().strip())

    def _al_presionar_enter(self) -> None:
        self._timer.stop()
        self.busqueda_ejecutada.emit(self.text().strip())
        self.texto_cambiado.emit(self.text().strip())

    def limpiar(self) -> None:
        """Limpia el contenido del campo y emite texto vacío inmediatamente."""
        self._timer.stop()
        self.clear()
        self.accion_limpiar.setVisible(False)
        self.texto_cambiado.emit("")
