"""Implementación de Multilista para productos compartidos entre grupos e investigadores."""

from collections.abc import Iterator
from typing import Any

from pea.estructuras.lista_doble import ListaDoble


class NodoProductoMultilista:
    """Nodo representativo de un Producto único enlazado multidireccionalmente."""

    def __init__(self, producto: Any, grupo: Any | None = None) -> None:
        self.producto: Any = producto
        self.grupo: Any | None = grupo
        self.autores: ListaDoble[Any] = ListaDoble()

        # Enlaces en la secuencia general de productos
        self.anterior_global: NodoProductoMultilista | None = None
        self.siguiente_global: NodoProductoMultilista | None = None

        # Enlaces en la secuencia de productos del mismo grupo
        self.anterior_en_grupo: NodoProductoMultilista | None = None
        self.siguiente_en_grupo: NodoProductoMultilista | None = None

    @property
    def codigo_identificador(self) -> str:
        return getattr(self.producto, "codigo_identificador", "")

    @property
    def activo(self) -> bool:
        return getattr(self.producto, "activo", True)

    def agregar_autor(self, investigador: Any) -> None:
        """Asocia un investigador como coautor si no está presente."""
        codigo_rh = getattr(investigador, "codigo_rh", None)
        ya_existe = self.autores.buscar(lambda inv: getattr(inv, "codigo_rh", None) == codigo_rh)
        if ya_existe is None:
            self.autores.insertar_final(investigador)

    def remover_autor(self, codigo_rh: str) -> Any | None:
        """Desvincula a un investigador de la lista de coautores."""
        return self.autores.eliminar_por_criterio(lambda inv: getattr(inv, "codigo_rh", None) == codigo_rh)


