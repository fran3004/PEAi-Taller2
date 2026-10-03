"""Entidad de dominio Investigador."""

from pydantic import BaseModel, ConfigDict, Field


class Investigador(BaseModel):
    """Modelo conceptual de Investigador según Minciencias y CvLAC."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    codigo_rh: str = Field(..., description="Código único de currículo CvLAC")
    nombre_completo: str = Field(..., description="Nombre y apellidos del investigador")
    nombre_en_citas: str | None = None
    documento_identidad: str | None = None
    nacionalidad: str = "Colombiana"
    sexo: str | None = None
    categoria: str | None = None  # Emerito, Senior, Asociado, Junior, Sin categoria
    formacion_academica: str | None = None  # Doctorado, Maestria, Especializacion, Pregrado
    activo: bool = True
    es_ejemplo: bool = False

    def desactivar(self) -> None:
        self.activo = False

    def activar(self) -> None:
        self.activo = True
