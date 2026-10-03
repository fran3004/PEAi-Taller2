#include "pea/datos/sesion.hpp"
#include "pea/excepciones.hpp"

namespace pea::datos {

QString Sesion::token_acceso() const {
    if (esta_expirada()) {
        const_cast<Sesion*>(this)->cerrar_sesion();
        throw ErrorAutenticacion("La sesión ha expirado. Por favor inicie sesión nuevamente.");
    }
    return m_token_acceso;
}

bool Sesion::esta_autenticado() const noexcept {
    if (m_token_acceso.isEmpty()) {
        return false;
    }
    if (esta_expirada()) {
        const_cast<Sesion*>(this)->cerrar_sesion();
        return false;
    }
    return true;
}

bool Sesion::esta_expirada() const noexcept {
    if (!m_expira_en_epoch.has_value()) {
        return false;
    }
    qint64 ahora = QDateTime::currentSecsSinceEpoch();
    return ahora >= *m_expira_en_epoch;
}

void Sesion::iniciar_sesion(
    const QString& token,
    const QString& correo,
    qint64 tiempo_expiracion_segundos,
    const QJsonObject& metadatos) {
    m_token_acceso = token;
    m_correo = correo;
    m_rol = "authenticated";
    m_expira_en_epoch = QDateTime::currentSecsSinceEpoch() + tiempo_expiracion_segundos;
    m_metadatos = metadatos;
}

void Sesion::cerrar_sesion() noexcept {
    m_token_acceso.clear();
    m_correo.clear();
    m_rol = "anon";
    m_expira_en_epoch.reset();
    m_metadatos = QJsonObject();
}

void Sesion::simular_expiracion() noexcept {
    if (m_expira_en_epoch.has_value()) {
        m_expira_en_epoch = QDateTime::currentSecsSinceEpoch() - 1;
    }
}

} // namespace pea::datos
