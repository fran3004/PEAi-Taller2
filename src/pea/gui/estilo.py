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

COLORES_CATEGORIAS: Final[dict[str, str]] = {
    "Emérito": COLOR_CAT_EMERITO,
    "Senior": COLOR_CAT_SENIOR,
    "Asociado": COLOR_CAT_ASOCIADO,
    "Junior": COLOR_CAT_JUNIOR,
}

# Red de colaboración
COLOR_RED_ARISTAS: Final[str] = "#9DB5C9"

# Paleta cíclica para series gráficas
SERIE: Final[tuple[str, ...]] = (
    COLOR_GNC,
    COLOR_DTI,
    COLOR_ASC,
    COLOR_FRH,
    COLOR_VALIDACION_AVALADO,
    COLOR_VALIDACION_CON_SOPORTE,
    COLOR_CAT_SENIOR,
    COLOR_CAT_EMERITO,
)

# ---------------------------------------------------------------------------
# Verificación de contraste WCAG 2.1 (Tabla 4.1 de la especificación)
# ---------------------------------------------------------------------------

PARES_CONTRASTE_TABLA_4_1: Final[list[tuple[str, str, str]]] = [
    (TEXTO_SOBRE_OSCURO, ENCABEZADO_INICIO, "Blanco sobre ENCABEZADO_INICIO"),
    (TEXTO_SOBRE_OSCURO, ENCABEZADO_MEDIO, "Blanco sobre ENCABEZADO_MEDIO"),
    (TEXTO_SOBRE_OSCURO, ENCABEZADO_FIN, "Blanco sobre ENCABEZADO_FIN"),
    (ACENTO, ENCABEZADO_INICIO, "ACENTO sobre ENCABEZADO_INICIO"),
    (TEXTO_SOBRE_OSCURO, PRIMARIO, "Blanco sobre PRIMARIO"),
    (TEXTO_SOBRE_OSCURO, PRIMARIO_HOVER, "Blanco sobre PRIMARIO_HOVER"),
    (TEXTO_SOBRE_OSCURO, PRIMARIO_PULSADO, "Blanco sobre PRIMARIO_PULSADO"),
    (TEXTO, SUPERFICIE, "TEXTO sobre SUPERFICIE"),
    (TEXTO, FICHA, "TEXTO sobre FICHA"),
    (TEXTO, PIE, "TEXTO sobre PIE"),
    (TEXTO_SECUNDARIO, SUPERFICIE, "TEXTO_SECUNDARIO sobre SUPERFICIE"),
    (TEXTO_SECUNDARIO, FICHA, "TEXTO_SECUNDARIO sobre FICHA"),
    (TEXTO_SOBRE_OSCURO_SUAVE, ENCABEZADO_MEDIO, "TEXTO_SOBRE_OSCURO_SUAVE sobre ENCABEZADO_MEDIO"),
    (ENLACE, SUPERFICIE, "ENLACE sobre SUPERFICIE"),
    (EXITO, EXITO_FONDO, "EXITO sobre EXITO_FONDO"),
    (AVISO, AVISO_FONDO, "AVISO sobre AVISO_FONDO"),
    (ERROR, ERROR_FONDO, "ERROR sobre ERROR_FONDO"),
    (TEXTO_SOBRE_OSCURO, COLOR_CAT_SENIOR, "Blanco sobre Senior"),
    (TEXTO_SOBRE_OSCURO, COLOR_CAT_ASOCIADO, "Blanco sobre Asociado"),
    (TEXTO_SOBRE_OSCURO, COLOR_CAT_JUNIOR, "Blanco sobre Junior"),
    (COLOR_CAT_SIN_CATEGORIA_TEXTO, COLOR_CAT_SIN_CATEGORIA_FONDO, "Texto sobre fondo sin categoría"),
]


def calcular_luminancia_relativa(color_hex: str) -> float:
    """Calcula la luminancia relativa según la fórmula oficial de WCAG 2.1."""
    hex_str = color_hex.lstrip("#")
    r_val = int(hex_str[0:2], 16) / 255.0
    g_val = int(hex_str[2:4], 16) / 255.0
    b_val = int(hex_str[4:6], 16) / 255.0

    def ajustar(canal: float) -> float:
        return canal / 12.92 if canal <= 0.03928 else ((canal + 0.055) / 1.055) ** 2.4

    r_lin = ajustar(r_val)
    g_lin = ajustar(g_val)
    b_lin = ajustar(b_val)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calcular_radio_contraste(color1_hex: str, color2_hex: str) -> float:
    """Calcula el ratio de contraste (X:1) entre dos colores según WCAG 2.1."""
    l1 = calcular_luminancia_relativa(color1_hex)
    l2 = calcular_luminancia_relativa(color2_hex)
    mas_claro = max(l1, l2)
    mas_oscuro = min(l1, l2)
    return (mas_claro + 0.05) / (mas_oscuro + 0.05)


# ---------------------------------------------------------------------------
# 4.2 Tipografía
# ---------------------------------------------------------------------------

FAMILIA_TIPOGRAFICA: Final[str] = '"Segoe UI", "Inter", "Noto Sans", "Helvetica Neue", sans-serif'

TAMANO_MARCA: Final[int] = 30           # pt, peso 800 (Black)
PESO_MARCA: Final[int] = 800