class Multilista:
    """Estructura de Multilista para navegación cruzada de productos, grupos y coautorías."""

    def __init__(self) -> None:
        self.cabeza_global: NodoProductoMultilista | None = None
        self.cola_global: NodoProductoMultilista | None = None
        self._tamano: int = 0

    @property
    def tamano(self) -> int:
        return self._tamano

    def __len__(self) -> int:
        return self._tamano

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def iterar_nodos(self) -> Iterator[NodoProductoMultilista]:
        actual = self.cabeza_global
        while actual is not None:
            yield actual
            actual = actual.siguiente_global

    def __iter__(self) -> Iterator[Any]:
        for nodo in self.iterar_nodos():
            yield nodo.producto

    def agregar_producto(
        self,
        producto: Any,
        grupo: Any | None = None,
        autores: Any = None,
    ) -> NodoProductoMultilista:
        """Inserta un producto en la multilista asegurando nodo único en memoria."""
        codigo_id = getattr(producto, "codigo_identificador", "")
        nodo_existente = self.buscar_nodo(codigo_id)
        if nodo_existente is not None:
            # Si el producto ya existe, actualizamos su grupo o coautores si aplica
            if grupo is not None:
                nodo_existente.grupo = grupo
            if autores is not None:
                for inv in autores:
                    nodo_existente.agregar_autor(inv)
            return nodo_existente

        nodo = NodoProductoMultilista(producto, grupo)

        # Asociar autores
        if autores is not None:
            for inv in autores:
                nodo.agregar_autor(inv)

        # Enlazar en la lista global de productos
        if self.cola_global is None:
            self.cabeza_global = nodo
            self.cola_global = nodo
        else:
            self.cola_global.siguiente_global = nodo
            nodo.anterior_global = self.cola_global
            self.cola_global = nodo

        self._tamano += 1

        # Enlazar en la lista del grupo si existe
        if grupo is not None:
            self._enlazar_en_grupo(nodo, grupo)

        return nodo

    def _enlazar_en_grupo(self, nodo: NodoProductoMultilista, grupo: Any) -> None:
        codigo_grupo = getattr(grupo, "codigo_gruplac", None)
        # Buscar el último producto que pertenezca a este mismo grupo
        ultimo_del_grupo: NodoProductoMultilista | None = None
        actual = self.cabeza_global
        while actual is not None:
            if actual is not nodo and actual.grupo is not None:
                if getattr(actual.grupo, "codigo_gruplac", None) == codigo_grupo:
                    ultimo_del_grupo = actual
            actual = actual.siguiente_global

        if ultimo_del_grupo is not None:
            ultimo_del_grupo.siguiente_en_grupo = nodo
            nodo.anterior_en_grupo = ultimo_del_grupo

    def buscar_nodo(self, codigo_identificador: str) -> NodoProductoMultilista | None:
        """Busca el nodo del producto por su código identificador único."""
        actual = self.cabeza_global
        while actual is not None:
            if actual.codigo_identificador == codigo_identificador:
                return actual
            actual = actual.siguiente_global
        return None

    def buscar_producto(self, codigo_identificador: str) -> Any | None:
        """Busca la entidad Producto por su código identificador."""
        nodo = self.buscar_nodo(codigo_identificador)
        return nodo.producto if nodo is not None else None

    def obtener_productos_grupo(self, codigo_gruplac: str) -> ListaDoble[Any]:
        """Obtiene la lista doblemente enlazada de productos de un grupo."""
        resultado: ListaDoble[Any] = ListaDoble()
        for nodo in self.iterar_nodos():
            if nodo.grupo is not None and getattr(nodo.grupo, "codigo_gruplac", None) == codigo_gruplac:
                resultado.insertar_final(nodo.producto)
        return resultado

    def obtener_productos_investigador(self, codigo_rh: str) -> ListaDoble[Any]:
        """Obtiene la lista doblemente enlazada de productos de un investigador."""
        resultado: ListaDoble[Any] = ListaDoble()
        for nodo in self.iterar_nodos():
            es_autor = nodo.autores.buscar(lambda inv: getattr(inv, "codigo_rh", None) == codigo_rh)
            if es_autor is not None:
                resultado.insertar_final(nodo.producto)
        return resultado

    def obtener_todos(self) -> ListaDoble[Any]:
        """Retorna todos los productos almacenados en una ListaDoble."""
        resultado: ListaDoble[Any] = ListaDoble()
        for nodo in self.iterar_nodos():
            resultado.insertar_final(nodo.producto)
        return resultado

    def eliminar_producto(self, codigo_identificador: str) -> Any | None:
        """Desenlaza y elimina físicamente el nodo producto de todas las listas."""
        nodo = self.buscar_nodo(codigo_identificador)
        if nodo is None:
            return None

        # 1. Desenlazar de la lista global
        if nodo is self.cabeza_global:
            self.cabeza_global = nodo.siguiente_global
        if nodo.anterior_global is not None:
            nodo.anterior_global.siguiente_global = nodo.siguiente_global

        if nodo is self.cola_global:
            self.cola_global = nodo.anterior_global
        if nodo.siguiente_global is not None:
            nodo.siguiente_global.anterior_global = nodo.anterior_global

        # 2. Desenlazar de la lista del grupo
        if nodo.anterior_en_grupo is not None:
            nodo.anterior_en_grupo.siguiente_en_grupo = nodo.siguiente_en_grupo
        if nodo.siguiente_en_grupo is not None:
            nodo.siguiente_en_grupo.anterior_en_grupo = nodo.anterior_en_grupo

        # 3. Limpiar referencias del nodo
        nodo.anterior_global = None
        nodo.siguiente_global = None
        nodo.anterior_en_grupo = None
        nodo.siguiente_en_grupo = None
        nodo.grupo = None
        nodo.autores.limpiar()

        self._tamano -= 1
        return nodo.producto

    def desactivar_producto(self, codigo_identificador: str) -> bool:
        """Desactiva lógicamente el producto preservando los enlaces intactos."""
        nodo = self.buscar_nodo(codigo_identificador)
        if nodo is not None:
            nodo.producto.activo = False
            return True
        return False

    def activar_producto(self, codigo_identificador: str) -> bool:
        """Reactiva lógicamente el producto."""
        nodo = self.buscar_nodo(codigo_identificador)
        if nodo is not None:
            nodo.producto.activo = True
            return True
        return False

    def desvincular_investigador_de_todos(self, codigo_rh: str) -> int:
        """Remueve al investigador de todas las listas de autores."""
        removidos = 0
        for nodo in self.iterar_nodos():
            if nodo.remover_autor(codigo_rh) is not None:
                removidos += 1
        return removidos

    def desvincular_grupo_de_todos(self, codigo_gruplac: str) -> int:
        """Desvincula el grupo de todos sus productos."""
        afectados = 0
        for nodo in self.iterar_nodos():
            if nodo.grupo is not None and getattr(nodo.grupo, "codigo_gruplac", None) == codigo_gruplac:
                nodo.grupo = None
                nodo.anterior_en_grupo = None
                nodo.siguiente_en_grupo = None
                afectados += 1
        return afectados

    def limpiar(self) -> None:
        """Vacía y desvincula completamente la multilista."""
        actual = self.cabeza_global
        while actual is not None:
            sig = actual.siguiente_global
            actual.anterior_global = None
            actual.siguiente_global = None
            actual.anterior_en_grupo = None
            actual.siguiente_en_grupo = None
            actual.grupo = None
            actual.autores.limpiar()
            actual = sig
        self.cabeza_global = None
        self.cola_global = None
        self._tamano = 0
