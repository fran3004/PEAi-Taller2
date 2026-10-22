"""Entidad de dominio Grupo de Investigación."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

INSTITUCION_SIN_INFORMACION = "Sin institución informada"


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
    institucion_principal: str = INSTITUCION_SIN_INFORMACION
    gran_area_ocde: str | None = None
    area_ocde: str | None = None
    categoria: str | None = None  # A1, A, B, C, Reconocido
    detalles: dict[str, Any] = Field(default_factory=dict)
    activo: bool = True
    es_ejemplo: bool = False

    def desactivar(self) -> None:
        self.activo = False

    def activar(self) -> None:
        self.activo = True
