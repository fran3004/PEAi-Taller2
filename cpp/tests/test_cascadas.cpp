#include <doctest/doctest.h>
#include "pea/servicios/catalogo_investigacion.hpp"

using namespace pea::servicios;
using namespace pea::dominio;

TEST_CASE("Cascadas - Eliminación de Grupo en memoria") {
    CatalogoInvestigacion catalogo;

    auto g = std::make_shared<Grupo>("GRP-CASCADA-01", "Grupo Cascadas", "A1");
    auto inv1 = std::make_shared<Investigador>("INV-CASCADA-01", "Investigador 1");
    auto inv2 = std::make_shared<Investigador>("INV-CASCADA-02", "Investigador 2");

    catalogo.crear_grupo(g, false);
    catalogo.crear_investigador(inv1, false);
    catalogo.crear_investigador(inv2, false);

    catalogo.vincular_integrante(g->codigo_gruplac, inv1->codigo_rh, "Lider", false);
    catalogo.vincular_integrante(g->codigo_gruplac, inv2->codigo_rh, "Investigador", false);

    auto prod = std::make_shared<Producto>("PRD-CASCADA-01", "Producto Grupo", "GNC", "Articulo", 2024);
    catalogo.crear_producto(prod, g->codigo_gruplac, {inv1->codigo_rh}, false);

    CHECK(catalogo.grupos.tamano() == 1);
    CHECK(catalogo.integrantes.tamano() == 2);
    CHECK(catalogo.multilista_productos.tamano() == 1);

    // Al eliminar el grupo:
    catalogo.eliminar_grupo(g->codigo_gruplac, false);

    CHECK(catalogo.grupos.tamano() == 0);
    CHECK(catalogo.integrantes.tamano() == 0);
    CHECK(catalogo.multilista_productos.tamano() == 1); // Producto preservado
    auto* nodoProd = catalogo.multilista_productos.buscar_nodo(prod->codigo_identificador);
    REQUIRE(nodoProd != nullptr);
    CHECK(nodoProd->grupo.get() == nullptr); // Grupo desvinculado

}

TEST_CASE("Cascadas - Eliminación de Investigador en memoria") {
    CatalogoInvestigacion catalogo;

    auto g = std::make_shared<Grupo>("GRP-INV-01", "Grupo Inv", "B");
    auto inv = std::make_shared<Investigador>("INV-COAUTOR-01", "Coautor Principal");

    catalogo.crear_grupo(g, false);
    catalogo.crear_investigador(inv, false);
    catalogo.vincular_integrante(g->codigo_gruplac, inv->codigo_rh, "Investigador", false);

    auto prod = std::make_shared<Producto>("PRD-AUTOR-01", "Producto Coautoria", "DTI", "Software", 2024);
    catalogo.crear_producto(prod, g->codigo_gruplac, {inv->codigo_rh}, false);

    CHECK(catalogo.investigadores.tamano() == 1);
    CHECK(catalogo.integrantes.tamano() == 1);

    auto prodsInv = catalogo.multilista_productos.obtener_productos_investigador(inv->codigo_rh);
    CHECK(prodsInv.tamano() == 1);

    // Eliminar investigador en cascada
    catalogo.eliminar_investigador(inv->codigo_rh, false);

    CHECK(catalogo.investigadores.tamano() == 0);
    CHECK(catalogo.integrantes.tamano() == 0);

    // El producto sigue existiendo pero ya no tiene este coautor
    auto prodsInvDespues = catalogo.multilista_productos.obtener_productos_investigador(inv->codigo_rh);
    CHECK(prodsInvDespues.tamano() == 0);
}
