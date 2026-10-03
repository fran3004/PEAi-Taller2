#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include <doctest/doctest.h>
#include "pea/version.hpp"

TEST_CASE("Verificación de constantes de versión e identidad institucional") {
    CHECK(std::string(pea::APP_NAME) == "PEA-i");
    CHECK(std::string(pea::APP_VERSION) == "0.1.0");
    CHECK(std::string(pea::INSTITUCION) == "Universidad Popular del Cesar");
    CHECK(pea::obtener_version().find("PEA-i versión 0.1.0") != std::string::npos);
}
