"""Modelos Pydantic v2 para validación, estructuración y transferencia de datos en ingesta."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetadatosOrigen(BaseModel):
    """Metadatos de procedencia y trazabilidad de una fuente ingerida."""

    model_config = ConfigDict(extra="ignore")

    url: str
    fecha_descarga: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    sha256: str
    metodo: str = "requests + bs4 + lxml"
    encoding_utilizada: str | None = None
    codigo_http: int | None = 200


class IntegranteIngesta(BaseModel):
    """Integrante extraído de la tabla de integrantes de GrupLAC."""

    model_config = ConfigDict(extra="ignore")

    nombre: str
    vinculacion: str
    horas_dedicacion: str | None = None
    inicio_vinculacion: str | None = None
    fin_vinculacion: str | None = None


class LineaIngesta(BaseModel):
    """Línea de investigación declarada por un grupo o investigador."""

    model_config = ConfigDict(extra="ignore")

    nombre: str
    activa: bool = True


class InstitucionIngesta(BaseModel):
    """Institución de aval o vinculación institucional."""

    model_config = ConfigDict(extra="ignore")

    nombre: str
    tipo: str | None = None


class FormacionIngesta(BaseModel):
    """Registro de formación académica extraído de CvLAC."""

    model_config = ConfigDict(extra="ignore")

    nivel: str  # Doctorado, Maestría, Especialización, Pregrado
    titulo: str
    institucion: str
    periodo: str | None = None


class ProductoIngesta(BaseModel):
    """Producto científico o tecnológico extraído de GrupLAC o CvLAC."""

    model_config = ConfigDict(extra="ignore")

    tipo: str  # Articulo, Libro, Capitulo, Software, TrabajoDirigido, Proyecto
    tipo_mayor: str = "GNC"  # GNC, DTI, ASC, FRH
    subtipo: str | None = None
    titulo: str
    ano: int | None = None
    mes: int | None = None
    autores: str | None = None
    detalles: str | None = None
    doi_o_isbn: str | None = None
    categoria_declarada: str | None = None
    institucion: str | None = None
    persona_orientada: str | None = None


class GrupoIngesta(BaseModel):
    """Entidad Grupo de Investigación validada desde GrupLAC."""

    model_config = ConfigDict(extra="ignore")

    codigo_gruplac: str
    nombre_grupo: str | None = None
    ano_mes_formacion: str | None = None
    departamento_ciudad: str | None = None
    lider: str | None = None
    certificacion: str | None = None
    pagina_web: str | None = None
    email: str | None = None
    clasificacion: str | None = None
    area_conocimiento: str | None = None
    programa_nacional: str | None = None
    instituciones: list[InstitucionIngesta] = Field(default_factory=list)
    lineas_investigacion: list[LineaIngesta] = Field(default_factory=list)
    integrantes: list[IntegranteIngesta] = Field(default_factory=list)
    articulos: list[ProductoIngesta] = Field(default_factory=list)
    libros: list[ProductoIngesta] = Field(default_factory=list)
    capitulos: list[ProductoIngesta] = Field(default_factory=list)
    softwares: list[ProductoIngesta] = Field(default_factory=list)
    trabajos_dirigidos: list[ProductoIngesta] = Field(default_factory=list)
    proyectos: list[ProductoIngesta] = Field(default_factory=list)
    origen: MetadatosOrigen


class InvestigadorIngesta(BaseModel):
    """Entidad Investigador validada desde CvLAC."""

    model_config = ConfigDict(extra="ignore")

    codigo_rh: str
    nombre_completo: str | None = None
    nombre_citaciones: str | None = None
    nacionalidad: str | None = "Colombiana"
    sexo: str | None = None
    categoria_declarada: str | None = None
    par_evaluador: bool = False
    areas_actuacion: list[str] = Field(default_factory=list)
    lineas_investigacion: list[str] = Field(default_factory=list)
    formacion: list[FormacionIngesta] = Field(default_factory=list)
    articulos: list[ProductoIngesta] = Field(default_factory=list)
    libros: list[ProductoIngesta] = Field(default_factory=list)
    capitulos: list[ProductoIngesta] = Field(default_factory=list)
    softwares: list[ProductoIngesta] = Field(default_factory=list)
    trabajos_dirigidos: list[ProductoIngesta] = Field(default_factory=list)
    proyectos: list[ProductoIngesta] = Field(default_factory=list)
    origen: MetadatosOrigen


# =============================================================================
# MODELOS PARA CSV CANÓNICOS
# =============================================================================

class FilaGrupoCSV(BaseModel):
    """Estructura de fila esperada en grupos.csv."""

    model_config = ConfigDict(extra="ignore")

    codigo_gruplac: str
    nombre: str
    categoria: str | None = None
    lider: str | None = None
    institucion_principal: str = "Universidad Popular del Cesar"
    pais: str = "Colombia"
    departamento_ciudad: str | None = None
    gran_area_ocde: str | None = None
    area_ocde: str | None = None
    activo: bool = True
    es_ejemplo: bool = False


class FilaInvestigadorCSV(BaseModel):
    """Estructura de fila esperada en investigadores.csv."""

    model_config = ConfigDict(extra="ignore")

    codigo_rh: str
    nombre_completo: str
    categoria: str | None = None
    formacion_academica: str | None = None
    nacionalidad: str = "Colombiana"
    nombre_en_citas: str | None = None
    documento_identidad: str | None = None
    sexo: str | None = None
    activo: bool = True
    es_ejemplo: bool = False


class FilaProductoCSV(BaseModel):
    """Estructura de fila esperada en productos.csv."""

    model_config = ConfigDict(extra="ignore")

    codigo_identificador: str
    titulo: str
    tipo_mayor: str = "GNC"
    subtipo: str | None = None
    ano: int
    mes: int | None = None
    pais: str | None = None
    estado_validacion: str = "No avalado"
    grupo_codigo: str | None = None
    activo: bool = True
    es_ejemplo: bool = False


class FilaAutorCSV(BaseModel):
    """Estructura de fila esperada en autores.csv."""

    model_config = ConfigDict(extra="ignore")

    producto_codigo: str
    investigador_codigo: str
    orden_autoria: int = 1


# =============================================================================
# MODELOS PARA PDF Y REPORTES
# =============================================================================

class PaginaPDF(BaseModel):
    """Resultado de extracción de una página individual de un PDF."""

    model_config = ConfigDict(extra="ignore")

    numero: int
    longitud_texto: int
    tablas_encontradas: int
    tiene_imagenes: bool = False
    es_escaneada_sospechosa: bool = False
    texto: str = ""
    tablas: list[list[list[str | None]]] = Field(default_factory=list)


class DocumentoPDF(BaseModel):
    """Resultado de extracción global de un archivo PDF con pdfplumber."""

    model_config = ConfigDict(extra="ignore")

    ruta_archivo: str
    sha256: str
    total_paginas: int
    total_caracteres: int
    total_tablas: int
    es_escaneado: bool = False
    advertencias: list[str] = Field(default_factory=list)
    paginas: list[PaginaPDF] = Field(default_factory=list)


class InformeIngesta(BaseModel):
    """Informe consolidado de una operación de ingesta (URL, PDF o CSV)."""

    model_config = ConfigDict(extra="ignore")

    origen: str
    tipo_fuente: str  # 'url_gruplac', 'url_cvlac', 'archivo_csv', 'archivo_pdf'
    fecha: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    exito: bool = True
    mensaje: str = ""
    grupos_procesados: int = 0
    investigadores_procesados: int = 0
    productos_procesados: int = 0
    autores_procesados: int = 0
    filas_erroneas: list[dict[str, Any]] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    archivos_generados: dict[str, str] = Field(default_factory=dict)
