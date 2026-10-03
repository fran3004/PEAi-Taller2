#include <doctest/doctest.h>

#include "pea/ingesta/modelos.hpp"
#include "pea/ingesta/parser_html.hpp"
#include "pea/ingesta/lector_csv.hpp"
#include "pea/ingesta/extractor_url.hpp"
#include "pea/ingesta/servicio_ingesta.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QTemporaryDir>
#include <iostream>

using namespace pea;
using namespace pea::ingesta;

TEST_CASE("Ingesta C++ - Extracción y Parsing HTML contra Oráculo") {
    // Buscar la ruta de fixtures (puede correr desde cpp/build o desde la raíz del repo)
    QString ruta_fixtures = QStringLiteral("tests/fixtures/scienti");
    if (!QDir(ruta_fixtures).exists()) {
        ruta_fixtures = QStringLiteral("../../tests/fixtures/scienti");
    }
    REQUIRE(QDir(ruta_fixtures).exists());

    SUBCASE("Oráculo GrupLAC vacío (gruplac_0000000002099)") {
        QString ruta_html = ruta_fixtures + QStringLiteral("/gruplac_0000000002099.html");
        QString ruta_json = ruta_fixtures + QStringLiteral("/gruplac_0000000002099.esperado.json");

        QFile file_html(ruta_html);
        REQUIRE(file_html.open(QIODevice::ReadOnly));
        QByteArray bytes_html = file_html.readAll();
        QString html_text = QString::fromLatin1(bytes_html);

        QFile file_json(ruta_json);
        REQUIRE(file_json.open(QIODevice::ReadOnly));
        QJsonDocument doc_json = QJsonDocument::fromJson(file_json.readAll());
        QJsonObject oraculo = doc_json.object();

        QJsonObject meta;
        meta[QStringLiteral("url")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("url")].toString();
        meta[QStringLiteral("alias")] = QStringLiteral("gruplac_0000000002099");
        meta[QStringLiteral("fecha_descarga")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("fecha_descarga")].toString();
        meta[QStringLiteral("sha256")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("sha256")].toString();

        auto grupo = ParserHTML::parsear_gruplac(html_text, meta, false);
        QJsonObject res = grupo.a_json();

        CHECK(res[QStringLiteral("codigo_gruplac")].toString() == oraculo[QStringLiteral("codigo_gruplac")].toString());
        CHECK(res[QStringLiteral("nombre_grupo")].isNull());
        CHECK(res[QStringLiteral("departamento_ciudad")].isNull());
        CHECK(res[QStringLiteral("integrantes")].toArray().isEmpty());
        CHECK(res[QStringLiteral("articulos")].toArray().isEmpty());
        CHECK(res[QStringLiteral("softwares")].toArray().isEmpty());
    }

    SUBCASE("Oráculo GrupLAC canónico (gruplac_00000000002099)") {
        QString ruta_html = ruta_fixtures + QStringLiteral("/gruplac_00000000002099.html");
        QString ruta_json = ruta_fixtures + QStringLiteral("/gruplac_00000000002099.esperado.json");

        QFile file_html(ruta_html);
        REQUIRE(file_html.open(QIODevice::ReadOnly));
        QByteArray bytes_html = file_html.readAll();
        QString html_text = QString::fromLatin1(bytes_html);

        QFile file_json(ruta_json);
        REQUIRE(file_json.open(QIODevice::ReadOnly));
        QJsonDocument doc_json = QJsonDocument::fromJson(file_json.readAll());
        QJsonObject oraculo = doc_json.object();

        QJsonObject meta;
        meta[QStringLiteral("url")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("url")].toString();
        meta[QStringLiteral("alias")] = QStringLiteral("gruplac_00000000002099");
        meta[QStringLiteral("fecha_descarga")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("fecha_descarga")].toString();
        meta[QStringLiteral("sha256")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("sha256")].toString();

        auto grupo = ParserHTML::parsear_gruplac(html_text, meta, false);
        QJsonObject res = grupo.a_json();

        CHECK(res[QStringLiteral("codigo_gruplac")].toString() == oraculo[QStringLiteral("codigo_gruplac")].toString());
        CHECK(res[QStringLiteral("departamento_ciudad")].toString() == oraculo[QStringLiteral("departamento_ciudad")].toString());
        CHECK(res[QStringLiteral("ano_mes_formacion")].toString() == oraculo[QStringLiteral("ano_mes_formacion")].toString());
        CHECK(res[QStringLiteral("lider")].toString() == oraculo[QStringLiteral("lider")].toString());
        CHECK(res[QStringLiteral("clasificacion")].toString() == oraculo[QStringLiteral("clasificacion")].toString());
        CHECK((res[QStringLiteral("email")].toString().contains(QStringLiteral("unicesar")) ||
               res[QStringLiteral("email")].toString().contains(QStringLiteral("CORREO"))));

        // Comprobar colecciones
        QJsonArray oraculo_integrantes = oraculo[QStringLiteral("integrantes")].toArray();
        QJsonArray res_integrantes = res[QStringLiteral("integrantes")].toArray();
        CHECK(res_integrantes.size() == oraculo_integrantes.size());
        CHECK(res_integrantes.size() >= 10);

        QJsonArray oraculo_articulos = oraculo[QStringLiteral("articulos")].toArray();
        QJsonArray res_articulos = res[QStringLiteral("articulos")].toArray();
        CHECK(res_articulos.size() == oraculo_articulos.size());
        CHECK(res_articulos.size() >= 10);

        QJsonArray oraculo_softwares = oraculo[QStringLiteral("softwares")].toArray();
        QJsonArray res_softwares = res[QStringLiteral("softwares")].toArray();
        CHECK(res_softwares.size() == oraculo_softwares.size());
        CHECK(res_softwares.size() >= 10);

        QJsonArray oraculo_inst = oraculo[QStringLiteral("instituciones")].toArray();
        QJsonArray res_inst = res[QStringLiteral("instituciones")].toArray();
        CHECK(res_inst.size() == oraculo_inst.size());

        QJsonArray oraculo_lin = oraculo[QStringLiteral("lineas_investigacion")].toArray();
        QJsonArray res_lin = res[QStringLiteral("lineas_investigacion")].toArray();
        CHECK(res_lin.size() == oraculo_lin.size());

        QJsonArray oraculo_lib = oraculo[QStringLiteral("libros")].toArray();
        QJsonArray res_lib = res[QStringLiteral("libros")].toArray();
        CHECK(res_lib.size() == oraculo_lib.size());

        QJsonArray oraculo_cap = oraculo[QStringLiteral("capitulos")].toArray();
        QJsonArray res_cap = res[QStringLiteral("capitulos")].toArray();
        CHECK(res_cap.size() == oraculo_cap.size());

        QJsonArray oraculo_td = oraculo[QStringLiteral("trabajos_dirigidos")].toArray();
        QJsonArray res_td = res[QStringLiteral("trabajos_dirigidos")].toArray();
        CHECK(res_td.size() == oraculo_td.size());

        QJsonArray oraculo_proy = oraculo[QStringLiteral("proyectos")].toArray();
        QJsonArray res_proy = res[QStringLiteral("proyectos")].toArray();
        CHECK(res_proy.size() == oraculo_proy.size());
    }

    SUBCASE("Oráculo CvLAC canónico (cvlac_0000494917)") {
        QString ruta_html = ruta_fixtures + QStringLiteral("/cvlac_0000494917.html");
        QString ruta_json = ruta_fixtures + QStringLiteral("/cvlac_0000494917.esperado.json");

        QFile file_html(ruta_html);
        REQUIRE(file_html.open(QIODevice::ReadOnly));
        QByteArray bytes_html = file_html.readAll();
        QString html_text = QString::fromLatin1(bytes_html);

        QFile file_json(ruta_json);
        REQUIRE(file_json.open(QIODevice::ReadOnly));
        QJsonDocument doc_json = QJsonDocument::fromJson(file_json.readAll());
        QJsonObject oraculo = doc_json.object();

        QJsonObject meta;
        meta[QStringLiteral("url")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("url")].toString();
        meta[QStringLiteral("alias")] = QStringLiteral("cvlac_0000494917");
        meta[QStringLiteral("fecha_descarga")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("fecha_descarga")].toString();
        meta[QStringLiteral("sha256")] = oraculo[QStringLiteral("origen")].toObject()[QStringLiteral("sha256")].toString();

        auto inv = ParserHTML::parsear_cvlac(html_text, meta, false);
        QJsonObject res = inv.a_json();

        CHECK(res[QStringLiteral("codigo_rh")].toString() == oraculo[QStringLiteral("codigo_rh")].toString());
        CHECK(res[QStringLiteral("nombre_completo")].toString() == oraculo[QStringLiteral("nombre_completo")].toString());
        CHECK(res[QStringLiteral("nacionalidad")].toString() == oraculo[QStringLiteral("nacionalidad")].toString());
        CHECK(res[QStringLiteral("sexo")].toString() == oraculo[QStringLiteral("sexo")].toString());
        CHECK(res[QStringLiteral("categoria_declarada")].toString() == oraculo[QStringLiteral("categoria_declarada")].toString());
        CHECK(res[QStringLiteral("par_evaluador")].toBool() == oraculo[QStringLiteral("par_evaluador")].toBool());

        QJsonArray oraculo_form = oraculo[QStringLiteral("formacion")].toArray();
        QJsonArray res_form = res[QStringLiteral("formacion")].toArray();
        CHECK(res_form.size() == oraculo_form.size());
        CHECK(res_form.size() >= 1);

        QJsonArray oraculo_art = oraculo[QStringLiteral("articulos")].toArray();
        QJsonArray res_art = res[QStringLiteral("articulos")].toArray();
        CHECK(res_art.size() == oraculo_art.size());
        CHECK(res_art.size() >= 10);

        QJsonArray oraculo_soft = oraculo[QStringLiteral("softwares")].toArray();
        QJsonArray res_soft = res[QStringLiteral("softwares")].toArray();
        CHECK(res_soft.size() == oraculo_soft.size());
        CHECK(res_soft.size() >= 5);

        QJsonArray oraculo_areas = oraculo[QStringLiteral("areas_actuacion")].toArray();
        QJsonArray res_areas = res[QStringLiteral("areas_actuacion")].toArray();
        CHECK(res_areas.size() == oraculo_areas.size());

        QJsonArray oraculo_lin = oraculo[QStringLiteral("lineas_investigacion")].toArray();
        QJsonArray res_lin = res[QStringLiteral("lineas_investigacion")].toArray();
        CHECK(res_lin.size() == oraculo_lin.size());

        QJsonArray oraculo_cap = oraculo[QStringLiteral("capitulos")].toArray();
        QJsonArray res_cap = res[QStringLiteral("capitulos")].toArray();
        CHECK(res_cap.size() == oraculo_cap.size());

        QJsonArray oraculo_td = oraculo[QStringLiteral("trabajos_dirigidos")].toArray();
        QJsonArray res_td = res[QStringLiteral("trabajos_dirigidos")].toArray();
        CHECK(res_td.size() == oraculo_td.size());

        QJsonArray oraculo_proy = oraculo[QStringLiteral("proyectos")].toArray();
        QJsonArray res_proy = res[QStringLiteral("proyectos")].toArray();
        CHECK(res_proy.size() == oraculo_proy.size());
    }
}

