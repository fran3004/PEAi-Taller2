#pragma once

#include <QtGlobal>

namespace pea {
class ClienteHTTPSupabase;
}

namespace pea::datos {

class ControladorRevision {
public:
    explicit ControladorRevision(qint64 revision_inicial = 1) noexcept
        : m_revision_local(revision_inicial) {}

    [[nodiscard]] qint64 revision_local() const noexcept { return m_revision_local; }
    void actualizar_local(qint64 nueva_revision) noexcept { m_revision_local = nueva_revision; }

    [[nodiscard]] qint64 consultar_remota(ClienteHTTPSupabase& cliente);
    void verificar_consistencia(ClienteHTTPSupabase& cliente);
    qint64 sincronizar(ClienteHTTPSupabase& cliente);

private:
    qint64 m_revision_local{1};
};

} // namespace pea::datos
