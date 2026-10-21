#include <doctest/doctest.h>
#include "pea/excepciones.hpp"
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

TEST_CASE("Deshacer - Reversión de edición de producto y sincronización del hipercubo") {
    CatalogoInvestigacion catalogo;
    auto prod = std::make_shared<Producto>("PRD-EDIT-01", "Título anterior", "GNC", "Artículo", 2024);
    catalogo.crear_producto(prod, QString(), {}, false);

    QJsonObject cambios;
    cambios["titulo"] = "Título actualizado";
    cambios["ano"] = 2023;
    cambios["mes"] = 8;
    catalogo.actualizar_producto(prod->codigo_identificador, cambios, false);
    CHECK(prod->titulo == "Título actualizado");
    CHECK(prod->ano == 2023);
    REQUIRE(prod->mes.has_value());
    CHECK(*prod->mes == 8);
    CHECK(catalogo.estadisticas.productosPorAnio().value(2023) == 1);

    const auto comando = catalogo.deshacer(false);
    REQUIRE(comando.has_value());
    CHECK(comando->tipo_operacion == "editar");
    CHECK(prod->titulo == "Título anterior");
    CHECK(prod->ano == 2024);
    CHECK_FALSE(prod->mes.has_value());
    CHECK(catalogo.estadisticas.productosPorAnio().value(2024) == 1);
}

TEST_CASE("Actualizar producto cambia o quita grupo y deshacer restaura la relación") {
    CatalogoInvestigacion catalogo;
    auto grupo_original = std::make_shared<Grupo>("GRP-ORIGINAL", "Grupo original", "A");
    auto grupo_nuevo = std::make_shared<Grupo>("GRP-NUEVO", "Grupo nuevo", "B");
    catalogo.crear_grupo(grupo_original, false);
    catalogo.crear_grupo(grupo_nuevo, false);

    auto producto = std::make_shared<Producto>(
        "PRD-GRUPO-01", "Producto", "GNC", "Articulo", 2024);
    catalogo.crear_producto(producto, grupo_original->codigo_gruplac, {}, false);
    auto* nodo = catalogo.multilista_productos.buscar_nodo(
        producto->codigo_identificador);
    REQUIRE(nodo != nullptr);
    CHECK(nodo->grupo.get() == grupo_original.get());

    QJsonObject grupo_inexistente;
    grupo_inexistente["titulo"] = "No se debe aplicar";
    grupo_inexistente["codigo_grupo"] = "GRP-INEXISTENTE";
    CHECK_THROWS_AS(
        catalogo.actualizar_producto(
            producto->codigo_identificador, grupo_inexistente, false),
        pea::RecursoNoEncontrado);
    CHECK(producto->titulo == "Producto");
    CHECK(nodo->grupo.get() == grupo_original.get());

    QJsonObject cambio_grupo;
    cambio_grupo["codigo_grupo"] = grupo_nuevo->codigo_gruplac;
    catalogo.actualizar_producto(producto->codigo_identificador, cambio_grupo, false);
    CHECK(nodo->grupo.get() == grupo_nuevo.get());
    CHECK(catalogo.multilista_productos.obtener_productos_grupo(
              grupo_original->codigo_gruplac).esta_vacia());
    CHECK(catalogo.multilista_productos.obtener_productos_grupo(
              grupo_nuevo->codigo_gruplac).tamano() == 1);

    REQUIRE(catalogo.deshacer(false).has_value());
    CHECK(nodo->grupo.get() == grupo_original.get());

    QJsonObject quitar_grupo;
    quitar_grupo["codigo_grupo"] = QJsonValue(QJsonValue::Null);
    catalogo.actualizar_producto(producto->codigo_identificador, quitar_grupo, false);
    CHECK(nodo->grupo.get() == nullptr);
    REQUIRE(catalogo.deshacer(false).has_value());
    CHECK(nodo->grupo.get() == grupo_original.get());
}

TEST_CASE("Actualizar producto rechaza campos desconocidos sin mutar datos") {
    CatalogoInvestigacion catalogo;
    auto prod = std::make_shared<Producto>("PRD-INVALID-01", "Sin cambios", "ASC", "Artículo", 2024);
    catalogo.crear_producto(prod, QString(), {}, false);

    QJsonObject cambios;
    cambios["titulo"] = "Cambio parcial";
    cambios["campo_no_permitido"] = "valor";
    CHECK_THROWS_AS(catalogo.actualizar_producto(prod->codigo_identificador, cambios, false),
                    pea::ErrorValidacion);
    CHECK(prod->titulo == "Sin cambios");
}
