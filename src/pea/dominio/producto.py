"""Entidad de dominio Producto de Investigación."""

import datetime
import hashlib
import unicodedata
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ANO_MINIMO_BASE: int = 1970
ANO_MAXIMO_BASE: int = 2100
ANO_MINIMO_PRODUCTO: int = ANO_MINIMO_BASE
ANO_MAXIMO_PRODUCTO: int = ANO_MAXIMO_BASE


def normalizar_cita(cita: str | None) -> str:
    """Normaliza una cita bibliográfica a texto Unicode NFC, minúsculas y espacios colapsados."""
    if not cita:
        return ""
    colapsado = " ".join(cita.split()).strip()
    nfc = unicodedata.normalize("NFC", colapsado)
    return nfc.lower()


def calcular_hash_cita(cita: str | None) -> str:
    """Calcula los primeros 12 caracteres hexadecimales del SHA-1 de la cita normalizada."""
    norm = normalizar_cita(cita)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


def generar_codigo_producto_cvlac(
    codigo_rh: str,
    cita: str | None = None,
    ocurrencia: int = 1,
    titulo: str | None = None,
) -> str:
    """Genera el código identificador estable para un producto CvLAC.

    Formato: PROD-CVLAC-{codigo_rh}-{hash_12}[-{ocurrencia}]
    """
    rh_limpio = (codigo_rh or "").strip()
    texto_a_hashear = cita if (cita and str(cita).strip()) else (titulo or "")
    h = calcular_hash_cita(texto_a_hashear)
    base = f"PROD-CVLAC-{rh_limpio}-{h}"
    if ocurrencia > 1:
        return f"{base}-{ocurrencia}"
    return base


def validar_ano_producto(ano: int, anio_actual: int | None = None) -> int:
    """Valida el año de producción conforme al requisito RF-04."""
    if type(ano) is not int:
        raise ValueError("El año debe ser un número entero.")

    limite_superior = datetime.date.today().year if anio_actual is None else anio_actual
    if not ANO_MINIMO_BASE <= ano <= limite_superior:
        raise ValueError(f"El año debe estar entre {ANO_MINIMO_BASE} y {limite_superior}.")
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

    @field_validator("ano", mode="before")
    @classmethod
    def _validar_ano(cls, v: Any) -> int:
        if isinstance(v, bool):
            raise ValueError("El año debe ser un número entero.")
        if isinstance(v, float) and not v.is_integer():
            raise ValueError("El año debe ser un número entero.")
        try:
            valor = int(v)
        except (TypeError, ValueError) as err:
            raise ValueError("El año debe ser un número entero.") from err

        if valor < ANO_MINIMO_BASE or valor > ANO_MAXIMO_BASE:
            raise ValueError(
                f"El año debe estar entre {ANO_MINIMO_BASE} y {ANO_MAXIMO_BASE}."
            )
        return valor

    def desactivar(self) -> None:
        self.activo = False

    def activar(self) -> None:
        self.activo = True
