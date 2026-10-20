"""Tokens de diseño oficiales y hoja de estilos global de PEA-i (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 4).
Todos los colores, tipografías, espaciados, radios, sombras y duraciones
provienen de las constantes aquí definidas.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# 4.1 Color (Paleta oficial PEA-i / UPC)
# ---------------------------------------------------------------------------

# Encabezado (degradado horizontal de izquierda a derecha)
ENCABEZADO_INICIO: Final[str] = "#0A2045"
ENCABEZADO_MEDIO: Final[str] = "#0E3A5C"
ENCABEZADO_FIN: Final[str] = "#0E405C"

# Acento de interacción y foco
ACENTO: Final[str] = "#35B6E8"

# Botón primario y acentos principales de acción
PRIMARIO: Final[str] = "#0E3A5C"
PRIMARIO_HOVER: Final[str] = "#0A2D49"
PRIMARIO_PULSADO: Final[str] = "#082338"

# Superficies y fondos
FONDO_APP: Final[str] = "#F1F5F9"
SUPERFICIE: Final[str] = "#FFFFFF"
FICHA: Final[str] = "#E9EEF6"
PIE: Final[str] = "#D4DAE3"

# Líneas y bordes
LINEA: Final[str] = "#D9E1EA"
LINEA_FUERTE: Final[str] = "#C3CFDC"

# Textos
TEXTO: Final[str] = "#102B44"
TEXTO_SECUNDARIO: Final[str] = "#475A6C"
TEXTO_SOBRE_OSCURO: Final[str] = "#FFFFFF"
TEXTO_SOBRE_OSCURO_SUAVE: Final[str] = "#C9D8EA"
ENLACE: Final[str] = "#1F6F94"

# Estados visuales auxiliares y superficies de controles.
SUPERFICIE_ALTERNADA: Final[str] = "#F8FAFC"
SUPERFICIE_HOVER: Final[str] = "#EEF3FA"
SUPERFICIE_PULSADA: Final[str] = "#E2EBF5"
SUPERFICIE_SELECCIONADA: Final[str] = "#E3EEF7"
SUPERFICIE_GRAFICO: Final[str] = "#F3F7FB"
SUPERFICIE_GRAFICO_GUIA: Final[str] = "#E2E8F0"
SUPERFICIE_GRAFICO_HOVER: Final[str] = "#EBF2FA"
SUPERFICIE_ERROR: Final[str] = "#FFF0F0"
SUPERFICIE_EXITO: Final[str] = "#E6F4EC"
SUPERFICIE_EXITO_HOVER: Final[str] = "#D7EFE0"
SUPERFICIE_DESHABILITADA: Final[str] = "#F1F3F4"
SUPERFICIE_DESHABILITADA_SUAVE: Final[str] = "#DDE5F0"
SUPERFICIE_DESHABILITADA_ERROR: Final[str] = "#FDE8E8"
TEXTO_DESHABILITADO: Final[str] = TEXTO_SECUNDARIO
TEXTO_DESHABILITADO_SOBRE_PRIMARIO: Final[str] = TEXTO_SOBRE_OSCURO
PRIMARIO_DESHABILITADO: Final[str] = PRIMARIO_PULSADO
ERROR_HOVER: Final[str] = "#821D1D"
ERROR_DESHABILITADO: Final[str] = "#E2A7A7"
BORDE_ERROR_SUAVE: Final[str] = "#F5C6C6"
EXITO_BORDE_SUAVE: Final[str] = "#B8E2CB"
TEXTO_TOOLTIP: Final[str] = "#1F3E68"

# Transparencias usadas por la barra superior y las capas de interacción.
SUPERPOSICION_NEGRA_8: Final[str] = "rgba(0, 0, 0, 0.08)"
SUPERPOSICION_CLARA_5: Final[str] = "rgba(255, 255, 255, 0.05)"
SUPERPOSICION_CLARA_8: Final[str] = "rgba(255, 255, 255, 0.08)"
SUPERPOSICION_CLARA_10: Final[str] = "rgba(255, 255, 255, 0.1)"
SUPERPOSICION_CLARA_12: Final[str] = "rgba(255, 255, 255, 0.12)"
SUPERPOSICION_CLARA_14: Final[str] = "rgba(255, 255, 255, 0.14)"
SUPERPOSICION_CLARA_20: Final[str] = "rgba(255, 255, 255, 0.20)"
SUPERPOSICION_CLARA_22: Final[str] = "rgba(255, 255, 255, 0.22)"
SUPERPOSICION_CLARA_25: Final[str] = "rgba(255, 255, 255, 0.25)"
SUPERPOSICION_CLARA_40: Final[str] = "rgba(255, 255, 255, 0.4)"
SUPERPOSICION_CLARA_45: Final[str] = "rgba(255, 255, 255, 0.45)"
SUPERPOSICION_CLARA_94: Final[str] = "rgba(255, 255, 255, 0.94)"

# Identidad institucional Universidad Popular del Cesar (filete de 3 px)
UPC_VERDE_OSCURO: Final[str] = "#0F7B47"
UPC_VERDE: Final[str] = "#43A242"
UPC_VERDE_CLARO: Final[str] = "#A3CD91"

# Estados semánticos (texto / fondo)
EXITO: Final[str] = "#1B6E3F"
EXITO_FONDO: Final[str] = "#E6F4EC"

AVISO: Final[str] = "#8A4B00"
AVISO_FONDO: Final[str] = "#FFF1DC"

ERROR: Final[str] = "#A12626"
ERROR_FONDO: Final[str] = "#FDECEC"

INFO: Final[str] = "#196E8F"
INFO_FONDO: Final[str] = "#E3F1F7"

# Colores de datos: Tipologías Minciencias
COLOR_GNC: Final[str] = "#17375E"  # Azul datos
COLOR_DTI: Final[str] = "#1F7A9E"  # Petróleo
COLOR_ASC: Final[str] = "#2BB0A0"  # Turquesa
COLOR_FRH: Final[str] = "#4B4C9D"  # Índigo

COLORES_TIPOLOGIAS: Final[dict[str, str]] = {
    "GNC": COLOR_GNC,
    "DTI": COLOR_DTI,
    "ASC": COLOR_ASC,
    "FRH": COLOR_FRH,
}

# Colores de datos: Validaciones Minciencias
COLOR_VALIDACION_AVALADO: Final[str] = "#6BBF8E"      # Verde suave
COLOR_VALIDACION_CON_SOPORTE: Final[str] = "#E59D53"  # Naranja
COLOR_VALIDACION_NO_AVALADO: Final[str] = "#9DB5C9"   # Gris azulado

COLORES_VALIDACIONES: Final[dict[str, str]] = {
    "Avalado": COLOR_VALIDACION_AVALADO,
    "Con soporte": COLOR_VALIDACION_CON_SOPORTE,
    "No avalado": COLOR_VALIDACION_NO_AVALADO,
}

# Colores de datos: Categorías de investigador Minciencias
COLOR_CAT_EMERITO: Final[str] = "#4B4C9D"   # Índigo
COLOR_CAT_SENIOR: Final[str] = "#196E8F"    # Petróleo oscuro
COLOR_CAT_ASOCIADO: Final[str] = "#17375E"  # Azul datos
COLOR_CAT_JUNIOR: Final[str] = "#0F7F73"    # Turquesa oscuro

COLOR_CAT_SIN_CATEGORIA_FONDO: Final[str] = "#E3E9F0"
COLOR_CAT_SIN_CATEGORIA_TEXTO: Final[str] = "#3F5163"

# Red de colaboración
COLOR_RED_ARISTAS: Final[str] = "#7E9AB8"
COLOR_RED_ARISTA_ACTIVA: Final[str] = "#1F6FA8"
COLOR_NODO_SIN_CATEGORIA: Final[str] = "#4F709C"
COLOR_NODO_AISLADO: Final[str] = "#7B8FA6"

# Paleta cromática para nodos de red por comunidad/grado cuando no tienen categoría
PALETA_NODOS_RED: Final[tuple[str, ...]] = (
    "#1F6FA8",
    "#0F7F73",
    "#4B4C9D",
    "#2B5B84",
    "#196E8F",
    "#2E8B57",
    "#8E5B23",
    "#3B6EA5",
)

# ---------------------------------------------------------------------------
# 4.2 Tipografía
# ---------------------------------------------------------------------------

FAMILIA_TIPOGRAFICA: Final[str] = '"Inter", "Segoe UI", "Noto Sans", "Helvetica Neue", sans-serif'
FAMILIA_FUENTE: Final[str] = "Inter"

TAMANO_MARCA: Final[int] = 30           # pt, peso 800 (Black)
PESO_MARCA: Final[int] = 800

TAMANO_KPI: Final[int] = 22             # pt, Bold

TAMANO_TITULO_PANTALLA: Final[int] = 18 # pt, Semibold (600)
PESO_TITULO_PANTALLA: Final[int] = 600

TAMANO_TITULO_TARJETA: Final[int] = 14  # pt, Bold (con barra de acento)

TAMANO_SUBTITULO: Final[int] = 12       # pt, Regular
TAMANO_CUERPO: Final[int] = 11          # pt, Regular (cuerpo, tablas, pestañas; no baja de 11)
TAMANO_AUXILIAR: Final[int] = 10        # pt, Regular / Bold (pie, encabezados, ayudas)
TAMANO_ESLOGAN: Final[int] = 9          # pt, Regular (única excepción de tamaño, solo en barra superior)
TAMANO_MICRO: Final[int] = 8            # pt, etiquetas compactas de gráficos / insignias
TAMANO_COMPACTO_VALOR: Final[int] = 13  # pt, cifra compacta en tarjetas / leyendas
TAMANO_CENTRO_DONA_COMPACTO: Final[int] = 16  # pt, centro de dona en vista compacta
TAMANO_CENTRO_DONA: Final[int] = 20     # pt, centro de dona en vista estándar

# ---------------------------------------------------------------------------
# 4.3 Espaciado, radios, sombras y movimiento
# ---------------------------------------------------------------------------

ESPACIADO_4: Final[int] = 4
ESPACIADO_8: Final[int] = 8
ESPACIADO_16: Final[int] = 16

RELLENO_TARJETA: Final[int] = 20
SEPARACION_TARJETAS: Final[int] = 16
MARGEN_CONTENIDO: Final[int] = 24

# Radios de esquina y dimensiones de controles
RADIO_BOTON: Final[int] = 8
RADIO_CAMPO: Final[int] = 8
ALTURA_CAMPO_MINIMA: Final[int] = 36
RADIO_FICHA_KPI: Final[int] = 12
RADIO_PESTANA_ACTIVA: Final[int] = 12
RADIO_TARJETA: Final[int] = 16
RADIO_PILDORA: Final[int] = 999

# Sombras
SOMBRA_TARJETA_DESENFOQUE: Final[int] = 24
SOMBRA_TARJETA_DESPLAZAMIENTO: Final[tuple[int, int]] = (0, 4)
SOMBRA_TARJETA_COLOR: Final[str] = "#0A2045"
SOMBRA_TARJETA_OPACIDAD: Final[float] = 0.10

# ---------------------------------------------------------------------------
# Generador de la hoja de estilo global (QSS)
# ---------------------------------------------------------------------------

def generar_hoja_estilos() -> str:
    """Genera la hoja de estilos global Qt (QSS) basada estrictamente en los tokens."""
    return f"""
    /* Fondo principal de la aplicación */
    QMainWindow, QWidget#fondo {{
        background-color: {FONDO_APP};
        font-family: {FAMILIA_TIPOGRAFICA};
        color: {TEXTO};
    }}

    QWidget {{
        font-family: {FAMILIA_TIPOGRAFICA};
        color: {TEXTO};
        font-size: {TAMANO_CUERPO}pt;
    }}

    /* Barra superior con degradado institucional */
    QFrame#barraSuperior {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ENCABEZADO_INICIO},
            stop:0.5 {ENCABEZADO_MEDIO},
            stop:1 {ENCABEZADO_FIN});
        border: none;
    }}

    QFrame#barraSuperior QWidget {{
        background-color: transparent;
    }}

    QFrame#barraSuperior QLabel {{
        color: {TEXTO_SOBRE_OSCURO};
    }}

    QLabel#marcaPEA {{
        font-size: {TAMANO_MARCA}pt;
        font-weight: {PESO_MARCA};
        color: {TEXTO_SOBRE_OSCURO};
    }}

    QLabel#esloganApp {{
        font-size: {TAMANO_ESLOGAN}pt;
        color: {TEXTO_SOBRE_OSCURO_SUAVE};
    }}

    /* Pestañas de navegación de la barra superior */
    QListWidget#navegacion {{
        background: transparent;
        border: none;
        outline: none;
    }}

    QListWidget#navegacion::item {{
        color: {TEXTO_SOBRE_OSCURO_SUAVE};
        padding: 8px 14px;
        border-radius: {RADIO_PESTANA_ACTIVA}px;
    }}

    QListWidget#navegacion::item:hover {{
        background-color: {SUPERPOSICION_CLARA_8};
        color: {TEXTO_SOBRE_OSCURO};
    }}

    QListWidget#navegacion::item:selected {{
        background-color: {SUPERPOSICION_CLARA_14};
        color: {TEXTO_SOBRE_OSCURO};
        font-weight: 600;
    }}

    /* Tarjetas y paneles de contenido */
    QFrame#tarjeta, QFrame#panel {{
        background-color: {SUPERFICIE};
        border: 1px solid {LINEA};
        border-radius: {RADIO_TARJETA}px;
    }}

    QFrame#fichaKPI {{
        background-color: {FICHA};
        border: none;
        border-radius: {RADIO_FICHA_KPI}px;
    }}

    QLabel#tarjetaTitulo {{
        color: {TEXTO};
        font-size: {TAMANO_TITULO_TARJETA}pt;
        font-weight: bold;
    }}

    QLabel#tarjetaValor {{
        color: {PRIMARIO};
        font-size: {TAMANO_KPI}pt;
        font-weight: bold;
    }}

    QLabel#tarjetaSub {{
        color: {TEXTO_SECUNDARIO};
        font-size: {TAMANO_AUXILIAR}pt;
    }}

    QLabel#tituloPantalla {{
        font-size: {TAMANO_TITULO_PANTALLA}pt;
        font-weight: {PESO_TITULO_PANTALLA};
        color: {TEXTO};
    }}

    QLabel#ayuda {{
        color: {TEXTO_SECUNDARIO};
        font-size: {TAMANO_AUXILIAR}pt;
    }}

    QLabel#sinDatos {{
        font-size: {TAMANO_TITULO_PANTALLA}pt;
        color: {TEXTO_SECUNDARIO};
    }}

    /* Botones */
    QPushButton {{
        background-color: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {LINEA};
        border-radius: {RADIO_BOTON}px;
        padding: 7px 16px;
        font-size: {TAMANO_CUERPO}pt;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {SUPERFICIE_HOVER};
        border-color: {LINEA_FUERTE};
    }}

    QPushButton:pressed {{
        background-color: {SUPERFICIE_PULSADA};
    }}

    QPushButton:disabled {{
        color: {TEXTO_DESHABILITADO};
        background-color: {SUPERFICIE_DESHABILITADA};
        border-color: {LINEA};
    }}

    QPushButton#primario {{
        background-color: {PRIMARIO};
        color: {TEXTO_SOBRE_OSCURO};
        border: none;
        font-weight: bold;
    }}

    QPushButton#primario:hover {{
        background-color: {PRIMARIO_HOVER};
    }}

    QPushButton#primario:pressed {{
        background-color: {PRIMARIO_PULSADO};
    }}

    QPushButton#primario:disabled {{
        background-color: {PRIMARIO_DESHABILITADO};
        color: {TEXTO_DESHABILITADO_SOBRE_PRIMARIO};
        border: none;
    }}

    QPushButton#peligro {{
        background-color: {ERROR};
        color: {TEXTO_SOBRE_OSCURO};
        border: none;
        font-weight: bold;
    }}

    QPushButton#peligro:hover {{
        background-color: {ERROR_HOVER};
    }}

    QPushButton#peligro:disabled {{
        background-color: {ERROR_DESHABILITADO};
    }}

    QFrame#barraSuperior QPushButton {{
        background-color: {SUPERPOSICION_CLARA_12};
        color: {TEXTO_SOBRE_OSCURO};
        border: 1px solid {SUPERPOSICION_CLARA_25};
        border-radius: {RADIO_BOTON}px;
    }}

    QFrame#barraSuperior QPushButton:hover {{
        background-color: {SUPERPOSICION_CLARA_20};
    }}

    /* Tablas */
    QTableView {{
        background-color: {SUPERFICIE};
        alternate-background-color: {SUPERFICIE_ALTERNADA};
        gridline-color: {LINEA};
        selection-background-color: {SUPERFICIE_SELECCIONADA};
        selection-color: {TEXTO};
        border: 1px solid {LINEA};
        border-radius: {RADIO_BOTON}px;
        font-size: {TAMANO_CUERPO}pt;
    }}

    QHeaderView::section {{
        background-color: {FICHA};
        color: {TEXTO};
        font-size: {TAMANO_AUXILIAR}pt;
        font-weight: bold;
        padding: 8px 12px;
        border: none;
        border-right: 1px solid {LINEA};
        border-bottom: 1px solid {LINEA};
    }}

    /* Campos de formulario */
    QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
        background-color: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {LINEA_FUERTE};
        border-radius: {RADIO_CAMPO}px;
        padding: 6px 10px;
        font-size: {TAMANO_CUERPO}pt;
    }}

    QSpinBox {{
        background-color: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {LINEA_FUERTE};
        border-radius: {RADIO_CAMPO}px;
        padding: 4px 6px;
        font-size: {TAMANO_CUERPO}pt;
        min-height: 24px;
    }}

    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{
        border: 2px solid {ACENTO};
        padding: 5px 9px;
    }}

    QSpinBox:focus {{
        border: 2px solid {ACENTO};
        padding: 3px 5px;
    }}

    /* Pie institucional */
    QFrame#pieInstitucional, QStatusBar {{
        background-color: {PIE};
        color: {TEXTO};
        border-top: 1px solid {LINEA};
    }}

    QFrame#pieInstitucional QLabel, QStatusBar QLabel {{
        color: {TEXTO};
        font-size: {TAMANO_AUXILIAR}pt;
    }}

    /* Avisos de servidor y cambios */
    QFrame#avisoCambio {{
        background-color: {AVISO_FONDO};
        border: 1px solid {AVISO};
        border-radius: {RADIO_BOTON}px;
    }}

    QFrame#avisoError {{
        background-color: {ERROR_FONDO};
        border: 1px solid {ERROR};
        border-radius: {RADIO_BOTON}px;
    }}

    QLabel#bloqueo {{
        background-color: {AVISO_FONDO};
        color: {AVISO};
        border: 1px solid {AVISO};
        border-radius: {RADIO_CAMPO}px;
        padding: 6px;
    }}

    /* Pestañas de subsecciones */
    QTabWidget::pane {{
        border: 1px solid {LINEA};
        background: {SUPERFICIE};
        border-radius: {RADIO_BOTON}px;
    }}

    QTabBar::tab {{
        padding: 8px 16px;
        font-size: {TAMANO_CUERPO}pt;
        color: {TEXTO_SECUNDARIO};
    }}

    QTabBar::tab:selected {{
        color: {PRIMARIO};
        font-weight: bold;
        border-bottom: 3px solid {ACENTO};
    }}

    QToolTip {{
        background-color: {TEXTO};
        color: {TEXTO_SOBRE_OSCURO};
        border: 1px solid {LINEA_FUERTE};
        font-size: {TAMANO_CUERPO}pt;
    }}

    QMenu {{
        background-color: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {LINEA};
        border-radius: {RADIO_BOTON}px;
        font-size: {TAMANO_CUERPO}pt;
    }}

    QComboBox {{
        font-size: {TAMANO_CUERPO}pt;
    }}
    """


HOJA_ESTILOS_GLOBAL: Final[str] = generar_hoja_estilos()
HOJA_ESTILO: Final[str] = HOJA_ESTILOS_GLOBAL
