"""Utilidades de formateo numérico, porcentajes y textos institucionales para la GUI de PEA-i.

Asegura consistencia cultural colombiana (QLocale es_CO: miles con punto y decimales con coma)
y correspondencia con el Modelo de Medición de Minciencias 2024.
"""

from __future__ import annotations

import re
from typing import Final

from PySide6.QtCore import QLocale

LOCALE_COLOMBIA: Final[QLocale] = QLocale(QLocale.Language.Spanish, QLocale.Country.Colombia)

NOMBRES_TIPOLOGIAS: Final[dict[str, str]] = {
    "GNC": "Generación de nuevo conocimiento",
    "DTI": "Desarrollo tecnológico e innovación",
    "ASC": "Apropiación social del conocimiento",
    "FRH": "Formación de recurso humano",
}

DESCRIPCIONES_TIPOLOGIAS: Final[dict[str, str]] = {
    "GNC": "Artículos científicos, libros de investigación, capítulos y patentes con nuevo conocimiento.",
    "DTI": "Productos tecnológicos, secretos empresariales, variedades vegetales y software con registro.",
    "ASC": "Procesos y estrategias de apropiación social, divulgación pública y circulación de saberes.",
    "FRH": "Tesis doctorales, de maestría y trabajos de grado guiados para formación investigativa.",
}

NOMBRES_VALIDACIONES: Final[dict[str, str]] = {
    "Avalado": "Avalado en convocatoria",
    "Con soporte": "Con soporte verificado",
    "No avalado": "No avalado",
}

NOMBRES_CATEGORIAS_INVESTIGADOR: Final[dict[str, str]] = {
    "Emérito": "Investigador Emérito",
    "Senior": "Investigador Senior",
    "Asociado": "Investigador Asociado",
    "Junior": "Investigador Junior",
    "Sin categoría": "Sin categoría asignada",
}


def formatear_entero(valor: int | float | None, sustituto_nulo: str = "0") -> str:
    """Formatea un número entero con separador de miles usando la convención colombiana (punto).

    Ejemplo: 1234567 -> '1.234.567'
    """
    if valor is None:
        return sustituto_nulo
    val_int = int(round(valor))
    return LOCALE_COLOMBIA.toString(val_int)


def formatear_decimal(valor: float | int | None, decimales: int = 2, sustituto_nulo: str = "0,00") -> str:
    """Formatea un número decimal con coma y separador de miles con punto.

    Ejemplo: 1234.56 -> '1.234,56'
    """
    if valor is None:
        return sustituto_nulo
    return LOCALE_COLOMBIA.toString(float(valor), "f", decimales)


def formatear_porcentaje(
    valor: float | int | None,
    decimales: int = 1,
    incluir_simbolo: bool = True,
    sustituto_nulo: str = "0,0 %",
) -> str:
    """Formatea un valor porcentual con coma decimal.

    Ejemplo: 25.5 -> '25,5 %'
    """
    if valor is None:
        return sustituto_nulo if incluir_simbolo else sustituto_nulo.replace("%", "").strip()
    cadena = LOCALE_COLOMBIA.toString(float(valor), "f", decimales)
    return f"{cadena} %" if incluir_simbolo else cadena


def iniciales_nombre(nombre: str | None, max_letras: int = 2) -> str:
    """Extrae las iniciales en mayúscula de un nombre de persona o grupo para avatares.

    Ignora signos de puntuación y conectores menores cuando es posible.
    Ejemplos:
        'Juan Carlos Pérez' -> 'JP'
        'Sistemas Inteligentes' -> 'SI'
        'PEA-i' -> 'PE'
    """
    if not nombre or not nombre.strip():
        return "--"

    # Limpiar y separar palabras
    limpio = re.sub(r"[^\w\s]", " ", nombre.strip())
    palabras = [p for p in limpio.split() if p]

    if not palabras:
        return "--"

    if len(palabras) == 1:
        return palabras[0][:max_letras].upper()

    return "".join(p[0] for p in palabras[:max_letras]).upper()


def nombre_tipologia(codigo: str | None) -> str:
    """Devuelve el nombre completo oficial de una tipología según el Modelo 2024."""
    if not codigo:
        return "Desconocida"
    return NOMBRES_TIPOLOGIAS.get(codigo.strip().upper(), codigo.strip())


def descripcion_tipologia(codigo: str | None) -> str:
    """Devuelve la descripción breve del propósito de una tipología."""
    if not codigo:
        return ""
    return DESCRIPCIONES_TIPOLOGIAS.get(codigo.strip().upper(), "")


def nombre_validacion(codigo: str | None) -> str:
    """Devuelve el nombre descriptivo del estado de validación."""
    if not codigo:
        return "Sin validación"
    return NOMBRES_VALIDACIONES.get(codigo.strip(), codigo.strip())


def nombre_categoria_investigador(categoria: str | None) -> str:
    """Devuelve el nombre completo de la categoría de investigador Minciencias."""
    if not categoria or not categoria.strip():
        return NOMBRES_CATEGORIAS_INVESTIGADOR["Sin categoría"]
    return NOMBRES_CATEGORIAS_INVESTIGADOR.get(categoria.strip(), categoria.strip())
