#include "pea/datos/repositorios.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include <QJsonDocument>
#include <QUrlQuery>

namespace pea::datos {

// ============================================================================
// RepositorioGrupos
// ============================================================================

estructuras::ListaDoble<dominio::Grupo> RepositorioGrupos::listar(std::optional<bool> es_ejemplo) {
    estructuras::ListaDoble<dominio::Grupo> lista;
    QJsonArray filas;
    if (es_ejemplo.has_value()) {
        QString params = QString("select=*&es_ejemplo=eq.%1").arg(*es_ejemplo ? "true" : "false");
        QJsonDocument doc = m_cliente.get("grupos", params);
        if (doc.isArray()) {
            filas = doc.array();
        }
    } else {
        filas = m_cliente.getPaginado("grupos");
    }

    for (const auto& val : filas) {
        if (val.isObject()) {
            lista.insertar_final(dominio::Grupo::desdeJson(val.toObject()));
        }
    }
    return lista;
}

std::optional<dominio::Grupo> RepositorioGrupos::obtener_por_codigo(const QString& codigo_gruplac) {
    QString params = QString("codigo_gruplac=eq.%1&select=*").arg(codigo_gruplac);
    QJsonDocument doc = m_cliente.get("grupos", params);
    if (doc.isArray()) {
        QJsonArray arr = doc.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Grupo::desdeJson(arr[0].toObject());
        }
    }
    return std::nullopt;
}

dominio::Grupo RepositorioGrupos::crear(const dominio::Grupo& grupo) {
    QJsonObject obj = grupo.aJson(false); // excluir id
    QJsonDocument docEnvio(obj);
    QJsonDocument res = m_cliente.post("grupos", docEnvio);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Grupo::desdeJson(arr[0].toObject());
        }
    }
    return grupo;
}

dominio::Grupo RepositorioGrupos::actualizar(const QString& codigo_gruplac, const QJsonObject& datos) {
    QJsonDocument docEnvio(datos);
    QString filtros = QString("codigo_gruplac=eq.%1").arg(codigo_gruplac);
    QJsonDocument res = m_cliente.patch("grupos", docEnvio, filtros);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Grupo::desdeJson(arr[0].toObject());
        }
    }
    auto g = obtener_por_codigo(codigo_gruplac);
    if (!g.has_value()) {
        throw RecursoNoEncontrado("Grupo con código " + codigo_gruplac.toStdString() + " no encontrado tras actualizar");
    }
    return *g;
}

void RepositorioGrupos::desactivar(qint64 id_grupo, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "grupo";
    params["p_id"] = id_grupo;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_desactivar_nodo", params);
}

void RepositorioGrupos::eliminar(qint64 id_grupo, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "grupo";
    params["p_id"] = id_grupo;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_eliminar_cascada", params);
}

// ============================================================================
// RepositorioInvestigadores
// ============================================================================

estructuras::ListaDoble<dominio::Investigador> RepositorioInvestigadores::listar(std::optional<bool> es_ejemplo) {
    estructuras::ListaDoble<dominio::Investigador> lista;
    QJsonArray filas;
    if (es_ejemplo.has_value()) {
        QString params = QString("select=*&es_ejemplo=eq.%1").arg(*es_ejemplo ? "true" : "false");
        QJsonDocument doc = m_cliente.get("investigadores", params);
        if (doc.isArray()) {
            filas = doc.array();
        }
    } else {
        filas = m_cliente.getPaginado("investigadores");
    }

    for (const auto& val : filas) {
        if (val.isObject()) {
            lista.insertar_final(dominio::Investigador::desdeJson(val.toObject()));
        }
    }
    return lista;
}

std::optional<dominio::Investigador> RepositorioInvestigadores::obtener_por_codigo(const QString& codigo_rh) {
    QString params = QString("codigo_rh=eq.%1&select=*").arg(codigo_rh);
    QJsonDocument doc = m_cliente.get("investigadores", params);
    if (doc.isArray()) {
        QJsonArray arr = doc.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Investigador::desdeJson(arr[0].toObject());
        }
    }
    return std::nullopt;
}

dominio::Investigador RepositorioInvestigadores::crear(const dominio::Investigador& inv) {
    QJsonObject obj = inv.aJson(false);
    QJsonDocument docEnvio(obj);
    QJsonDocument res = m_cliente.post("investigadores", docEnvio);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Investigador::desdeJson(arr[0].toObject());
        }
    }
    return inv;
}

