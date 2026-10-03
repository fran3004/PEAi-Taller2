"""Entidad de dominio Grupo de Investigación."""

from pydantic import BaseModel, ConfigDict, Field


class Grupo(BaseModel):
    """Modelo conceptual de Grupo de Investigación según Minciencias y GrupLAC."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    codigo_gruplac: str = Field(..., description="Código oficial GrupLAC único")
    nombre: str = Field(..., description="Nombre del grupo de investigación")
    fecha_creacion: str | None = None
    pais: str = "Colombia"
    departamento_ciudad: str | None = None
    lider: str | None = None
    institucion_principal: str = "Universidad Popular del Cesar"
    gran_area_ocde: str | None = None
    area_ocde: str | None = None
    categoria: str | None = None  # A1, A, B, C, Reconocido
    activo: bool = True
    es_ejemplo: bool = False

    def desactivar(self) -> None:
        self.activo = False

    def activar(self) -> None:
        self.activo = True