TEST_CASE("Ingesta C++ - ExtractorURL y Políticas de Seguridad") {
    SUBCASE("Rechazo de esquemas no seguros y hosts no permitidos") {
        // 1. Debe rechazar esquemas no seguros (HTTP)
        CHECK_THROWS_WITH_AS(
            ExtractorURL::validar_url(QStringLiteral("http://scienti.minciencias.gov.co/gruplac")),
            "Protocolo no permitido ('http'). Solo se permite HTTPS.",
            std::runtime_error
        );

        // 2. Debe rechazar hosts ajenos
        CHECK_THROWS_WITH_AS(
            ExtractorURL::validar_url(QStringLiteral("https://otro-dominio.com/gruplac")),
            "Host no permitido ('otro-dominio.com'). Solo se permite scienti.minciencias.gov.co.",
            std::runtime_error
        );

        // 3. Debe rechazar rutas no reconocidas
        CHECK_THROWS_WITH_AS(
            ExtractorURL::validar_url(QStringLiteral("https://scienti.minciencias.gov.co/ruta_invalida")),
            "URL no reconocida como GrupLAC ni CvLAC: https://scienti.minciencias.gov.co/ruta_invalida",
            std::runtime_error
        );

        // 4. Aceptación correcta de URLs oficiales
        auto [tipo_g, query_g] = ExtractorURL::validar_url(
            QStringLiteral("https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099")
        );
        CHECK(tipo_g == QStringLiteral("gruplac"));
        CHECK(query_g.contains(QStringLiteral("00000000002099")));

        auto [tipo_c, query_c] = ExtractorURL::validar_url(
            QStringLiteral("https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917")
        );
        CHECK(tipo_c == QStringLiteral("cvlac"));
        CHECK(query_c.contains(QStringLiteral("0000494917")));
    }
}

