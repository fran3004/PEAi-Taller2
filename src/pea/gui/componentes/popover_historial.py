"""Popover flotante para visualización del historial de operaciones deshacibles.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 5.1 y 8, ADR-0013).
- Se abre al pulsar el botón/chevron de Deshacer en la barra superior.
- Muestra la lista de operaciones apiladas en orden cronológico inverso (la más reciente arriba).
- Permite ejecutar la última operación de deshacer (Ctrl+Z) o inspeccionar el historial.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.estilo import (
    COLOR_DTI,
    FICHA,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    RADIO_FICHA_KPI,
    TEXTO,
    TEXTO_SECUNDARIO,
)


class PopoverHistorial(QFrame):
    """Menú desplegable tipo popover que muestra la pila de deshacer institucional."""

    deshacer_solicitado = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("popoverHistorial")
        self.setFixedWidth(340)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QFrame#popoverHistorial {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_FICHA_KPI}px;"
            f"}}"
        )

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(24)
        sombra.setOffset(0, 6)
        sombra.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(sombra)

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(16, 14, 16, 14)
        layout_raiz.setSpacing(10)

        # 1. Cabecera
        fila_cabecera = QHBoxLayout()
        fila_cabecera.setContentsMargins(0, 0, 0, 0)
        fila_cabecera.setSpacing(8)

        lbl_tit = QLabel("Historial de operaciones", self)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};")
        fila_cabecera.addWidget(lbl_tit)
        fila_cabecera.addStretch()

        self._lbl_contador = QLabel("0 ops", self)
        self._lbl_contador.setStyleSheet(
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {TEXTO_SECUNDARIO}; "
            f"background-color: {FICHA}; border-radius: 4px; padding: 2px 6px;"
        )
        fila_cabecera.addWidget(self._lbl_contador)
        layout_raiz.addLayout(fila_cabecera)

        # 2. Lista de operaciones con scroll
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setMaximumHeight(260)
        self._scroll.setStyleSheet("background: transparent;")

        self._cuerpo_lista = QWidget(self._scroll)
        self._cuerpo_lista.setStyleSheet("background: transparent;")
        self._layout_lista = QVBoxLayout(self._cuerpo_lista)
        self._layout_lista.setContentsMargins(0, 0, 0, 0)
        self._layout_lista.setSpacing(6)

        self._scroll.setWidget(self._cuerpo_lista)
        layout_raiz.addWidget(self._scroll)

        # Estado vacío
        self._lbl_vacio = QLabel("No hay operaciones para deshacer", self)
        self._lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_vacio.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; padding: 18px 0;")
        layout_raiz.addWidget(self._lbl_vacio)

        # 3. Pie con acción principal
        self.btn_deshacer = QPushButton("Deshacer última (Ctrl+Z)", self)
        self.btn_deshacer.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_deshacer.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: {estilo.SUPERFICIE}; font-weight: 600; "
            f"border: none; border-radius: {RADIO_BOTON}px; padding: 7px 12px; font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {FICHA}; color: {TEXTO_SECUNDARIO}; }}"
        )
        self.btn_deshacer.clicked.connect(self._al_pulsar_deshacer)
        layout_raiz.addWidget(self.btn_deshacer)

    def actualizar_operaciones(self, operaciones: list[str]) -> None:
        """Actualiza la lista de operaciones apiladas (la más reciente primero)."""
        # Limpiar lista anterior
        while self._layout_lista.count() > 0:
            item = self._layout_lista.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        total = len(operaciones)
        self._lbl_contador.setText(f"{total} ops")

        if total == 0:
            self._scroll.setVisible(False)
            self._lbl_vacio.setVisible(True)
            self.btn_deshacer.setEnabled(False)
            return

        self._lbl_vacio.setVisible(False)
        self._scroll.setVisible(True)
        self.btn_deshacer.setEnabled(True)

        for idx, op_texto in enumerate(operaciones):
            fila_w = QWidget(self._cuerpo_lista)
            fondo_fila = estilo.SUPERFICIE_ALTERNADA if idx == 0 else estilo.SUPERFICIE
            fila_w.setStyleSheet(
                f"QWidget {{ background-color: {fondo_fila}; "
                f"border: 1px solid {LINEA}; border-radius: 6px; padding: 4px; }}"
            )
            layout_f = QHBoxLayout(fila_w)
            layout_f.setContentsMargins(6, 4, 6, 4)
            layout_f.setSpacing(8)

            punto = QFrame(fila_w)
            punto.setFixedSize(6, 6)
            color_punto = COLOR_DTI if idx == 0 else TEXTO_SECUNDARIO
            punto.setStyleSheet(f"background-color: {color_punto}; border-radius: 3px;")
            layout_f.addWidget(punto)

            lbl_txt = QLabel(op_texto, fila_w)
            lbl_txt.setStyleSheet(
                f"font-size: {estilo.TAMANO_AUXILIAR}pt; {'font-weight: bold; ' if idx == 0 else ''}color: {TEXTO};"
            )
            lbl_txt.setWordWrap(True)
            layout_f.addWidget(lbl_txt)

            self._layout_lista.addWidget(fila_w)

        self._layout_lista.addStretch()

    def mostrar_bajo(self, widget: QWidget) -> None:
        """Ubica y muestra el popover directamente debajo del widget objetivo."""
        pos_global = widget.mapToGlobal(QPoint(0, widget.height() + 4))
        self.move(pos_global)
        self.show()

    def _al_pulsar_deshacer(self) -> None:
        self.deshacer_solicitado.emit()
        self.close()
