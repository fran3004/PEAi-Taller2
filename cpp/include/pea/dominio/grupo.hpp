#pragma once

#include <optional>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

class Grupo {
public:
    std::optional<qint64> id;
    QString codigo_gruplac;
    QString nombre;
    QString fecha_creacion;
    QString pais{"Colombia"};
    QString departamento_ciudad;
    QString lider;
    QString institucion_principal{"Universidad Popular del Cesar"};
    QString gran_area_ocde;
    QString area_ocde;
    QString categoria;
    bool activo{true};
    bool es_ejemplo{false};

    Grupo() = default;
    Grupo(QString codigo, QString nom, QString cat = QString(), QString lid = QString(), bool ejemplo = false)
        : codigo_gruplac(std::move(codigo)),
          nombre(std::move(nom)),
          lider(std::move(lid)),
          categoria(std::move(cat)),
          es_ejemplo(ejemplo) {}


    void desactivar() noexcept { activo = false; }
    void activar() noexcept { activo = true; }

    [[nodiscard]] QJsonObject aJson(bool incluirId = true) const {
        QJsonObject json;
        if (incluirId && id.has_value()) {
            json["id"] = *id;
        }
        json["codigo_gruplac"] = codigo_gruplac;
        json["nombre"] = nombre;
        if (!fecha_creacion.isEmpty()) json["fecha_creacion"] = fecha_creacion;
        json["pais"] = pais;
        if (!departamento_ciudad.isEmpty()) json["departamento_ciudad"] = departamento_ciudad;
        if (!lider.isEmpty()) json["lider"] = lider;
        json["institucion_principal"] = institucion_principal;
        if (!gran_area_ocde.isEmpty()) json["gran_area_ocde"] = gran_area_ocde;
        if (!area_ocde.isEmpty()) json["area_ocde"] = area_ocde;
        if (!categoria.isEmpty()) json["categoria"] = categoria;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static Grupo desdeJson(const QJsonObject& json) {
        Grupo g;
        if (json.contains("id") && !json["id"].isNull()) {
            g.id = json["id"].toVariant().toLongLong();
        }
        g.codigo_gruplac = json["codigo_gruplac"].toString();
        g.nombre = json["nombre"].toString();
        g.fecha_creacion = json["fecha_creacion"].toString();
        if (json.contains("pais") && !json["pais"].toString().isEmpty()) {
            g.pais = json["pais"].toString();
        }
        g.departamento_ciudad = json["departamento_ciudad"].toString();
        g.lider = json["lider"].toString();
        if (json.contains("institucion_principal") && !json["institucion_principal"].toString().isEmpty()) {
            g.institucion_principal = json["institucion_principal"].toString();
        }
        g.gran_area_ocde = json["gran_area_ocde"].toString();
        g.area_ocde = json["area_ocde"].toString();
        g.categoria = json["categoria"].toString();
        if (json.contains("activo")) {
            g.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            g.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return g;
    }
};

} // namespace pea::dominio
