"""Diálogos y utilidades comunes para exportar archivos (PDF, PNG y CSV).

Todas las pantallas piden el destino con el explorador de archivos del sistema; nunca se escribe
en una carpeta fija. Estas funciones concentran esa lógica para que el comportamiento sea idéntico
en toda la aplicación: carpeta inicial razonable, nombre sugerido seguro, extensión garantizada y
mensajes de error comprensibles.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFileDialog, QWidget

FILTRO_PDF = "Documento PDF (*.pdf)"
FILTRO_PNG = "Imagen PNG (*.png)"
FILTRO_CSV = "Archivo CSV para Excel (*.csv)"

_ultimo_directorio: Path | None = None


def carpeta_inicial() -> Path:
    """Carpeta que propone el explorador: la última usada o «Documentos» del usuario."""
    if _ultimo_directorio is not None and _ultimo_directorio.is_dir():
        return _ultimo_directorio
    documentos = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    if documentos and Path(documentos).is_dir():
        return Path(documentos)
    return Path.home()


def _recordar_directorio(directorio: Path) -> None:
    global _ultimo_directorio
    if directorio.is_dir():
        _ultimo_directorio = directorio


def destino_explicito(valor: object) -> Path | None:
    """Convierte un destino recibido por parámetro en ruta, o devuelve None si no es una ruta.

    Las señales ``triggered``/``clicked`` de Qt envían un booleano («checked»). Si ese valor llegara
    a un método con parámetro opcional de destino, se interpretaría como ruta («False»). Aquí solo
    se aceptan cadenas no vacías y objetos ``Path``.
    """
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, Path):
        return valor
    if isinstance(valor, str) and valor.strip():
        return Path(valor)
    return None


def nombre_archivo_seguro(base: str, extension: str, *, con_fecha: bool = True) -> str:
    """Genera un nombre de archivo válido en Windows, sin tildes ni espacios, con fecha opcional."""
    limpio = base.strip().lower()
    for origen, destino in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"), ("ü", "u")):
        limpio = limpio.replace(origen, destino)
    limpio = re.sub(r"[^a-z0-9]+", "_", limpio).strip("_") or "exportacion"
    sufijo = f"_{datetime.now():%Y-%m-%d}" if con_fecha else ""
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"{limpio[:80]}{sufijo}{ext}"


def asegurar_extension(ruta: Path, extension: str) -> Path:
    """Añade la extensión esperada si el usuario la omitió o escribió otra distinta."""
    ext = extension if extension.startswith(".") else f".{extension}"
    if ruta.suffix.lower() != ext.lower():
        return ruta.with_name(ruta.name + ext)
    return ruta


def pedir_archivo_guardado(
    parent: QWidget | None,
    titulo: str,
    nombre_sugerido: str,
    filtro: str,
    extension: str,
) -> Path | None:
    """Abre el explorador «Guardar como» y devuelve la ruta elegida (o None si se cancela)."""
    inicial = carpeta_inicial() / nombre_sugerido
    ruta, _ = QFileDialog.getSaveFileName(parent, titulo, str(inicial), filtro)
    if not ruta:
        return None
    destino = asegurar_extension(Path(ruta), extension)
    _recordar_directorio(destino.parent)
    return destino


def pedir_carpeta(parent: QWidget | None, titulo: str) -> Path | None:
    """Abre el explorador para elegir una carpeta de destino (o None si se cancela)."""
    directorio = QFileDialog.getExistingDirectory(parent, titulo, str(carpeta_inicial()))
    if not directorio:
        return None
    destino = Path(directorio)
    _recordar_directorio(destino)
    return destino


def resolver_archivo_destino(
    parent: QWidget | None,
    destino: object,
    *,
    titulo: str,
    nombre_base: str,
    filtro: str,
    extension: str,
) -> Path | None:
    """Usa el destino indicado por código o, si no hay, pide uno al usuario con el explorador."""
    explicito = destino_explicito(destino)
    if explicito is not None:
        return asegurar_extension(explicito, extension)
    return pedir_archivo_guardado(
        parent,
        titulo,
        nombre_archivo_seguro(nombre_base, extension),
        filtro,
        extension,
    )


def resolver_carpeta_destino(parent: QWidget | None, destino: object, *, titulo: str) -> Path | None:
    """Usa la carpeta indicada por código o pide una con el explorador de archivos."""
    explicito = destino_explicito(destino)
    if explicito is not None:
        return explicito
    return pedir_carpeta(parent, titulo)


def describir_ubicacion(ruta: Path) -> str:
    """Texto breve «archivo · carpeta» para los avisos de éxito."""
    carpeta = ruta.parent.name or str(ruta.parent)
    return f"«{ruta.name}» en la carpeta «{carpeta}»"


def mensaje_error(error: BaseException, ruta: Path | None = None) -> str:
    """Traduce una excepción de escritura a un mensaje claro para la persona usuaria."""
    if isinstance(error, PermissionError):
        return (
            "No se pudo escribir el archivo. Cierre el documento si está abierto en otra aplicación "
            "o elija una carpeta con permiso de escritura."
        )
    if isinstance(error, FileNotFoundError):
        return "La carpeta elegida ya no existe. Seleccione otra ubicación."
    if isinstance(error, OSError):
        destino = f" en «{ruta}»" if ruta is not None else ""
        return f"No se pudo guardar el archivo{destino}: {error.strerror or error}."
    return str(error) or error.__class__.__name__

