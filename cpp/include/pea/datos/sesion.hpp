#pragma once

#include <optional>
#include <QDateTime>
#include <QJsonObject>
#include <QString>

namespace pea::datos {

class Sesion {
public:
    Sesion() = default;

    QString token_acceso() const;

    [[nodiscard]] QString correo() const noexcept { return m_correo; }
    [[nodiscard]] QString rol() const noexcept { return m_rol; }
    [[nodiscard]] bool esta_autenticado() const noexcept;
    [[nodiscard]] bool esta_expirada() const noexcept;

    void iniciar_sesion(
        const QString& token,
        const QString& correo,
        qint64 tiempo_expiracion_segundos = 3600,
        const QJsonObject& metadatos = {});

    void cerrar_sesion() noexcept;
    void simular_expiracion() noexcept;

private:
    QString m_token_acceso;
    QString m_correo;
    QString m_rol{"anon"};
    std::optional<qint64> m_expira_en_epoch;
    QJsonObject m_metadatos;
};

} // namespace pea::datos
