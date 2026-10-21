#include "pea/datos/configuracion_conexion.hpp"

#include <QByteArray>
#include <QCoreApplication>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QProcessEnvironment>
#include <QStringList>
#include <QUrl>

#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include "pea/datos/sesion.hpp"

namespace pea::datos {
namespace {

QString primera_variable(
    const QProcessEnvironment& entorno,
    const QStringList& nombres) {
    for (const auto& nombre : nombres) {
        const QString valor = entorno.value(nombre).trimmed();
        if (!valor.isEmpty()) {
            return valor;
        }
    }
    return {};
}

bool es_clave_no_publicable(const QString& clave) {
    if (clave.startsWith(QStringLiteral("sb_secret_"), Qt::CaseInsensitive)) {
        return true;
    }
    const auto segmentos = clave.split('.');
    if (segmentos.size() != 3) {
        return false;
    }
    const auto carga = QByteArray::fromBase64(
        segmentos[1].toLatin1(), QByteArray::Base64UrlEncoding);
    const auto json = QJsonDocument::fromJson(carga);
    return json.isObject() &&
           json.object().value(QStringLiteral("role")).toString() == QStringLiteral("service_role");
}

} // namespace

ConfiguracionConexion leer_configuracion_conexion() {
    const auto entorno = QProcessEnvironment::systemEnvironment();
    QJsonObject publica;
    if (entorno.value("PEA_OMITIR_CONFIG_PUBLICA") != "1") {
        QFile archivo(QDir(QCoreApplication::applicationDirPath()).filePath("../config/pea.config.json"));
        if (archivo.exists()) {
            if (!archivo.open(QIODevice::ReadOnly)) {
                throw ErrorValidacion("No se pudo leer la configuración pública del paquete.");
            }
            publica = QJsonDocument::fromJson(archivo.readAll()).object();
            if (publica.size() != 3 ||
                publica.value("url").toString() != "https://wdmchsncexayqbjueamb.supabase.co" ||
                !publica.value("clave_publishable").toString().startsWith("sb_publishable_") ||
                !publica.value("acceso_evaluacion").toBool()) {
                throw ErrorValidacion("La configuración pública no es válida para pea-prod.");
            }
        }
    }
    QString url = primera_variable(entorno, {
        QStringLiteral("PEA_SUPABASE_URL"),
        QStringLiteral("PEA_SUPABASE_URL_PROD"),
        QStringLiteral("PEA_SUPABASE_URL_TEST"),
    });
    if (url.isEmpty()) url = publica.value("url").toString();
    while (url.endsWith('/')) {
        url.chop(1);
    }
    if (url.endsWith(QStringLiteral("/rest/v1"), Qt::CaseInsensitive)) {
        url.chop(QStringLiteral("/rest/v1").size());
    }
    QString clave = primera_variable(entorno, {
        QStringLiteral("PEA_SUPABASE_PUBLISHABLE_KEY"),
        QStringLiteral("PEA_SUPABASE_ANON_KEY"),
        QStringLiteral("PEA_SUPABASE_KEY_PROD"),
        QStringLiteral("PEA_SUPABASE_ANON_PROD"),
        QStringLiteral("PEA_SUPABASE_KEY_TEST"),
        QStringLiteral("PEA_SUPABASE_ANON_TEST"),
    });
    if (clave.isEmpty()) clave = publica.value("clave_publishable").toString();
    return {
        url,
        clave,
        primera_variable(entorno, {QStringLiteral("PEA_USUARIO_CORREO")}),
        !url.isEmpty(),
        !clave.isEmpty(),
        publica.value("acceso_evaluacion").toBool(),
    };
}

QString leer_clave_usuario() {
    return QProcessEnvironment::systemEnvironment().value(QStringLiteral("PEA_USUARIO_CLAVE"));
}

void validar_configuracion_conexion(const ConfiguracionConexion& configuracion) {
    const QUrl url(configuracion.url);
    if (url.scheme().compare(QStringLiteral("https"), Qt::CaseInsensitive) != 0) {
        throw ErrorValidacion("La URL de Supabase debe usar HTTPS.");
    }
    if (url.host().compare(QStringLiteral("wdmchsncexayqbjueamb.supabase.co"),
                           Qt::CaseInsensitive) != 0 ||
        !url.userInfo().isEmpty() || url.port(-1) != -1 ||
        !url.query().isEmpty() || !url.fragment().isEmpty() ||
        (!url.path().isEmpty() && url.path() != QStringLiteral("/"))) {
        throw ErrorValidacion("La URL configurada no corresponde al proyecto pea-prod.");
    }
    if (configuracion.clave_publicable.isEmpty()) {
        throw ErrorValidacion("Falta la clave publicable de Supabase.");
    }
    if (es_clave_no_publicable(configuracion.clave_publicable)) {
        throw ErrorValidacion("PEA-i solo acepta claves publicables de Supabase.");
    }
}

std::unique_ptr<ClienteHTTPSupabase> crear_cliente_configurado(
    QString* correo,
    std::shared_ptr<Sesion>* sesion) {
    const auto configuracion = leer_configuracion_conexion();
    if (!configuracion.url_configurada && !configuracion.clave_configurada) {
        return nullptr;
    }
    validar_configuracion_conexion(configuracion);

    auto cliente = std::make_unique<ClienteHTTPSupabase>(
        configuracion.url, configuracion.clave_publicable, 15000);
    QString clave = leer_clave_usuario();
    if (configuracion.correo.isEmpty() != clave.isEmpty()) {
        clave.fill(QChar('\0'));
        throw ErrorValidacion("Configure conjuntamente PEA_USUARIO_CORREO y PEA_USUARIO_CLAVE.");
    }
    if (!configuracion.correo.isEmpty()) {
        const auto respuesta = cliente->autenticar(configuracion.correo, std::move(clave));
        const QString token = respuesta.value(QStringLiteral("access_token")).toString();
        cliente->establecerTokenAcceso(token);
        if (sesion) {
            auto nueva_sesion = std::make_shared<Sesion>();
            nueva_sesion->iniciar_sesion(
                token,
                configuracion.correo,
                respuesta.value(QStringLiteral("expires_in")).toInt(3600),
                respuesta.value(QStringLiteral("user")).toObject());
            *sesion = std::move(nueva_sesion);
        }
    }
    if (configuracion.correo.isEmpty() && configuracion.acceso_evaluacion) {
        const auto respuesta = cliente->autenticarEvaluacion();
        if (sesion) {
            auto nueva_sesion = std::make_shared<Sesion>();
            nueva_sesion->iniciar_sesion(
                respuesta.value("access_token").toString(), QStringLiteral("Evaluación automática"),
                respuesta.value("expires_in").toInt(3600), respuesta.value("user").toObject());
            *sesion = std::move(nueva_sesion);
        }
    }
    if (correo) {
        *correo = configuracion.correo;
    }
    return cliente;
}

} // namespace pea::datos
