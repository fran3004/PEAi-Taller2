#include <doctest/doctest.h>
#include <QCoreApplication>
#include <QHostAddress>
#include <QTcpServer>
#include <QTcpSocket>
#include "pea/cliente_http.hpp"
#include "pea/datos/sesion.hpp"
#include "pea/datos/revision.hpp"
#include "pea/excepciones.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

using namespace pea::datos;
using namespace pea::servicios;
using namespace pea::dominio;

TEST_CASE("La revisión remota usa meta como respaldo y falla explícitamente si ambos mecanismos fallan") {
    int argc = 1;
    char nombre_aplicacion[] = "pruebas_cpp";
    char* argumentos[] = {nombre_aplicacion, nullptr};
    QCoreApplication aplicacion(argc, argumentos);
    QTcpServer servidor;
    REQUIRE(servidor.listen(QHostAddress::LocalHost, 0));

    bool meta_disponible = true;
    QObject::connect(&servidor, &QTcpServer::newConnection, &servidor, [&] {
        while (servidor.hasPendingConnections()) {
            QTcpSocket* socket = servidor.nextPendingConnection();
            auto* solicitud = new QByteArray;
            QObject::connect(socket, &QTcpSocket::readyRead, socket, [socket, solicitud, &meta_disponible] {
                *solicitud += socket->readAll();
                const qsizetype fin_cabeceras = solicitud->indexOf("\r\n\r\n");
                if (fin_cabeceras < 0) return;

                qsizetype longitud_cuerpo = 0;
                const auto lineas = solicitud->left(fin_cabeceras).split('\n');
                for (const QByteArray& linea : lineas) {
                    if (linea.toLower().startsWith("content-length:")) {
                        longitud_cuerpo = linea.mid(linea.indexOf(':') + 1).trimmed().toLongLong();
                    }
                }
                if (solicitud->size() < fin_cabeceras + 4 + longitud_cuerpo) return;

                const bool es_meta = solicitud->startsWith("GET /rest/v1/meta?");
                const bool exito = es_meta && meta_disponible;
                const QByteArray cuerpo = exito ? "[{\"revision\":7}]" : "{\"mensaje\":\"fallo de prueba\"}";
                const QByteArray estado = exito ? "200 OK" : "500 Error de prueba";
                const QByteArray respuesta =
                    "HTTP/1.1 " + estado + "\r\nContent-Type: application/json\r\nContent-Length: " +
                    QByteArray::number(cuerpo.size()) + "\r\nConnection: close\r\n\r\n" + cuerpo;
                socket->write(respuesta);
                socket->disconnectFromHost();
            });
            QObject::connect(socket, &QTcpSocket::disconnected, socket, [socket, solicitud] {
                delete solicitud;
                socket->deleteLater();
            });
        }
    });

    const QString url = QString("http://127.0.0.1:%1").arg(servidor.serverPort());
    pea::ClienteHTTPSupabase cliente(url, "clave-publicable-de-prueba", 2000);
    ControladorRevision controlador(3);

    CHECK(controlador.consultar_remota(cliente) == 7);
    CHECK(controlador.revision_local() == 3);

    meta_disponible = false;
    CHECK_THROWS_AS((void)controlador.consultar_remota(cliente), pea::ErrorConexion);
    CHECK(controlador.revision_local() == 3);
}

TEST_CASE("El cliente clasifica P0001 de PostgREST como conflicto de revisión") {
    int argc = 1;
    char nombre_aplicacion[] = "pruebas_cpp";
    char* argumentos[] = {nombre_aplicacion, nullptr};
    QCoreApplication aplicacion(argc, argumentos);
    QTcpServer servidor;
    REQUIRE(servidor.listen(QHostAddress::LocalHost, 0));

    QObject::connect(&servidor, &QTcpServer::newConnection, &servidor, [&] {
        while (servidor.hasPendingConnections()) {
            QTcpSocket* socket = servidor.nextPendingConnection();
            auto* solicitud = new QByteArray;
            QObject::connect(socket, &QTcpSocket::readyRead, socket, [socket, solicitud] {
                *solicitud += socket->readAll();
                const qsizetype fin_cabeceras = solicitud->indexOf("\r\n\r\n");
                if (fin_cabeceras < 0) return;

                qsizetype longitud_cuerpo = 0;
                const auto lineas = solicitud->left(fin_cabeceras).split('\n');
                for (const QByteArray& linea : lineas) {
                    if (linea.toLower().startsWith("content-length:")) {
                        longitud_cuerpo = linea.mid(linea.indexOf(':') + 1).trimmed().toLongLong();
                    }
                }
                if (solicitud->size() < fin_cabeceras + 4 + longitud_cuerpo) return;

                const QByteArray cuerpo =
                    R"json({"code":"P0001","message":"CONFLICTO_REVISION: La base de datos cambio (remota 2, esperada 1)"})json";
                const QByteArray respuesta =
                    "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: " +
                    QByteArray::number(cuerpo.size()) + "\r\nConnection: close\r\n\r\n" + cuerpo;
                socket->write(respuesta);
                socket->disconnectFromHost();
            });
            QObject::connect(socket, &QTcpSocket::disconnected, socket, [socket, solicitud] {
                delete solicitud;
                socket->deleteLater();
            });
        }
    });

    const QString url = QString("http://127.0.0.1:%1").arg(servidor.serverPort());
    pea::ClienteHTTPSupabase cliente(url, "clave-publicable-de-prueba", 2000);
    CHECK_THROWS_AS(cliente.rpc("transaccion_crear_producto"), pea::ConflictoRevision);
}

