"""Tarjeta KPI superior para métricas agregadas del Hipercubo."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class TarjetaKPI(QFrame):
    """Muestra una métrica clave con valor destacado y subtítulo explicativo."""

    def __init__(
        self,
        titulo: str,
        valor_inicial: str = "0",
        subtitulo: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("tarjeta")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.lbl_titulo = QLabel(titulo, self)
        self.lbl_titulo.setObjectName("tarjetaTitulo")
        layout.addWidget(self.lbl_titulo)

        self.lbl_valor = QLabel(str(valor_inicial), self)
        self.lbl_valor.setObjectName("tarjetaValor")
        layout.addWidget(self.lbl_valor)

        self.lbl_subtitulo = QLabel(subtitulo, self)
        self.lbl_subtitulo.setObjectName("tarjetaSub")
        layout.addWidget(self.lbl_subtitulo)

    def actualizar(self, valor: str | int | float, subtitulo: str | None = None) -> None:
        self.lbl_valor.setText(str(valor))
        if subtitulo is not None:
            self.lbl_subtitulo.setText(subtitulo)

