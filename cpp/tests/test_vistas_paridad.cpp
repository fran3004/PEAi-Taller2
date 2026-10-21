#include <doctest/doctest.h>

#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSet>

#include "pea/estructuras/hipercubo.hpp"
#include "pea/servicios/servicio_estadisticas.hpp"

TEST_CASE("Las vistas analíticas C++ conservan el contrato JSON común") {
    QFile archivo(QStringLiteral(PEA_TEST_FIXTURES_DIR) +
                  "/vistas_analiticas.json");
    REQUIRE(archivo.open(QIODevice::ReadOnly));
    const QJsonObject fixture =
        QJsonDocument::fromJson(archivo.readAll()).object();
    const QJsonObject esperado = fixture.value("esperado").toObject();

    QSet<QString> investigadores;
    for (const QJsonValue& valor :
         fixture.value("investigadores").toArray()) {
        investigadores.insert(valor.toString());
    }

    pea::estructuras::Hipercubo5D cubo;
    for (const QJsonValue& valor : fixture.value("productos").toArray()) {
        const QJsonObject producto = valor.toObject();
        cubo.acumular(
            producto.value("grupo").toString(),
            producto.value("investigador").toString(),
            producto.value("categoria").toString(),
            producto.value("anio").toInt(),
            producto.value("validacion").toString(),
            producto.value("id").toString());
    }

    pea::servicios::ServicioEstadisticas estadisticas(&cubo);
    CHECK(estadisticas.obtenerVistaInstitucional(
              std::nullopt, false, investigadores) ==
          esperado.value("institucional").toObject());
    CHECK(estadisticas.obtenerVistaGrupo(
              "G1", std::nullopt, false, investigadores) ==
          esperado.value("grupo").toObject());
    CHECK(estadisticas.obtenerVistaInvestigador("I1") ==
          esperado.value("investigador").toObject());
}
