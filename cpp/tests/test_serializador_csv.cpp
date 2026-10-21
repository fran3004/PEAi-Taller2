#include <doctest/doctest.h>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

#include "pea/datos/serializador_csv.hpp"

TEST_CASE("Serializador CSV escapa comas, comillas y saltos de línea") {
    CHECK(pea::datos::serializar_fila_csv({"codigo", "nombre", "activo"}) ==
          "codigo,nombre,activo\r\n");
    CHECK(pea::datos::serializar_fila_csv({"PRUEBA-1", "Grupo, investigación",
                                           "Dijo \"sí\"\ny continúa"}) ==
          "PRUEBA-1,\"Grupo, investigación\",\"Dijo \"\"sí\"\"\ny continúa\"\r\n");
}

TEST_CASE("Serializador CSV cumple los fixtures compartidos Python/C++") {
    QFile archivo(QStringLiteral(PEA_TEST_FIXTURES_DIR) + "/csv_paridad.json");
    REQUIRE(archivo.open(QIODevice::ReadOnly));
    const QJsonDocument documento = QJsonDocument::fromJson(archivo.readAll());
    REQUIRE(documento.isObject());
    const QJsonArray casos = documento.object().value("casos").toArray();
    REQUIRE(casos.size() == 2);

    for (const QJsonValue& valor : casos) {
        REQUIRE(valor.isObject());
        const QJsonObject caso = valor.toObject();
        QStringList entrada;
        for (const QJsonValue& celda : caso.value("entrada").toArray()) {
            entrada.append(celda.toString());
        }
        CAPTURE(caso.value("nombre").toString().toStdString());
        CHECK(pea::datos::serializar_fila_csv(entrada) == caso.value("salida").toString());
    }
}
