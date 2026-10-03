#include "pea/ingesta/extractor_url.hpp"
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDateTime>
#include <QDir>
#include <QEventLoop>
#include <QFile>
#include <QJsonDocument>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QThread>
#include <QTimer>
#include <QUrl>
#include "pea/ingesta/parser_html.hpp"

namespace pea::ingesta {

static const QString HOST_PERMITIDO = QStringLiteral("scienti.minciencias.gov.co");
static const QString USER_AGENT_UPC = QStringLiteral(
    "PEAi-Taller2-UPC/1.0 (Proyecto Academico Estructura de Datos; "
    "Universidad Popular del Cesar; contact: fandresfernandez@unicesar.edu.co)"
);

ExtractorURL::ExtractorURL(const QString& cache_dir, double pausa_segundos)
    : m_cache_dir(cache_dir), m_pausa_segundos(pausa_segundos) {
    QDir().mkpath(m_cache_dir);
}

std::pair<QString, QString> ExtractorURL::validar_url(const QString& url_str) {
    QUrl url(url_str);
    if (url.scheme().toLower() != QStringLiteral("https")) {
        throw std::runtime_error("Protocolo no permitido ('" + url.scheme().toStdString() + "'). Solo se permite HTTPS.");
    }
    if (url.host().toLower() != HOST_PERMITIDO) {
        throw std::runtime_error("Host no permitido ('" + url.host().toStdString() + "'). Solo se permite " + HOST_PERMITIDO.toStdString() + ".");
    }

    QString path = url.path().toLower();
    if (path.contains(QStringLiteral("gruplac"))) {
        return {QStringLiteral("gruplac"), url.query()};
    } else if (path.contains(QStringLiteral("cvlac"))) {
        return {QStringLiteral("cvlac"), url.query()};
    } else {
        throw std::runtime_error("URL no reconocida como GrupLAC ni CvLAC: " + url_str.toStdString());
    }
}

std::pair<QByteArray, QJsonObject> ExtractorURL::descargar_o_cargar_cache(
    const QString& url,
    const QString& alias,
    bool forzar_descarga
) {
    validar_url(url);

    QDir().mkpath(m_cache_dir);
    QString url_hash = QString::fromUtf8(QCryptographicHash::hash(url.toUtf8(), QCryptographicHash::Sha256).toHex());
    QString ruta_html = QDir(m_cache_dir).filePath(url_hash + QStringLiteral(".html"));
    QString ruta_meta = QDir(m_cache_dir).filePath(url_hash + QStringLiteral(".meta.json"));

    // 1. Verificar caché
    if (!forzar_descarga && QFile::exists(ruta_html) && QFile::exists(ruta_meta)) {
        QFile f_html(ruta_html);
        QFile f_meta(ruta_meta);
        if (f_html.open(QIODevice::ReadOnly) && f_meta.open(QIODevice::ReadOnly)) {
            QByteArray content = f_html.readAll();
            QJsonObject meta = QJsonDocument::fromJson(f_meta.readAll()).object();
            return {content, meta};
        }
    }

    // 2. Control de cortesía / pausa
    qint64 ahora_ms = QDateTime::currentMSecsSinceEpoch();
    qint64 pausa_ms = static_cast<qint64>(m_pausa_segundos * 1000.0);
    qint64 transcurrido = ahora_ms - m_ultima_peticion_tiempo_ms;
    if (transcurrido < pausa_ms) {
        QThread::msleep(static_cast<unsigned long>(pausa_ms - transcurrido));
    }

    QNetworkAccessManager nam;
    int max_reintentos = 3;
    QString ultimo_error;

    for (int intento = 0; intento < max_reintentos; ++intento) {
        m_ultima_peticion_tiempo_ms = QDateTime::currentMSecsSinceEpoch();

        QNetworkRequest req(QUrl{url});
        req.setHeader(QNetworkRequest::UserAgentHeader, USER_AGENT_UPC);
        req.setRawHeader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
        req.setRawHeader("Accept-Language", "es-CO,es-ES;q=0.9,es;q=0.8");

        QEventLoop loop;
        QTimer timer;
        timer.setSingleShot(true);

        QNetworkReply* reply = nam.get(req);
        QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
        QObject::connect(&timer, &QTimer::timeout, &loop, [&]() {
            reply->abort();
            loop.quit();
        });

        timer.start(15000); // 15s timeout
        loop.exec();

        if (reply->error() == QNetworkReply::NoError) {
            int code = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
            if (code == 200) {
                QByteArray bytes = reply->readAll();
                reply->deleteLater();

                QString sha256_str = QString::fromUtf8(QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex());

                QJsonObject meta;
                meta[QStringLiteral("url")] = url;
                if (!alias.isEmpty()) meta[QStringLiteral("alias")] = alias;
                meta[QStringLiteral("fecha_descarga")] = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
                meta[QStringLiteral("codigo_http")] = code;
                meta[QStringLiteral("encoding_utilizada")] = QStringLiteral("ISO-8859-1");
                meta[QStringLiteral("longitud_bytes")] = static_cast<qint64>(bytes.size());
                meta[QStringLiteral("sha256")] = sha256_str;
                meta[QStringLiteral("url_hash")] = url_hash;

                // Guardar en caché
                QFile f_html(ruta_html);
                if (f_html.open(QIODevice::WriteOnly)) {
                    f_html.write(bytes);
                    f_html.close();
                }

                QFile f_meta(ruta_meta);
                if (f_meta.open(QIODevice::WriteOnly)) {
                    f_meta.write(QJsonDocument(meta).toJson(QJsonDocument::Indented));
                    f_meta.close();
                }

                if (!alias.isEmpty()) {
                    QString alias_h = QDir(m_cache_dir).filePath(alias + QStringLiteral(".html"));
                    QString alias_m = QDir(m_cache_dir).filePath(alias + QStringLiteral(".meta.json"));
                    QFile fa_h(alias_h);
                    if (fa_h.open(QIODevice::WriteOnly)) { fa_h.write(bytes); fa_h.close(); }
                    QFile fa_m(alias_m);
                    if (fa_m.open(QIODevice::WriteOnly)) {
                        fa_m.write(QJsonDocument(meta).toJson(QJsonDocument::Indented));
                        fa_m.close();
                    }
                }

                return {bytes, meta};
            } else {
                ultimo_error = QStringLiteral("HTTP %1").arg(code);
            }
        } else {
            ultimo_error = reply->errorString();
        }

        reply->deleteLater();
        unsigned long espera_ms = static_cast<unsigned long>(pausa_ms * (1 << intento));
        QThread::msleep(espera_ms);
    }

    throw std::runtime_error("Fallo al descargar '" + url.toStdString() + "': " + ultimo_error.toStdString());
}

InformeIngesta ExtractorURL::procesar_url(
    const QString& url,
    const QString& salida_dir,
    bool anonimizar,
    bool forzar_descarga
) {
    auto [tipo_fuente, _] = validar_url(url);
    QDir().mkpath(salida_dir);

    QString sha_corto = QString::fromUtf8(QCryptographicHash::hash(url.toUtf8(), QCryptographicHash::Sha256).toHex()).left(12);
    QString alias = QStringLiteral("%1_%2").arg(tipo_fuente, sha_corto);

    auto [bytes, meta] = descargar_o_cargar_cache(url, alias, forzar_descarga);
    QString html = QString::fromLatin1(bytes);

    InformeIngesta informe;
    informe.origen = url;
    informe.tipo_fuente = QStringLiteral("url_%1").arg(tipo_fuente);
    informe.fecha = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
    informe.exito = true;
    informe.mensaje = QStringLiteral("Extracción web completada con éxito");

    QJsonObject archivos;

    if (tipo_fuente == QStringLiteral("gruplac")) {
        GrupoIngesta grupo = ParserHTML::parsear_gruplac(html, meta, anonimizar);
        informe.grupos_procesados = 1;
        informe.productos_procesados = static_cast<int>(
            grupo.articulos.size() + grupo.libros.size() + grupo.capitulos.size() + grupo.softwares.size()
        );

        // Guardar JSON
        QString ruta_json = QDir(salida_dir).filePath(QStringLiteral("GrupLAC-%1.json").arg(grupo.codigo_gruplac));
        QFile fj(ruta_json);
        if (fj.open(QIODevice::WriteOnly)) {
            fj.write(QJsonDocument(grupo.a_json()).toJson(QJsonDocument::Indented));
            fj.close();
            archivos[QStringLiteral("json")] = ruta_json;
        }

        // Guardar Markdown
        QString ruta_md = QDir(salida_dir).filePath(QStringLiteral("GrupLAC-%1.md").arg(grupo.codigo_gruplac));
        QFile fm(ruta_md);
        if (fm.open(QIODevice::WriteOnly)) {
            fm.write(ParserHTML::generar_markdown_gruplac(grupo, meta, anonimizar).toUtf8());
            fm.close();
            archivos[QStringLiteral("markdown")] = ruta_md;
        }
    } else if (tipo_fuente == QStringLiteral("cvlac")) {
        InvestigadorIngesta inv = ParserHTML::parsear_cvlac(html, meta, anonimizar);
        informe.investigadores_procesados = 1;
        informe.productos_procesados = static_cast<int>(
            inv.articulos.size() + inv.libros.size() + inv.capitulos.size() + inv.softwares.size()
        );

        QString ruta_json = QDir(salida_dir).filePath(QStringLiteral("CvLAC-%1.json").arg(inv.codigo_rh));
        QFile fj(ruta_json);
        if (fj.open(QIODevice::WriteOnly)) {
            fj.write(QJsonDocument(inv.a_json()).toJson(QJsonDocument::Indented));
            fj.close();
            archivos[QStringLiteral("json")] = ruta_json;
        }

        QString ruta_md = QDir(salida_dir).filePath(QStringLiteral("CvLAC-%1.md").arg(inv.codigo_rh));
        QFile fm(ruta_md);
        if (fm.open(QIODevice::WriteOnly)) {
            fm.write(ParserHTML::generar_markdown_cvlac(inv, meta, anonimizar).toUtf8());
            fm.close();
            archivos[QStringLiteral("markdown")] = ruta_md;
        }
    }

    informe.archivos_generados = archivos;
    return informe;
}

} // namespace pea::ingesta
