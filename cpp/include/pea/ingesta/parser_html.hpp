#pragma once

#include <QString>
#include <QJsonObject>
#include "pea/ingesta/modelos.hpp"

namespace pea::ingesta {

class ParserHTML {
public:
    static QString decodificar_entidades(const QString& texto);
    static QString limpiar_texto(const QString& fragmento_html);

    static GrupoIngesta parsear_gruplac(
        const QString& html,
        const QJsonObject& meta,
        bool anonimizar = false
    );

    static InvestigadorIngesta parsear_cvlac(
        const QString& html,
        const QJsonObject& meta,
        bool anonimizar = false
    );

    static QString generar_markdown_gruplac(
        const GrupoIngesta& grupo,
        const QJsonObject& meta,
        bool anonimizar = false
    );

    static QString generar_markdown_cvlac(
        const InvestigadorIngesta& inv,
        const QJsonObject& meta,
        bool anonimizar = false
    );
};

} // namespace pea::ingesta
