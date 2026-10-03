#pragma once

#include <optional>
#include <vector>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>
#include "pea/estructuras/lista_doble.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/integrante.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/dominio/proyecto.hpp"

namespace pea {
class ClienteHTTPSupabase;
}

namespace pea::datos {

class RepositorioGrupos {
public:
    explicit RepositorioGrupos(ClienteHTTPSupabase& cliente) : m_cliente(cliente) {}

    [[nodiscard]] estructuras::ListaDoble<dominio::Grupo> listar(std::optional<bool> es_ejemplo = std::nullopt);
    [[nodiscard]] std::optional<dominio::Grupo> obtener_por_codigo(const QString& codigo_gruplac);
    dominio::Grupo crear(const dominio::Grupo& grupo);
    dominio::Grupo actualizar(const QString& codigo_gruplac, const QJsonObject& datos);
    void desactivar(qint64 id_grupo, qint64 revision_esperada);
    void eliminar(qint64 id_grupo, qint64 revision_esperada);

private:
    ClienteHTTPSupabase& m_cliente;
};

class RepositorioInvestigadores {
public:
    explicit RepositorioInvestigadores(ClienteHTTPSupabase& cliente) : m_cliente(cliente) {}

    [[nodiscard]] estructuras::ListaDoble<dominio::Investigador> listar(std::optional<bool> es_ejemplo = std::nullopt);
    [[nodiscard]] std::optional<dominio::Investigador> obtener_por_codigo(const QString& codigo_rh);
    dominio::Investigador crear(const dominio::Investigador& inv);
    dominio::Investigador actualizar(const QString& codigo_rh, const QJsonObject& datos);
    void desactivar(qint64 id_inv, qint64 revision_esperada);
    void eliminar(qint64 id_inv, qint64 revision_esperada);

private:
    ClienteHTTPSupabase& m_cliente;
};

class RepositorioIntegrantes {
public:
    explicit RepositorioIntegrantes(ClienteHTTPSupabase& cliente) : m_cliente(cliente) {}

    [[nodiscard]] estructuras::ListaDoble<dominio::IntegranteGrupo> listar(const QString& codigo_gruplac = QString());
    dominio::IntegranteGrupo vincular(const dominio::IntegranteGrupo& integrante);
    void desvincular(const QString& codigo_gruplac, const QString& codigo_rh);

private:
    ClienteHTTPSupabase& m_cliente;
};

class RepositorioProductos {
public:
    explicit RepositorioProductos(ClienteHTTPSupabase& cliente) : m_cliente(cliente) {}

    [[nodiscard]] estructuras::ListaDoble<dominio::Producto> listar(std::optional<bool> es_ejemplo = std::nullopt);
    [[nodiscard]] std::optional<dominio::Producto> obtener_por_codigo(const QString& codigo_identificador);
    qint64 crear_con_rpc(
        const dominio::Producto& producto,
        std::optional<qint64> grupo_id,
        const std::vector<qint64>& investigadores_ids,
        qint64 revision_esperada);
    dominio::Producto crear_directo(const dominio::Producto& producto);
    void asociar_grupo(qint64 producto_id, qint64 grupo_id, bool es_ejemplo = false);
    void asociar_autor(qint64 producto_id, qint64 investigador_id, int orden = 1, bool es_ejemplo = false);
    [[nodiscard]] QJsonArray listar_relaciones_grupos();
    [[nodiscard]] QJsonArray listar_relaciones_autores();
    void desactivar(qint64 id_producto, qint64 revision_esperada);
    void eliminar_cascada(qint64 id_producto, qint64 revision_esperada);

private:
    ClienteHTTPSupabase& m_cliente;
};

class RepositorioProyectos {
public:
    explicit RepositorioProyectos(ClienteHTTPSupabase& cliente) : m_cliente(cliente) {}

    [[nodiscard]] estructuras::ListaDoble<dominio::Proyecto> listar(const QString& codigo_gruplac = QString());
    dominio::Proyecto crear(const dominio::Proyecto& proyecto);

private:
    ClienteHTTPSupabase& m_cliente;
};

} // namespace pea::datos
