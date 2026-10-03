"""Módulo de ingesta de datos para PEA-i (URL, PDF y CSV)."""

from pea.ingesta.extractor_pdf import ExtractorPDF, ResultadoPDF
from pea.ingesta.extractor_url import ExtractorURL
from pea.ingesta.lector_csv import LectorCSV
from pea.ingesta.modelos import (
    DocumentoPDF,
    FilaAutorCSV,
    FilaGrupoCSV,
    FilaInvestigadorCSV,
    FilaProductoCSV,
    GrupoIngesta,
    InformeIngesta,
    InvestigadorIngesta,
    MetadatosOrigen,
    ProductoIngesta,
)
from pea.ingesta.servicio_ingesta import ServicioIngesta

__all__ = [
    "DocumentoPDF",
    "ExtractorPDF",
    "ExtractorURL",
    "FilaAutorCSV",
    "FilaGrupoCSV",
    "FilaInvestigadorCSV",
    "FilaProductoCSV",
    "GrupoIngesta",
    "InformeIngesta",
    "InvestigadorIngesta",
    "LectorCSV",
    "MetadatosOrigen",
    "ProductoIngesta",
    "ResultadoPDF",
    "ServicioIngesta",
]
