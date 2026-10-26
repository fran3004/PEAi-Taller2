#include <doctest/doctest.h>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QTemporaryDir>
#include <cmath>
#include "pea/datos/archivo_local.hpp"
#include "pea/servicios/indicadores.hpp"
#include "pea/ingesta/extractor_pdf.hpp"
#include "pea/ingesta/parser_html.hpp"

namespace {
QJsonObject ejemplo() {
    QFile f(QStringLiteral(PEA_TEST_FIXTURES_DIR) + "/../../../datos/ejemplo-parcial.json");
    if (!f.open(QIODevice::ReadOnly)) throw std::runtime_error("No se encontró el catálogo de prueba.");
    return QJsonDocument::fromJson(f.readAll()).object();
}
}

TEST_CASE("Indicador usa pesos originales, logaritmos y productos únicos") {
    const auto datos = ejemplo();
    auto r = pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023);
    CHECK(r["brutos"].toObject()["Nc.Top"].toDouble() == doctest::Approx(550 * std::log1p(2.0 / 7)));
    CHECK(r["brutos"].toObject()["Nc.B"].toDouble() == doctest::Approx(280 * std::log1p(1.0 / 5)));
    CHECK(r["brutos"].toObject()["Cohe"].toDouble() == doctest::Approx(1.0 / 3));
    CHECK(r["brutos"].toObject()["Coop"].toDouble() == doctest::Approx(1.0 / 3));
    CHECK(r["incluidos"].toArray().size() == 3);
    CHECK(r["excluidos"].toArray().size() == 2);
    CHECK(r["indicador"].toDouble() == doctest::Approx(4.5));
    auto individual = pea::servicios::calcular_indicador(datos, "investigador", "PRUEBA-I1", 2023);
    CHECK(individual["brutos"].toObject()["Cohe"].toDouble() == doctest::Approx(2.0 / 3));
    auto recorte = pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, 2023);
    CHECK(recorte["brutos"].toObject()["Nc.Top"].toDouble() == doctest::Approx(550 * std::log(2.0)));
}

TEST_CASE("Pesos globales y relativos se mantienen separados") {
    for (const auto& ejemplo_peso : std::vector<std::tuple<QString, QString, double>>{
        {"ART_A2", "GNC", 550}, {"CAP_LIB_B", "GNC", 480}, {"PA1", "GNC", 5000},
        {"MA1", "GNC", 3000}, {"SF", "DTI", 280}, {"TD_B", "FRH", 800}}) {
        auto p = pea::servicios::puntaje_producto({{"subtipo", std::get<0>(ejemplo_peso)}, {"tipo_mayor", std::get<1>(ejemplo_peso)}});
        CHECK(p["puntaje"].toDouble() == doctest::Approx(std::get<2>(ejemplo_peso)));
    }
    CHECK(pea::servicios::modelo_puntajes()["categorias"].toArray().size() == 169);
    CHECK(pea::servicios::puntaje_producto({{"subtipo", "Artículo"}, {"tipo_mayor", "GNC"}})["puntaje"].isNull());
}

TEST_CASE("Referencia explícita valida máximos y periodo") {
    auto datos = ejemplo();
    auto r = pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023);
    auto maximos = r["maximos"].toObject();
    for (auto it = maximos.begin(); it != maximos.end(); ++it) it.value() = it.value().toDouble() * 2;
    QJsonObject ref{{"fuente", "Población de prueba"}, {"corte", 2023}, {"desde", QJsonValue::Null}, {"maximos", maximos}};
    CHECK(pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, {}, ref)["indicador"].toDouble() == doctest::Approx(2.25));
    maximos["Nc.Top"] = -1; ref["maximos"] = maximos;
    CHECK_THROWS(pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, {}, ref));
}

TEST_CASE("Archivo local restaura referencias compartidas y rechaza huérfanos") {
    auto datos = ejemplo();
    auto cat = pea::datos::restaurar_catalogo(datos);
    QTemporaryDir temporal;
    auto ruta = temporal.filePath("catalogo.json");
    pea::datos::guardar_archivo(ruta, pea::datos::serializar_catalogo(cat));
    auto nuevo = pea::datos::cargar_archivo(ruta);
    CHECK(pea::datos::serializar_catalogo(nuevo) == pea::datos::serializar_catalogo(cat));
    auto nodo = nuevo.multilista_productos.buscar_nodo("PRUEBA-P1");
    REQUIRE(nodo != nullptr);
    CHECK(nodo->grupo == nuevo.buscar_grupo("PRUEBA-G1"));
    auto relaciones = datos["relaciones"].toArray();
    auto rel = relaciones[0].toObject(); rel["autores"] = QJsonArray{"NO-EXISTE"}; relaciones[0] = rel; datos["relaciones"] = relaciones;
    CHECK_THROWS(pea::datos::restaurar_catalogo(datos));
}

