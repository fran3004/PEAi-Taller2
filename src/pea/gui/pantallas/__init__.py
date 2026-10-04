"""Paquete de pantallas de PEA-i."""

from __future__ import annotations

from pea.gui.pantallas.acerca import PantallaAcerca
from pea.gui.pantallas.configuracion import PantallaConfiguracion
from pea.gui.pantallas.grupos import FichaGrupo, PantallaGrupos
from pea.gui.pantallas.importar import PantallaImportar, ZonaSoltarArchivo
from pea.gui.pantallas.inicio import PantallaInicio
from pea.gui.pantallas.investigadores import PantallaInvestigadores
from pea.gui.pantallas.productos import FichaProducto, PantallaProductos
from pea.gui.pantallas.redes import PantallaRedes

__all__ = [
    "FichaGrupo",
    "FichaProducto",
    "PantallaAcerca",
    "PantallaConfiguracion",
    "PantallaGrupos",
    "PantallaImportar",
    "PantallaInicio",
    "PantallaInvestigadores",
    "PantallaProductos",
    "PantallaRedes",
    "ZonaSoltarArchivo",
]
