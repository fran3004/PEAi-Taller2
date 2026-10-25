// Solo importa una autoría entre dos entidades sintéticas ya creadas por el orquestador.
#include <QCoreApplication>
#include <QFile>
#include <QJsonDocument>
#include <iostream>
#include "pea/cliente_http.hpp"
#include "pea/ingesta/lector_csv.hpp"
#include "pea/ingesta/servicio_ingesta.hpp"

int main(int argc, char** argv) {
    QCoreApplication app(argc, argv);
    try {
        if (argc != 3) return 2;
        QFile archivo(argv[1]);
        if (!archivo.open(QIODevice::ReadOnly)) return 2;
        const auto fixture = QJsonDocument::fromJson(archivo.readAll()).object();
        auto producto = std::make_shared<pea::dominio::Producto>(
            pea::dominio::Producto::desdeJson(fixture.value("producto").toObject()));
        auto investigador = std::make_shared<pea::dominio::Investigador>(
            pea::dominio::Investigador::desdeJson(fixture.value("investigador").toObject()));
        if (!producto->es_ejemplo || !investigador->es_ejemplo ||
            !producto->codigo_identificador.startsWith("PRUEBA-") ||
            !investigador->codigo_rh.startsWith("PRUEBA-") ||
            !producto->id.value_or(0) || !investigador->id.value_or(0)) return 2;
        const auto [relaciones, errores] = pea::ingesta::LectorCSV::leer_autores(argv[2]);
        if (!errores.isEmpty() || relaciones.size() != 1 ||
            relaciones.front().producto_codigo != producto->codigo_identificador ||
            relaciones.front().investigador_codigo != investigador->codigo_rh ||
            relaciones.front().orden_autoria != 2) return 2;

        pea::ClienteHTTPSupabase cliente(qEnvironmentVariable("PRUEBA_URL"), qEnvironmentVariable("PRUEBA_KEY"));
        cliente.establecerTokenAcceso(qEnvironmentVariable("PRUEBA_TOKEN"));
        // Validar también los padres remotos antes de permitir la escritura.
        for (const auto& tabla : {QStringLiteral("productos"), QStringLiteral("investigadores")}) {
            const bool es_producto = tabla == "productos";
            const auto id = es_producto ? *producto->id : *investigador->id;
            const auto codigo = es_producto ? producto->codigo_identificador : investigador->codigo_rh;
            const auto campo = es_producto ? QStringLiteral("codigo_identificador") : QStringLiteral("codigo_rh");
            const auto filas = cliente.get(tabla, QStringLiteral("id=eq.%1&es_ejemplo=eq.true").arg(id)).array();
            if (filas.size() != 1 || filas.first().toObject().value(campo).toString() != codigo) return 2;
        }
        auto catalogo = std::make_shared<pea::servicios::CatalogoInvestigacion>(&cliente);
        catalogo->crear_producto(producto, {}, {}, false);
        catalogo->crear_investigador(investigador, false);
        pea::ingesta::ServicioIngesta servicio(catalogo);
        const auto filtro = QStringLiteral("producto_id=eq.%1&investigador_id=eq.%2").arg(*producto->id).arg(*investigador->id);
        if (!cliente.get("producto_autores", filtro).array().isEmpty()) return 2;
        QJsonObject guardada;
        for (int intento = 0; intento < 2; ++intento) {
            servicio.encolar_csv(argv[2], "autores", true);
            const auto informe = servicio.procesar_siguiente();
            if (!informe || !informe->exito || informe->autores_procesados != 1 ||
                !informe->advertencias.isEmpty() || !informe->filas_erroneas.isEmpty()) return 1;
            const auto filas = cliente.get("producto_autores", filtro).array();
            if (filas.size() != 1) return 1;
            const auto fila = filas.first().toObject();
            if (!fila.value("es_ejemplo").toBool() || !fila.value("activo").toBool() ||
                fila.value("orden_autoria").toInt() != 2) return 1;
            if (intento == 0) {
                guardada = fila;
                // Confirmar el código PostgreSQL real, sin imprimir detalles de la respuesta.
                bool duplicado = false;
                try {
                    cliente.post("producto_autores", QJsonDocument(QJsonObject{
                        {"producto_id", *producto->id}, {"investigador_id", *investigador->id},
                        {"orden_autoria", 2}, {"activo", true}, {"es_ejemplo", true}}));
                } catch (const pea::ConflictoRevision& error) {
                    duplicado = QJsonDocument::fromJson(QByteArray::fromStdString(error.detalle()))
                                    .object().value("code").toString() == "23505";
                }
                if (!duplicado) return 1;
            } else if (fila != guardada) return 1;
        }
        cliente.cerrarSesion();
        std::cout << "{\"guardado\":true,\"duplicado_idempotente\":true,\"codigo_duplicado\":\"23505\",\"importaciones_csv\":2}\n";
        return 0;
    } catch (const pea::ErrorPEA& error) {
        const auto codigo = QJsonDocument::fromJson(QByteArray::fromStdString(error.detalle()))
                                .object().value("code").toString();
        std::cerr << "Fallo remoto C++; codigo PostgreSQL: " << codigo.toStdString() << '\n';
        return 1;
    } catch (const std::exception&) {
        std::cerr << "Comprobacion C++ incompleta\n";
        return 1;
    }
}
