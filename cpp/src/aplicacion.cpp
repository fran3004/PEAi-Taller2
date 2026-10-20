#include "pea/aplicacion.hpp"

#include <QCoreApplication>
#include <QStringList>
#include <iostream>

#include "pea/cli.hpp"
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

    if (argumentos.isEmpty()) {
        std::cout << "PEA-i ejecuta modo terminal. Use -h o --help para ver la CLI disponible.\n";
        return pea::cli::ejecutar(QStringList{"-h"});
    }

    return pea::cli::ejecutar(argumentos);
}

} // namespace pea