dominio::Investigador RepositorioInvestigadores::actualizar(const QString& codigo_rh, const QJsonObject& datos) {
    QJsonDocument docEnvio(datos);
    QString filtros = QString("codigo_rh=eq.%1").arg(codigo_rh);
    QJsonDocument res = m_cliente.patch("investigadores", docEnvio, filtros);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Investigador::desdeJson(arr[0].toObject());
        }
    }
    auto inv = obtener_por_codigo(codigo_rh);
    if (!inv.has_value()) {
        throw RecursoNoEncontrado("Investigador con código " + codigo_rh.toStdString() + " no encontrado tras actualizar");
    }
    return *inv;
}

void RepositorioInvestigadores::desactivar(qint64 id_inv, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "investigador";
    params["p_id"] = id_inv;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_desactivar_nodo", params);
}

void RepositorioInvestigadores::eliminar(qint64 id_inv, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "investigador";
    params["p_id"] = id_inv;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_eliminar_cascada", params);
}

// ============================================================================
// RepositorioIntegrantes
// ============================================================================

estructuras::ListaDoble<dominio::IntegranteGrupo> RepositorioIntegrantes::listar(const QString& codigo_gruplac) {
    estructuras::ListaDoble<dominio::IntegranteGrupo> lista;
    QJsonArray filas;
    if (!codigo_gruplac.isEmpty()) {
        QString params = QString("select=*&codigo_gruplac=eq.%1").arg(codigo_gruplac);
        QJsonDocument doc = m_cliente.get("integrantes_grupo", params);
        if (doc.isArray()) {
            filas = doc.array();
        }
    } else {
        filas = m_cliente.getPaginado("integrantes_grupo");
    }

    for (const auto& val : filas) {
        if (val.isObject()) {
            lista.insertar_final(dominio::IntegranteGrupo::desdeJson(val.toObject()));
        }
    }
    return lista;
}

dominio::IntegranteGrupo RepositorioIntegrantes::vincular(const dominio::IntegranteGrupo& integrante) {
    QJsonObject obj = integrante.aJson(false);
    QJsonDocument docEnvio(obj);
    QJsonDocument res = m_cliente.post("integrantes_grupo", docEnvio);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::IntegranteGrupo::desdeJson(arr[0].toObject());
        }
    }
    return integrante;
}

void RepositorioIntegrantes::desvincular(const QString& codigo_gruplac, const QString& codigo_rh) {
    QString filtros = QString("codigo_gruplac=eq.%1&codigo_rh=eq.%2").arg(codigo_gruplac, codigo_rh);
    m_cliente.eliminar("integrantes_grupo", filtros);
}

// ============================================================================
// RepositorioProductos
// ============================================================================

estructuras::ListaDoble<dominio::Producto> RepositorioProductos::listar(std::optional<bool> es_ejemplo) {
    estructuras::ListaDoble<dominio::Producto> lista;
    QJsonArray filas;
    if (es_ejemplo.has_value()) {
        QString params = QString("select=*&es_ejemplo=eq.%1").arg(*es_ejemplo ? "true" : "false");
        QJsonDocument doc = m_cliente.get("productos", params);
        if (doc.isArray()) {
            filas = doc.array();
        }
    } else {
        filas = m_cliente.getPaginado("productos");
    }

    for (const auto& val : filas) {
        if (val.isObject()) {
            lista.insertar_final(dominio::Producto::desdeJson(val.toObject()));
        }
    }
    return lista;
}

std::optional<dominio::Producto> RepositorioProductos::obtener_por_codigo(const QString& codigo_identificador) {
    QString params = QString("codigo_identificador=eq.%1&select=*").arg(codigo_identificador);
    QJsonDocument doc = m_cliente.get("productos", params);
    if (doc.isArray()) {
        QJsonArray arr = doc.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Producto::desdeJson(arr[0].toObject());
        }
    }
    return std::nullopt;
}

