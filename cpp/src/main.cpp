#include <QApplication>
#include <QStringList>
#include <iostream>
#include <string>
#include "pea/version.hpp"
#include "pea/cli.hpp"
#include "pea/gui/ventana_principal.hpp"

int main(int argc, char* argv[]) {
    QStringList args;
    for (int i = 1; i < argc; ++i) {
        args.append(QString::fromLocal8Bit(argv[i]));
    }

    // Si se pasa --autoprueba para prueba offscreen de GUI
    bool autoprueba = args.contains("--autoprueba");

    // Si hay argumentos de CLI y no es autoprueba de GUI, ejecutar CLI directamente
    if (!args.isEmpty() && !autoprueba) {
        return pea::cli::ejecutar(args);
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
