#include <doctest/doctest.h>
#include "pea/cliente_http.hpp"
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

TEST_CASE("Excepciones PEA - Jerarquía y mensajes de error") {
    pea::ErrorAutenticacion errorAuth("Credenciales no válidas", "Código 401");
    CHECK(errorAuth.mensaje() == "Credenciales no válidas");
    CHECK(errorAuth.detalle() == "Código 401");

    pea::ConflictoRevision errorRev("Conflicto de revisión concurrente");
    CHECK(errorRev.mensaje() == "Conflicto de revisión concurrente");
    CHECK(errorRev.detalle().empty());
}
