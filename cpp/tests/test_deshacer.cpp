#include <doctest/doctest.h>
#include "pea/servicios/catalogo_investigacion.hpp"

using namespace pea::servicios;
using namespace pea::dominio;

TEST_CASE("Deshacer - Reversión de creación de entidades") {
    CatalogoInvestigacion catalogo;

    auto g = std::make_shared<Grupo>("GRP-UNDO-01", "Grupo Undo", "A");
    catalogo.crear_grupo(g, false);
    CHECK(catalogo.grupos.tamano() == 1);
    CHECK(catalogo.pila_deshacer.tamano() == 1);

    auto cmd = catalogo.deshacer(false);
    REQUIRE(cmd.has_value());
    CHECK(cmd->tipo_operacion == "crear");
    CHECK(cmd->tipo_entidad == "grupo");
    CHECK(catalogo.grupos.tamano() == 0);
    CHECK(catalogo.pila_deshacer.tamano() == 0);
}

TEST_CASE("Deshacer - Reversión de desactivación y activación") {
    CatalogoInvestigacion catalogo;

    auto prod = std::make_shared<Producto>("PRD-UNDO-01", "Producto Desactivar Undo", "ASC", "Divulgacion", 2024);
    catalogo.crear_producto(prod, QString(), {}, false);
    CHECK(prod->activo);

    // Desactivar
    catalogo.desactivar_producto(prod->codigo_identificador, false);
    CHECK_FALSE(prod->activo);

    // Deshacer desactivación (debe reactivarlo)
    auto cmd1 = catalogo.deshacer(false);
    REQUIRE(cmd1.has_value());
    CHECK(cmd1->tipo_operacion == "desactivar");
    CHECK(prod->activo);

    // Activar (desde ya activo o cambio forzado)
    prod->desactivar();
    catalogo.activar_producto(prod->codigo_identificador, false);
    CHECK(prod->activo);

    // Deshacer activación (debe desactivarlo)
    auto cmd2 = catalogo.deshacer(false);
    REQUIRE(cmd2.has_value());
    CHECK(cmd2->tipo_operacion == "activar");
    CHECK_FALSE(prod->activo);
}

TEST_CASE("Deshacer - Reversión de edición de grupo") {
    CatalogoInvestigacion catalogo;

    auto g = std::make_shared<Grupo>("GRP-EDIT-01", "Nombre Original", "B");
    catalogo.crear_grupo(g, false);

    QJsonObject cambios;
    cambios["nombre"] = "Nombre Modificado";
    cambios["categoria"] = "A1";
    catalogo.actualizar_grupo(g->codigo_gruplac, cambios, false);

    CHECK(g->nombre == "Nombre Modificado");
    CHECK(g->categoria == "A1");

    auto cmd = catalogo.deshacer(false);
    REQUIRE(cmd.has_value());
    CHECK(cmd->tipo_operacion == "editar");
    CHECK(g->nombre == "Nombre Original");
    CHECK(g->categoria == "B");
}