TAMANO_KPI: Final[int] = 22             # pt, Bold
PESO_KPI: Final[str] = "bold"

TAMANO_TITULO_PANTALLA: Final[int] = 18 # pt, Semibold (600)
PESO_TITULO_PANTALLA: Final[int] = 600

TAMANO_TITULO_TARJETA: Final[int] = 14  # pt, Bold (con barra de acento)
PESO_TITULO_TARJETA: Final[str] = "bold"

TAMANO_SUBTITULO: Final[int] = 12       # pt, Regular
TAMANO_CUERPO: Final[int] = 11          # pt, Regular (cuerpo, tablas, pestañas; no baja de 11)
TAMANO_AUXILIAR: Final[int] = 10        # pt, Regular / Bold (pie, encabezados, ayudas)
TAMANO_ESLOGAN: Final[int] = 9          # pt, Regular (única excepción de tamaño, solo en barra superior)

# ---------------------------------------------------------------------------
# 4.3 Espaciado, radios, sombras y movimiento
# ---------------------------------------------------------------------------

ESPACIADO_4: Final[int] = 4
ESPACIADO_8: Final[int] = 8
ESPACIADO_12: Final[int] = 12
ESPACIADO_16: Final[int] = 16
ESPACIADO_20: Final[int] = 20
ESPACIADO_24: Final[int] = 24
ESPACIADO_32: Final[int] = 32

ESPACIADOS: Final[tuple[int, ...]] = (4, 8, 12, 16, 20, 24, 32)

RELLENO_TARJETA: Final[int] = 20
SEPARACION_TARJETAS: Final[int] = 16
MARGEN_CONTENIDO: Final[int] = 24
MARGEN_CONTENIDO_COMPACTO: Final[int] = 20

# Radios de esquina
RADIO_BOTON: Final[int] = 8
RADIO_CAMPO: Final[int] = 8
RADIO_FICHA_KPI: Final[int] = 12
RADIO_PESTANA_ACTIVA: Final[int] = 12
RADIO_TARJETA: Final[int] = 16
RADIO_PILDORA: Final[int] = 999
RADIO_AVATAR: Final[int] = 999

# Sombras
SOMBRA_TARJETA_DESENFOQUE: Final[int] = 24
SOMBRA_TARJETA_DESPLAZAMIENTO: Final[tuple[int, int]] = (0, 4)
SOMBRA_TARJETA_COLOR: Final[str] = "#0A2045"
SOMBRA_TARJETA_OPACIDAD: Final[float] = 0.10

SOMBRA_TARJETA_HOVER_DESENFOQUE: Final[int] = 32
SOMBRA_TARJETA_HOVER_DESPLAZAMIENTO: Final[tuple[int, int]] = (0, 8)
SOMBRA_TARJETA_HOVER_OPACIDAD: Final[float] = 0.16

SOMBRA_BARRA_SUPERIOR_DESENFOQUE: Final[int] = 16
SOMBRA_BARRA_SUPERIOR_OPACIDAD: Final[float] = 0.25

# Movimiento (duraciones en milisegundos)
DURACION_HOVER_MS: Final[int] = 120
DURACION_TRANSICION_PANTALLA_MS: Final[int] = 200
DURACION_GRAFICO_MS: Final[int] = 400
DESPLAZAMIENTO_TRANSICION_PX: Final[int] = 8


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
        background-color: rgba(255, 255, 255, 0.08);
        color: {TEXTO_SOBRE_OSCURO};
    }}

    QListWidget#navegacion::item:selected {{
        background-color: rgba(255, 255, 255, 0.14);
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
        background-color: #EEF3FA;
        border-color: {LINEA_FUERTE};
    }}

    QPushButton:pressed {{
        background-color: #E2EBF5;
    }}

    QPushButton:disabled {{
        color: #9AA0A6;
        background-color: #F1F3F4;
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
        background-color: #8A9EAF;
        color: #E0E7EE;
    }}

    QPushButton#peligro {{
        background-color: {ERROR};
        color: {TEXTO_SOBRE_OSCURO};
        border: none;
        font-weight: bold;
    }}

    QPushButton#peligro:hover {{
        background-color: #821D1D;
    }}

    QPushButton#peligro:disabled {{
        background-color: #E2A7A7;
    }}

    QFrame#barraSuperior QPushButton {{
        background-color: rgba(255, 255, 255, 0.12);
        color: {TEXTO_SOBRE_OSCURO};
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: {RADIO_BOTON}px;
    }}

    QFrame#barraSuperior QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.20);
    }}

    /* Tablas */
    QTableView {{
        background-color: {SUPERFICIE};
        alternate-background-color: #F8FAFC;
        gridline-color: {LINEA};
        selection-background-color: #E3EEF7;
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
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextBrowser {{
        background-color: {SUPERFICIE};
        color: {TEXTO};
        border: 1px solid {LINEA_FUERTE};
        border-radius: {RADIO_CAMPO}px;
        padding: 6px 10px;
        font-size: {TAMANO_CUERPO}pt;
    }}

    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus {{
        border: 2px solid {ACENTO};
        padding: 5px 9px;
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
    """


HOJA_ESTILOS_GLOBAL: Final[str] = generar_hoja_estilos()
HOJA_ESTILO: Final[str] = HOJA_ESTILOS_GLOBAL