qint64 RepositorioProductos::crear_con_rpc(
    const dominio::Producto& producto,
    std::optional<qint64> grupo_id,
    const std::vector<qint64>& investigadores_ids,
    qint64 revision_esperada) {

    QJsonObject params;
    params["p_codigo_identificador"] = producto.codigo_identificador;
    params["p_titulo"] = producto.titulo;
    params["p_tipo_mayor"] = producto.tipo_mayor;
    if (!producto.subtipo.isEmpty()) params["p_subtipo"] = producto.subtipo;
    params["p_ano"] = producto.ano;
    if (producto.mes.has_value()) params["p_mes"] = *producto.mes;
    if (!producto.pais.isEmpty()) params["p_pais"] = producto.pais;
    params["p_estado_validacion"] = producto.estado_validacion;
    params["p_detalles"] = producto.detalles;
    params["p_es_ejemplo"] = producto.es_ejemplo;

    if (grupo_id.has_value()) {
        params["p_grupo_id"] = *grupo_id;
    } else {
        params["p_grupo_id"] = QJsonValue(QJsonValue::Null);
    }

    QJsonArray arrInv;
    for (qint64 iid : investigadores_ids) {
        arrInv.append(iid);
    }
    params["p_investigadores_ids"] = arrInv;
    params["p_revision_esperada"] = revision_esperada;

    QJsonDocument res = m_cliente.rpc("transaccion_crear_producto", params);
    if (res.isObject()) {
        QJsonObject obj = res.object();
        if (obj.contains("producto_id")) {
            return obj["producto_id"].toVariant().toLongLong();
        }
    }
    return 0;
}

dominio::Producto RepositorioProductos::crear_directo(const dominio::Producto& producto) {
    QJsonObject obj = producto.aJson(false);
    QJsonDocument docEnvio(obj);
    QJsonDocument res = m_cliente.post("productos", docEnvio);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Producto::desdeJson(arr[0].toObject());
        }
    }
    return producto;
}

void RepositorioProductos::asociar_grupo(qint64 producto_id, qint64 grupo_id, bool es_ejemplo) {
    QJsonObject obj;
    obj["producto_id"] = producto_id;
    obj["grupo_id"] = grupo_id;
    obj["activo"] = true;
    obj["es_ejemplo"] = es_ejemplo;
    m_cliente.post("producto_grupos", QJsonDocument(obj));
}

void RepositorioProductos::asociar_autor(qint64 producto_id, qint64 investigador_id, int orden, bool es_ejemplo) {
    QJsonObject obj;
    obj["producto_id"] = producto_id;
    obj["investigador_id"] = investigador_id;
    obj["orden_autoria"] = orden;
    obj["activo"] = true;
    obj["es_ejemplo"] = es_ejemplo;
    m_cliente.post("producto_autores", QJsonDocument(obj));
}

QJsonArray RepositorioProductos::listar_relaciones_grupos() {
    return m_cliente.getPaginado("producto_grupos");
}

QJsonArray RepositorioProductos::listar_relaciones_autores() {
    return m_cliente.getPaginado("producto_autores");
}

void RepositorioProductos::desactivar(qint64 id_producto, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "producto";
    params["p_id"] = id_producto;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_desactivar_nodo", params);
}

void RepositorioProductos::eliminar_cascada(qint64 id_producto, qint64 revision_esperada) {
    QJsonObject params;
    params["p_tipo"] = "producto";
    params["p_id"] = id_producto;
    params["p_revision_esperada"] = revision_esperada;
    m_cliente.rpc("transaccion_eliminar_cascada", params);
}

// ============================================================================
// RepositorioProyectos
// ============================================================================

estructuras::ListaDoble<dominio::Proyecto> RepositorioProyectos::listar(const QString& codigo_gruplac) {
    estructuras::ListaDoble<dominio::Proyecto> lista;
    QJsonArray filas;
    if (!codigo_gruplac.isEmpty()) {
        QString params = QString("select=*&codigo_gruplac=eq.%1").arg(codigo_gruplac);
        QJsonDocument doc = m_cliente.get("proyectos", params);
        if (doc.isArray()) {
            filas = doc.array();
        }
    } else {
        filas = m_cliente.getPaginado("proyectos");
    }

    for (const auto& val : filas) {
        if (val.isObject()) {
            lista.insertar_final(dominio::Proyecto::desdeJson(val.toObject()));
        }
    }
    return lista;
}

dominio::Proyecto RepositorioProyectos::crear(const dominio::Proyecto& proyecto) {
    QJsonObject obj = proyecto.aJson(false);
    QJsonDocument docEnvio(obj);
    QJsonDocument res = m_cliente.post("proyectos", docEnvio);
    if (res.isArray()) {
        QJsonArray arr = res.array();
        if (!arr.isEmpty() && arr[0].isObject()) {
            return dominio::Proyecto::desdeJson(arr[0].toObject());
        }
    }
    return proyecto;
}

} // namespace pea::datos
