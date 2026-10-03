"""Entidades del modelo de dominio de PEA-i."""

from pea.dominio.grupo import Grupo
from pea.dominio.integrante import IntegranteGrupo
from pea.dominio.investigador import Investigador
from pea.dominio.plan import Plan
from pea.dominio.producto import Producto
from pea.dominio.proyecto import Proyecto

__all__ = [
    "Grupo",
    "IntegranteGrupo",
    "Investigador",
    "Plan",
    "Producto",
    "Proyecto",
]
