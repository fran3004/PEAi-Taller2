#pragma once

#include <optional>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

class Investigador {
public:
    std::optional<qint64> id;
    QString codigo_rh;
    QString nombre_completo;
    QString nombre_en_citas;
    QString documento_identidad;
    QString nacionalidad{"Colombiana"};
    QString sexo;
    QString categoria;
    QString formacion_academica;
    bool activo{true};
    bool es_ejemplo{false};

    Investigador() = default;
    Investigador(QString rh, QString nombre, QString cat = QString(), QString formacion = QString(), bool ejemplo = false)
        : codigo_rh(std::move(rh)),
          nombre_completo(std::move(nombre)),
          categoria(std::move(cat)),
          formacion_academica(std::move(formacion)),
          es_ejemplo(ejemplo) {}

    void desactivar() noexcept { activo = false; }
    void activar() noexcept { activo = true; }

    [[nodiscard]] QJsonObject aJson(bool incluirId = true) const {
        QJsonObject json;
        if (incluirId && id.has_value()) {
            json["id"] = *id;
        }
        json["codigo_rh"] = codigo_rh;
        json["nombre_completo"] = nombre_completo;
        if (!nombre_en_citas.isEmpty()) json["nombre_en_citas"] = nombre_en_citas;
        if (!documento_identidad.isEmpty()) json["documento_identidad"] = documento_identidad;
        json["nacionalidad"] = nacionalidad;
        if (!sexo.isEmpty()) json["sexo"] = sexo;
        if (!categoria.isEmpty()) json["categoria"] = categoria;
        if (!formacion_academica.isEmpty()) json["formacion_academica"] = formacion_academica;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static Investigador desdeJson(const QJsonObject& json) {
        Investigador inv;
        if (json.contains("id") && !json["id"].isNull()) {
            inv.id = json["id"].toVariant().toLongLong();
        }
        inv.codigo_rh = json["codigo_rh"].toString();
        inv.nombre_completo = json["nombre_completo"].toString();
        inv.nombre_en_citas = json["nombre_en_citas"].toString();
        inv.documento_identidad = json["documento_identidad"].toString();
        if (json.contains("nacionalidad") && !json["nacionalidad"].toString().isEmpty()) {
            inv.nacionalidad = json["nacionalidad"].toString();
        }
        inv.sexo = json["sexo"].toString();
        inv.categoria = json["categoria"].toString();
        inv.formacion_academica = json["formacion_academica"].toString();
        if (json.contains("activo")) {
            inv.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            inv.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return inv;
    }
};

} // namespace pea::dominio
