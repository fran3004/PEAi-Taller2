#include <doctest/doctest.h>

#include <array>
#include <optional>

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
              std::nullopt, false, std::nullopt, std::nullopt,
              investigadores) ==
          esperado.value("institucional").toObject());
    CHECK(estadisticas.obtenerVistaGrupo(
              "G1", std::nullopt, false, std::nullopt, std::nullopt,
              investigadores) ==
          esperado.value("grupo").toObject());
    CHECK(estadisticas.obtenerVistaInvestigador("I1") ==
          esperado.value("investigador").toObject());

    const QJsonObject esperado_rango =
        fixture.value("esperado_rango_2023").toObject();
    CHECK(estadisticas.obtenerVistaInstitucional(
              std::nullopt, false, 2023, 2023, investigadores) ==
          esperado_rango.value("institucional").toObject());
    CHECK(estadisticas.obtenerVistaGrupo(
              "G1", std::nullopt, false, 2023, 2023, investigadores) ==
          esperado_rango.value("grupo").toObject());
    CHECK(estadisticas.obtenerVistaInvestigador(
              "I1", std::nullopt, false, 2023, 2023) ==
          esperado_rango.value("investigador").toObject());

    const auto opcional_entero =
        [](const QJsonObject& objeto, const QString& clave)
        -> std::optional<int> {
        const QJsonValue valor = objeto.value(clave);
        return valor.isDouble()
            ? std::optional<int>(valor.toInt())
            : std::nullopt;
    };
    pea::estructuras::Hipercubo5D cubo_temporal;
    for (const QJsonValue& valor :
         fixture.value("productos_temporales").toArray()) {
        const QJsonObject producto = valor.toObject();
        cubo_temporal.acumular(
            producto.value("grupo").toString(),
            producto.value("investigador").toString(),
            producto.value("categoria").toString(),
            producto.value("anio").toInt(),
            producto.value("validacion").toString(),
            producto.value("id").toString());
    }
    pea::servicios::ServicioEstadisticas estadisticas_temporales(
        &cubo_temporal);
    for (const QJsonValue& valor :
         fixture.value("casos_temporales").toArray()) {
        const QJsonObject caso = valor.toObject();
        const std::optional<int> ventana =
            opcional_entero(caso, "ventana_anios");
        const bool modelo = caso.value("modelo_2024").toBool();
        const std::optional<int> inicio =
            opcional_entero(caso, "anio_inicio");
        const std::optional<int> fin = opcional_entero(caso, "anio_fin");
        const QJsonObject esperado_caso = caso.value("esperado").toObject();
        const std::array<QJsonObject, 3> vistas{
            estadisticas_temporales.obtenerVistaInstitucional(
                ventana, modelo, inicio, fin),
            estadisticas_temporales.obtenerVistaGrupo(
                "G1", ventana, modelo, inicio, fin),
            estadisticas_temporales.obtenerVistaInvestigador(
                "I1", ventana, modelo, inicio, fin),
        };
        for (const QJsonObject& vista : vistas) {
            CHECK(vista.value("total_productos").toInt() ==
                  esperado_caso.value("total_productos").toInt());
            CHECK(vista.value("productos_por_anio").toObject() ==
                  esperado_caso.value("productos_por_anio").toObject());
        }
    }
}
