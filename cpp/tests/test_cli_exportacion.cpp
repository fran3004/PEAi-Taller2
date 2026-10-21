#include <doctest/doctest.h>

#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QTemporaryDir>

#include <iostream>
#include <memory>
#include <sstream>

#include "pea/cli.hpp"
#include "pea/datos/exportador_csv.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

TEST_CASE("CLI exportar-csv crea las tres tablas con el directorio solicitado") {
    QTemporaryDir temporal;
    REQUIRE(temporal.isValid());
    const QString destino = temporal.filePath("exportacion");
    const pea::cli::CargadorCatalogoCsv cargar_catalogo =
        [](pea::servicios::CatalogoInvestigacion& catalogo) {
            auto grupo = std::make_shared<pea::dominio::Grupo>(
                "PRUEBA-GRP-CLI", "Grupo, científico", "A1", "Líder", true);
            grupo->institucion_principal = "UPC";
            catalogo.crear_grupo(grupo, false);

            auto investigador = std::make_shared<pea::dominio::Investigador>(
                "PRUEBA-RH-CLI", "Investigadora de prueba", "Junior",
                "Doctorado", true);
            investigador->nacionalidad = "Colombiana";
            catalogo.crear_investigador(investigador, false);

            auto producto = std::make_shared<pea::dominio::Producto>(
                "PRUEBA-PROD-CLI", "Producto de prueba", "GNC", "Artículo",
                2025, "Avalado", true);
            catalogo.crear_producto(producto, {}, {}, false);
        };

    CHECK(pea::cli::ejecutar(
              {"exportar-csv", "--directorio", destino}, cargar_catalogo) == 0);

    QFile grupos(QDir(destino).filePath("grupos.csv"));
    REQUIRE(grupos.open(QIODevice::ReadOnly));
    CHECK(grupos.readAll() ==
          "codigo_gruplac,nombre,categoria,lider,institucion_principal,activo\r\n"
          "PRUEBA-GRP-CLI,\"Grupo, científico\",A1,Líder,UPC,True\r\n");

    QFile investigadores(QDir(destino).filePath("investigadores.csv"));
    REQUIRE(investigadores.open(QIODevice::ReadOnly));
    CHECK(investigadores.readAll() ==
          "codigo_rh,nombre_completo,categoria,formacion_academica,nacionalidad,activo\r\n"
          "PRUEBA-RH-CLI,Investigadora de prueba,Junior,Doctorado,Colombiana,True\r\n");

    QFile productos(QDir(destino).filePath("productos.csv"));
    REQUIRE(productos.open(QIODevice::ReadOnly));
    CHECK(productos.readAll() ==
          "codigo_identificador,titulo,tipo_mayor,subtipo,ano,estado_validacion,activo\r\n"
          "PRUEBA-PROD-CLI,Producto de prueba,GNC,Artículo,2025,Avalado,True\r\n");
}

TEST_CASE("Escritura CSV atómica informa errores y limpia archivos temporales") {
    QTemporaryDir temporal;
    REQUIRE(temporal.isValid());

    const QString ruta_correcta = temporal.filePath("correcto.csv");
    QString error = "error previo";
    CHECK(pea::datos::guardar_csv_atomico(
        ruta_correcta, "contenido de prueba", error));
    CHECK(error.isEmpty());
    QFile correcto(ruta_correcta);
    REQUIRE(correcto.open(QIODevice::ReadOnly));
    CHECK(correcto.readAll() == "contenido de prueba");

    const QString destino = temporal.filePath("bloqueado.csv");
    REQUIRE(QDir().mkpath(destino));

    CHECK_FALSE(pea::datos::guardar_csv_atomico(
        destino, "contenido de prueba", error));
    CHECK_FALSE(error.isEmpty());
    CHECK(QFileInfo(destino).isDir());
    const QStringList archivos = QDir(temporal.path()).entryList(
        QDir::AllEntries | QDir::NoDotAndDotDot);
    CHECK(archivos.size() == 2);
    CHECK(archivos.contains("bloqueado.csv"));
    CHECK(archivos.contains("correcto.csv"));
}

TEST_CASE("CLI formatea los errores CSV individuales") {
    const QString salida = pea::cli::formatear_errores_importacion_csv(
        {QStringLiteral("Fila 2: Nombre ausente"),
         QStringLiteral("Fila 4: Año fuera del rango permitido")});

    CHECK(salida ==
          QStringLiteral("Filas con errores:\n"
                         "  - Fila 2: Nombre ausente\n"
                         "  - Fila 4: Año fuera del rango permitido"));
    CHECK(pea::cli::formatear_errores_importacion_csv({}).isEmpty());
}

TEST_CASE("La ayuda CLI anuncia el tipo CSV de autores") {
    std::ostringstream salida;
    std::streambuf* salida_anterior = std::cout.rdbuf(salida.rdbuf());
    const int resultado = pea::cli::ejecutar({"--help"});
    std::cout.rdbuf(salida_anterior);

    CHECK(resultado == 0);
    CHECK(salida.str().find("grupos|investigadores|productos|autores") != std::string::npos);
}
