"""Clase base para componentes de visualización gráfica nativa con QPainter.

Proporciona exportación a PNG en alta resolución (doble resolución),
dibujo accesible de estado vacío, tooltip oscuro institucional y
control de animación de entrada según PEA_SIN_ANIMACIONES.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from pea.gui import estilo
from pea.gui.componentes.animacion import animaciones_habilitadas
from pea.gui.estilo import (
    ENCABEZADO_INICIO,
    LINEA,
    LINEA_FUERTE,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
    TEXTO_SOBRE_OSCURO_SUAVE,
)


class GraficoBase(QWidget):
    """Componente base de graficación nativa para PEA-i."""

    def __init__(
        self,
        titulo: str = "",
        subtitulo: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.titulo = titulo
        self.subtitulo = subtitulo
        self._progreso_animacion: float = 1.0
        self._animacion: QVariantAnimation | None = None
        self._pos_cursor: QPointF | None = None
        self._tooltip_visible: bool = False

        self.setMouseTracking(True)
        self.setMinimumSize(QSize(0, 0))
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

    def esta_vacio(self) -> bool:
        """Indica si el gráfico no contiene datos para renderizar."""
        return True

    def _iniciar_animacion(self, duracion_ms: int = 400) -> None:
        """Inicia la animación de entrada si las animaciones están habilitadas."""
        if not animaciones_habilitadas() or duracion_ms <= 0:
            self._progreso_animacion = 1.0
            self.update()
            return

        if self._animacion is not None:
            self._animacion.stop()

        self._progreso_animacion = 0.0
        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duracion_ms)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _actualizar(val: object) -> None:
            self._progreso_animacion = float(val)  # type: ignore[arg-type]
            self.update()

        anim.valueChanged.connect(_actualizar)
        self._animacion = anim
        anim.start()

    def exportar_png(
        self,
        ruta: Path | str,
        ancho: int = 800,
        alto: int = 500,
        escala: float = 2.0,
    ) -> bool:
        """Renderiza el gráfico a un archivo PNG a doble resolución con fondo blanco y título.

        Args:
            ruta: Ruta destino del archivo .png.
            ancho: Ancho base en píxeles lógicos.
            alto: Alto base en píxeles lógicos.
            escala: Factor de escala HiDPI (por defecto 2.0 para doble resolución).

        Returns:
            True si se guardó correctamente en disco.
        """
        ancho_px = int(round(ancho * escala))
        alto_px = int(round(alto * escala))
        imagen = QImage(ancho_px, alto_px, QImage.Format.Format_ARGB32)
        imagen.fill(QColor(estilo.SUPERFICIE))

        painter = QPainter(imagen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.scale(escala, escala)

        # Para exportación, animaciones al 100% y sin tooltip activo
        progreso_prev = self._progreso_animacion
        tooltip_prev = self._tooltip_visible
        self._progreso_animacion = 1.0
        self._tooltip_visible = False

        rect_export = QRectF(0, 0, float(ancho), float(alto))
        self._dibujar(painter, rect_export)

        self._progreso_animacion = progreso_prev
        self._tooltip_visible = tooltip_prev
        painter.end()

        destino = Path(ruta)
        if destino.suffix.lower() != ".png":
            destino = destino.with_suffix(".png")
        destino.parent.mkdir(parents=True, exist_ok=True)
        return imagen.save(str(destino), "PNG")

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        rect = QRectF(self.rect())
        self._dibujar(painter, rect)
        painter.end()

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        """Método de dibujo base; por defecto dibuja fondo, encabezado y estado vacío si aplica."""
        painter.fillRect(rect, QColor(estilo.SUPERFICIE))
        alto_enc = self.dibujar_encabezado(painter, rect)
        if self.esta_vacio():
            rect_vacio = rect.adjusted(16.0, alto_enc + 10.0, -16.0, -16.0)
            self.dibujar_estado_vacio(painter, rect_vacio)

    def dibujar_encabezado(self, painter: QPainter, rect: QRectF) -> float:
        """Dibuja título y subtítulo opcionales en la parte superior.

        Returns:
            Altura consumida por el encabezado.
        """
        if not self.titulo and not self.subtitulo:
            return 0.0

        margen = 16.0
        y_act = rect.top() + margen
        if self.titulo:
            fuente_tit = QFont()
            fuente_tit.setPointSize(estilo.TAMANO_CUERPO)
            fuente_tit.setBold(True)
            painter.setFont(fuente_tit)
            painter.setPen(QPen(QColor(TEXTO)))
            rect_tit = QRectF(rect.left() + margen, y_act, rect.width() - 2 * margen, 20)
            painter.drawText(rect_tit, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)
            y_act += 22.0

        if self.subtitulo:
            fuente_sub = QFont()
            fuente_sub.setPointSize(estilo.TAMANO_AUXILIAR)
            painter.setFont(fuente_sub)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_sub = QRectF(rect.left() + margen, y_act, rect.width() - 2 * margen, 18)
            painter.drawText(rect_sub, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.subtitulo)
            y_act += 20.0

        return y_act - rect.top()

    def dibujar_estado_vacio(
        self,
        painter: QPainter,
        rect: QRectF,
        mensaje: str = "Sin datos en esta ventana",
        sugerencia: str = "Prueba con “Todos los años”",
    ) -> None:
        """Dibuja el estado vacío con ícono vectorial tenue y textos centrados."""
        cx = rect.center().x()
        cy = rect.center().y() - 10.0

        # Ícono tenue de gráfico vacío (barras estilizadas en gris claro)
        painter.save()
        pen_icono = QPen(QColor(LINEA_FUERTE), 2)
        painter.setPen(pen_icono)
        painter.setBrush(QBrush(QColor(LINEA)))

        # Eje base del icono
        painter.drawLine(QPointF(cx - 30, cy + 16), QPointF(cx + 30, cy + 16))
        # 3 barritas tenues
        barras = [
            (cx - 24, cy - 6, 12, 22),
            (cx - 6, cy - 16, 12, 32),
            (cx + 12, cy - 2, 12, 18),
        ]
        for bx, by, bw, bh in barras:
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), 2, 2)
        painter.restore()

        # Texto principal
        fuente_msg = QFont()
        fuente_msg.setPointSize(estilo.TAMANO_CUERPO)
        fuente_msg.setBold(True)
        painter.setFont(fuente_msg)
        painter.setPen(QPen(QColor(TEXTO)))
        rect_msg = QRectF(rect.left() + 10, cy + 28, rect.width() - 20, 22)
        painter.drawText(rect_msg, Qt.AlignmentFlag.AlignCenter, mensaje)

        # Sugerencia
        fuente_sug = QFont()
        fuente_sug.setPointSize(estilo.TAMANO_AUXILIAR)
        painter.setFont(fuente_sug)
        painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
        rect_sug = QRectF(rect.left() + 10, cy + 50, rect.width() - 20, 18)
        painter.drawText(rect_sug, Qt.AlignmentFlag.AlignCenter, sugerencia)

    def _dibujar_tooltip(
        self,
        painter: QPainter,
        rect_limite: QRectF,
        punto: QPointF,
        titulo: str,
        filas: list[tuple[str, str, str | None]],
    ) -> None:
        """Dibuja un tooltip flotante oscuro institucional ({estilo.ENCABEZADO_INICIO}, radio 8, texto blanco).

        Args:
            painter: Pintor activo.
            rect_limite: Rectángulo del contenedor para evitar recortes.
            punto: Posición base del cursor.
            titulo: Título destacado (ej. '2021 · 21 productos').
            filas: Lista de (etiqueta, valor, color_hex_opcional).
        """
        fuente_tit = QFont()
        fuente_tit.setPointSize(estilo.TAMANO_AUXILIAR)
        fuente_tit.setBold(True)

        fuente_cuerpo = QFont()
        fuente_cuerpo.setPointSize(estilo.TAMANO_AUXILIAR)

        fm_tit = QFontMetrics(fuente_tit)
        fm_cuerpo = QFontMetrics(fuente_cuerpo)

        ancho_min = fm_tit.horizontalAdvance(titulo) + 24
        for eti, val, _ in filas:
            ancho_fila = fm_cuerpo.horizontalAdvance(f"{eti}: {val}") + 32
            if ancho_fila > ancho_min:
                ancho_min = ancho_fila

        ancho_box = max(130.0, float(ancho_min))
        alto_box = 18.0 + (len(filas) * 18.0) + (16.0 if titulo else 8.0)

        # Posicionamiento al lado del cursor con margen de seguridad
        bx = punto.x() + 12.0
        by = punto.y() - alto_box / 2.0

        if bx + ancho_box > rect_limite.right() - 8.0:
            bx = punto.x() - ancho_box - 12.0
        if bx < rect_limite.left() + 8.0:
            bx = rect_limite.left() + 8.0

        if by + alto_box > rect_limite.bottom() - 8.0:
            by = rect_limite.bottom() - alto_box - 8.0
        if by < rect_limite.top() + 8.0:
            by = rect_limite.top() + 8.0

        rect_tt = QRectF(bx, by, ancho_box, alto_box)

        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect_tt, RADIO_BOTON, RADIO_BOTON)

        # Fondo oscuro {estilo.ENCABEZADO_INICIO}
        painter.fillPath(path, QColor(ENCABEZADO_INICIO))
        painter.setPen(QPen(QColor(estilo.TEXTO_TOOLTIP), 1))
        painter.drawPath(path)

        # Título
        y_cursor = rect_tt.top() + 12.0
        if titulo:
            painter.setFont(fuente_tit)
            painter.setPen(QPen(QColor(TEXTO_SOBRE_OSCURO)))
            rect_tit = QRectF(rect_tt.left() + 10.0, y_cursor - 2, ancho_box - 20.0, 16.0)
            painter.drawText(rect_tit, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, titulo)
            y_cursor += 20.0

        # Filas de datos
        painter.setFont(fuente_cuerpo)
        for eti, val, col_hex in filas:
            x_linea = rect_tt.left() + 10.0
            if col_hex:
                painter.setBrush(QBrush(QColor(col_hex)))
                painter.setPen(QPen(QColor(estilo.SUPERFICIE), 0.5))
                painter.drawEllipse(QRectF(x_linea, y_cursor + 3, 7, 7))
                x_linea += 12.0

            painter.setPen(QPen(QColor(TEXTO_SOBRE_OSCURO_SUAVE)))
            rect_eti = QRectF(x_linea, y_cursor, ancho_box - (x_linea - rect_tt.left()) - 35, 14.0)
            painter.drawText(rect_eti, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, eti)

            painter.setPen(QPen(QColor(TEXTO_SOBRE_OSCURO)))
            rect_val = QRectF(rect_tt.right() - 40.0, y_cursor, 30.0, 14.0)
            painter.drawText(rect_val, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, val)

            y_cursor += 18.0

        painter.restore()
