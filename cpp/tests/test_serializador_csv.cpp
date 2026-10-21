#include <doctest/doctest.h>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>

#include "pea/datos/exportador_csv.hpp"
#include "pea/datos/serializador_csv.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

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

TEST_CASE("Exportación CSV completa conserva esquema, orden, UTF-8 y escapes del fixture común") {
    QFile archivo(QStringLiteral(PEA_TEST_FIXTURES_DIR) + "/exportacion_csv.json");
    REQUIRE(archivo.open(QIODevice::ReadOnly));
    const QJsonObject fixture = QJsonDocument::fromJson(archivo.readAll()).object();
    pea::servicios::CatalogoInvestigacion catalogo;

    for (const QJsonValue& valor : fixture.value("grupos").toArray()) {
        const QJsonObject fila = valor.toObject();
        auto grupo = std::make_shared<pea::dominio::Grupo>();
        grupo->codigo_gruplac = fila.value("codigo_gruplac").toString();
        grupo->nombre = fila.value("nombre").toString();
        grupo->categoria = fila.value("categoria").toString();
        grupo->lider = fila.value("lider").toString();
        grupo->institucion_principal = fila.value("institucion_principal").toString();
        grupo->activo = fila.value("activo").toBool();
        catalogo.crear_grupo(grupo, false);
    }

    for (const QJsonValue& valor : fixture.value("investigadores").toArray()) {
        const QJsonObject fila = valor.toObject();
        auto investigador = std::make_shared<pea::dominio::Investigador>();
        investigador->codigo_rh = fila.value("codigo_rh").toString();
        investigador->nombre_completo = fila.value("nombre_completo").toString();
        investigador->categoria = fila.value("categoria").toString();
        investigador->formacion_academica = fila.value("formacion_academica").toString();
        investigador->nacionalidad = fila.value("nacionalidad").toString();
        investigador->activo = fila.value("activo").toBool();
        catalogo.crear_investigador(investigador, false);
    }

    for (const QJsonValue& valor : fixture.value("productos").toArray()) {
        const QJsonObject fila = valor.toObject();
        auto producto = std::make_shared<pea::dominio::Producto>();
        producto->codigo_identificador = fila.value("codigo_identificador").toString();
        producto->titulo = fila.value("titulo").toString();
        producto->tipo_mayor = fila.value("tipo_mayor").toString();
        producto->subtipo = fila.value("subtipo").toString();
        producto->ano = fila.value("ano").toInt();
        producto->estado_validacion = fila.value("estado_validacion").toString();
        producto->activo = fila.value("activo").toBool();
        catalogo.crear_producto(producto, {}, {}, false);
    }

    const auto exportaciones = pea::datos::serializar_catalogo_csv(catalogo);
    const QJsonObject esperados = fixture.value("esperado").toObject();
    CHECK(exportaciones[0] == esperados.value("grupos.csv").toString());
    CHECK(exportaciones[1] == esperados.value("investigadores.csv").toString());
    CHECK(exportaciones[2] == esperados.value("productos.csv").toString());
    CHECK(exportaciones[0].toUtf8().endsWith("\r\n"));
    CHECK(exportaciones[1].toUtf8().endsWith("\r\n"));
    CHECK(exportaciones[2].toUtf8().endsWith("\r\n"));
}