TEST_CASE("Las escrituras persistentes sin cliente Supabase se bloquean antes de mutar") {
    CatalogoInvestigacion catalogo;
    auto grupo = std::make_shared<Grupo>("PRUEBA-OFFLINE-01", "Grupo fuera de línea");

    CHECK_THROWS_AS(catalogo.crear_grupo(grupo), pea::ErrorConexion);
    CHECK(catalogo.grupos.estaVacia());

    CHECK_NOTHROW(catalogo.crear_grupo(grupo, false));
    CHECK(catalogo.grupos.tamano() == 1);
}

TEST_CASE("Sesión - ciclo de vida en memoria y expiración") {
    Sesion sesion;
    CHECK_FALSE(sesion.esta_autenticado());
    CHECK(sesion.rol() == "anon");

    sesion.iniciar_sesion("test_jwt_token_123", "usuario@upc.edu.co", 3600);
    CHECK(sesion.esta_autenticado());
    CHECK(sesion.rol() == "authenticated");
    CHECK(sesion.token_acceso() == "test_jwt_token_123");

    // Simular expiración de token
    sesion.simular_expiracion();
    CHECK(sesion.esta_expirada());
    CHECK_THROWS_AS((void)sesion.token_acceso(), pea::ErrorAutenticacion);
    CHECK_FALSE(sesion.esta_autenticado());


}

TEST_CASE("Resumen JSON - Paridad canónica con Python") {
    CatalogoInvestigacion catalogo;

    // Catálogo vacío
    QByteArray jsonVacio = catalogo.resumen_json();
    QByteArray esperadoVacio = "{\"grupos_activos\":0,\"grupos_totales\":0,\"investigadores_activos\":0,\"investigadores_totales\":0,\"pila_deshacer_tamano\":0,\"productos_activos\":0,\"productos_totales\":0}";
    CHECK(jsonVacio == esperadoVacio);

    // Con entidades añadidas
    auto g = std::make_shared<Grupo>("GRP-PAR-01", "Grupo Paridad", "A");
    auto inv = std::make_shared<Investigador>("INV-PAR-01", "Investigador Paridad");
    catalogo.crear_grupo(g, false);
    catalogo.crear_investigador(inv, false);

    auto p1 = std::make_shared<Producto>("P-PAR-01", "Prod Activo", "GNC", "Articulo", 2024);
    auto p2 = std::make_shared<Producto>("P-PAR-02", "Prod Inactivo", "DTI", "Software", 2025);
    catalogo.crear_producto(p1, g->codigo_gruplac, {inv->codigo_rh}, false);
    catalogo.crear_producto(p2, g->codigo_gruplac, {inv->codigo_rh}, false);
    catalogo.desactivar_producto(p2->codigo_identificador, false);

    QByteArray jsonConDatos = catalogo.resumen_json();
    // 1 grupo activo (1 total)
    // 1 investigador activo (1 total)
    // 1 producto activo (2 totales)
    // 4 operaciones en pila (crear grupo, crear inv, crear p1, crear p2, desactivar p2 = 5)
    QJsonObject dict = catalogo.resumen_dict();
    CHECK(dict["grupos_activos"].toInt() == 1);
    CHECK(dict["grupos_totales"].toInt() == 1);
    CHECK(dict["investigadores_activos"].toInt() == 1);
    CHECK(dict["investigadores_totales"].toInt() == 1);
    CHECK(dict["productos_activos"].toInt() == 1);
    CHECK(dict["productos_totales"].toInt() == 2);
    CHECK(dict["pila_deshacer_tamano"].toInt() == 5);
}

