#include "pea/datos/revision.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QVariant>

namespace pea::datos {

qint64 ControladorRevision::consultar_remota(ClienteHTTPSupabase& cliente) {
    try {
        // 1. Intentar RPC rápida
        QJsonDocument docRpc = cliente.rpc("obtener_revision_actual");
        if (docRpc.isObject()) {
            QJsonObject obj = docRpc.object();
            if (obj.contains("revision")) {
                return obj["revision"].toVariant().toLongLong();
            }
        } else if (!docRpc.isNull() && !docRpc.isEmpty()) {
            // Podría ser un entero escalar directamente
            bool ok = false;
            qint64 rev = docRpc.toJson(QJsonDocument::Compact).trimmed().toLongLong(&ok);
            if (ok) return rev;
        }
    } catch (...) {
        // Respaldo por consulta a tabla meta
    }

    try {
        QJsonDocument docMeta = cliente.get("meta", "select=revision&id=eq.1");
        if (docMeta.isArray()) {
            QJsonArray arr = docMeta.array();
            if (!arr.isEmpty() && arr[0].isObject()) {
                QJsonObject f = arr[0].toObject();
                if (f.contains("revision")) {
                    return f["revision"].toVariant().toLongLong();
                }
            }
        }
    } catch (...) {
        // En caso de fallo total, mantener local
    }

    return m_revision_local;
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
