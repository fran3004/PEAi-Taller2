"""
tools/fuentes/modelos_scienti.py
Modelos Pydantic v2 para validación y tipificación de datos extraídos
desde páginas GrupLAC y CvLAC (SCIENTI - Minciencias) para PEA-i.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class MetadatosOrigen(BaseModel):
    url: str
    fecha_descarga: str
    sha256: str
    metodo: str = "requests + bs4 + lxml"


class IntegranteGrupo(BaseModel):
    nombre: str
    vinculacion: str
    horas_dedicacion: Optional[str] = None
    inicio_vinculacion: Optional[str] = None
    fin_vinculacion: Optional[str] = None


class LineaInvestigacion(BaseModel):
    nombre: str
    activa: bool = True


class InstitucionAval(BaseModel):
    nombre: str
    tipo: Optional[str] = None


class ProductoBibliografico(BaseModel):
    tipo: str  # Articulo, Libro, Capitulo
    titulo: str
    ano: Optional[int] = None
    autores: Optional[str] = None
    detalles: Optional[str] = None
    doi_o_isbn: Optional[str] = None
    categoria_declarada: Optional[str] = None


class ProductoSoftware(BaseModel):
    titulo: str
    ano: Optional[int] = None
    autores: Optional[str] = None
    tipo: str = "Software"
    disponibilidad: Optional[str] = None
    plataforma: Optional[str] = None
    ambiente: Optional[str] = None


class TrabajoDirigido(BaseModel):
    tipo_trabajo: str
    titulo: str
    ano: Optional[int] = None
    institucion: Optional[str] = None
    persona_orientada: Optional[str] = None
    rol: Optional[str] = None


class ProyectoInvestigacion(BaseModel):
    titulo: str
    tipo: Optional[str] = None
    periodo: Optional[str] = None
    institucion: Optional[str] = None


class GrupoGrupLAC(BaseModel):
    codigo_gruplac: str
    nombre_grupo: Optional[str] = None
    ano_mes_formacion: Optional[str] = None
    departamento_ciudad: Optional[str] = None
    lider: Optional[str] = None
    certificacion: Optional[str] = None
    pagina_web: Optional[str] = None
    email: Optional[str] = None
    clasificacion: Optional[str] = None
    area_conocimiento: Optional[str] = None
    programa_nacional: Optional[str] = None
    instituciones: List[InstitucionAval] = Field(default_factory=list)
    lineas_investigacion: List[LineaInvestigacion] = Field(default_factory=list)
    integrantes: List[IntegranteGrupo] = Field(default_factory=list)
    articulos: List[ProductoBibliografico] = Field(default_factory=list)
    libros: List[ProductoBibliografico] = Field(default_factory=list)
    capitulos: List[ProductoBibliografico] = Field(default_factory=list)
    softwares: List[ProductoSoftware] = Field(default_factory=list)
    trabajos_dirigidos: List[TrabajoDirigido] = Field(default_factory=list)
    proyectos: List[ProyectoInvestigacion] = Field(default_factory=list)
    origen: MetadatosOrigen


class FormacionAcademica(BaseModel):
    nivel: str
    titulo: str
    institucion: str
    periodo: Optional[str] = None


class InvestigadorCvLAC(BaseModel):
    codigo_rh: str
    nombre_completo: Optional[str] = None
    nombre_citaciones: Optional[str] = None
    nacionalidad: Optional[str] = None
    sexo: Optional[str] = None
    categoria_declarada: Optional[str] = None
    par_evaluador: bool = False
    areas_actuacion: List[str] = Field(default_factory=list)
    lineas_investigacion: List[str] = Field(default_factory=list)
    formacion: List[FormacionAcademica] = Field(default_factory=list)
    articulos: List[ProductoBibliografico] = Field(default_factory=list)
    capitulos: List[ProductoBibliografico] = Field(default_factory=list)
    softwares: List[ProductoSoftware] = Field(default_factory=list)
    trabajos_dirigidos: List[TrabajoDirigido] = Field(default_factory=list)
    proyectos: List[ProyectoInvestigacion] = Field(default_factory=list)
    origen: MetadatosOrigen