TEST_CASE("La revisión remota solo acepta valores mayores que cero (paridad con Python)") {
    int argc = 1;
    char nombre_aplicacion[] = "pruebas_cpp";
    char* argumentos[] = {nombre_aplicacion, nullptr};
    QCoreApplication aplicacion(argc, argumentos);
    QTcpServer servidor;
    REQUIRE(servidor.listen(QHostAddress::LocalHost, 0));

    // Mismos casos que tests/unit/test_revision_remota.py
    QByteArray cuerpo_rpc;
    QByteArray estado_rpc;
    QByteArray cuerpo_meta;
    QByteArray estado_meta;
    QObject::connect(&servidor, &QTcpServer::newConnection, &servidor, [&] {
        while (servidor.hasPendingConnections()) {
            QTcpSocket* socket = servidor.nextPendingConnection();
            auto* solicitud = new QByteArray;
            QObject::connect(socket, &QTcpSocket::readyRead, socket, [&, socket, solicitud] {
                *solicitud += socket->readAll();
                const qsizetype fin_cabeceras = solicitud->indexOf("\r\n\r\n");
                if (fin_cabeceras < 0) return;

                qsizetype longitud_cuerpo = 0;
                const auto lineas = solicitud->left(fin_cabeceras).split('\n');
                for (const QByteArray& linea : lineas) {
                    if (linea.toLower().startsWith("content-length:")) {
                        longitud_cuerpo = linea.mid(linea.indexOf(':') + 1).trimmed().toLongLong();
                    }
                }
                if (solicitud->size() < fin_cabeceras + 4 + longitud_cuerpo) return;

                const bool es_meta = solicitud->startsWith("GET /rest/v1/meta?");
                const QByteArray cuerpo = es_meta ? cuerpo_meta : cuerpo_rpc;
                const QByteArray estado = es_meta ? estado_meta : estado_rpc;
                const QByteArray respuesta =
                    "HTTP/1.1 " + estado + "\r\nContent-Type: application/json\r\nContent-Length: " +
                    QByteArray::number(cuerpo.size()) + "\r\nConnection: close\r\n\r\n" + cuerpo;
                socket->write(respuesta);
                socket->disconnectFromHost();
            });
            QObject::connect(socket, &QTcpSocket::disconnected, socket, [socket, solicitud] {
                delete solicitud;
                socket->deleteLater();
            });
        }
    });

    const QString url = QString("http://127.0.0.1:%1").arg(servidor.serverPort());
    pea::ClienteHTTPSupabase cliente(url, "clave-publicable-de-prueba", 2000);
    ControladorRevision controlador(3);
    const QByteArray error_500 = "500 Error de prueba";
    const QByteArray fallo = "{\"mensaje\":\"fallo de prueba\"}";

    // (a) La RPC responde bien.
    cuerpo_rpc = "{\"revision\":7}";
    estado_rpc = "200 OK";
    cuerpo_meta = fallo;
    estado_meta = error_500;
    CHECK(controlador.consultar_remota(cliente) == 7);

    // (b) La RPC falla o devuelve cero/negativo; meta responde bien.
    for (const QByteArray& rpc : {QByteArray(), QByteArray("{\"revision\":0}"), QByteArray("{\"revision\":-1}")}) {
        cuerpo_rpc = rpc.isEmpty() ? fallo : rpc;
        estado_rpc = rpc.isEmpty() ? error_500 : QByteArray("200 OK");
        cuerpo_meta = "[{\"revision\":9}]";
        estado_meta = "200 OK";
        CHECK(controlador.consultar_remota(cliente) == 9);
    }

    // (c) Ambas fallan.
    cuerpo_rpc = fallo;
    estado_rpc = error_500;
    cuerpo_meta = fallo;
    estado_meta = error_500;
    CHECK_THROWS_AS((void)controlador.consultar_remota(cliente), pea::ErrorConexion);

    // (d) meta vacía o con revisión no válida.
    for (const QByteArray& meta : {QByteArray("[]"), QByteArray("[{}]"), QByteArray("[{\"revision\":0}]"),
                                   QByteArray("[{\"revision\":-4}]"), QByteArray("[{\"revision\":null}]")}) {
        cuerpo_meta = meta;
        estado_meta = "200 OK";
        try {
            (void)controlador.consultar_remota(cliente);
            FAIL("Se esperaba ErrorConexion para meta = " << meta.toStdString());
        } catch (const pea::ErrorConexion& error) {
            const std::string texto = error.what();
            CHECK(texto.rfind("No fue posible verificar la revisión remota. RPC: ", 0) == 0);
            CHECK(texto.find(" Consulta meta: La tabla meta no devolvió una revisión válida.") !=
                  std::string::npos);
        }
    }
    CHECK(controlador.revision_local() == 3);
}
