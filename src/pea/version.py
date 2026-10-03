"""Definición de versión e identidad institucional de PEA-i."""

APP_NAME = "PEA-i"
APP_VERSION = "0.1.0"
INSTITUCION = "Universidad Popular del Cesar"


def obtener_version() -> str:
    """Devuelve la cadena descriptiva de versión e institución."""
    return f"{APP_NAME} versión {APP_VERSION} ({INSTITUCION})"
