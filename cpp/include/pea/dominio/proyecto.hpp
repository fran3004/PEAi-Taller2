#pragma once

#include <optional>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

class Proyecto {
public:
    std::optional<qint64> id;
    std::optional<qint64> grupo_id;
    QString codigo_gruplac;
    QString codigo_identificador;
    QString nombre;
    QString tipo;
    std::optional<int> ano_inicio;
    std::optional<int> ano_fin;
    QString estado;
    bool activo{true};
    bool es_ejemplo{false};

    Proyecto() = default;
    Proyecto(QString gruplac, QString nom, QString t = QString(), bool ejemplo = false)
        : codigo_gruplac(std::move(gruplac)),
          nombre(std::move(nom)),
          tipo(std::move(t)),
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
        if (!codigo_identificador.isEmpty()) json["codigo_identificador"] = codigo_identificador;
        json["nombre"] = nombre;
        if (!tipo.isEmpty()) json["tipo"] = tipo;
        if (ano_inicio.has_value()) json["ano_inicio"] = *ano_inicio;
        if (ano_fin.has_value()) json["ano_fin"] = *ano_fin;
        if (!estado.isEmpty()) json["estado"] = estado;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static Proyecto desdeJson(const QJsonObject& json) {
        Proyecto py;
        if (json.contains("id") && !json["id"].isNull()) {
            py.id = json["id"].toVariant().toLongLong();
        }
        if (json.contains("grupo_id") && !json["grupo_id"].isNull()) {
            py.grupo_id = json["grupo_id"].toVariant().toLongLong();
        }
        py.codigo_gruplac = json["codigo_gruplac"].toString();
        py.codigo_identificador = json["codigo_identificador"].toString();
        py.nombre = json["nombre"].toString();
        py.tipo = json["tipo"].toString();
        if (json.contains("ano_inicio") && !json["ano_inicio"].isNull()) {
            py.ano_inicio = json["ano_inicio"].toInt();
        }
        if (json.contains("ano_fin") && !json["ano_fin"].isNull()) {
            py.ano_fin = json["ano_fin"].toInt();
        }
        py.estado = json["estado"].toString();
        if (json.contains("activo")) {
            py.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            py.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return py;
    }
};

} // namespace pea::dominio
