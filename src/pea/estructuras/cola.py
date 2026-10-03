"""Implementación de la Cola FIFO hecha a mano para ingesta y procesamiento por lotes."""

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from pea.estructuras.nodo import NodoSimple

T = TypeVar("T")


class EstadoTarea(StrEnum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    TERMINADA = "terminada"
    CON_ERROR = "con_error"


@dataclass
class TareaIngesta:
    """Modela una tarea de importación desde URL o archivo CSV."""

    id_tarea: str
    tipo_fuente: str  # 'url_gruplac', 'url_cvlac', 'archivo_csv'
    origen: str
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    mensaje_error: str | None = None
    elementos_procesados: int = 0
    detalles: dict[str, Any] | None = None


class Cola[T]:
    """Cola (FIFO) enlazada manualmente para tareas de procesamiento por lotes."""

    def __init__(self) -> None:
        self.frente_nodo: NodoSimple[T] | None = None
        self.final_nodo: NodoSimple[T] | None = None
        self._tamano: int = 0

    @property
    def tamano(self) -> int:
        return self._tamano

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def __len__(self) -> int:
        return self._tamano

    def encolar(self, dato: T) -> None:
        """Inserta un nuevo elemento al final de la cola en O(1)."""
        nuevo = NodoSimple(dato)
        if self.final_nodo is None:
            self.frente_nodo = nuevo
            self.final_nodo = nuevo
        else:
            self.final_nodo.siguiente = nuevo
            self.final_nodo = nuevo
        self._tamano += 1

    def desencolar(self) -> T:
        """Extrae y retorna el elemento en el frente de la cola en O(1)."""
        if self.frente_nodo is None:
            raise IndexError("No se puede desencolar de una cola vacía")

        nodo = self.frente_nodo
        self.frente_nodo = nodo.siguiente
        if self.frente_nodo is None:
            self.final_nodo = None

        nodo.siguiente = None
        self._tamano -= 1
        return nodo.dato

    def ver_frente(self) -> T | None:
        """Consulta el dato del frente sin extraerlo."""
        return self.frente_nodo.dato if self.frente_nodo is not None else None

    def __iter__(self) -> Iterator[T]:
        actual = self.frente_nodo
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def limpiar(self) -> None:
        """Vacía completamente la cola."""
        actual = self.frente_nodo
        while actual is not None:
            sig = actual.siguiente
            actual.siguiente = None
            actual = sig
        self.frente_nodo = None
        self.final_nodo = None
        self._tamano = 0
