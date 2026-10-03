"""Entidad de dominio Proyecto de Investigación (según SPEC y esquema relacional)."""

from pydantic import BaseModel, ConfigDict, Field


class Proyecto(BaseModel):
    """Proyecto de I+D ejecutado o auspiciado por un grupo de investigación."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    grupo_id: int | None = None
    codigo_gruplac: str = Field(..., description="Código del grupo ejecutor")
    codigo_identificador: str | None = None
    nombre: str = Field(..., description="Nombre del proyecto de investigación")
    tipo: str | None = None  # Investigacion y desarrollo, Extension, etc.
    ano_inicio: int | None = None
    ano_fin: int | None = None
    estado: str | None = None  # En ejecucion, Finalizado
    activo: bool = True
    es_ejemplo: bool = False
