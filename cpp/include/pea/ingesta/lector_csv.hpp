#pragma once

#include <utility>
#include <QList>
#include <QString>
#include <QStringList>
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/estructuras/lista_doble.hpp"
#include "pea/ingesta/modelos.hpp"

namespace pea::ingesta {

class LectorCSV {
public:
    static QChar detectar_delimitador(const QString& contenido);
    static QString leer_texto_archivo(const QString& ruta, QString* encoding_detectada = nullptr);
    static QStringList parsear_linea(const QString& linea, QChar delimitador);
    static QString detectar_tipo_archivo(const QString& ruta);

    static std::pair<estructuras::ListaDoble<dominio::Grupo>, QList<QString>> leer_grupos(
        const QString& ruta,
        QChar delimitador = QLatin1Char('\0')
    );

    static std::pair<estructuras::ListaDoble<dominio::Investigador>, QList<QString>> leer_investigadores(
        const QString& ruta,
        QChar delimitador = QLatin1Char('\0')
    );

    static std::pair<QList<std::pair<dominio::Producto, QString>>, QList<QString>> leer_productos(
        const QString& ruta,
        QChar delimitador = QLatin1Char('\0')
    );

    static std::pair<QList<FilaAutorCSV>, QList<QString>> leer_autores(
        const QString& ruta,
        QChar delimitador = QLatin1Char('\0')
    );
};

} // namespace pea::ingesta