TEST_CASE("Ingesta C++ - LectorCSV Delimitadores, BOM y Tolerancia a Filas") {
    QTemporaryDir temp_dir;
    REQUIRE(temp_dir.isValid());

    SUBCASE("Delimitador coma y detección de columnas") {
        QString ruta = temp_dir.filePath(QStringLiteral("grupos_coma.csv"));
        QFile f(ruta);
        REQUIRE(f.open(QIODevice::WriteOnly | QIODevice::Text));
        f.write("codigo_minciencias,nombre,clasificacion,institucion\n"
                "COL0008543,Grupo de Tecnologias UPC,A1,Universidad Popular del Cesar\n"
                "COL0009999,Grupo de Materiales,B,Universidad Popular del Cesar\n");
        f.close();

        auto [grupos, errores] = LectorCSV::leer_grupos(ruta);
        CHECK(errores.isEmpty());
        CHECK(grupos.tamano() == 2);
        CHECK(grupos.cabeza()->dato.codigo_gruplac == QStringLiteral("COL0008543"));
        CHECK(grupos.cabeza()->dato.categoria == QStringLiteral("A1"));
    }

    SUBCASE("Delimitador punto y coma") {
        QString ruta = temp_dir.filePath(QStringLiteral("inv_punto_coma.csv"));
        QFile f(ruta);
        REQUIRE(f.open(QIODevice::WriteOnly | QIODevice::Text));
        f.write("codigo_cvlac;nombre_completo;categoria;nacionalidad\n"
                "0000494917;Perez Juan Carlos;Investigador Senior;Colombia\n"
                "0000123456;Gomez Maria;Investigador Junior;Colombia\n");
        f.close();

        auto [invs, errores] = LectorCSV::leer_investigadores(ruta);
        CHECK(errores.isEmpty());
        CHECK(invs.tamano() == 2);
        CHECK(invs.cabeza()->dato.codigo_rh == QStringLiteral("0000494917"));
        CHECK(invs.cola()->dato.categoria == QStringLiteral("Investigador Junior"));
    }

    SUBCASE("Soporte BOM UTF-8 (\\xef\\xbb\\xbf)") {
        QString ruta = temp_dir.filePath(QStringLiteral("grupos_bom.csv"));
        QFile f(ruta);
        REQUIRE(f.open(QIODevice::WriteOnly));
        QByteArray bom_content = "\xef\xbb\xbf" "codigo_minciencias,nombre,clasificacion\nCOL001,Grupo Con BOM,A1\n";
        f.write(bom_content);
        f.close();

        auto [grupos, errores] = LectorCSV::leer_grupos(ruta);
        CHECK(errores.isEmpty());
        CHECK(grupos.tamano() == 1);
        CHECK(grupos.cabeza()->dato.codigo_gruplac == QStringLiteral("COL001"));
        CHECK(grupos.cabeza()->dato.nombre == QStringLiteral("Grupo Con BOM"));
    }

    SUBCASE("Comillas escapadas y comas internas") {
        QString ruta = temp_dir.filePath(QStringLiteral("prods_comillas.csv"));
        QFile f(ruta);
        REQUIRE(f.open(QIODevice::WriteOnly | QIODevice::Text));
        f.write("codigo_identificador,titulo,tipo_categoria,anio,estado_validacion,grupo_codigo\n"
                "PROD-001,\"Analisis de \"\"Redes Complejas\"\", con comas y comillas\",Articulo,2023,Aprobado,COL0008543\n");
        f.close();

        auto [prods, errores] = LectorCSV::leer_productos(ruta);
        CHECK(errores.isEmpty());
        REQUIRE(prods.size() == 1);
        CHECK(prods[0].first.codigo_identificador == QStringLiteral("PROD-001"));
        CHECK(prods[0].first.titulo.contains(QStringLiteral("Analisis de \"Redes Complejas\", con comas y comillas")));
        CHECK(prods[0].second == QStringLiteral("COL0008543"));
    }

    SUBCASE("Tolerancia a filas erróneas sin romper el procesamiento general") {
        QString ruta = temp_dir.filePath(QStringLiteral("prods_con_error.csv"));
        QFile f(ruta);
        REQUIRE(f.open(QIODevice::WriteOnly | QIODevice::Text));
        f.write("codigo_identificador,titulo,tipo_categoria,anio,estado_validacion\n"
                "PROD-001,Producto Valido 1,Articulo,2021,Aprobado\n"
                "PROD-002,Producto Fila Rota,Articulo,ANO_INVALIDO,Aprobado\n"
                "PROD-003,Producto Valido 3,Software,2023,Aprobado\n");
        f.close();

        auto [prods, errores] = LectorCSV::leer_productos(ruta);
        CHECK(prods.size() == 2);
        CHECK(errores.size() == 1);
        CHECK(errores[0].contains(QStringLiteral("3"))); // Fila 3 del archivo (encabezado es 1, fila 1 es 2, fila 2 es 3)
        CHECK(prods[0].first.codigo_identificador == QStringLiteral("PROD-001"));
        CHECK(prods[1].first.codigo_identificador == QStringLiteral("PROD-003"));
    }
}

