"""Ficha KPI institucional con valor destacado, rótulo y minigráfico opcional."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from pea.gui.estilo import (
    ACENTO,
    COLOR_DTI,
    FICHA,
    PRIMARIO,
    RADIO_FICHA_KPI,
    TAMANO_AUXILIAR,
    TAMANO_KPI,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import formatear_decimal, formatear_entero


class Minigrafico(QWidget):
    """Minigráfico de tendencia (sparkline) de 56×18 px sin ejes para fichas KPI."""

    def __init__(
        self,
        datos: list[float] | list[int] | None = None,
        color_linea: str = COLOR_DTI,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(56, 18))
        self._datos: list[float] = [float(v) for v in datos] if datos else []
        self._color_linea = color_linea

    def actualizar_datos(self, datos: list[float] | list[int]) -> None:
        """Actualiza la serie temporal del minigráfico y repinta."""
        self._datos = [float(v) for v in datos]
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if len(self._datos) < 2:
            painter.end()
            return

        w = float(self.width() - 4)
        h = float(self.height() - 4)
        min_v = min(self._datos)
        max_v = max(self._datos)
        rango = max_v - min_v if max_v != min_v else 1.0

        puntos: list[QPointF] = []
        paso_x = w / float(len(self._datos) - 1)
        for i, val in enumerate(self._datos):
            x = 2.0 + i * paso_x
            y = 2.0 + h - ((val - min_v) / rango) * h
            puntos.append(QPointF(x, y))

        # Dibujar trazo suave
        pen = QPen(QColor(self._color_linea), 1.75)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        for i in range(len(puntos) - 1):
            painter.drawLine(puntos[i], puntos[i + 1])

        # Punto destacado en el valor más reciente
        ultimo = puntos[-1]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(ACENTO)))
        painter.drawEllipse(ultimo, 2.5, 2.5)

        painter.end()


class FichaKPI(QFrame):
    """Muestra una métrica clave con valor destacado, subtítulo y minigráfico opcional."""

    def __init__(
        self,
        titulo: str,
        valor_inicial: str | int | float = "0",
        subtitulo: str = "",
        con_minigrafico: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("fichaKPI")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"QFrame#fichaKPI {{ background-color: {FICHA}; border-radius: {RADIO_FICHA_KPI}px; border: none; }}"
        )

        self._titulo = titulo
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 12, 16, 12)
        layout_principal.setSpacing(4)

        # Rótulo auxiliar superior (10 pt)
        self.lbl_titulo = QLabel(titulo, self)
        self.lbl_titulo.setObjectName("tarjetaTitulo")
        self.lbl_titulo.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; font-weight: 600; color: {TEXTO_SECUNDARIO};"
        )
        layout_principal.addWidget(self.lbl_titulo)

        # Fila intermedia: Valor principal (22 pt) + minigráfico opcional
        fila_valor = QHBoxLayout()
        fila_valor.setContentsMargins(0, 0, 0, 0)
        fila_valor.setSpacing(8)

        self.lbl_valor = QLabel(str(valor_inicial), self)
        self.lbl_valor.setObjectName("tarjetaValor")
        self.lbl_valor.setStyleSheet(
            f"font-size: {TAMANO_KPI}pt; font-weight: bold; color: {PRIMARIO};"
        )
        fila_valor.addWidget(self.lbl_valor)
        fila_valor.addStretch()

        self._minigrafico: Minigrafico | None = None
        if con_minigrafico:
            self._minigrafico = Minigrafico(parent=self)
            fila_valor.addWidget(self._minigrafico)

        layout_principal.addLayout(fila_valor)

        # Subtítulo explicativo inferior
        self.lbl_subtitulo = QLabel(subtitulo, self)
        self.lbl_subtitulo.setObjectName("tarjetaSub")
        self.lbl_subtitulo.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};"
        )
        layout_principal.addWidget(self.lbl_subtitulo)

        self.actualizar(valor_inicial, subtitulo)

    @property
    def minigrafico(self) -> Minigrafico | None:
        """Devuelve el widget del minigráfico si está habilitado."""
        return self._minigrafico

    def actualizar(
        self,
        valor: str | int | float,
        subtitulo: str | None = None,
        tendencia: list[float] | list[int] | None = None,
    ) -> None:
        """Actualiza el valor numérico o textual, el subtítulo y opcionalmente la tendencia."""
        if isinstance(valor, int):
            texto_valor = formatear_entero(valor)
        elif isinstance(valor, float):
            texto_valor = formatear_decimal(valor, decimales=2)
        else:
            texto_valor = str(valor)

        self.lbl_valor.setText(texto_valor)
        if subtitulo is not None:
            self.lbl_subtitulo.setText(subtitulo)

        if tendencia is not None and self._minigrafico is not None:
            self._minigrafico.actualizar_datos(tendencia)

        self.setAccessibleName(f"KPI {self._titulo}: {texto_valor}. {self.lbl_subtitulo.text()}")


# Alias para compatibilidad total con pantallas y pruebas existentes
TarjetaKPI = FichaKPI

__all__ = ["FichaKPI", "Minigrafico", "TarjetaKPI"]
