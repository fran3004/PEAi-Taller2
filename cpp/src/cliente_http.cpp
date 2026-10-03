#include "pea/cliente_http.hpp"
#include <QUrl>
#include <QUrlQuery>
#include <QEventLoop>
#include <QTimer>
#include <QSslSocket>
#include <QJsonParseError>

namespace pea {

ClienteHTTPSupabase::ClienteHTTPSupabase(const QString& baseUrl, const QString& anonKey, int timeoutMs)
    : m_baseUrl(baseUrl),
      m_anonKey(anonKey),
      m_timeoutMs(timeoutMs),
      m_manager(std::make_unique<QNetworkAccessManager>()) {
    if (m_baseUrl.endsWith('/')) {
        m_baseUrl.chop(1);
    }
}

void ClienteHTTPSupabase::establecerTokenAcceso(const QString& token) {
    m_tokenAcceso = token;
}

void ClienteHTTPSupabase::cerrarSesion() {
    m_tokenAcceso.clear();
}

QString ClienteHTTPSupabase::tokenAcceso() const {
    return m_tokenAcceso;
}

bool ClienteHTTPSupabase::soportaTLS() {
    return QSslSocket::supportsSsl();
}

QString ClienteHTTPSupabase::backendTLS() {
    return QSslSocket::sslLibraryBuildVersionString();
}

QNetworkRequest ClienteHTTPSupabase::prepararSolicitud(const QUrl& url, const QByteArray& preferHeader) const {
    QNetworkRequest req(url);
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    req.setRawHeader("apikey", m_anonKey.toUtf8());

    if (!m_tokenAcceso.isEmpty()) {
        req.setRawHeader("Authorization", "Bearer " + m_tokenAcceso.toUtf8());
    } else {
        req.setRawHeader("Authorization", "Bearer " + m_anonKey.toUtf8());
    }

    if (!preferHeader.isEmpty()) {
        req.setRawHeader("Prefer", preferHeader);
    }

    return req;
}

QJsonDocument ClienteHTTPSupabase::ejecutarSolicitud(const QNetworkRequest& req, const QByteArray& verbo, const QByteArray& cuerpo) {
    QEventLoop loop;
    QTimer timer;
    timer.setSingleShot(true);

    QNetworkReply* reply = nullptr;

    if (verbo == "GET") {
        reply = m_manager->get(req);
    } else if (verbo == "POST") {
        reply = m_manager->post(req, cuerpo);
    } else if (verbo == "PATCH") {
        reply = m_manager->sendCustomRequest(req, "PATCH", cuerpo);
    } else if (verbo == "DELETE") {
        reply = m_manager->deleteResource(req);
    } else {
        throw ErrorPEA("Verbo HTTP no soportado: " + verbo.toStdString());
    }

    bool tiempoAgotado = false;
    QObject::connect(&timer, &QTimer::timeout, [&]() {
        tiempoAgotado = true;
        if (reply) {
            reply->abort();
        }
        loop.quit();
    });

    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);

    timer.start(m_timeoutMs);
    loop.exec();

    if (timer.isActive()) {
        timer.stop();
    }

    if (tiempoAgotado) {
        reply->deleteLater();
        throw ErrorConexion("Tiempo de espera agotado al conectar con Supabase");
    }

    int codigoEstado = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    QByteArray respuestaBytes = reply->readAll();
    std::string respuestaStr = respuestaBytes.toStdString();
    auto errorRed = reply->error();

    reply->deleteLater();

    if (errorRed != QNetworkReply::NoError) {
        if (codigoEstado == 0) {
            throw ErrorConexion("Error de red o conexión: " + reply->errorString().toStdString());
        }
        if (codigoEstado == 401) {
            throw ErrorAutenticacion("Credenciales inválidas o expiradas", respuestaStr);
        }
        if (codigoEstado == 403) {
            throw ErrorAutorizacion("Acceso denegado por políticas de seguridad RLS", respuestaStr);
        }
        if (codigoEstado == 404) {
            throw RecursoNoEncontrado("Recurso no encontrado", respuestaStr);
        }
        if (codigoEstado == 409) {
            throw ConflictoRevision("Conflicto de concurrencia o violación de clave", respuestaStr);
        }
        if (codigoEstado == 422) {
            throw ErrorValidacion("Error de validación en los datos enviados", respuestaStr);
        }
        if (codigoEstado >= 500) {
            throw ErrorServidor("Error interno en Supabase/PostgreSQL", respuestaStr);
        }
        throw ErrorPEA("Error HTTP " + std::to_string(codigoEstado), respuestaStr);
    }

