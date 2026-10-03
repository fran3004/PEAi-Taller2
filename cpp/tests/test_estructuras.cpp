#include <doctest/doctest.h>
#include "pea/estructuras/nodo.hpp"
#include "pea/estructuras/lista_doble.hpp"
#include "pea/estructuras/multilista.hpp"
#include "pea/estructuras/pila.hpp"
#include "pea/estructuras/cola.hpp"

using namespace pea::estructuras;
using namespace pea::dominio;

TEST_CASE("ListaDoble - operaciones básicas y ciclo de vida") {
    ListaDoble<int> lista;
    CHECK(lista.esta_vacia());
    CHECK(lista.tamano() == 0);

    lista.insertar_final(10);
    lista.insertar_final(20);
    lista.insertar_inicio(5);

    CHECK(lista.tamano() == 3);
    CHECK_FALSE(lista.esta_vacia());

    CHECK(lista.cabeza()->dato == 5);
    CHECK(lista.cola()->dato == 20);

    // Iteración
    int suma = 0;
    for (int v : lista) {
        suma += v;
    }
    CHECK(suma == 35);

    // Búsqueda
    auto* encontrado = lista.buscar([](int x) { return x == 20; });
    REQUIRE(encontrado != nullptr);
    CHECK(encontrado->dato == 20);

    // Eliminación
    auto elim_inicio = lista.eliminar_inicio();
    CHECK(elim_inicio == 5);
    CHECK(lista.tamano() == 2);

    auto elim_final = lista.eliminar_final();
    CHECK(elim_final == 20);
    CHECK(lista.tamano() == 1);

    auto elim_ultimo = lista.eliminar_inicio();
    CHECK(elim_ultimo == 10);
    CHECK(lista.esta_vacia());
    CHECK_THROWS_AS(lista.eliminar_inicio(), std::out_of_range);
}

TEST_CASE("ListaDoble - regla de los cinco y copia profunda") {
    ListaDoble<int> original;
    original.insertar_final(1);
    original.insertar_final(2);
    original.insertar_final(3);

    ListaDoble<int> copia(original);
    CHECK(copia.tamano() == 3);

    original.insertar_final(4);
    CHECK(original.tamano() == 4);
    CHECK(copia.tamano() == 3);

    ListaDoble<int> movida(std::move(original));
    CHECK(movida.tamano() == 4);
    CHECK(original.tamano() == 0);
    CHECK(original.esta_vacia());
}

TEST_CASE("Pila - LIFO y descarte acotado de capacidad") {
    Pila<int> pila(3); // capacidad máxima de 3 para test
    CHECK(pila.esta_vacia());

    pila.apilar(1);
    pila.apilar(2);
    pila.apilar(3);
    CHECK(pila.tamano() == 3);
    CHECK(*pila.ver_tope() == 3);

    // Al apilar el 4to, se descarta el fondo (1)
    pila.apilar(4);
    CHECK(pila.tamano() == 3);
    CHECK(*pila.ver_tope() == 4);

    CHECK(pila.desapilar() == 4);
    CHECK(pila.desapilar() == 3);
    CHECK(pila.desapilar() == 2);
    CHECK(pila.esta_vacia());
    CHECK_THROWS_AS(pila.desapilar(), std::out_of_range);
}

TEST_CASE("Cola - FIFO estricto y operaciones de borde") {
    Cola<QString> cola;
    CHECK(cola.esta_vacia());

    cola.encolar("primero");
    cola.encolar("segundo");
    cola.encolar("tercero");
    CHECK(cola.tamano() == 3);
    CHECK(*cola.ver_frente() == "primero");

    CHECK(cola.desencolar() == "primero");
    CHECK(cola.desencolar() == "segundo");
    CHECK(cola.desencolar() == "tercero");
    CHECK(cola.esta_vacia());
    CHECK_THROWS_AS(cola.desencolar(), std::out_of_range);
}

TEST_CASE("Multilista - navegación multidireccional y enlaces cruzados") {
    Multilista multi;
    CHECK(multi.esta_vacia());

    auto g1 = std::make_shared<Grupo>("GRP-01", "Grupo 1", "A");
    auto g2 = std::make_shared<Grupo>("GRP-02", "Grupo 2", "B");
    auto inv1 = std::make_shared<Investigador>("INV-01", "Investigador 1");
    auto inv2 = std::make_shared<Investigador>("INV-02", "Investigador 2");

    auto p1 = std::make_shared<Producto>("P-01", "Prod 1", "GNC", "Articulo", 2024);
    auto p2 = std::make_shared<Producto>("P-02", "Prod 2", "DTI", "Software", 2025);

    ListaDoble<std::shared_ptr<Investigador>> auts1;
    auts1.insertar_final(inv1);
    auts1.insertar_final(inv2);

    ListaDoble<std::shared_ptr<Investigador>> auts2;
    auts2.insertar_final(inv2);

    multi.agregar_producto(p1, g1, auts1);
    multi.agregar_producto(p2, g1, auts2);

    CHECK(multi.tamano() == 2);

    // Navegación por grupo
    auto prodsG1 = multi.obtener_productos_grupo("GRP-01");
    CHECK(prodsG1.tamano() == 2);

    auto prodsG2 = multi.obtener_productos_grupo("GRP-02");
    CHECK(prodsG2.tamano() == 0);

    // Navegación por autor
    auto prodsInv1 = multi.obtener_productos_investigador("INV-01");
    CHECK(prodsInv1.tamano() == 1);

    auto prodsInv2 = multi.obtener_productos_investigador("INV-02");
    CHECK(prodsInv2.tamano() == 2);

    // Activación y desactivación
    CHECK(multi.desactivar_producto("P-01"));
    CHECK_FALSE(p1->activo);
    CHECK(multi.activar_producto("P-01"));
    CHECK(p1->activo);

    // Eliminación física
    auto prodElim = multi.eliminar_producto("P-01");
    REQUIRE(prodElim.get() != nullptr);
    CHECK(prodElim->codigo_identificador == "P-01");
    CHECK(multi.tamano() == 1);
    CHECK(multi.buscar_producto("P-01").get() == nullptr);

}
