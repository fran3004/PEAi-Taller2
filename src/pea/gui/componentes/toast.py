"""Sistema de avisos flotantes (toasts) apilables y efímeros."""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.animacion import animar_desvanecimiento
from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    ERROR,
    ERROR_FONDO,
    EXITO,
    EXITO_FONDO,
    INFO,
    INFO_FONDO,
    RADIO_FICHA_KPI,
    SOMBRA_TARJETA_COLOR,
    SOMBRA_TARJETA_DESENFOQUE,
    SOMBRA_TARJETA_DESPLAZAMIENTO,
    SOMBRA_TARJETA_OPACIDAD,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TEXTO,
)

ANCHO_TOAST: Final[int] = 320
DURACION_TOAST_DEFECTO_MS: Final[int] = 4000


class Toast(QFrame):
    """Notificación flotante individual con color semántico, ícono y cierre automático."""

    descartado = Signal(object)  # Emite self al cerrarse

    def __init__(
        self,
        mensaje: str,
        titulo: str = "",
        tipo: str = "exito",
        duracion_ms: int = DURACION_TOAST_DEFECTO_MS,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setFixedWidth(ANCHO_TOAST)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._tipo = tipo.lower()
        self._mensaje = mensaje
        self._titulo = titulo

        fondo, color_borde, icono = self._obtener_estilo_tipo(self._tipo)

        self.setStyleSheet(
            f"QFrame#toast {{"
            f"  background-color: {fondo};"
            f"  border: 1px solid {color_borde};"
            f"  border-radius: {RADIO_FICHA_KPI}px;"
            f"}}"
        )

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(SOMBRA_TARJETA_DESENFOQUE)
        sombra.setOffset(*SOMBRA_TARJETA_DESPLAZAMIENTO)
        c_sombra = QColor(SOMBRA_TARJETA_COLOR)
        c_sombra.setAlphaF(SOMBRA_TARJETA_OPACIDAD * 1.5)
        sombra.setColor(c_sombra)
        self.setGraphicsEffect(sombra)

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(14, 12, 12, 12)
        layout_principal.setSpacing(10)

        # Icono visual a la izquierda
        lbl_icono = QLabel(icono, self)
        lbl_icono.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; color: {color_borde}; font-weight: bold;")
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_principal.addWidget(lbl_icono)

        # Contenedor de textos (título y mensaje)
        layout_textos = QVBoxLayout()
        layout_textos.setContentsMargins(0, 0, 0, 0)
        layout_textos.setSpacing(2)

        if titulo:
            lbl_tit = QLabel(titulo, self)
            lbl_tit.setStyleSheet(
                f"font-size: {TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};"
            )
            layout_textos.addWidget(lbl_tit)

        lbl_msg = QLabel(mensaje, self)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO};"
        )
        layout_textos.addWidget(lbl_msg)
        layout_principal.addLayout(layout_textos, stretch=1)

        # Botón cerrar "×"
        btn_cerrar = QPushButton("×", self)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setStyleSheet(
            f"QPushButton {{"
            f"  border: none; background: transparent; color: {color_borde};"
            f"  font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; padding: 0px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {estilo.SUPERPOSICION_NEGRA_8}; border-radius: {estilo.RADIO_BOTON}px;"
            f"}}"
        )
        btn_cerrar.clicked.connect(self.cerrar)
        layout_principal.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignTop)

        self.setAccessibleName(f"Aviso {tipo}: {titulo} - {mensaje}")

        # Temporizador de auto-cierre
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(duracion_ms)
        self._timer.timeout.connect(self.cerrar)
        self._timer.start()

        # Animación inicial suave
        animar_desvanecimiento(self, inicio=0.0, fin=1.0, duracion_ms=180)

    def _obtener_estilo_tipo(self, tipo: str) -> tuple[str, str, str]:
        if tipo == "exito":
            return (EXITO_FONDO, EXITO, "✓")
        if tipo == "aviso":
            return (AVISO_FONDO, AVISO, "▲")
        if tipo == "error":
            return (ERROR_FONDO, ERROR, "X")
        return (INFO_FONDO, INFO, "ℹ")

    def enterEvent(self, event: QEvent) -> None:
        """Pausa el temporizador mientras el usuario pasa el ratón por encima."""
        super().enterEvent(event)
        self._timer.stop()

    def leaveEvent(self, event: QEvent) -> None:
        """Reanuda el temporizador cuando el cursor sale del toast."""
        super().leaveEvent(event)
        self._timer.start()

    def cerrar(self) -> None:
        """Cierra el toast y emite la señal de descarte."""
        self._timer.stop()
        self.descartado.emit(self)
        self.deleteLater()


class GestorAvisos(QObject):
    """Administra y posiciona toasts apilables en la esquina inferior derecha de la ventana."""

    def __init__(self, ventana_padre: QWidget) -> None:
        self._ventana: QWidget = ventana_padre
        self._toasts: list[Toast] = []
        super().__init__(ventana_padre)
        self._ventana.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        ventana = getattr(self, "_ventana", None)
        if ventana is not None and watched == ventana and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            self._reubicar_toasts()
        return super().eventFilter(watched, event)

    def mostrar_exito(self, mensaje: str, titulo: str = "Éxito", duracion_ms: int = 4000) -> Toast:
        return self._crear_y_mostrar(mensaje, titulo, "exito", duracion_ms)

    def mostrar_aviso(self, mensaje: str, titulo: str = "Advertencia", duracion_ms: int = 4000) -> Toast:
        return self._crear_y_mostrar(mensaje, titulo, "aviso", duracion_ms)

    def mostrar_error(self, mensaje: str, titulo: str = "Error", duracion_ms: int = 5000) -> Toast:
        return self._crear_y_mostrar(mensaje, titulo, "error", duracion_ms)

    def mostrar_info(self, mensaje: str, titulo: str = "Información", duracion_ms: int = 4000) -> Toast:
        return self._crear_y_mostrar(mensaje, titulo, "info", duracion_ms)

    def _crear_y_mostrar(self, mensaje: str, titulo: str, tipo: str, duracion_ms: int) -> Toast:
        toast = Toast(mensaje, titulo=titulo, tipo=tipo, duracion_ms=duracion_ms, parent=self._ventana)
        toast.descartado.connect(self._al_descartar_toast)
        self._toasts.append(toast)
        toast.show()
        self._reubicar_toasts()
        return toast

    def _al_descartar_toast(self, toast: Toast) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
            self._reubicar_toasts()

    def _reubicar_toasts(self) -> None:
        if not self._toasts:
            return

        margen_derecho = 24
        margen_inferior = 76  # Espacio superior al pie institucional
        espaciado = 10

        ancho_padre = self._ventana.width()
        alto_padre = self._ventana.height()

        y_actual = alto_padre - margen_inferior

        # Apilar de abajo hacia arriba (el más nuevo abajo)
        for toast in reversed(self._toasts):
            toast.adjustSize()
            h = toast.height()
            x = ancho_padre - ANCHO_TOAST - margen_derecho
            y = y_actual - h
            toast.move(x, y)
            toast.raise_()
            y_actual = y - espaciado

    def limpiar_todos(self) -> None:
        """Cierra todos los avisos activos."""
        for t in list(self._toasts):
            t.cerrar()
        self._toasts.clear()


__all__ = ["GestorAvisos", "Toast"]
