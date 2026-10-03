#include <doctest/doctest.h>
#include "pea/datos/sesion.hpp"
#include "pea/datos/revision.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"
#include "pea/excepciones.hpp"

using namespace pea::datos;
using namespace pea::servicios;
using namespace pea::dominio;

TEST_CASE("Sesión - ciclo de vida en memoria y expiración") {
    Sesion sesion;
    CHECK_FALSE(sesion.esta_autenticado());
    CHECK(sesion.rol() == "anon");

    sesion.iniciar_sesion("test_jwt_token_123", "usuario@upc.edu.co", 3600);
    CHECK(sesion.esta_autenticado());
    CHECK(sesion.rol() == "authenticated");
    CHECK(sesion.token_acceso() == "test_jwt_token_123");

    // Simular expiración de token
    sesion.simular_expiracion();
    CHECK(sesion.esta_expirada());
    CHECK_THROWS_AS((void)sesion.token_acceso(), pea::ErrorAutenticacion);
    CHECK_FALSE(sesion.esta_autenticado());


}

TEST_CASE("Resumen JSON - Paridad canónica con Python") {
    CatalogoInvestigacion catalogo;

    // Catálogo vacío
    QByteArray jsonVacio = catalogo.resumen_json();
    QByteArray esperadoVacio = "{\"grupos_activos\":0,\"grupos_totales\":0,\"investigadores_activos\":0,\"investigadores_totales\":0,\"pila_deshacer_tamano\":0,\"productos_activos\":0,\"productos_totales\":0}";
    CHECK(jsonVacio == esperadoVacio);

    // Con entidades añadidas
    auto g = std::make_shared<Grupo>("GRP-PAR-01", "Grupo Paridad", "A");
    auto inv = std::make_shared<Investigador>("INV-PAR-01", "Investigador Paridad");
    catalogo.crear_grupo(g, false);
    catalogo.crear_investigador(inv, false);

    auto p1 = std::make_shared<Producto>("P-PAR-01", "Prod Activo", "GNC", "Articulo", 2024);
    auto p2 = std::make_shared<Producto>("P-PAR-02", "Prod Inactivo", "DTI", "Software", 2025);
    catalogo.crear_producto(p1, g->codigo_gruplac, {inv->codigo_rh}, false);
    catalogo.crear_producto(p2, g->codigo_gruplac, {inv->codigo_rh}, false);
    catalogo.desactivar_producto(p2->codigo_identificador, false);

    QByteArray jsonConDatos = catalogo.resumen_json();
    // 1 grupo activo (1 total)
    // 1 investigador activo (1 total)
    // 1 producto activo (2 totales)
    // 4 operaciones en pila (crear grupo, crear inv, crear p1, crear p2, desactivar p2 = 5)
    QJsonObject dict = catalogo.resumen_dict();
    CHECK(dict["grupos_activos"].toInt() == 1);
    CHECK(dict["grupos_totales"].toInt() == 1);
    CHECK(dict["investigadores_activos"].toInt() == 1);
    CHECK(dict["investigadores_totales"].toInt() == 1);
    CHECK(dict["productos_activos"].toInt() == 1);
    CHECK(dict["productos_totales"].toInt() == 2);
    CHECK(dict["pila_deshacer_tamano"].toInt() == 5);
}
