#include <doctest/doctest.h>

#include "pea/datos/serializador_csv.hpp"

TEST_CASE("Serializador CSV escapa comas, comillas y saltos de línea") {
    CHECK(pea::datos::serializar_fila_csv({"codigo", "nombre", "activo"}) ==
          "codigo,nombre,activo\r\n");
    CHECK(pea::datos::serializar_fila_csv({"PRUEBA-1", "Grupo, investigación",
                                           "Dijo \"sí\"\ny continúa"}) ==
          "PRUEBA-1,\"Grupo, investigación\",\"Dijo \"\"sí\"\"\ny continúa\"\r\n");
}
