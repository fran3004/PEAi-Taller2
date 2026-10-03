#include "pea/cli.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"
#include "pea/version.hpp"

#include <iostream>
#include <memory>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QProcessEnvironment>
#include <QTextStream>

namespace pea::cli {

namespace {

std::unique_ptr<ClienteHTTPSupabase> obtenerClienteDesdeEntorno() {
    auto env = QProcessEnvironment::systemEnvironment();
    QString url = env.value("PEA_SUPABASE_URL_PROD");
    if (url.isEmpty()) url = env.value("PEA_SUPABASE_URL_TEST");

    QString key = env.value("PEA_SUPABASE_ANON_PROD");
    if (key.isEmpty()) key = env.value("PEA_SUPABASE_ANON_TEST");

    if (!url.isEmpty() && !key.isEmpty()) {
        return std::make_unique<ClienteHTTPSupabase>(url, key, 10000);
    }
    return nullptr;
}

void mostrarAyuda() {
    std::cout << "PEA-i · Programa Estadístico de Análisis de Investigación (" << INSTITUCION << ")\n"
              << "Uso: pea-cpp [COMANDO] [OPCIONES]\n\n"
              << "Comandos disponibles:\n"
              << "  info                     Muestra información del sistema y arquitectura\n"
              << "  verificar                Verifica conectividad HTTPS, TLS y número de revisión\n"
              << "  ping                     Alias de verificar\n"
              << "  resumen [--json]         Muestra el resumen de entidades (o JSON canónico)\n"
              << "  importar-csv -a <f> -t <t> Importa entidades desde archivo CSV (grupos|investigadores|productos)\n"
              << "  exportar-csv -d <dir>    Exporta entidades del catálogo a archivos CSV\n"
              << "  cargar-ejemplo           Carga datos oficiales de prueba con prefijo PRUEBA-\n"
              << "  aplicar-escenario        Ejecuta escenario de mutación y reversión (Undo LIFO)\n"
              << "  --autoprueba             Ejecuta verificación de GUI offscreen\n"
              << "  -v, --version            Muestra la versión de la aplicación y sale\n"
              << "  -h, --help               Muestra este mensaje de ayuda y sale\n";
}

int comandoInfo() {
    std::cout << "Nombre: " << APP_NAME << "\n";
    std::cout << "Versión: " << APP_VERSION << "\n";
    std::cout << "Institución: " << INSTITUCION << "\n";
    std::cout << "Arquitectura: C++17 / Qt6 Widgets / HTTPS PostgREST / Estructuras Hechas a Mano\n";
    return 0;
}


int comandoVerificar() {
    auto cliente = obtenerClienteDesdeEntorno();
    if (!cliente) {
        std::cout << "Aviso: Variables PEA_SUPABASE_URL y PEA_SUPABASE_ANON no configuradas en el entorno.\n";
        std::cout << "Estado local: " << obtener_version() << " operando en modo desconectado.\n";
        return 0;
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
            if (!salidaJson) {
                std::cout << "Aviso: no se pudo recargar de la base remota (" << err.what() << "). Mostrando estado local.\n";
            }
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
    QFile archivo(rutaArchivo);
    if (!archivo.open(QIODevice::ReadOnly | QIODevice::Text)) {
        std::cerr << "Error: El archivo " << rutaArchivo.toStdString() << " no existe o no se puede leer.\n";
        return 1;
    }

    auto cliente = obtenerClienteDesdeEntorno();
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    bool persistir = (cliente != nullptr);
    int procesados = 0;

    QTextStream in(&archivo);
    QString cabecera = in.readLine();
    QStringList columnas = cabecera.split(',');
    for (int i = 0; i < columnas.size(); ++i) {
        columnas[i] = columnas[i].trimmed();
    }

    while (!in.atEnd()) {
        QString linea = in.readLine().trimmed();
        if (linea.isEmpty()) continue;
        QStringList valores = linea.split(',');
        QJsonObject datos;
        for (int i = 0; i < columnas.size() && i < valores.size(); ++i) {
            datos[columnas[i]] = valores[i].trimmed();
        }

        try {
            if (tipo == "grupos") {
                auto g = std::make_shared<dominio::Grupo>(dominio::Grupo::desdeJson(datos));
                catalogo.crear_grupo(g, persistir);
                procesados++;
            } else if (tipo == "investigadores") {
                auto inv = std::make_shared<dominio::Investigador>(dominio::Investigador::desdeJson(datos));
                catalogo.crear_investigador(inv, persistir);
                procesados++;
            } else if (tipo == "productos") {
                auto p = std::make_shared<dominio::Producto>(dominio::Producto::desdeJson(datos));
                catalogo.crear_producto(p, QString(), {}, persistir);
                procesados++;
            }
        } catch (const std::exception& err) {
            std::cerr << "Aviso al importar fila: " << err.what() << "\n";
        }
    }

    std::cout << "Importación completada: " << procesados << " entidades de tipo '" << tipo.toStdString() << "' procesadas con éxito.\n";
    return 0;
}

int comandoExportarCsv(const QString& dirDestino) {
    QDir dir(dirDestino);
    if (!dir.exists()) {
        dir.mkpath(".");
    }

    auto cliente = obtenerClienteDesdeEntorno();
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    if (cliente) {
        try {
            catalogo.recargar_todo();
        } catch (const std::exception& err) {
            std::cout << "Aviso al recargar datos remotos: " << err.what() << "\n";
        }
    }

    // 1. Exportar Grupos
    QFile fGrupos(dir.filePath("grupos.csv"));
    if (fGrupos.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&fGrupos);
        out << "codigo_gruplac,nombre,categoria,lider,institucion_principal,activo\n";
        for (const auto& g : catalogo.grupos) {
            if (!g) continue;
            out << g->codigo_gruplac << "," << g->nombre << "," << g->categoria << ","
                << g->lider << "," << g->institucion_principal << ","
                << (g->activo ? "True" : "False") << "\n";
        }
    }

    // 2. Exportar Investigadores
    QFile fInvs(dir.filePath("investigadores.csv"));
    if (fInvs.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&fInvs);
        out << "codigo_rh,nombre_completo,categoria,formacion_academica,nacionalidad,activo\n";
        for (const auto& inv : catalogo.investigadores) {
            if (!inv) continue;
            out << inv->codigo_rh << "," << inv->nombre_completo << "," << inv->categoria << ","
                << inv->formacion_academica << "," << inv->nacionalidad << ","
                << (inv->activo ? "True" : "False") << "\n";
        }
    }