TEST_CASE("Ingesta C++ - ServicioIngesta y Cola de Tareas") {
    QTemporaryDir temp_dir;
    REQUIRE(temp_dir.isValid());

    auto catalogo = std::make_shared<servicios::CatalogoInvestigacion>();
    ServicioIngesta servicio(catalogo);

    SUBCASE("Ciclo de estados FIFO de la cola propia") {
        QString csv_path = temp_dir.filePath(QStringLiteral("grupos.csv"));
        QFile f(csv_path);
        REQUIRE(f.open(QIODevice::WriteOnly | QIODevice::Text));
        f.write("codigo_minciencias,nombre,clasificacion\n"
                "PRUEBA-GRP-ING-1,Grupo Ingesta 1,A1\n");
        f.close();

        auto tarea = servicio.encolar_csv(csv_path, QStringLiteral("grupos"), false);
        CHECK(tarea.estado == estructuras::EstadoTarea::Pendiente);
        CHECK(!servicio.cola().esta_vacia());

        auto informe = servicio.procesar_siguiente();
        REQUIRE(informe.has_value());
        CHECK(informe->exito);
        CHECK(informe->grupos_procesados == 1);
        CHECK(servicio.cola().esta_vacia());

        // Verificar inserción en memoria del catálogo
        auto g = catalogo->buscar_grupo(QStringLiteral("PRUEBA-GRP-ING-1"));
        REQUIRE(g != nullptr);
        CHECK(g->nombre == QStringLiteral("Grupo Ingesta 1"));
    }

    SUBCASE("Tarea con error no rompe la cola") {
        auto tarea = servicio.encolar_csv(QStringLiteral("archivo_inexistente.csv"), QStringLiteral("grupos"), false);
        CHECK(tarea.estado == estructuras::EstadoTarea::Pendiente);

        auto informe = servicio.procesar_siguiente();
        REQUIRE(informe.has_value());
        CHECK(!informe->exito);
        CHECK(servicio.cola().esta_vacia());
    }

    SUBCASE("Desduplicación y vinculación en Multilista") {
        // 1. Crear grupo
        catalogo->crear_grupo(std::make_shared<dominio::Grupo>(QStringLiteral("GRP-01"), QStringLiteral("Grupo 01")), false);
        // 2. Crear investigador
        catalogo->crear_investigador(std::make_shared<dominio::Investigador>(QStringLiteral("INV-01"), QStringLiteral("Investigador 01")), false);

        // 3. Encolar CSVs de producto y autor
        QString csv_prods = temp_dir.filePath(QStringLiteral("prods.csv"));
        QFile fp(csv_prods);
        REQUIRE(fp.open(QIODevice::WriteOnly | QIODevice::Text));
        fp.write("codigo_identificador,titulo,tipo_categoria,anio,grupo_codigo\n"
                 "P-001,Articulo Base,Articulo,2023,GRP-01\n");
        fp.close();

        QString csv_autores = temp_dir.filePath(QStringLiteral("autores.csv"));
        QFile fa(csv_autores);
        REQUIRE(fa.open(QIODevice::WriteOnly | QIODevice::Text));
        fa.write("producto_codigo,investigador_codigo,orden_autoria\n"
                 "P-001,INV-01,1\n");
        fa.close();

        servicio.encolar_csv(csv_prods, QStringLiteral("productos"), false);
        servicio.encolar_csv(csv_autores, QStringLiteral("autores"), false);

        auto informes = servicio.procesar_todas();
        CHECK(informes.size() == 2);

        // Verificar nodo en la multilista
        auto* nodo_p = catalogo->multilista_productos.buscar_nodo(QStringLiteral("P-001"));
        REQUIRE(nodo_p != nullptr);
        REQUIRE(nodo_p->producto != nullptr);
        REQUIRE(nodo_p->grupo != nullptr);
        CHECK(nodo_p->grupo->codigo_gruplac == QStringLiteral("GRP-01"));
        REQUIRE(nodo_p->autores.tamano() == 1);
        CHECK(nodo_p->autores.cabeza()->dato->codigo_rh == QStringLiteral("INV-01"));
    }
}
