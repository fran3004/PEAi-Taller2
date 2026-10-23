#pragma once

#include <optional>
#include <utility>
#include <QCryptographicHash>
#include <QJsonObject>
#include <QString>

namespace pea::dominio {

inline QString normalizar_cita(const QString& cita) {
    if (cita.isEmpty()) {
        return QString();
    }
    return cita.simplified().normalized(QString::NormalizationForm_C).toLower();
}

inline QString calcular_hash_cita(const QString& cita) {
    const QString norm = normalizar_cita(cita);
    const QByteArray bytes = norm.toUtf8();
    const QByteArray hash = QCryptographicHash::hash(bytes, QCryptographicHash::Sha1).toHex();
    return QString::fromLatin1(hash.left(12));
}

inline QString generar_codigo_producto_cvlac(
    const QString& codigo_rh,
    const QString& cita,
    int ocurrencia = 1,
    const QString& titulo = QString()
) {
    const QString rh_limpio = codigo_rh.trimmed();
    QString texto = cita.trimmed();
    if (texto.isEmpty()) {
        texto = titulo.trimmed();
    }
    const QString h = calcular_hash_cita(texto);
    QString base = QStringLiteral("PROD-CVLAC-%1-%2").arg(rh_limpio, h);
    if (ocurrencia > 1) {
        return QStringLiteral("%1-%2").arg(base, QString::number(ocurrencia));
    }
    return base;
}

class Producto {
public:
    std::optional<qint64> id;
    QString codigo_identificador;
    QString titulo;
    QString tipo_mayor; // GNC, DTI, ASC, FRH
    QString subtipo;
    int ano{2024};
    std::optional<int> mes;
    QString pais;
    QString estado_validacion{"No avalado"}; // Avalado, Con soporte, No avalado
    QJsonObject detalles;
    bool activo{true};
    bool es_ejemplo{false};

    Producto() = default;
    Producto(QString codigo, QString tit, QString tipo, QString sub, int a, QString est = "No avalado", bool ejemplo = false)
        : codigo_identificador(std::move(codigo)),
          titulo(std::move(tit)),
          tipo_mayor(std::move(tipo)),
          subtipo(std::move(sub)),
          ano(a),
          estado_validacion(std::move(est)),
          es_ejemplo(ejemplo) {}

    void desactivar() noexcept { activo = false; }
    void activar() noexcept { activo = true; }

    [[nodiscard]] QJsonObject aJson(bool incluirId = true) const {
        QJsonObject json;
        if (incluirId && id.has_value()) {
            json["id"] = *id;
        }
        json["codigo_identificador"] = codigo_identificador;
        json["titulo"] = titulo;
        json["tipo_mayor"] = tipo_mayor;
        if (!subtipo.isEmpty()) json["subtipo"] = subtipo;
        json["ano"] = ano;
        if (mes.has_value()) json["mes"] = *mes;
        if (!pais.isEmpty()) json["pais"] = pais;
        json["estado_validacion"] = estado_validacion;
        json["detalles"] = detalles;
        json["activo"] = activo;
        json["es_ejemplo"] = es_ejemplo;
        return json;
    }

    [[nodiscard]] static Producto desdeJson(const QJsonObject& json) {
        Producto p;
        if (json.contains("id") && !json["id"].isNull()) {
            p.id = json["id"].toVariant().toLongLong();
        }
        p.codigo_identificador = json["codigo_identificador"].toString();
        p.titulo = json["titulo"].toString();
        p.tipo_mayor = json["tipo_mayor"].toString();
        p.subtipo = json["subtipo"].toString();
        p.ano = json["ano"].toInt(2024);
        if (json.contains("mes") && !json["mes"].isNull()) {
            p.mes = json["mes"].toInt();
        }
        p.pais = json["pais"].toString();
        if (json.contains("estado_validacion") && !json["estado_validacion"].toString().isEmpty()) {
            p.estado_validacion = json["estado_validacion"].toString();
        }
        if (json.contains("detalles") && json["detalles"].isObject()) {
            p.detalles = json["detalles"].toObject();
        }
        if (json.contains("activo")) {
            p.activo = json["activo"].toBool(true);
        }
        if (json.contains("es_ejemplo")) {
            p.es_ejemplo = json["es_ejemplo"].toBool(false);
        }
        return p;
    }
};

} // namespace pea::dominio
