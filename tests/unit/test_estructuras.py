"""Pruebas unitarias para las estructuras de datos hechas a mano."""

import pytest

from pea.dominio.grupo import Grupo
from pea.dominio.investigador import Investigador
from pea.dominio.producto import Producto
from pea.estructuras.cola import Cola, TareaIngesta
from pea.estructuras.lista_doble import ListaDoble
from pea.estructuras.multilista import Multilista
from pea.estructuras.pila import Pila


def test_lista_doble_operaciones_basicas() -> None:
    lista: ListaDoble[str] = ListaDoble()
    assert lista.esta_vacia()
    assert len(lista) == 0

    # Inserción en extremos
    nodo_b = lista.insertar_final("B")
    lista.insertar_inicio("A")
    lista.insertar_final("C")

    assert len(lista) == 3
    assert list(lista) == ["A", "B", "C"]
    assert lista.cabeza.dato == "A"
    assert lista.cola.dato == "C"

    # Inserción intermedia
    lista.insertar_en(1, "A.5")
    assert list(lista) == ["A", "A.5", "B", "C"]

    # Acceso por índice
    assert lista[0] == "A"
    assert lista[1] == "A.5"
    assert lista[3] == "C"

    # Búsqueda
    hallado = lista.buscar_dato(lambda x: x == "B")
    assert hallado == "B"

    # Eliminación por nodo conocido en O(1)
    dato_eliminado = lista.eliminar_nodo(nodo_b)
    assert dato_eliminado == "B"
    assert list(lista) == ["A", "A.5", "C"]
    assert len(lista) == 3

    # Eliminación en índice
    removido = lista.eliminar_en(1)
    assert removido == "A.5"
    assert list(lista) == ["A", "C"]

    # Limpiar
    lista.limpiar()
    assert lista.esta_vacia()
    assert lista.cabeza is None
    assert lista.cola is None


def test_multilista_principio_nodo_unico_compartido() -> None:
    multilista = Multilista()

    grupo = Grupo(codigo_gruplac="GRP-01", nombre="Grupo Sinfonía")
    inv_ana = Investigador(codigo_rh="RH-01", nombre_completo="Ana María López")
    inv_carlos = Investigador(codigo_rh="RH-02", nombre_completo="Carlos Andrés Pérez")

    prod = Producto(
        codigo_identificador="PRD-001",
        titulo="Artículo Algoritmos Cuánticos",
        tipo_mayor="GNC",
        ano=2024,
        estado_validacion="Avalado",
    )

    # Inserción del producto vinculado al grupo y a dos autores
    multilista.agregar_producto(prod, grupo=grupo, autores=[inv_ana, inv_carlos])
    assert len(multilista) == 1

    # Verificar consultas por grupo y por autor
    prods_grupo = multilista.obtener_productos_grupo("GRP-01")
    prods_ana = multilista.obtener_productos_investigador("RH-01")
    prods_carlos = multilista.obtener_productos_investigador("RH-02")

    assert len(prods_grupo) == 1
    assert len(prods_ana) == 1
    assert len(prods_carlos) == 1

    # Principio de Identidad de Objeto: es EXACTAMENTE la misma instancia física en memoria
    instancia_grupo = prods_grupo.cabeza.dato
    instancia_ana = prods_ana.cabeza.dato
    instancia_carlos = prods_carlos.cabeza.dato

    assert id(instancia_grupo) == id(instancia_ana)
    assert id(instancia_ana) == id(instancia_carlos)
    assert id(instancia_grupo) == id(prod)

    # Mutación reactiva: modificar un campo se observa instantáneamente desde todas las vistas
    prod.titulo = "Artículo Algoritmos Cuánticos (Versión Final)"
    assert instancia_grupo.titulo == "Artículo Algoritmos Cuánticos (Versión Final)"
    assert instancia_ana.titulo == "Artículo Algoritmos Cuánticos (Versión Final)"
    assert instancia_carlos.titulo == "Artículo Algoritmos Cuánticos (Versión Final)"


def test_pila_lifo_y_capacidad_maxima() -> None:
    pila: Pila[int] = Pila(capacidad_maxima=3)
    assert pila.esta_vacia()

    pila.apilar(1)
    pila.apilar(2)
    pila.apilar(3)
    assert len(pila) == 3
    assert pila.ver_tope() == 3

    # Al superar la capacidad máxima (3), descarta el más antiguo (1)
    pila.apilar(4)
    assert len(pila) == 3
    assert list(pila) == [4, 3, 2]

    # Desapilar en orden LIFO
    assert pila.desapilar() == 4
    assert pila.desapilar() == 3
    assert pila.desapilar() == 2
    assert pila.esta_vacia()

    with pytest.raises(IndexError):
        pila.desapilar()


def test_cola_fifo_y_tareas_ingesta() -> None:
    cola: Cola[TareaIngesta] = Cola()
    assert cola.esta_vacia()

    t1 = TareaIngesta(id_tarea="1", tipo_fuente="archivo_csv", origen="datos.csv")
    t2 = TareaIngesta(id_tarea="2", tipo_fuente="url_gruplac", origen="https://scienti.minciencias.gov.co/gruplac/...")

    cola.encolar(t1)
    cola.encolar(t2)
    assert len(cola) == 2
    assert cola.ver_frente().id_tarea == "1"

    # Desencolar en orden FIFO
    primero = cola.desencolar()
    assert primero.id_tarea == "1"
    assert len(cola) == 1

    segundo = cola.desencolar()
    assert segundo.id_tarea == "2"
    assert cola.esta_vacia()

    with pytest.raises(IndexError):
        cola.desencolar()
