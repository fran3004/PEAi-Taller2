#pragma once

#include <utility>
#include <QByteArray>
#include <QJsonObject>
#include <QString>
#include "pea/ingesta/modelos.hpp"

namespace pea::ingesta {

class ExtractorURL {
public:
    explicit ExtractorURL(const QString& cache_dir = QStringLiteral("datos/cache"), double pausa_segundos = 1.0);

    static std::pair<QString, QString> validar_url(const QString& url);

    std::pair<QByteArray, QJsonObject> descargar_o_cargar_cache(
        const QString& url,
        const QString& alias = QString(),
        bool forzar_descarga = false
    );

    InformeIngesta procesar_url(
        const QString& url,
        const QString& salida_dir = QStringLiteral("datos/fuentes/extraccion"),
        bool anonimizar = false,
        bool forzar_descarga = false
    );

private:
    QString m_cache_dir;
    double m_pausa_segundos{1.0};
    qint64 m_ultima_peticion_tiempo_ms{0};
};

} // namespace pea::ingesta
