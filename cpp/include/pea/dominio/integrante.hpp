#pragma once

#include <optional>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

class IntegranteGrupo {
public:
    std::optional<qint64> id;
    std::optional<qint64> grupo_id;
    QString codigo_gruplac;
    std::optional<qint64> investigador_id;
    QString codigo_rh;
    QString rol{"Investigador"};
    QString fecha_inicio;
    QString fecha_fin;
    bool activo{true};
    bool es_ejemplo{false};

    IntegranteGrupo() = default;
    IntegranteGrupo(QString c_gruplac, QString c_rh, QString r = "Investigador", bool ejemplo = false)
        : codigo_gruplac(std::move(c_gruplac)),
          codigo_rh(std::move(c_rh)),
          rol(std::move(r)),
          es_ejemplo(ejemplo) {}

    [[nodiscard]] QJsonObject aJson(bool incluirId = true) const {
        QJsonObject json;
        if (incluirId && id.has_value()) {
            json["id"] = *id;
        }
        if (grupo_id.has_value()) {
            json["grupo_id"] = *grupo_id;
        }
        json["codigo_gruplac"] = codigo_gruplac;
        if (investigador_id.has_value()) {
            json["investigador_id"] = *investigador_id;
        }
        json["codigo_rh"] = codigo_rh;
        json["rol"] = rol;
        if (!fecha_inicio.isEmpty()) json["fecha_inicio"] = fecha_inicio;
        if (!fecha_fin.isEmpty()) json["fecha_fin"] = fecha_fin;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static IntegranteGrupo desdeJson(const QJsonObject& json) {
        IntegranteGrupo ig;
        if (json.contains("id") && !json["id"].isNull()) {
            ig.id = json["id"].toVariant().toLongLong();
        }
        if (json.contains("grupo_id") && !json["grupo_id"].isNull()) {
            ig.grupo_id = json["grupo_id"].toVariant().toLongLong();
        }
        ig.codigo_gruplac = json["codigo_gruplac"].toString();
        if (json.contains("investigador_id") && !json["investigador_id"].isNull()) {
            ig.investigador_id = json["investigador_id"].toVariant().toLongLong();
        }
        ig.codigo_rh = json["codigo_rh"].toString();
        if (json.contains("rol") && !json["rol"].toString().isEmpty()) {
            ig.rol = json["rol"].toString();
        }
        ig.fecha_inicio = json["fecha_inicio"].toString();
        ig.fecha_fin = json["fecha_fin"].toString();
        if (json.contains("activo")) {
            ig.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            ig.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return ig;
    }
};

} // namespace pea::dominio
