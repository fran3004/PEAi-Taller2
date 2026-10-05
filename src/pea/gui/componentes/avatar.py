"""Avatar circular con degradado estable por nombre, iniciales, variante con anillo y soporte para logos."""

from __future__ import annotations

import hashlib
from typing import Final

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

from pea.gui import estilo
from pea.gui.estilo import (
    ACENTO,
    COLOR_ASC,
    COLOR_DTI,
    COLOR_FRH,
    COLOR_GNC,
    ENCABEZADO_FIN,
    ENCABEZADO_INICIO,
    PRIMARIO,
    SUPERFICIE,
    TEXTO_SOBRE_OSCURO,
    UPC_VERDE,
    UPC_VERDE_OSCURO,
)
from pea.gui.formato import iniciales_nombre

# Paleta de degradados armónicos institucionales para avatares basados en nombre
PALETA_DEGRADADOS: Final[list[tuple[str, str]]] = [
    (ENCABEZADO_INICIO, COLOR_DTI),
    (PRIMARIO, COLOR_ASC),
    (COLOR_GNC, COLOR_FRH),
    (ENCABEZADO_FIN, ACENTO),
    (UPC_VERDE_OSCURO, UPC_VERDE),
    (COLOR_DTI, COLOR_GNC),
]


class Avatar(QWidget):
    """Componente visual de avatar circular para usuarios, investigadores y grupos."""

    def __init__(
        self,
        diametro: int = 44,
        nombre: str = "",
        con_anillo: bool = False,
        pixmap: QPixmap | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("avatar")
        self._diametro = diametro
        self._nombre = nombre
        self._con_anillo = con_anillo
        self._pixmap = pixmap
        self.setFixedSize(QSize(diametro, diametro))
        self._actualizar_accesibilidad()

    @property
    def diametro(self) -> int:
        return self._diametro

    @property
    def nombre(self) -> str:
        return self._nombre

    def establecer_nombre(self, nombre: str) -> None:
        """Actualiza el nombre, regenera las iniciales y repinta."""
        self._nombre = nombre
        self._actualizar_accesibilidad()
        self.update()

    def establecer_pixmap(self, pixmap: QPixmap | None) -> None:
        """Configura una imagen personalizada o logo institucional."""
        self._pixmap = pixmap
        self.update()

    def establecer_anillo(self, con_anillo: bool) -> None:
        """Activa o desactiva el anillo perimetral de acento."""
        self._con_anillo = con_anillo
        self.update()

    def _obtener_degradado(self) -> tuple[str, str]:
        if not self._nombre:
            return (ENCABEZADO_INICIO, PRIMARIO)
        # Hashing determinista del nombre para asociar siempre el mismo color
        hash_val = int(hashlib.md5(self._nombre.encode("utf-8")).hexdigest(), 16)
        return PALETA_DEGRADADOS[hash_val % len(PALETA_DEGRADADOS)]

    def _actualizar_accesibilidad(self) -> None:
        nombre_desc = self._nombre if self._nombre else "Avatar institucional"
        self.setAccessibleName(f"Avatar de {nombre_desc}")

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        ancho = float(self.width())
        alto = float(self.height())
        lado = min(ancho, alto)

        rect_completo = QRectF((ancho - lado) / 2.0, (alto - lado) / 2.0, lado, lado)

        # 1. Dibujar anillo si está habilitado
        margen_anillo = 0.0
        if self._con_anillo:
            grosor_anillo = 3.0
            margen_anillo = grosor_anillo + 1.5
            pen_anillo = QPen(QColor(PRIMARIO), grosor_anillo)
            painter.setPen(pen_anillo)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            rect_anillo = rect_completo.adjusted(
                grosor_anillo / 2.0, grosor_anillo / 2.0, -grosor_anillo / 2.0, -grosor_anillo / 2.0
            )
            painter.drawEllipse(rect_anillo)

        rect_avatar = rect_completo.adjusted(
            margen_anillo, margen_anillo, -margen_anillo, -margen_anillo
        )

        path_clip = QPainterPath()
        path_clip.addEllipse(rect_avatar)
        painter.save()
        painter.setClipPath(path_clip)

        # 2. Si hay pixmap/logo, dibujarlo centrado
        if self._pixmap is not None and not self._pixmap.isNull():
            painter.fillRect(rect_avatar, QColor(SUPERFICIE))
            pixmap_escalado = self._pixmap.scaled(
                int(rect_avatar.width()),
                int(rect_avatar.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x_pm = rect_avatar.center().x() - pixmap_escalado.width() / 2.0
            y_pm = rect_avatar.center().y() - pixmap_escalado.height() / 2.0
            painter.drawPixmap(int(x_pm), int(y_pm), pixmap_escalado)
        else:
            # 3. Dibujar degradado e iniciales
            c_inicio, c_fin = self._obtener_degradado()
            degradado = QLinearGradient(
                rect_avatar.topLeft(), rect_avatar.bottomRight()
            )
            degradado.setColorAt(0.0, QColor(c_inicio))
            degradado.setColorAt(1.0, QColor(c_fin))
            painter.fillRect(rect_avatar, QBrush(degradado))

            # Iniciales centradas
            texto_iniciales = iniciales_nombre(self._nombre)
            tam_fuente = estilo.TAMANO_AUXILIAR
            fuente = QFont(self.font())
            fuente.setPointSize(tam_fuente)
            fuente.setBold(True)
            painter.setFont(fuente)
            painter.setPen(QColor(TEXTO_SOBRE_OSCURO))
            painter.drawText(
                rect_avatar,
                Qt.AlignmentFlag.AlignCenter,
                texto_iniciales,
            )

        painter.restore()
        painter.end()
