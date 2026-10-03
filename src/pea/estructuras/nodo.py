"""Definición de nodos fundamentales para estructuras de datos hechas a mano."""

from typing import TypeVar

T = TypeVar("T")


class NodoDoble[T]:
    """Nodo con enlace doble (anterior y siguiente) para ListaDoble."""

    def __init__(self, dato: T) -> None:
        self.dato: T = dato
        self.anterior: NodoDoble[T] | None = None
        self.siguiente: NodoDoble[T] | None = None

    def __repr__(self) -> str:
        return f"NodoDoble({self.dato!r})"


class NodoSimple[T]:
    """Nodo con enlace simple (siguiente) para Pila y Cola."""

    def __init__(self, dato: T) -> None:
        self.dato: T = dato
        self.siguiente: NodoSimple[T] | None = None

    def __repr__(self) -> str:
        return f"NodoSimple({self.dato!r})"
