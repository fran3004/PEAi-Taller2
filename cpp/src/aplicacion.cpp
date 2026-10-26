#include "pea/aplicacion.hpp"

#include <QCoreApplication>
#include <QStringList>
#include <iostream>

#include "pea/cli.hpp"
#include "pea/tui/aplicacion_tui.hpp"
#include "pea/version.hpp"

namespace pea {

int ejecutar_aplicacion(int argc, char* argv[]) {
    QStringList argumentos;
    for (int i = 1; i < argc; ++i) {
        argumentos.append(QString::fromLocal8Bit(argv[i]));
    }

    QCoreApplication aplicacion(argc, argv);
    aplicacion.setApplicationName(APP_NAME);
    aplicacion.setApplicationVersion(APP_VERSION);
    aplicacion.setOrganizationName(INSTITUCION);

    const bool demo = argumentos.removeAll("--demo") > 0;
    const bool sin_color = argumentos.removeAll("--sin-color") > 0;
    const bool ascii = argumentos.removeAll("--ascii") > 0;
    argumentos.removeAll("--sin-animacion");
    const bool autoprueba = argumentos.removeAll("--autoprueba") > 0;
    bool vacio = false;
    QString archivo_local;
    if (!argumentos.isEmpty() && argumentos[0] == "--vacio") {
        vacio = true;
        argumentos.removeFirst();
    } else if (argumentos.size() == 2 && argumentos[0] == "--archivo") {
        archivo_local = argumentos[1];
        argumentos.clear();
    }

    if (!argumentos.isEmpty() && argumentos[0] == "--respuestas") argumentos[0] = "respuestas-parcial";

    if (argumentos.isEmpty() || demo || autoprueba) {
        return pea::tui::ejecutar(demo, autoprueba, sin_color, ascii, archivo_local, vacio);
    }

    return pea::cli::ejecutar(argumentos);
}

} // namespace pea
