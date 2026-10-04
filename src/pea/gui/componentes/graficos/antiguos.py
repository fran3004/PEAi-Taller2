"""Componentes gráficos antiguos conservados para compatibilidad regresiva.

Se mantendrán hasta el reemplazo de pantallas en el prompt 13.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from pea.gui.estilo import ACENTO, LINEA, PRIMARIO, SERIE, TEXTO, TEXTO_SECUNDARIO

BORDE = LINEA
AZUL_UPC = PRIMARIO
AZUL_ACENTO = ACENTO


class GraficoBaseAntiguo(QWidget):
    """Clase base para componentes de graficación antiguos con exportación PNG."""

    def __init__(self, titulo: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.titulo = titulo
        self.setMinimumSize(QSize(280, 200))

    def exportar_png(self, ruta: Path | str, ancho: int = 800, alto: int = 500) -> bool:
        """Renderiza el gráfico a un archivo PNG."""
        imagen = QImage(ancho, alto, QImage.Format.Format_ARGB32)
        imagen.fill(QColor("#FFFFFF"))
        painter = QPainter(imagen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._dibujar(painter, QRectF(0, 0, ancho, alto))
        painter.end()
        destino = Path(ruta)
        if destino.suffix.lower() != ".png":
            destino = destino.with_suffix(".png")
        destino.parent.mkdir(parents=True, exist_ok=True)
        return imagen.save(str(destino), "PNG")

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._dibujar(painter, QRectF(self.rect()))
        painter.end()

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        raise NotImplementedError


class GraficoBarras(GraficoBaseAntiguo):
    """Gráfico de barras horizontales antiguo con etiquetas, conteos y porcentajes."""

    def __init__(
        self,
        titulo: str = "",
        datos: dict[str, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo, parent)
        self._datos: dict[str, int] = datos or {}

    def establecer_datos(self, datos: dict[str, int]) -> None:
        self._datos = dict(datos)
        self.update()

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(BORDE), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        margen = 16.0
        fuente_titulo = QFont()
        fuente_titulo.setPointSize(11)
        fuente_titulo.setBold(True)
        painter.setFont(fuente_titulo)
        painter.setPen(QPen(QColor(AZUL_UPC)))
        rect_titulo = QRectF(rect.left() + margen, rect.top() + margen, rect.width() - 2 * margen, 24)
        painter.drawText(rect_titulo, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)

        if not self._datos or sum(self._datos.values()) == 0:
            fuente_aviso = QFont()
            fuente_aviso.setPointSize(11)
            painter.setFont(fuente_aviso)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Sin datos disponibles")
            return

        total = sum(self._datos.values())
        max_val = max(self._datos.values()) if self._datos else 1
        items = list(self._datos.items())

        area_y = rect.top() + 48.0
        alto_disponible = rect.bottom() - area_y - margen
        n = len(items)
        alto_fila = alto_disponible / max(1, n)
        alto_barra = min(26.0, alto_fila * 0.65)

        ancho_etiqueta = min(120.0, rect.width() * 0.3)
        ancho_valor = 80.0
        ancho_barras = rect.width() - 2 * margen - ancho_etiqueta - ancho_valor - 12.0

        fuente_texto = QFont()
        fuente_texto.setPointSize(9)
        painter.setFont(fuente_texto)

        for i, (cat, val) in enumerate(items):
            y_base = area_y + i * alto_fila + (alto_fila - alto_barra) / 2.0
            color = QColor(SERIE[i % len(SERIE)])

            painter.setPen(QPen(QColor(TEXTO)))
            rect_etiq = QRectF(rect.left() + margen, y_base, ancho_etiqueta, alto_barra)
            painter.drawText(rect_etiq, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(cat))

            longitud = (val / max_val) * ancho_barras if max_val > 0 else 0
            rect_barra = QRectF(rect.left() + margen + ancho_etiqueta + 8.0, y_base, max(2.0, longitud), alto_barra)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect_barra, 3, 3)

            pct = (val / total * 100.0) if total > 0 else 0.0
            texto_valor = f"{val} ({pct:.1f}%)"
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            rect_val = QRectF(rect_barra.right() + 8.0, y_base, ancho_valor, alto_barra)
            painter.drawText(rect_val, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto_valor)


class GraficoTorta(GraficoBaseAntiguo):
    """Gráfico circular antiguo tipo anillo con leyenda lateral y porcentajes."""

    def __init__(
        self,
        titulo: str = "",
        datos: dict[str, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo, parent)
        self._datos: dict[str, int] = datos or {}

    def establecer_datos(self, datos: dict[str, int]) -> None:
        self._datos = dict(datos)
        self.update()

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(BORDE), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        margen = 16.0
        fuente_titulo = QFont()
        fuente_titulo.setPointSize(11)
        fuente_titulo.setBold(True)
        painter.setFont(fuente_titulo)
        painter.setPen(QPen(QColor(AZUL_UPC)))
        rect_titulo = QRectF(rect.left() + margen, rect.top() + margen, rect.width() - 2 * margen, 24)
        painter.drawText(rect_titulo, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)

        total = sum(self._datos.values())
        if not self._datos or total == 0:
            fuente_aviso = QFont()
            fuente_aviso.setPointSize(11)
            painter.setFont(fuente_aviso)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Sin datos disponibles")
            return

        area_util = rect.adjusted(margen, 40, -margen, -margen)
        ancho_leyenda = min(150.0, area_util.width() * 0.45)
        diametro = min(area_util.height() - 10, area_util.width() - ancho_leyenda - 20)
        diametro = max(50.0, diametro)

        rect_torta = QRectF(
            area_util.left() + 10,
            area_util.top() + (area_util.height() - diametro) / 2.0,
            diametro,
            diametro,
        )

        angulo_inicio = 90 * 16
        items = list(self._datos.items())

        for i, (_cat, val) in enumerate(items):
            if val <= 0:
                continue
            span = int((val / total) * 360 * 16)
            color = QColor(SERIE[i % len(SERIE)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
            painter.drawPie(rect_torta, angulo_inicio, -span)
            angulo_inicio -= span

        radio_interior = diametro * 0.55
        rect_interior = QRectF(
            rect_torta.center().x() - radio_interior / 2.0,
            rect_torta.center().y() - radio_interior / 2.0,
            radio_interior,
            radio_interior,
        )
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect_interior)

        fuente_centro = QFont()
        fuente_centro.setPointSize(12)
        fuente_centro.setBold(True)
        painter.setFont(fuente_centro)
        painter.setPen(QPen(QColor(AZUL_UPC)))
        painter.drawText(rect_interior, Qt.AlignmentFlag.AlignCenter, str(total))

        fuente_leyenda = QFont()
        fuente_leyenda.setPointSize(9)
        painter.setFont(fuente_leyenda)
        x_leyenda = rect_torta.right() + 20
        y_leyenda = area_util.top() + 10
        alto_item_leyenda = 22.0

        for i, (cat, val) in enumerate(items):
            pct = (val / total * 100.0) if total > 0 else 0.0
            color = QColor(SERIE[i % len(SERIE)])

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x_leyenda, y_leyenda + i * alto_item_leyenda + 4, 12, 12), 2, 2)

            painter.setPen(QPen(QColor(TEXTO)))
            rect_txt = QRectF(x_leyenda + 18, y_leyenda + i * alto_item_leyenda, ancho_leyenda - 18, alto_item_leyenda)
            painter.drawText(
                rect_txt,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{cat}: {val} ({pct:.1f}%)",
            )


class GraficoSeries(GraficoBaseAntiguo):
    """Gráfico de evolución temporal antiguo con barras verticales y línea de tendencia."""

    def __init__(
        self,
        titulo: str = "",
        datos: dict[int, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(titulo, parent)
        self._datos: dict[int, int] = datos or {}

    def establecer_datos(self, datos: dict[int, int]) -> None:
        self._datos = dict(datos)
        self.update()

    def _dibujar(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor(BORDE), 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        margen = 16.0
        fuente_titulo = QFont()
        fuente_titulo.setPointSize(11)
        fuente_titulo.setBold(True)
        painter.setFont(fuente_titulo)
        painter.setPen(QPen(QColor(AZUL_UPC)))
        rect_titulo = QRectF(rect.left() + margen, rect.top() + margen, rect.width() - 2 * margen, 24)
        painter.drawText(rect_titulo, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.titulo)

        if not self._datos or sum(self._datos.values()) == 0:
            fuente_aviso = QFont()
            fuente_aviso.setPointSize(11)
            painter.setFont(fuente_aviso)
            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Sin datos disponibles")
            return

        items = sorted(self._datos.items(), key=lambda t: t[0])
        anios = [str(a) for a, _ in items]
        valores = [v for _, v in items]
        max_val = max(valores) if valores else 1

        area_grafico = rect.adjusted(margen + 20, 50, -margen, -30)
        n = len(items)
        ancho_columna = area_grafico.width() / max(1, n)
        ancho_barra = min(32.0, ancho_columna * 0.6)

        painter.setPen(QPen(QColor("#E2E8F0"), 1, Qt.PenStyle.DashLine))
        for division in (0.25, 0.5, 0.75, 1.0):
            y_div = area_grafico.bottom() - division * area_grafico.height()
            painter.drawLine(QPointF(area_grafico.left(), y_div), QPointF(area_grafico.right(), y_div))

        painter.setPen(QPen(QColor(BORDE), 1))
        painter.drawLine(
            QPointF(area_grafico.left(), area_grafico.bottom()),
            QPointF(area_grafico.right(), area_grafico.bottom()),
        )

        fuente_etiquetas = QFont()
        fuente_etiquetas.setPointSize(8)
        painter.setFont(fuente_etiquetas)

        puntos_linea: list[QPointF] = []

        for i, val in enumerate(valores):
            x_centro = area_grafico.left() + i * ancho_columna + ancho_columna / 2.0
            altura = (val / max_val) * (area_grafico.height() - 20) if max_val > 0 else 0
            rect_barra = QRectF(x_centro - ancho_barra / 2.0, area_grafico.bottom() - altura, ancho_barra, altura)

            painter.setBrush(QBrush(QColor(AZUL_ACENTO)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect_barra, 3, 3)

            painter.setPen(QPen(QColor(AZUL_UPC)))
            painter.drawText(
                QRectF(x_centro - 20, rect_barra.top() - 16, 40, 14),
                Qt.AlignmentFlag.AlignCenter,
                str(val),
            )

            painter.setPen(QPen(QColor(TEXTO_SECUNDARIO)))
            painter.drawText(
                QRectF(x_centro - 24, area_grafico.bottom() + 6, 48, 16),
                Qt.AlignmentFlag.AlignCenter,
                anios[i],
            )

            puntos_linea.append(QPointF(x_centro, rect_barra.top()))

        if len(puntos_linea) > 1:
            pen_linea = QPen(QColor(SERIE[2]), 2)
            painter.setPen(pen_linea)
            for j in range(len(puntos_linea) - 1):
                painter.drawLine(puntos_linea[j], puntos_linea[j + 1])
