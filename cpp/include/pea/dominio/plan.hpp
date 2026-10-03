#pragma once

#include <optional>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

class Plan {
public:
    std::optional<qint64> id;
    QString codigo_gruplac;
    int ano_inicio{2024};
    int ano_fin{2026};
    QString descripcion;
    QString estado{"En ejecucion"};
    bool activo{true};
    bool es_ejemplo{false};

    Plan() = default;
    Plan(QString gruplac, int inicio, int fin, QString desc, QString est = "En ejecucion", bool ejemplo = false)
        : codigo_gruplac(std::move(gruplac)),
          ano_inicio(inicio),
          ano_fin(fin),
          descripcion(std::move(desc)),
          estado(std::move(est)),
          es_ejemplo(ejemplo) {}

    [[nodiscard]] QJsonObject aJson(bool incluirId = true) const {
        QJsonObject json;
        if (incluirId && id.has_value()) {
            json["id"] = *id;
        }
        json["codigo_gruplac"] = codigo_gruplac;
        json["ano_inicio"] = ano_inicio;
        json["ano_fin"] = ano_fin;
        json["descripcion"] = descripcion;
        json["estado"] = estado;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static Plan desdeJson(const QJsonObject& json) {
        Plan pl;
        if (json.contains("id") && !json["id"].isNull()) {
            pl.id = json["id"].toVariant().toLongLong();
        }
        pl.codigo_gruplac = json["codigo_gruplac"].toString();
        pl.ano_inicio = json["ano_inicio"].toInt(2024);
        pl.ano_fin = json["ano_fin"].toInt(2026);
        pl.descripcion = json["descripcion"].toString();
        if (json.contains("estado") && !json["estado"].toString().isEmpty()) {
            pl.estado = json["estado"].toString();
        }
        if (json.contains("activo")) {
            pl.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            pl.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return pl;
    }
};

} // namespace pea::dominio
