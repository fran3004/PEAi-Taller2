"""Implementación manual de Lista Doblemente Enlazada."""

from collections.abc import Callable, Iterator
from typing import TypeVar

from pea.estructuras.nodo import NodoDoble

T = TypeVar("T")


class ListaDoble[T]:
    """Lista doblemente enlazada con operaciones en extremos en tiempo O(1)."""

    def __init__(self) -> None:
        self.cabeza: NodoDoble[T] | None = None
        self.cola: NodoDoble[T] | None = None
        self._tamano: int = 0

    @property
    def tamano(self) -> int:
        return self._tamano

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def __len__(self) -> int:
        return self._tamano

    def __iter__(self) -> Iterator[T]:
        actual = self.cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def iterar_nodos(self) -> Iterator[NodoDoble[T]]:
        actual = self.cabeza
        while actual is not None:
            yield actual
            actual = actual.siguiente

    def insertar_inicio(self, dato: T) -> NodoDoble[T]:
        """Inserta un nuevo elemento al inicio de la lista en O(1)."""
        nuevo = NodoDoble(dato)
        if self.cabeza is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo
            self.cabeza = nuevo
        self._tamano += 1
        return nuevo

    def insertar_final(self, dato: T) -> NodoDoble[T]:
        """Inserta un nuevo elemento al final de la lista en O(1)."""
        nuevo = NodoDoble(dato)
        if self.cola is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            self.cola.siguiente = nuevo
            nuevo.anterior = self.cola
            self.cola = nuevo
        self._tamano += 1
        return nuevo

    def insertar_en(self, indice: int, dato: T) -> NodoDoble[T]:
        """Inserta un nuevo elemento en una posición específica."""
        if indice < 0 or indice > self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice} (tamaño: {self._tamano})")

        if indice == 0:
            return self.insertar_inicio(dato)
        if indice == self._tamano:
            return self.insertar_final(dato)

        actual = self._nodo_en(indice)
        nuevo = NodoDoble(dato)
        predecesor = actual.anterior

        if predecesor is not None:
            predecesor.siguiente = nuevo
            nuevo.anterior = predecesor

        nuevo.siguiente = actual
        actual.anterior = nuevo
        self._tamano += 1
        return nuevo

    def _nodo_en(self, indice: int) -> NodoDoble[T]:
        if indice < 0 or indice >= self._tamano:
            raise IndexError(f"Índice fuera de rango: {indice} (tamaño: {self._tamano})")

        # Optimización: buscar desde la cabeza o desde la cola según proximidad
        if indice < self._tamano // 2:
            actual = self.cabeza
            for _ in range(indice):
                if actual is not None:
                    actual = actual.siguiente
        else:
            actual = self.cola
            for _ in range(self._tamano - 1 - indice):
                if actual is not None:
                    actual = actual.anterior

        if actual is None:
            raise IndexError(f"No se pudo acceder al nodo en índice {indice}")
        return actual

    def obtener(self, indice: int) -> T:
        """Obtiene el dato ubicado en la posición dada."""
        return self._nodo_en(indice).dato

    def __getitem__(self, indice: int) -> T:
        return self.obtener(indice)

    def eliminar_nodo(self, nodo: NodoDoble[T]) -> T:
        """Elimina un nodo en tiempo O(1) cuando se posee su referencia directa."""
        if nodo is None:
            raise ValueError("El nodo a eliminar no puede ser None")

        # Si es el primer elemento
        if nodo is self.cabeza:
            self.cabeza = nodo.siguiente
        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente

        # Si es el último elemento
        if nodo is self.cola:
            self.cola = nodo.anterior
        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = None
        self._tamano -= 1
        return nodo.dato

    def eliminar_en(self, indice: int) -> T:
        """Elimina y retorna el dato en el índice indicado."""
        nodo = self._nodo_en(indice)
        return self.eliminar_nodo(nodo)

    def eliminar_por_criterio(self, predicado: Callable[[T], bool]) -> T | None:
        """Elimina el primer nodo que satisfaga el predicado."""
        nodo = self.buscar(predicado)
        if nodo is not None:
            return self.eliminar_nodo(nodo)
        return None

    def buscar(self, predicado: Callable[[T], bool]) -> NodoDoble[T] | None:
        """Busca el primer nodo que satisfaga la condición dada."""
        actual = self.cabeza
        while actual is not None:
            if predicado(actual.dato):
                return actual
            actual = actual.siguiente
        return None

    def buscar_dato(self, predicado: Callable[[T], bool]) -> T | None:
        """Retorna el dato del primer nodo que cumpla la condición."""
        nodo = self.buscar(predicado)
        return nodo.dato if nodo is not None else None

    def limpiar(self) -> None:
        """Rompe enlaces bidireccionales y vacía la lista."""
        actual = self.cabeza
        while actual is not None:
            siguiente = actual.siguiente
            actual.anterior = None
            actual.siguiente = None
            actual = siguiente
        self.cabeza = None
        self.cola = None
        self._tamano = 0

    def a_lista_auxiliar(self) -> list[T]:
        """Convierte temporalmente los elementos a una lista nativa (solo para exportación/inspección)."""
        return list(self)
