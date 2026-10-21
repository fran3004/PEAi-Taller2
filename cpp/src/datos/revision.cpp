#include "pea/datos/revision.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QVariant>
#include <string>

namespace pea::datos {

qint64 ControladorRevision::consultar_remota(ClienteHTTPSupabase& cliente) {
    std::string error_rpc = "La RPC no devolvió una revisión válida.";
    try {
        const QJsonDocument doc_rpc = cliente.rpc("obtener_revision_actual");
        if (doc_rpc.isObject()) {
            const QJsonObject obj = doc_rpc.object();
            if (obj.contains("revision")) {
                bool valido = false;
                const qint64 revision = obj["revision"].toVariant().toLongLong(&valido);
                if (valido && revision > 0) return revision;
            }
        } else if (!doc_rpc.isNull() && !doc_rpc.isEmpty()) {
            bool valido = false;
            const qint64 revision =
                doc_rpc.toJson(QJsonDocument::Compact).trimmed().toLongLong(&valido);
            if (valido && revision > 0) return revision;
        }
    } catch (const std::exception& error) {
        error_rpc = error.what();
    } catch (...) {
        error_rpc = "Error desconocido al consultar la RPC.";
    }

    std::string error_meta = "La tabla meta no devolvió una revisión válida.";
    try {
        const QJsonDocument doc_meta = cliente.get("meta", "select=revision&id=eq.1");
        if (doc_meta.isArray()) {
            const QJsonArray filas = doc_meta.array();
            if (!filas.isEmpty() && filas[0].isObject()) {
                const QJsonObject fila = filas[0].toObject();
                if (fila.contains("revision")) {
                    bool valido = false;
                    const qint64 revision = fila["revision"].toVariant().toLongLong(&valido);
                    if (valido && revision > 0) return revision;
                }
            }
        }
    } catch (const std::exception& error) {
        error_meta = error.what();
    } catch (...) {
        error_meta = "Error desconocido al consultar la tabla meta.";
    }

    throw ErrorConexion(
        "No fue posible verificar la revisión remota. RPC: " + error_rpc +
        " Consulta meta: " + error_meta);
}

void ControladorRevision::verificar_consistencia(ClienteHTTPSupabase& cliente) {
    qint64 remota = consultar_remota(cliente);
    if (remota != m_revision_local) {
        throw ConflictoRevision(
            "La base de datos cambió",
            "Revisión remota: " + std::to_string(remota) +
            ", Revisión local esperada: " + std::to_string(m_revision_local)
        );
    }
}

qint64 ControladorRevision::sincronizar(ClienteHTTPSupabase& cliente) {
    m_revision_local = consultar_remota(cliente);
    return m_revision_local;
}

} // namespace pea::datos
