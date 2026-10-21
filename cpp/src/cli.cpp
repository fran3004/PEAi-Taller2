#include "pea/cli.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"
#include "pea/ingesta/servicio_ingesta.hpp"
#include "pea/ingesta/extractor_url.hpp"
#include "pea/version.hpp"
#include "pea/datos/configuracion_conexion.hpp"
#include "pea/datos/exportador_csv.hpp"

#include <iostream>
#include <memory>
#include <exception>
#include <array>
#include <QDir>
#include <QFileInfo>
#include <QStringList>

namespace pea::cli {

namespace {

std::unique_ptr<ClienteHTTPSupabase> obtenerClienteDesdeEntorno() {
    return datos::crear_cliente_configurado();
}

void mostrarAyuda() {
    std::cout << "PEA-i · Programa Estadístico de Análisis de Investigación (" << INSTITUCION << ")\n"
              << "Uso: pea-cpp [COMANDO] [OPCIONES]\n\n"
              << "Comandos disponibles:\n"
              << "  info                     Muestra información del sistema y arquitectura\n"
              << "  verificar                Verifica conectividad HTTPS, TLS y número de revisión\n"
              << "  ping                     Alias de verificar\n"
              << "  resumen [--json]         Muestra el resumen de entidades (o JSON canónico)\n"
              << "  importar-csv -a <f> -t <t> Importa entidades desde archivo CSV (grupos|investigadores|productos|autores)\n"
              << "  importar-url -u <u>        Importa entidades desde URL SCIENTI (GrupLAC o CvLAC)\n"
              << "  exportar-csv -d <dir>    Exporta entidades del catálogo a archivos CSV\n"
              << "  cargar-ejemplo           Carga datos oficiales de prueba con prefijo PRUEBA-\n"
              << "  aplicar-escenario        Ejecuta escenario de mutación y reversión (Undo LIFO)\n"
              << "  -v, --version            Muestra la versión de la aplicación y sale\n"
              << "  -h, --help               Muestra este mensaje de ayuda y sale\n"
              << "Opciones de terminal: --demo, --sin-color, --ascii, --sin-animacion\n"
              << "Terminal recomendada: Windows Terminal.\n";
}

int comandoInfo() {
    std::cout << "Nombre: " << APP_NAME << "\n";
    std::cout << "Versión: " << APP_VERSION << "\n";
    std::cout << "Institución: " << INSTITUCION << "\n";
    std::cout << "Arquitectura: C++17 / Qt6 Core + Network / terminal TUI / Estructuras Hechas a Mano\n";
    return 0;
}


int comandoVerificar() {
    auto cliente = obtenerClienteDesdeEntorno();
    if (!cliente) {
        std::cerr << "Error: configure la URL y la clave publicable de pea-prod para verificar la conexión.\n";
        return 1;
    }

    try {
        servicios::CatalogoInvestigacion catalogo(cliente.get());
        qint64 rev = catalogo.controlador_revision.consultar_remota(*cliente);
        std::cout << "============================================================\n";
        std::cout << "ESTADO DE CONEXIÓN REMOTA SUPABASE\n";
        std::cout << "============================================================\n";
        std::cout << "Base URL: " << cliente->baseUrl().toStdString() << "\n";
        std::cout << "Protocolo: HTTPS / TLS activo\n";
        std::cout << "Revisión remota actual (meta.revision): " << rev << "\n";
        std::cout << "Conectividad: OK\n";
        std::cout << "============================================================\n";
        return 0;
    } catch (const std::exception& err) {
        std::cerr << "Error conectando a Supabase: " << err.what() << "\n";
        return 1;
    }
}

int comandoResumen(bool salidaJson) {
    auto cliente = obtenerClienteDesdeEntorno();
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    if (cliente) {
        try {
            catalogo.recargar_todo();
        } catch (const std::exception& err) {
            std::cerr << "Error: no se pudo recargar de Supabase; se cancela el resumen para evitar mostrar datos obsoletos ("
                      << err.what() << ").\n";
            return 1;
        }
    }

    if (salidaJson) {
        std::cout << catalogo.resumen_json().toStdString() << "\n";
        return 0;
    }

    QJsonObject obj = catalogo.resumen_dict();
    std::cout << "============================================================\n";
    std::cout << "RESUMEN GENERAL DEL CATÁLOGO DE INVESTIGACIÓN\n";
    std::cout << "============================================================\n";
    std::cout << "Grupos de Investigación: " << obj["grupos_totales"].toInt() << " totales (" << obj["grupos_activos"].toInt() << " activos)\n";
    std::cout << "Investigadores:          " << obj["investigadores_totales"].toInt() << " totales (" << obj["investigadores_activos"].toInt() << " activos)\n";
    std::cout << "Productos Científicos:   " << obj["productos_totales"].toInt() << " totales (" << obj["productos_activos"].toInt() << " activos)\n";
    std::cout << "Pila de Deshacer:        " << obj["pila_deshacer_tamano"].toInt() << " operaciones apiladas\n";
    std::cout << "============================================================\n";
    return 0;
}

int comandoImportarCsv(const QString& rutaArchivo, const QString& tipo) {
    auto cliente = obtenerClienteDesdeEntorno();
    if (!cliente) {
        std::cerr << "Error: conectar con Supabase antes de importar; no se guardaron datos locales como si fueran actuales.\n";
        return 1;
    }
    auto catalogo = std::make_shared<servicios::CatalogoInvestigacion>(cliente.get());

    ingesta::ServicioIngesta servicio(catalogo);
    servicio.encolar_csv(rutaArchivo, tipo, true);
    auto informe = servicio.procesar_siguiente();

    if (!informe || !informe->exito) {
        std::cerr << "Error al importar CSV: " << (informe ? informe->mensaje.toStdString() : "Error desconocido") << "\n";
        return 1;
    }

    int total = informe->grupos_procesados + informe->investigadores_procesados + informe->productos_procesados + informe->autores_procesados;
    std::cout << "Importación completada: " << total << " entidades procesadas con éxito.\n";
    if (!informe->filas_erroneas.isEmpty()) {
        std::cout << "Aviso: " << informe->filas_erroneas.size() << " filas omitidas por inconsistencias.\n";
        std::cout << formatear_errores_importacion_csv(informe->filas_erroneas).toStdString() << "\n";
    }
    return 0;
}

int comandoImportarUrl(const QString& url, bool persistir, bool anonimizar) {
    auto cliente = obtenerClienteDesdeEntorno();
    if (persistir && !cliente) {
        std::cerr << "Error: se solicitó persistir la importación, pero no hay conexión a Supabase.\n";
        return 1;
    }
    auto catalogo = std::make_shared<servicios::CatalogoInvestigacion>(cliente.get());

    ingesta::ServicioIngesta servicio(catalogo);
    try {
        servicio.encolar_url(url, persistir, anonimizar);
        auto informe = servicio.procesar_siguiente();
        if (!informe || !informe->exito) {
            std::cerr << "Error en extracción web: " << (informe ? informe->mensaje.toStdString() : "Error desconocido") << "\n";
            return 1;
        }

        std::cout << "============================================================\n";
        std::cout << "INFORME DE EXTRACCIÓN SCIENTI\n";
        std::cout << "============================================================\n";
        std::cout << "Origen:                   " << informe->origen.toStdString() << "\n";
        std::cout << "Tipo de Fuente:           " << informe->tipo_fuente.toStdString() << "\n";
        std::cout << "Grupos procesados:        " << informe->grupos_procesados << "\n";
        std::cout << "Investigadores procesados: " << informe->investigadores_procesados << "\n";
        std::cout << "Productos procesados:      " << informe->productos_procesados << "\n";
        std::cout << "Estado:                   "
                  << (persistir ? "Importación guardada en Supabase.\n"
                                : "Extracción completada; no se guardó en Supabase.\n");
        std::cout << "============================================================\n";
        return 0;
    } catch (const std::exception& err) {
        std::cerr << "Error: " << err.what() << "\n";
        return 1;
    }
}

int comandoExportarCsv(
    const QString& dirDestino,
    const CargadorCatalogoCsv& cargar_catalogo_csv) {
    QDir dir(dirDestino);
    std::unique_ptr<ClienteHTTPSupabase> cliente;
    if (!cargar_catalogo_csv) {
        cliente = obtenerClienteDesdeEntorno();
    }
    if (!cargar_catalogo_csv && !cliente) {
        std::cerr << "Error: conectar con Supabase antes de exportar el catálogo.\n";
        return 1;
    }
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    try {
        if (cargar_catalogo_csv) {
            cargar_catalogo_csv(catalogo);
        } else {
            catalogo.recargar_todo();
        }
    } catch (const std::exception& err) {
        std::cerr << "Error: no se pudo cargar el catálogo; exportación cancelada ("
                  << err.what() << ").\n";
        return 1;
    }
    if (!dir.exists() && !QDir().mkpath(dirDestino)) {
        std::cerr << "Error: no se pudo crear el directorio de exportación.\n";
        return 1;
    }

    const auto contenidos = datos::serializar_catalogo_csv(catalogo);
    const std::array<QString, 3> nombres{
        "grupos.csv", "investigadores.csv", "productos.csv"};
    for (std::size_t indice = 0; indice < nombres.size(); ++indice) {
        const QString ruta = dir.filePath(nombres[indice]);
        QString error;
        if (!datos::guardar_csv_atomico(ruta, contenidos[indice], error)) {
            std::cerr << "Error: no se pudo guardar " << ruta.toStdString()
                      << " (" << error.toStdString() << ").\n";
            return 1;
        }
    }

    std::cout << "Exportación completada en directorio: " << QFileInfo(dirDestino).absoluteFilePath().toStdString() << "\n";
    return 0;
}

int comandoCargarEjemplo() {
    auto cliente = obtenerClienteDesdeEntorno();
    if (!cliente) {
        std::cerr << "Error: conectar con Supabase antes de cargar los datos de ejemplo PRUEBA-.\n";
        return 1;
    }
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    constexpr bool persistir = true;

    auto g = std::make_shared<dominio::Grupo>(
        "PRUEBA-GRP-CLI-01",
        "Grupo de Prueba Automatizada CLI",
        "A1",
        "Investigador Líder CLI",
        true
    );
    auto inv1 = std::make_shared<dominio::Investigador>(
        "PRUEBA-INV-CLI-01",
        "Investigador Líder CLI",
        "Senior",
        "Doctorado",
        true
    );
    auto inv2 = std::make_shared<dominio::Investigador>(
        "PRUEBA-INV-CLI-02",
        "Investigador Asistente CLI",
        "Junior",
        "Maestria",
        true
    );

    try {
        catalogo.crear_grupo(g, persistir);
        catalogo.crear_investigador(inv1, persistir);
        catalogo.crear_investigador(inv2, persistir);
        catalogo.vincular_integrante(g->codigo_gruplac, inv1->codigo_rh, "Lider", persistir);
        catalogo.vincular_integrante(g->codigo_gruplac, inv2->codigo_rh, "Investigador", persistir);

        auto p = std::make_shared<dominio::Producto>(
            "PRUEBA-PROD-CLI-01",
            "Artículo Científico de Prueba CLI",
            "GNC",
            "Artículo",
            2024,
            "Avalado",
            true
        );
        catalogo.crear_producto(p, g->codigo_gruplac, {inv1->codigo_rh, inv2->codigo_rh}, persistir);
        std::cout << "Datos de ejemplo cargados exitosamente (1 grupo, 2 investigadores, 1 producto enlazado).\n";
        return 0;
    } catch (const std::exception& err) {
        std::cout << "Aviso al cargar datos de ejemplo: " << err.what() << "\n";
        return 0;
    }
}

int comandoAplicarEscenario() {
    std::cout << "Iniciando escenario funcional de mutaciones y reversión...\n";
    servicios::CatalogoInvestigacion catalogo;

    // 1. Crear entidades
    auto g = std::make_shared<dominio::Grupo>("SCN-GRP-01", "Grupo Escenario 1", "A");
    auto inv = std::make_shared<dominio::Investigador>("SCN-INV-01", "Dra. Investigadora Escenario");
    catalogo.crear_grupo(g, false);
    catalogo.crear_investigador(inv, false);
    std::cout << " [OK] Grupo " << g->codigo_gruplac.toStdString() << " e Investigador " << inv->codigo_rh.toStdString() << " creados en estructuras.\n";

    // 2. Crear producto en Multilista
    auto prod = std::make_shared<dominio::Producto>(
        "SCN-PRD-01",
        "Software de Simulación Multidimensional",
        "DTI",
        "Software",
        2025,
        "Avalado"
    );
    catalogo.crear_producto(prod, g->codigo_gruplac, {inv->codigo_rh}, false);
    std::cout << " [OK] Producto creado y enlazado en Multilista (Grupo e Investigador).\n";

    // 3. Desactivar producto
    catalogo.desactivar_producto(prod->codigo_identificador, false);
    if (prod->activo) {
        std::cerr << "Fallo: el producto debería estar inactivo.\n";
        return 1;
    }
    std::cout << " [OK] Desactivación lógica aplicada: prod.activo = False.\n";

    // 4. Deshacer desactivación (Undo)
    auto cmd = catalogo.deshacer(false);
    if (!prod->activo) {
        std::cerr << "Fallo: el producto debería haber vuelto a activo=True tras deshacer.\n";
        return 1;
    }
    std::cout << " [OK] Deshacer completado (" << (cmd ? cmd->descripcion.toStdString() : "") << "): prod.activo = True.\n";

    // 5. Eliminar producto
    catalogo.eliminar_producto(prod->codigo_identificador, false);
    if (catalogo.buscar_producto(prod->codigo_identificador) != nullptr) {
        std::cerr << "Fallo: el producto debería haber sido eliminado de la multilista.\n";
        return 1;
    }
    std::cout << " [OK] Eliminación física completada: producto retirado de todas las listas.\n";

    std::cout << "Escenario completado exitosamente sin discrepancias.\n";
    return 0;
}

} // namespace

QString formatear_errores_importacion_csv(const QStringList& filas_erroneas) {
    if (filas_erroneas.isEmpty()) {
        return {};
    }

    QStringList lineas;
    lineas.reserve(filas_erroneas.size() + 1);
    lineas.append(QStringLiteral("Filas con errores:"));
    for (const auto& error : filas_erroneas) {
        lineas.append(QStringLiteral("  - %1").arg(error));
    }
    return lineas.join(QLatin1Char('\n'));
}

static int ejecutar_interno(
    const QStringList& args,
    const CargadorCatalogoCsv& cargar_catalogo_csv) {
    if (args.isEmpty()) {
        mostrarAyuda();
        return 0;
    }

    const QString& comando = args[0];

    if (comando == "-h" || comando == "--help" || comando == "help") {
        mostrarAyuda();
        return 0;
    }

    if (comando == "-v" || comando == "--version") {
        std::cout << obtener_version() << "\n";
        std::cout << "Soporte TLS/SSL: " << (ClienteHTTPSupabase::soportaTLS() ? "Activado (" + ClienteHTTPSupabase::backendTLS().toStdString() + ")" : "No disponible") << "\n";
        return 0;
    }

    if (comando == "info") {
        return comandoInfo();
    }

    if (comando == "verificar" || comando == "ping") {
        return comandoVerificar();
    }

    if (comando == "resumen") {
        bool salidaJson = args.contains("--json");
        return comandoResumen(salidaJson);
    }

    if (comando == "importar-csv") {
        QString archivo;
        QString tipo;
        for (int i = 1; i < args.size(); ++i) {
            if ((args[i] == "-a" || args[i] == "--archivo") && i + 1 < args.size()) {
                archivo = args[++i];
            } else if ((args[i] == "-t" || args[i] == "--tipo") && i + 1 < args.size()) {
                tipo = args[++i];
            }
        }
        if (archivo.isEmpty() || tipo.isEmpty()) {
            std::cerr << "Error: Debe especificar --archivo (-a) y --tipo (-t: grupos|investigadores|productos).\n";
            return 1;
        }
        return comandoImportarCsv(archivo, tipo);
    }

    if (comando == "importar-url") {
        QString url;
        bool persistir = false;
        bool anonimizar = false;
        for (int i = 1; i < args.size(); ++i) {
            if ((args[i] == "-u" || args[i] == "--url") && i + 1 < args.size()) {
                url = args[++i];
            } else if (args[i] == "--persistir") {
                persistir = true;
            } else if (args[i] == "--anonimizar") {
                anonimizar = true;
            }
        }
        if (url.isEmpty()) {
            std::cerr << "Error: Debe especificar la URL con -u o --url.\n";
            return 1;
        }
        return comandoImportarUrl(url, persistir, anonimizar);
    }

    if (comando == "exportar-csv") {
        QString dirDestino = "datos/fuentes/csv";
        for (int i = 1; i < args.size(); ++i) {
            if ((args[i] == "-d" || args[i] == "--directorio") && i + 1 < args.size()) {
                dirDestino = args[++i];
            }
        }
        return comandoExportarCsv(dirDestino, cargar_catalogo_csv);
    }

    if (comando == "cargar-ejemplo") {
        return comandoCargarEjemplo();
    }

    if (comando == "aplicar-escenario") {
        return comandoAplicarEscenario();
    }

    mostrarAyuda();
    return 1;
}

int ejecutar(const QStringList& args) {
    return ejecutar(args, {});
}

int ejecutar(
    const QStringList& args,
    const CargadorCatalogoCsv& cargar_catalogo_csv) {
    try {
        return ejecutar_interno(args, cargar_catalogo_csv);
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}

} // namespace pea::cli
