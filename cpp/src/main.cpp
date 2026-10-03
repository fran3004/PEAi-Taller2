#include <QApplication>
#include <iostream>
#include <string>
#include "pea/version.hpp"
#include "pea/cliente_http.hpp"
#include "pea/gui/ventana_principal.hpp"

int main(int argc, char* argv[]) {
    // Verificar argumentos de línea de comandos antes de QApplication si no requiere GUI
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--version" || arg == "-v") {
            std::cout << pea::obtener_version() << std::endl;
            std::cout << "Soporte TLS/SSL: " << (pea::ClienteHTTPSupabase::soportaTLS() ? "Activado (" + pea::ClienteHTTPSupabase::backendTLS().toStdString() + ")" : "No disponible") << std::endl;
            return 0;
        }
        if (arg == "--help" || arg == "-h") {
            std::cout << "PEA-i · Programa Estadístico de Análisis de Investigación\n"
                      << "Uso: pea-cpp [OPCIONES]\n\n"
                      << "Opciones:\n"
                      << "  -v, --version      Muestra la versión de la aplicación y sale\n"
                      << "  -h, --help         Muestra este mensaje de ayuda y sale\n"
                      << "  --autoprueba       Ejecuta un ciclo de verificación de GUI offscreen y sale\n";
            return 0;
        }
    }

    bool autoprueba = false;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--autoprueba") {
            autoprueba = true;
            break;
        }
    }

    if (autoprueba) {
        qputenv("QT_QPA_PLATFORM", "offscreen");
    }

    QApplication app(argc, argv);
    app.setApplicationName(pea::APP_NAME);
    app.setApplicationVersion(pea::APP_VERSION);
    app.setOrganizationName(pea::INSTITUCION);

    pea::gui::VentanaPrincipal ventana;

    if (autoprueba) {
        ventana.show();
        app.processEvents();
        std::cout << "Autoprueba de GUI C++ completada exitosamente." << std::endl;
        return 0;
    }

    ventana.show();
    return app.exec();
}
