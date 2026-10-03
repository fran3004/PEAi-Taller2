"""Paleta institucional y hoja de estilo Qt (brain/20-Diseno/GUI-paridad.md §1)."""

from __future__ import annotations

AZUL_UPC = "#003366"
AZUL_ACENTO = "#0D47A1"
FONDO = "#F5F7FA"
BLANCO = "#FFFFFF"
TEXTO = "#1A1A1A"
TEXTO_SECUNDARIO = "#5F6368"
VERDE = "#2E7D32"
NARANJA = "#ED6C02"
ROJO = "#D32F2F"
BORDE = "#DDE3EA"

# Colores para series de gráficos (azules institucionales y semánticos suaves).
SERIE: tuple[str, ...] = ("#0D47A1", "#2E7D32", "#ED6C02", "#6A1B9A", "#00838F", "#AD1457", "#5D4037", "#455A64")

HOJA_ESTILO = f"""
QMainWindow, QWidget#fondo {{ background-color: {FONDO}; }}
QWidget {{ color: {TEXTO}; font-size: 13px; }}
QFrame#barraSuperior {{ background-color: {AZUL_UPC}; }}
QFrame#barraSuperior QLabel {{ color: {BLANCO}; }}
QLabel#tituloApp {{ font-size: 18px; font-weight: bold; }}
QLabel#subtituloApp {{ color: #C9D6E8; font-size: 12px; }}
QLabel#tituloPantalla {{ font-size: 20px; font-weight: bold; color: {AZUL_UPC}; }}
QLabel#ayuda {{ color: {TEXTO_SECUNDARIO}; }}
QLabel#sinDatos {{ font-size: 18px; color: {TEXTO_SECUNDARIO}; }}
QListWidget#navegacion {{
    background-color: {BLANCO}; border: none; border-right: 1px solid {BORDE};
    font-size: 14px; padding-top: 8px; outline: none;
}}
QListWidget#navegacion::item {{ padding: 10px 14px; border-left: 4px solid transparent; }}
QListWidget#navegacion::item:selected {{
    background-color: #E3ECF8; color: {AZUL_ACENTO}; border-left: 4px solid {AZUL_ACENTO}; font-weight: bold;
}}
QFrame#tarjeta, QFrame#panel {{
    background-color: {BLANCO}; border: 1px solid {BORDE}; border-radius: 8px;
}}
QLabel#tarjetaTitulo {{ color: {TEXTO_SECUNDARIO}; font-size: 12px; }}
QLabel#tarjetaValor {{ color: {AZUL_UPC}; font-size: 26px; font-weight: bold; }}
QLabel#tarjetaSub {{ color: {TEXTO_SECUNDARIO}; font-size: 11px; }}
QLabel#panelTitulo {{ font-weight: bold; color: {AZUL_UPC}; }}
QPushButton {{
    background-color: {BLANCO}; border: 1px solid {BORDE}; border-radius: 5px; padding: 6px 12px;
}}
QPushButton:hover {{ background-color: #EEF3FA; }}
QPushButton:disabled {{ color: #9AA0A6; background-color: #F1F3F4; }}
QPushButton#primario {{ background-color: {AZUL_ACENTO}; color: {BLANCO}; border: none; font-weight: bold; }}
QPushButton#primario:disabled {{ background-color: #9FB4D6; }}
QPushButton#peligro {{ background-color: {ROJO}; color: {BLANCO}; border: none; }}
QPushButton#peligro:disabled {{ background-color: #E8A6A6; }}
QFrame#barraSuperior QPushButton {{ background-color: {AZUL_ACENTO}; color: {BLANCO}; border: 1px solid #3A6BC1; }}
QFrame#barraSuperior QPushButton:disabled {{ color: #9FB4D6; }}
QTableView {{
    background-color: {BLANCO}; alternate-background-color: #F7F9FC; gridline-color: {BORDE};
    selection-background-color: #CFE0F7; selection-color: {TEXTO}; border: 1px solid {BORDE};
}}
QHeaderView::section {{
    background-color: #EEF2F7; color: {AZUL_UPC}; font-weight: bold; padding: 5px; border: none;
    border-right: 1px solid {BORDE}; border-bottom: 1px solid {BORDE};
}}
QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextBrowser, QListWidget {{
    background-color: {BLANCO}; border: 1px solid {BORDE}; border-radius: 4px; padding: 4px;
}}
QTabWidget::pane {{ border: 1px solid {BORDE}; background: {BLANCO}; }}
QTabBar::tab {{ padding: 7px 14px; }}
QTabBar::tab:selected {{ color: {AZUL_ACENTO}; font-weight: bold; }}
QStatusBar {{ background-color: {AZUL_UPC}; color: {BLANCO}; }}
QStatusBar QLabel {{ color: {BLANCO}; padding: 0 8px; }}
QFrame#avisoCambio {{ background-color: #FFF4E5; border: 1px solid {NARANJA}; border-radius: 6px; }}
QFrame#avisoError {{ background-color: #FDECEA; border: 1px solid {ROJO}; border-radius: 6px; }}
QLabel#bloqueo {{ background-color: #FFF4E5; color: #8A4500; border: 1px solid {NARANJA}; border-radius: 4px; padding: 6px; }}
"""

HOJA_ESTILOS_GLOBAL = HOJA_ESTILO

