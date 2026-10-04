"""Componentes de estado vacío informativo y de esqueleto de carga (skeleton placeholder)."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.animacion import animaciones_habilitadas
from pea.gui.estilo import (
    FICHA,
    LINEA_FUERTE,
    RADIO_CAMPO,
    SUPERFICIE,
    TAMANO_CUERPO,
    TAMANO_TITULO_PANTALLA,
    TEXTO,
    TEXTO_SECUNDARIO,
)


class EstadoVacio(QFrame):
    """Presentación centrada cuando una vista no contiene datos o no tiene conexión."""

    accion_principal_pulsada = Signal()
    accion_secundaria_pulsada = Signal()

    def __init__(
        self,
        titulo: str = "Sin datos en esta ventana",
        mensaje: str = "No hay registros disponibles para los filtros seleccionados.",
        texto_principal: str | None = None,
        texto_secundario: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("estadoVacio")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QFrame#estadoVacio {{"
            f"  background-color: {SUPERFICIE};"
            f"  border: 1px dashed {LINEA_FUERTE};"
            f"  border-radius: 16px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(32, 40, 32, 40)
        layout.setSpacing(12)

        # Icono o glifo ilustrativo
        self.lbl_icono = QLabel("ⓘ", self)
        self.lbl_icono.setObjectName("estadoVacioIcono")
        self.lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icono.setStyleSheet(
            f"font-size: 32pt; color: {TEXTO_SECUNDARIO}; background: transparent;"
        )
        layout.addWidget(self.lbl_icono)

        # Título
        self.lbl_titulo = QLabel(titulo, self)
        self.lbl_titulo.setObjectName("estadoVacioTitulo")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet(
            f"font-size: {TAMANO_TITULO_PANTALLA}pt; font-weight: bold; color: {TEXTO};"
        )
        layout.addWidget(self.lbl_titulo)

        # Mensaje
        self.lbl_mensaje = QLabel(mensaje, self)
        self.lbl_mensaje.setObjectName("estadoVacioMensaje")
        self.lbl_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setStyleSheet(
            f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};"
        )
        layout.addWidget(self.lbl_mensaje)

        # Fila de botones de acción
        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)
        fila_botones.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_principal = QPushButton("", self)
        self.btn_principal.setObjectName("primario")
        self.btn_principal.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_principal.clicked.connect(self.accion_principal_pulsada)
        fila_botones.addWidget(self.btn_principal)

        self.btn_secundario = QPushButton("", self)
        self.btn_secundario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_secundario.clicked.connect(self.accion_secundaria_pulsada)
        fila_botones.addWidget(self.btn_secundario)

        layout.addSpacing(8)
        layout.addLayout(fila_botones)

        self.configurar(titulo, mensaje, texto_principal, texto_secundario)

    def configurar(
        self,
        titulo: str,
        mensaje: str,
        texto_principal: str | None = None,
        texto_secundario: str | None = None,
    ) -> None:
        """Actualiza textos y visibilidad de los botones."""
        self.lbl_titulo.setText(titulo)
        self.lbl_mensaje.setText(mensaje)

        if texto_principal:
            self.btn_principal.setText(texto_principal)
            self.btn_principal.setVisible(True)
        else:
            self.btn_principal.setVisible(False)

        if texto_secundario:
            self.btn_secundario.setText(texto_secundario)
            self.btn_secundario.setVisible(True)
        else:
            self.btn_secundario.setVisible(False)

        self.setAccessibleName(f"Estado vacío: {titulo}. {mensaje}")


class Esqueleto(QWidget):
    """Marcador de posición con bloques grises animados (shimmer) durante cargas."""

    def __init__(
        self,
        filas: int = 4,
        altura_fila: int = 24,
        espaciado: int = 12,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("esqueleto")
        self.setAccessibleName("Cargando contenido...")
        self._filas = filas
        self._altura_fila = altura_fila
        self._espaciado = espaciado

        self._opacidad: float = 0.55
        self._incrementando: bool = True

        self._timer: QTimer | None = None
        if animaciones_habilitadas():
            self._timer = QTimer(self)
            self._timer.setInterval(40)
            self._timer.timeout.connect(self._actualizar_pulso)
            self._timer.start()

    def sizeHint(self) -> QSize:
        alto = 8 + self._filas * self._altura_fila + (self._filas - 1) * self._espaciado
        return QSize(200, alto)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def _actualizar_pulso(self) -> None:
        if self._incrementando:
            self._opacidad += 0.025
            if self._opacidad >= 0.85:
                self._incrementando = False
        else:
            self._opacidad -= 0.025
            if self._opacidad <= 0.40:
                self._incrementando = True
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color_base = QColor(FICHA)
        color_base.setAlphaF(self._opacidad)
        painter.setBrush(QBrush(color_base))
        painter.setPen(Qt.PenStyle.NoPen)

        w = float(self.width() - 8)
        y = 4.0

        for i in range(self._filas):
            # Anchos variables para simular líneas naturales de texto
            factor_ancho = 1.0 if i == 0 else (0.85 if i % 2 == 1 else 0.65)
            ancho_bloque = w * factor_ancho
            rect = QRectF(4.0, y, ancho_bloque, float(self._altura_fila))
            painter.drawRoundedRect(rect, RADIO_CAMPO, RADIO_CAMPO)
            y += float(self._altura_fila + self._espaciado)

        painter.end()


__all__ = ["Esqueleto", "EstadoVacio"]
