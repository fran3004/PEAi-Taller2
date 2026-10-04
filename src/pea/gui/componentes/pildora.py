"""Etiqueta redondeada (píldora) para tipologías, validaciones, categorías y estados."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_CAT_SIN_CATEGORIA_FONDO,
    COLOR_CAT_SIN_CATEGORIA_TEXTO,
    COLOR_VALIDACION_AVALADO,
    COLOR_VALIDACION_CON_SOPORTE,
    COLOR_VALIDACION_NO_AVALADO,
    COLORES_TIPOLOGIAS,
    ERROR,
    ERROR_FONDO,
    EXITO,
    EXITO_FONDO,
    FICHA,
    INFO,
    INFO_FONDO,
    RADIO_PILDORA,
    TAMANO_AUXILIAR,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
)


def resolver_estilo_pildora(variante_o_texto: str) -> tuple[str, str]:
    """Determina los colores (fondo, texto) para un dato o variante semántica."""
    clave = variante_o_texto.strip()

    # 1. Tipologías (GNC, DTI, ASC, FRH)
    if clave.upper() in COLORES_TIPOLOGIAS:
        return (COLORES_TIPOLOGIAS[clave.upper()], TEXTO_SOBRE_OSCURO)

    # 2. Validaciones Minciencias
    if clave == "Avalado":
        return (COLOR_VALIDACION_AVALADO, TEXTO)
    if clave == "Con soporte":
        return (COLOR_VALIDACION_CON_SOPORTE, TEXTO)
    if clave == "No avalado":
        return (COLOR_VALIDACION_NO_AVALADO, TEXTO)

    # 3. Categorías de Investigadores
    if "Emérito" in clave or "Emerito" in clave:
        return (COLOR_CAT_EMERITO, TEXTO_SOBRE_OSCURO)
    if "Senior" in clave:
        return (COLOR_CAT_SENIOR, TEXTO_SOBRE_OSCURO)
    if "Asociado" in clave:
        return (COLOR_CAT_ASOCIADO, TEXTO_SOBRE_OSCURO)
    if "Junior" in clave:
        return (COLOR_CAT_JUNIOR, TEXTO_SOBRE_OSCURO)
    if "Sin categoría" in clave or "Sin categoria" in clave or clave == "Ninguna":
        return (COLOR_CAT_SIN_CATEGORIA_FONDO, COLOR_CAT_SIN_CATEGORIA_TEXTO)

    # 4. Estados semánticos
    clave_lower = clave.lower()
    if clave_lower in ("exito", "activo", "conectado"):
        return (EXITO_FONDO, EXITO)
    if clave_lower in ("aviso", "demostracion", "datos de demostración", "pendiente"):
        return (AVISO_FONDO, AVISO)
    if clave_lower in ("error", "peligro", "inactivo", "sin conexion", "sin conexión"):
        return (ERROR_FONDO, ERROR)
    if clave_lower in ("info", "informacion"):
        return (INFO_FONDO, INFO)
    if clave_lower in ("inactivo", "pausado", "deshabilitado"):
        return (FICHA, TEXTO_SECUNDARIO)

    # Por defecto
    return (FICHA, TEXTO)


class Pildora(QFrame):
    """Componente visual de píldora redondeada para badges y estados."""

    def __init__(
        self,
        texto: str,
        variante: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pildora")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(0)

        self._lbl_texto = QLabel(texto, self)
        self._lbl_texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl_texto)

        self._fondo = FICHA
        self._color_texto = TEXTO
        self.establecer_texto(texto, variante)

    @property
    def texto(self) -> str:
        return self._lbl_texto.text()

    def text(self) -> str:
        """Alias para compatibilidad con interfaz convencional de widgets Qt."""
        return self._lbl_texto.text()

    @property
    def color_fondo(self) -> str:
        return self._fondo

    @property
    def color_texto(self) -> str:
        return self._color_texto

    def establecer_texto(self, texto: str, variante: str | None = None) -> None:
        """Actualiza el texto y aplica los colores correspondientes a la variante o dato."""
        self._lbl_texto.setText(texto)
        clave = variante if variante is not None else texto
        fondo, color_texto = resolver_estilo_pildora(clave)
        self.establecer_colores(fondo, color_texto)

    def establecer_variante(self, variante: str) -> None:
        """Actualiza la variante semántica de color manteniendo el texto actual."""
        self.establecer_texto(self._lbl_texto.text(), variante=variante)

    def establecer_colores(self, fondo: str, color_texto: str) -> None:
        """Aplica colores específicos de fondo y texto asegurando bordes redondeados."""
        self._fondo = fondo
        self._color_texto = color_texto
        self.setStyleSheet(
            f"QFrame#pildora {{ background-color: {fondo}; border-radius: {RADIO_PILDORA}px; border: none; }} "
            f"QLabel {{ color: {color_texto}; font-size: {TAMANO_AUXILIAR}pt; font-weight: 600; background: transparent; }}"
        )
        self.setAccessibleName(f"Píldora {self._lbl_texto.text()}")
