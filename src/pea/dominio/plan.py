"""Entidad de dominio Plan de Trabajo / Estratégico."""

from pydantic import BaseModel, ConfigDict, Field


class Plan(BaseModel):
    """Plan estratégico o de trabajo de un grupo de investigación."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    codigo_gruplac: str = Field(..., description="Código del grupo formulador")
    ano_inicio: int
    ano_fin: int
    descripcion: str
    estado: str = "En ejecucion"  # En ejecucion, Cumplido, Cancelado
    activo: bool = True
    es_ejemplo: bool = False
