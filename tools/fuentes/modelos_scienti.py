"""
tools/fuentes/modelos_scienti.py
Modelos Pydantic v2 para validación y tipificación de datos extraídos
desde páginas GrupLAC y CvLAC (SCIENTI - Minciencias) para PEA-i.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MetadatosOrigen(BaseModel):
    url: str
    fecha_descarga: str
    sha256: str
    metodo: str = "requests + bs4 + lxml"


class IntegranteGrupo(BaseModel):
    nombre: str
    vinculacion: str
    horas_dedicacion: str | None = None
    inicio_vinculacion: str | None = None
    fin_vinculacion: str | None = None


class LineaInvestigacion(BaseModel):
    nombre: str
    activa: bool = True


class InstitucionAval(BaseModel):
    nombre: str
    tipo: str | None = None


class ProductoBibliografico(BaseModel):
    tipo: str  # Articulo, Libro, Capitulo
    titulo: str
    ano: int | None = None
    autores: str | None = None
    detalles: str | None = None
    doi_o_isbn: str | None = None
    categoria_declarada: str | None = None


class ProductoSoftware(BaseModel):
    titulo: str
    ano: int | None = None
    autores: str | None = None
    tipo: str = "Software"
    disponibilidad: str | None = None
    plataforma: str | None = None
    ambiente: str | None = None


class TrabajoDirigido(BaseModel):
    tipo_trabajo: str
    titulo: str
    ano: int | None = None
    institucion: str | None = None
    persona_orientada: str | None = None
    rol: str | None = None


class ProyectoInvestigacion(BaseModel):
    titulo: str
    tipo: str | None = None
    periodo: str | None = None
    institucion: str | None = None


class GrupoGrupLAC(BaseModel):
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
    instituciones: list[InstitucionAval] = Field(default_factory=list)
    lineas_investigacion: list[LineaInvestigacion] = Field(default_factory=list)
    integrantes: list[IntegranteGrupo] = Field(default_factory=list)
    articulos: list[ProductoBibliografico] = Field(default_factory=list)
    libros: list[ProductoBibliografico] = Field(default_factory=list)
    capitulos: list[ProductoBibliografico] = Field(default_factory=list)
    softwares: list[ProductoSoftware] = Field(default_factory=list)
    trabajos_dirigidos: list[TrabajoDirigido] = Field(default_factory=list)
    proyectos: list[ProyectoInvestigacion] = Field(default_factory=list)
    origen: MetadatosOrigen


class FormacionAcademica(BaseModel):
    nivel: str
    titulo: str
    institucion: str
    periodo: str | None = None


class InvestigadorCvLAC(BaseModel):
    codigo_rh: str
    nombre_completo: str | None = None
    nombre_citaciones: str | None = None
    nacionalidad: str | None = None
    sexo: str | None = None
    categoria_declarada: str | None = None
    par_evaluador: bool = False
    areas_actuacion: list[str] = Field(default_factory=list)
    lineas_investigacion: list[str] = Field(default_factory=list)
    formacion: list[FormacionAcademica] = Field(default_factory=list)
    articulos: list[ProductoBibliografico] = Field(default_factory=list)
    capitulos: list[ProductoBibliografico] = Field(default_factory=list)
    softwares: list[ProductoSoftware] = Field(default_factory=list)
    trabajos_dirigidos: list[TrabajoDirigido] = Field(default_factory=list)
    proyectos: list[ProyectoInvestigacion] = Field(default_factory=list)
    origen: MetadatosOrigen