    if (respuestaBytes.isEmpty()) {
        return QJsonDocument();
    }

    QJsonParseError jsonError;
    QJsonDocument doc = QJsonDocument::fromJson(respuestaBytes, &jsonError);
    if (jsonError.error != QJsonParseError::NoError) {
        return QJsonDocument();
    }

    return doc;
}

QJsonDocument ClienteHTTPSupabase::get(const QString& tabla, const QString& queryParams) {
    QString urlStr = m_baseUrl + "/rest/v1/" + tabla;
    if (!queryParams.isEmpty()) {
        urlStr += "?" + queryParams;
    }
    QNetworkRequest req = prepararSolicitud(QUrl(urlStr));
    return ejecutarSolicitud(req, "GET");
}

QJsonArray ClienteHTTPSupabase::getPaginado(const QString& tabla, int loteTamano) {
    QJsonArray resultadoTotal;
    int desde = 0;

    while (true) {
        int hasta = desde + loteTamano - 1;
        QString urlStr = m_baseUrl + "/rest/v1/" + tabla;
        QNetworkRequest req = prepararSolicitud(QUrl(urlStr));
        req.setRawHeader("Range-Unit", "items");
        req.setRawHeader("Range", QString("%1-%2").arg(desde).arg(hasta).toUtf8());

        QJsonDocument doc = ejecutarSolicitud(req, "GET");
        if (!doc.isArray()) {
            break;
        }

        QJsonArray lote = doc.array();
        if (lote.isEmpty()) {
            break;
        }

        for (const auto& valor : lote) {
            resultadoTotal.append(valor);
        }

        if (lote.size() < loteTamano) {
            break;
        }

        desde += loteTamano;
    }

    return resultadoTotal;
}

QJsonDocument ClienteHTTPSupabase::post(const QString& tabla, const QJsonDocument& datos) {
    QString urlStr = m_baseUrl + "/rest/v1/" + tabla;
    QNetworkRequest req = prepararSolicitud(QUrl(urlStr), "return=representation");
    return ejecutarSolicitud(req, "POST", datos.toJson(QJsonDocument::Compact));
}

QJsonDocument ClienteHTTPSupabase::patch(const QString& tabla, const QJsonDocument& datos, const QString& filtros) {
    QString urlStr = m_baseUrl + "/rest/v1/" + tabla;
    if (!filtros.isEmpty()) {
        urlStr += "?" + filtros;
    }
    QNetworkRequest req = prepararSolicitud(QUrl(urlStr), "return=representation");
    return ejecutarSolicitud(req, "PATCH", datos.toJson(QJsonDocument::Compact));
}

void ClienteHTTPSupabase::eliminar(const QString& tabla, const QString& filtros) {
    QString urlStr = m_baseUrl + "/rest/v1/" + tabla;
    if (!filtros.isEmpty()) {
        urlStr += "?" + filtros;
    }
    QNetworkRequest req = prepararSolicitud(QUrl(urlStr), "return=representation");
    ejecutarSolicitud(req, "DELETE");
}

QJsonDocument ClienteHTTPSupabase::rpc(const QString& funcion, const QJsonObject& parametros) {
    QString urlStr = m_baseUrl + "/rest/v1/rpc/" + funcion;
    QNetworkRequest req = prepararSolicitud(QUrl(urlStr));
    QJsonDocument doc(parametros);
    return ejecutarSolicitud(req, "POST", doc.toJson(QJsonDocument::Compact));
}

} // namespace pea
