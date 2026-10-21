#include <doctest/doctest.h>
#include "pea/cliente_http.hpp"
#include "pea/datos/configuracion_conexion.hpp"
#include "pea/datos/sesion.hpp"
#include "pea/excepciones.hpp"

TEST_CASE("ClienteHTTPSupabase - Configuración y gestión de tokens en memoria") {
    pea::ClienteHTTPSupabase cliente("https://ejemplo.supabase.co", "anon-key-12345");

    CHECK(cliente.baseUrl() == "https://ejemplo.supabase.co");
    CHECK(cliente.anonKey() == "anon-key-12345");
    CHECK(cliente.tokenAcceso().isEmpty());

    // Almacenar token en memoria volátil
    cliente.establecerTokenAcceso("jwt-token-sesion-secreta");
    CHECK(cliente.tokenAcceso() == "jwt-token-sesion-secreta");

    // Limpieza de token (cerrar sesión)
    cliente.cerrarSesion();
    CHECK(cliente.tokenAcceso().isEmpty());
}

TEST_CASE("ClienteHTTPSupabase - Verificación de capacidades TLS") {
    // La biblioteca QtNetwork debe tener soporte TLS compilado
    CHECK(pea::ClienteHTTPSupabase::soportaTLS() == true);
    CHECK(!pea::ClienteHTTPSupabase::backendTLS().isEmpty());
}

TEST_CASE("Configuración C++ acepta solo HTTPS y el host oficial de pea-prod") {
    pea::datos::ConfiguracionConexion configuracion{
        "https://wdmchsncexayqbjueamb.supabase.co", "sb_publishable_ejemplo", {}, true, true};
    CHECK_NOTHROW(pea::datos::validar_configuracion_conexion(configuracion));

    configuracion.url = "http://wdmchsncexayqbjueamb.supabase.co";
    CHECK_THROWS_AS(pea::datos::validar_configuracion_conexion(configuracion), pea::ErrorValidacion);

    configuracion.url = "https://otro-proyecto.supabase.co";
    CHECK_THROWS_AS(pea::datos::validar_configuracion_conexion(configuracion), pea::ErrorValidacion);

    configuracion.url = "https://wdmchsncexayqbjueamb.supabase.co";
    configuracion.clave_publicable = "sb_secret_ejemplo";
    CHECK_THROWS_AS(pea::datos::validar_configuracion_conexion(configuracion), pea::ErrorValidacion);
}

TEST_CASE("Excepciones PEA - Jerarquía y mensajes de error") {
    pea::ErrorAutenticacion errorAuth("Credenciales no válidas", "Código 401");
    CHECK(errorAuth.mensaje() == "Credenciales no válidas");
    CHECK(errorAuth.detalle() == "Código 401");

    pea::ConflictoRevision errorRev("Conflicto de revisión concurrente");
    CHECK(errorRev.mensaje() == "Conflicto de revisión concurrente");
    CHECK(errorRev.detalle().empty());
}

TEST_CASE("Sesión de evaluación conserva el indicador solo durante la sesión") {
    pea::datos::Sesion sesion;
    CHECK_FALSE(sesion.es_evaluacion());
    sesion.iniciar_sesion("ficticio", "Evaluación", 3600, QJsonObject{{"is_anonymous", true}});
    CHECK(sesion.es_evaluacion());
    CHECK_FALSE(sesion.necesita_renovacion());
    sesion.simular_expiracion();
    CHECK(sesion.necesita_renovacion());
    sesion.cerrar_sesion();
    CHECK_FALSE(sesion.es_evaluacion());
}

TEST_CASE("La renovación sin sesión no hace ninguna petición de red") {
    pea::ClienteHTTPSupabase cliente("https://ejemplo.supabase.co", "sb_publishable_ficticia");
    CHECK_FALSE(cliente.tieneSesionEvaluacion());
    CHECK_THROWS_AS(cliente.renovarEvaluacion(), pea::ErrorAutenticacion);
}
