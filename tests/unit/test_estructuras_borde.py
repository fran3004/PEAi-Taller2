"""Pruebas de casos borde y robustez para estructuras de datos hechas a mano."""

import pytest

from pea.dominio.producto import Producto
from pea.estructuras.cola import Cola
from pea.estructuras.lista_doble import ListaDoble
from pea.estructuras.multilista import Multilista
from pea.estructuras.pila import Pila


def test_lista_doble_casos_borde_vacia() -> None:
    lista: ListaDoble[int] = ListaDoble()

    # Operaciones sobre vacía
    assert lista.esta_vacia()
    assert len(lista) == 0
    assert lista.cabeza is None
    assert lista.cola is None
    assert list(lista) == []

    with pytest.raises(IndexError):
        lista.obtener(0)

    with pytest.raises(IndexError):
        lista.eliminar_en(0)

    with pytest.raises(ValueError):
        lista.eliminar_nodo(None)  # type: ignore[arg-type]

    assert lista.buscar(lambda x: x == 10) is None
    assert lista.buscar_dato(lambda x: x == 10) is None
    assert lista.eliminar_por_criterio(lambda x: x == 10) is None

    # Limpiar sobre vacía es seguro
    lista.limpiar()
    assert lista.esta_vacia()


def test_lista_doble_un_solo_elemento() -> None:
    lista: ListaDoble[str] = ListaDoble()
    nodo = lista.insertar_inicio("Único")

    assert len(lista) == 1
    assert lista.cabeza is nodo
    assert lista.cola is nodo
    assert nodo.anterior is None
    assert nodo.siguiente is None

    # Eliminar el único elemento
    eliminado = lista.eliminar_nodo(nodo)
    assert eliminado == "Único"
    assert lista.esta_vacia()
    assert lista.cabeza is None
    assert lista.cola is None


def test_lista_doble_indices_fuera_de_rango() -> None:
    lista: ListaDoble[int] = ListaDoble()
    lista.insertar_final(10)
    lista.insertar_final(20)

    with pytest.raises(IndexError):
        lista.insertar_en(-1, 99)

    with pytest.raises(IndexError):
        lista.insertar_en(5, 99)

    with pytest.raises(IndexError):
        lista.obtener(-1)

    with pytest.raises(IndexError):
        lista.obtener(2)


def test_lista_doble_insercion_masiva_10000_elementos() -> None:
    lista: ListaDoble[int] = ListaDoble()
    for i in range(10000):
        lista.insertar_final(i)

    assert len(lista) == 10000
    assert lista.cabeza.dato == 0
    assert lista.cola.dato == 9999
    assert lista[5000] == 5000

    # Limpiar y verificar liberación
    lista.limpiar()
    assert lista.esta_vacia()


def test_multilista_casos_borde() -> None:
    multilista = Multilista()
    assert multilista.esta_vacia()
    assert len(multilista) == 0

    # Buscar en vacía
    assert multilista.buscar_nodo("NO-EXISTE") is None
    assert multilista.buscar_producto("NO-EXISTE") is None
    assert multilista.eliminar_producto("NO-EXISTE") is None
    assert not multilista.desactivar_producto("NO-EXISTE")
    assert not multilista.activar_producto("NO-EXISTE")

    # Producto sin grupo ni autores
    prod_huerfano = Producto(
        codigo_identificador="HUERFANO-01",
        titulo="Producto Independiente",
        tipo_mayor="GNC",
        ano=2023,
    )
    multilista.agregar_producto(prod_huerfano)
    assert len(multilista) == 1
    assert multilista.buscar_producto("HUERFANO-01") is not None

    # Desactivar y reactivar
    assert multilista.desactivar_producto("HUERFANO-01")
    assert not prod_huerfano.activo
    assert multilista.activar_producto("HUERFANO-01")
    assert prod_huerfano.activo

    # Eliminar
    eliminado = multilista.eliminar_producto("HUERFANO-01")
    assert eliminado is prod_huerfano
    assert multilista.esta_vacia()


def test_pila_casos_borde() -> None:
    pila: Pila[str] = Pila()
    assert pila.esta_vacia()
    assert pila.ver_tope() is None

    with pytest.raises(IndexError):
        pila.desapilar()

    pila.apilar("A")
    assert not pila.esta_vacia()
    pila.limpiar()
    assert pila.esta_vacia()


def test_cola_casos_borde() -> None:
    cola: Cola[int] = Cola()
    assert cola.esta_vacia()
    assert cola.ver_frente() is None

    with pytest.raises(IndexError):
        cola.desencolar()

    cola.encolar(1)
    cola.encolar(2)
    assert len(cola) == 2
    cola.limpiar()
    assert cola.esta_vacia()
    assert cola.frente_nodo is None
    assert cola.final_nodo is None