TEST_CASE("PDF C++ extrae páginas y texto con Poppler") {
    auto doc = pea::ingesta::procesar_pdf(QStringLiteral(PEA_TEST_FIXTURES_DIR) + "/../../../tests/fixtures/parcial/texto.pdf");
    CHECK(doc["total_paginas"].toInt() == 1);
    CHECK(doc["paginas"].toArray()[0].toObject()["texto"].toString().contains("PEA-i Parcial 2"));
    CHECK_FALSE(doc["es_escaneado"].toBool());
}

TEST_CASE("URL C++ toma el año bibliográfico y conserva libros y formación") {
    const QString html = "<table><tr><td>Hoja de vida</td></tr></table>"
        "<table><tr><td>Artículos</td></tr><tr><td>Autor, Investigación verificable, ISSN: 1930-0000, 2023 vol: 4 p: 1</td></tr></table>"
        "<table><tr><td>Libros</td></tr><tr><td>Autor, Libro resultado de investigación, 2022 vol: 1 ISBN: 19300000</td></tr></table>"
        "<table><tr><td>Trabajos dirigidos</td></tr><tr><td>Autor, Trabajo de maestría terminado, 2021 vol: 1</td></tr></table>";
    auto perfil = pea::ingesta::ParserHTML::parsear_cvlac(html, {{"url", "https://scienti.minciencias.gov.co/cvlac/?cod_rh=00001"}});
    REQUIRE(perfil.articulos.size() == 1);
    CHECK(perfil.articulos[0].ano == 2023);
    REQUIRE(perfil.libros.size() == 1);
    CHECK(perfil.libros[0].ano == 2022);
    REQUIRE(perfil.trabajos_dirigidos.size() == 1);
    CHECK(perfil.trabajos_dirigidos[0].ano == 2021);
}

TEST_CASE("Estimación declarada de categorías faltantes") {
    auto datos = ejemplo();
    auto estricto = pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023);
    CHECK_FALSE(estricto["estimado"].toBool());
    auto estimado = pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, {}, {}, true);
    CHECK(estimado["estimado"].toBool());
    CHECK_FALSE(estimado["completo"].toBool());
    REQUIRE(estimado["estimadas"].toArray().size() == 1);
    CHECK(estimado["estimadas"].toArray()[0].toObject()["categoria"].toString() == "ART_D");
    CHECK(estimado["incluidos"].toArray().size() == 4);
    CHECK(estimado["excluidos"].toArray().size() == 1);
    CHECK(estimado["brutos"].toObject()["Nc.B"].toDouble() == doctest::Approx((280 + 45) * std::log1p(1.0 / 5)));
    CHECK(estimado["brutos"].toObject()["Nc.Top"].toDouble() == doctest::Approx(estricto["brutos"].toObject()["Nc.Top"].toDouble()));
}

TEST_CASE("Un vínculo con fecha final «Actual» sigue vigente") {
    auto datos = ejemplo();
    QJsonArray integrantes;
    for (const auto& v : datos["integrantes"].toArray()) {
        auto m = v.toObject();
        m["fecha_inicio"] = "2013/1"; m["fecha_fin"] = "Actual";
        integrantes.append(m);
    }
    datos["integrantes"] = integrantes;
    CHECK(pea::servicios::calcular_indicador(datos, "grupo", "PRUEBA-G1", 2023, {}, {}, true)["indicador"].toDouble() > 0);
}

TEST_CASE("El archivo local acepta fechas de vínculo de SCIENTI y rechaza texto arbitrario") {
    for (const auto& [inicio, fin] : std::vector<std::pair<QString, QString>>{
             {"2013/1", "Actual"}, {"2013-05", ""}, {"2013", "2020/12"}, {"2013-05-01", ""}}) {
        auto datos = ejemplo();
        QJsonArray integrantes;
        for (const auto& v : datos["integrantes"].toArray()) {
            auto m = v.toObject(); m["fecha_inicio"] = inicio; m["fecha_fin"] = fin; integrantes.append(m);
        }
        datos["integrantes"] = integrantes;
        CHECK_NOTHROW(pea::datos::restaurar_catalogo(datos));
    }
    auto malo = ejemplo();
    auto integrantes = malo["integrantes"].toArray();
    auto primero = integrantes[0].toObject(); primero["fecha_inicio"] = "ayer"; integrantes[0] = primero;
    malo["integrantes"] = integrantes;
    CHECK_THROWS(pea::datos::restaurar_catalogo(malo));
}
