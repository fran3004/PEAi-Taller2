"""Entidad de dominio Integrante de Grupo (membresía)."""

from pydantic import BaseModel, ConfigDict, Field


class IntegranteGrupo(BaseModel):
    """Vinculación temporal entre un Investigador y un Grupo de Investigación."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    grupo_id: int | None = None
    codigo_gruplac: str = Field(..., description="Código GrupLAC del grupo al que pertenece")
    investigador_id: int | None = None
    codigo_rh: str = Field(..., description="Código CvLAC del investigador vinculado")
    rol: str = "Investigador"  # Lider, Investigador, Estudiante
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
    activo: bool = True
    es_ejemplo: bool = False
