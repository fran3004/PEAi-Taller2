"""Componentes reutilizables de la interfaz gráfica PySide6 de PEA-i (Sección 8)."""

from __future__ import annotations

from pea.gui.componentes.animacion import animaciones_habilitadas, duracion_efectiva
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.campo_busqueda import CampoBusqueda
from pea.gui.componentes.estado_vacio import Esqueleto, EstadoVacio
from pea.gui.componentes.ficha_lateral import FichaLateral
from pea.gui.componentes.filtro_anios import (
    BarraFiltroAnios,
    ChipVentana,
    PopoverFiltroAnios,
)
from pea.gui.componentes.pildora import Pildora
from pea.gui.componentes.popover_historial import PopoverHistorial
from pea.gui.componentes.selector_segmentado import SelectorSegmentado
from pea.gui.componentes.tabla import (
    AvatarNombreDelegate,
    EnlaceDelegate,
    NumeroDelegate,
    PildoraDelegate,
    TablaEstilizada,
)
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI, Minigrafico, TarjetaKPI
from pea.gui.componentes.toast import GestorAvisos, Toast

__all__ = [
    "Avatar",
    "AvatarNombreDelegate",
    "BarraFiltroAnios",
    "CampoBusqueda",
    "ChipVentana",
    "EnlaceDelegate",
    "Esqueleto",
    "EstadoVacio",
    "FichaKPI",
    "FichaLateral",
    "GestorAvisos",
    "Minigrafico",
    "NumeroDelegate",
    "Pildora",
    "PildoraDelegate",
    "PopoverFiltroAnios",
    "PopoverHistorial",
    "SelectorSegmentado",
    "TablaEstilizada",
    "Tarjeta",
    "TarjetaKPI",
    "Toast",
    "animaciones_habilitadas",
    "duracion_efectiva",
]

