"""Implementación de la Pila LIFO hecha a mano para el mecanismo de Deshacer (Undo)."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pea.estructuras.nodo import NodoSimple

T = TypeVar("T")


@dataclass
class ComandoInverso:
    """Encapsula la acción y el estado anterior necesario para revertir una mutación."""

    tipo_operacion: str  # 'crear', 'editar', 'desactivar', 'activar', 'eliminar'
    tipo_entidad: str  # 'grupo', 'investigador', 'producto', 'integrante'
    identificador: str  # clave natural o id
    datos_reversion: dict[str, Any] = field(default_factory=dict)
    descripcion: str = ""


class Pila[T]:
    """Pila (LIFO) enlazada manualmente con límite de capacidad para historial de deshacer."""

    def __init__(self, capacidad_maxima: int = 50) -> None:
        self.tope_nodo: NodoSimple[T] | None = None
        self._tamano: int = 0
        self.capacidad_maxima: int = capacidad_maxima

    @property
    def tamano(self) -> int:
        return self._tamano

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def __len__(self) -> int:
        return self._tamano

    def apilar(self, dato: T) -> None:
        """Inserta un nuevo elemento en la cima de la pila."""
        if self._tamano >= self.capacidad_maxima:
            self._descartar_fondo()

        nuevo = NodoSimple(dato)
        nuevo.siguiente = self.tope_nodo
        self.tope_nodo = nuevo
        self._tamano += 1

    def _descartar_fondo(self) -> None:
        """Descarta el elemento en el fondo de la pila para respetar la capacidad máxima."""
        if self.tope_nodo is None or self.tope_nodo.siguiente is None:
            self.tope_nodo = None
            self._tamano = 0
            return

        anterior = self.tope_nodo
        actual = self.tope_nodo.siguiente
        while actual.siguiente is not None:
            anterior = actual
            actual = actual.siguiente

        anterior.siguiente = None
        self._tamano -= 1

    def desapilar(self) -> T:
        """Extrae y retorna el elemento en la cima de la pila."""
        if self.tope_nodo is None:
            raise IndexError("No se puede desapilar de una pila vacía")

        nodo = self.tope_nodo
        self.tope_nodo = nodo.siguiente
        nodo.siguiente = None
        self._tamano -= 1
        return nodo.dato

    def ver_tope(self) -> T | None:
        """Consulta el dato en la cima sin extraerlo."""
        return self.tope_nodo.dato if self.tope_nodo is not None else None

    def __iter__(self) -> Iterator[T]:
        actual = self.tope_nodo
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def limpiar(self) -> None:
        """Vacía completamente la pila."""
        actual = self.tope_nodo
        while actual is not None:
            sig = actual.siguiente
            actual.siguiente = None
            actual = sig
        self.tope_nodo = None
        self._tamano = 0
