"""Entidad de dominio Producto de Investigación."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Producto(BaseModel):
    """Resultado formal de CTeI clasificado bajo las 4 tipologías mayores de Minciencias 2024."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    codigo_identificador: str = Field(..., description="Código identificador único del producto")
    titulo: str = Field(..., description="Título del producto científico o tecnológico")
    tipo_mayor: str = Field(..., description="Tipología mayor: GNC, DTI, ASC o FRH")
    subtipo: str | None = None
    ano: int = Field(..., description="Año de publicación u obtención")
    mes: int | None = None
    pais: str | None = None
    estado_validacion: str = "No avalado"  # Avalado, Con soporte, No avalado
    detalles: dict[str, Any] = Field(default_factory=dict)
    activo: bool = True
    es_ejemplo: bool = False

    def desactivar(self) -> None:
        self.activo = False

    def activar(self) -> None:
        self.activo = True
