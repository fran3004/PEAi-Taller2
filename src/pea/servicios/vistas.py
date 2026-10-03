"""Modelos de vista (DTO) que los servicios entregan a la interfaz gráfica.

La GUI nunca recibe estructuras internas (ListaDoble, Multilista, Hipercubo5D) ni objetos de red:
solo estos objetos inmutables y tipos simples. Así la capa de presentación queda desacoplada
de las estructuras hechas a mano y de Supabase (AGENTS.md, Arquitectura).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

ANIO_CORTE_MODELO_2024 = 2023


class ModoConexion(StrEnum):
    """Origen de los datos que muestra la aplicación."""

    DESCONECTADO = "desconectado"
    SUPABASE = "supabase"
    DEMOSTRACION = "demostracion"


class ModoFiltroAnios(StrEnum):
    TODOS = "todos"
    ULTIMOS = "ultimos"
    RANGO = "rango"
    MODELO_2024 = "modelo_2024"


@dataclass(frozen=True)
class FiltroAnios:
    """Filtro temporal elegido en la interfaz.

    Diferencia (ver brain/20-Diseno/Hipercubo.md §7):
    - TODOS / ULTIMOS / RANGO son filtros de interfaz, ciegos a la tipología.
    - MODELO_2024 aplica la ventana normativa diferenciada de la convocatoria 2024
      (5 años para la mayoría de tipologías y 10 para libros y patentes, corte 2023).
    """

    modo: ModoFiltroAnios = ModoFiltroAnios.TODOS
    ultimos_n: int = 5
    desde: int | None = None
    hasta: int | None = None

    def resolver(self, anio_actual: int) -> tuple[int | None, int | None, bool]:
        """Devuelve (anio_inicio, anio_fin, usar_ventana_modelo_2024)."""
        if self.modo == ModoFiltroAnios.MODELO_2024:
            return None, None, True
        if self.modo == ModoFiltroAnios.ULTIMOS:
            n = max(1, int(self.ultimos_n))
            return anio_actual - n + 1, anio_actual, False
        if self.modo == ModoFiltroAnios.RANGO:
            desde, hasta = self.desde, self.hasta
            if desde is not None and hasta is not None and desde > hasta:
                desde, hasta = hasta, desde
            return desde, hasta, False
        return None, None, False

    def descripcion(self, anio_actual: int) -> str:
        if self.modo == ModoFiltroAnios.MODELO_2024:
            return "Ventana del Modelo 2024 (5 años; 10 para libros y patentes; corte 2023)"
        inicio, fin, _ = self.resolver(anio_actual)
        if self.modo == ModoFiltroAnios.ULTIMOS:
            return f"Últimos {max(1, int(self.ultimos_n))} años ({inicio}–{fin})"
        if self.modo == ModoFiltroAnios.RANGO:
            return f"Años {inicio if inicio is not None else '…'}–{fin if fin is not None else '…'}"
        return "Todos los años"


@dataclass(frozen=True)
class TablaDatos:
    """Tabla plana lista para mostrarse o exportarse."""

    columnas: tuple[str, ...]
    filas: tuple[tuple[Any, ...], ...]
    claves: tuple[str, ...] = ()

    @property
    def vacia(self) -> bool:
        return len(self.filas) == 0


@dataclass(frozen=True)
class EstadoAplicacion:
    """Fotografía del estado de conexión, revisión y colas para la barra de estado."""

    modo: ModoConexion = ModoConexion.DESCONECTADO
    sin_conexion: bool = False
    correo: str | None = None
    base_url: str | None = None
    revision_local: int | None = None
    revision_remota: int | None = None
    cambio_remoto: bool = False
    operaciones_deshacer: int = 0
    tareas_pendientes: int = 0
    hay_datos: bool = False
    mensaje: str = ""
    historial_deshacer: tuple[str, ...] = field(default_factory=tuple)

    @property
    def escritura_permitida(self) -> bool:
        return self.motivo_bloqueo is None

    @property
    def motivo_bloqueo(self) -> str | None:
        if self.modo == ModoConexion.DESCONECTADO:
            return "No hay conexión con PEA-i. Conéctese a la base de datos o cargue los datos de demostración."
        if self.sin_conexion:
            return "Sin conexión con la base de datos: la escritura está bloqueada hasta reconectar."
        if self.cambio_remoto:
            return "La base de datos cambió. Recargue antes de guardar cambios."
        return None

    @property
    def descripcion_modo(self) -> str:
        if self.modo == ModoConexion.SUPABASE:
            return "Sin conexión" if self.sin_conexion else "Conectado"
        if self.modo == ModoConexion.DEMOSTRACION:
            return "Datos de demostración (no se guardan)"
        return "Desconectado"

    @property
    def revision(self) -> int | None:
        return self.revision_local

    @property
    def modo_conexion(self) -> ModoConexion:
        return self.modo

    @property
    def operaciones_en_pila_deshacer(self) -> int:
        return self.operaciones_deshacer

    @property
    def elementos_en_cola(self) -> int:
        return self.tareas_pendientes

    @property
    def total_grupos(self) -> int:
        return 0

    @property
    def total_investigadores(self) -> int:
        return 0

    @property
    def total_productos(self) -> int:
        return 0