    // 3. Exportar Productos
    QFile fProds(dir.filePath("productos.csv"));
    if (fProds.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&fProds);
        out << "codigo_identificador,titulo,tipo_mayor,subtipo,ano,estado_validacion,activo\n";
        auto* actual = catalogo.multilista_productos.cabeza();
        while (actual) {
            if (actual->producto) {
                out << actual->producto->codigo_identificador << "," << actual->producto->titulo << ","
                    << actual->producto->tipo_mayor << "," << actual->producto->subtipo << ","
                    << actual->producto->ano << "," << actual->producto->estado_validacion << ","
                    << (actual->producto->activo ? "True" : "False") << "\n";
            }
            actual = actual->siguiente_global;
        }
    }

    std::cout << "Exportación completada en directorio: " << QFileInfo(dirDestino).absoluteFilePath().toStdString() << "\n";
    return 0;
}

int comandoCargarEjemplo() {
    auto cliente = obtenerClienteDesdeEntorno();
    servicios::CatalogoInvestigacion catalogo(cliente.get());
    bool persistir = (cliente != nullptr);

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

int ejecutar(const QStringList& args) {
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

    if (comando == "exportar-csv") {
        QString dirDestino = "datos/fuentes/csv";
        for (int i = 1; i < args.size(); ++i) {
            if ((args[i] == "-d" || args[i] == "--directorio") && i + 1 < args.size()) {
                dirDestino = args[++i];
            }
        }
        return comandoExportarCsv(dirDestino);
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

} // namespace pea::cli
