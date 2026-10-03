#pragma once

#include <QString>
#include <QByteArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <memory>
#include "pea/excepciones.hpp"

namespace pea {

class ClienteHTTPSupabase {
public:
    ClienteHTTPSupabase(const QString& baseUrl, const QString& anonKey, int timeoutMs = 15000);
    ~ClienteHTTPSupabase() = default;

    // Gestión de tokens en memoria volátil (nunca en disco)
    void establecerTokenAcceso(const QString& token);
    void cerrarSesion();
    QString tokenAcceso() const;

    // Métodos REST principales
    QJsonDocument get(const QString& tabla, const QString& queryParams = QString());
    QJsonArray getPaginado(const QString& tabla, int loteTamano = 1000);
    QJsonDocument post(const QString& tabla, const QJsonDocument& datos);
    QJsonDocument patch(const QString& tabla, const QJsonDocument& datos, const QString& filtros);
    void eliminar(const QString& tabla, const QString& filtros);
    QJsonDocument rpc(const QString& funcion, const QJsonObject& parametros = QJsonObject());

    // Verificación de capacidades TLS
    static bool soportaTLS();
    static QString backendTLS();

    QString baseUrl() const { return m_baseUrl; }
    QString anonKey() const { return m_anonKey; }

private:
    QNetworkRequest prepararSolicitud(const QUrl& url, const QByteArray& preferHeader = QByteArray()) const;
    QJsonDocument ejecutarSolicitud(const QNetworkRequest& req, const QByteArray& verbo, const QByteArray& cuerpo = QByteArray());

    QString m_baseUrl;
    QString m_anonKey;
    int m_timeoutMs;
    QString m_tokenAcceso;
    std::unique_ptr<QNetworkAccessManager> m_manager;
};

} // namespace pea
