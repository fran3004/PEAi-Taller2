"""Entidad de dominio Producto de Investigación."""

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def validar_ano_producto(ano: int, anio_actual: int | None = None) -> int:
    """Valida el año de producción conforme al requisito RF-04."""
    if type(ano) is not int:
        raise ValueError("El año debe ser un número entero.")

    limite_superior = datetime.date.today().year if anio_actual is None else anio_actual
    if not 1970 <= ano <= limite_superior:
        raise ValueError(f"El año debe estar entre 1970 y {limite_superior}.")
    return ano


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
