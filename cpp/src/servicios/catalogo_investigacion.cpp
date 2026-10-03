#include "pea/servicios/catalogo_investigacion.hpp"
#include "pea/cliente_http.hpp"
#include "pea/excepciones.hpp"
#include <QJsonDocument>
#include <QJsonObject>
#include <unordered_map>

namespace pea::servicios {

CatalogoInvestigacion::CatalogoInvestigacion(ClienteHTTPSupabase* cliente,
                                            std::shared_ptr<datos::Sesion> s)
    : sesion(s ? std::move(s) : std::make_shared<datos::Sesion>()),
      m_cliente(cliente) {
    if (m_cliente) {
        m_repo_grupos = std::make_unique<datos::RepositorioGrupos>(*m_cliente);
        m_repo_investigadores = std::make_unique<datos::RepositorioInvestigadores>(*m_cliente);
        m_repo_integrantes = std::make_unique<datos::RepositorioIntegrantes>(*m_cliente);
        m_repo_productos = std::make_unique<datos::RepositorioProductos>(*m_cliente);
        m_repo_proyectos = std::make_unique<datos::RepositorioProyectos>(*m_cliente);
    }
    estadisticas.setHipercubo(&hipercubo);
}

void CatalogoInvestigacion::sincronizarHipercubo() {
    hipercubo.poblarDesdeMultilista(multilista_productos);
}

void CatalogoInvestigacion::verificar_autenticacion_si_aplica() {
    if (m_cliente && sesion && sesion->esta_expirada()) {
        sesion->cerrar_sesion();
        throw ErrorAutenticacion("La sesión ha expirado.");
    }
}

// ============================================================================
// GESTIÓN DE GRUPOS
// ============================================================================

std::shared_ptr<dominio::Grupo> CatalogoInvestigacion::crear_grupo(
    std::shared_ptr<dominio::Grupo> grupo,
    bool persistir) {
    if (!grupo) return nullptr;
    verificar_autenticacion_si_aplica();

    // 1. Unicidad en memoria
    auto* existente = grupos.buscar([&grupo](const std::shared_ptr<dominio::Grupo>& g) {
        return g && g->codigo_gruplac == grupo->codigo_gruplac;
    });
    if (existente) {
        throw ErrorValidacion("Ya existe un grupo registrado con código " + grupo->codigo_gruplac.toStdString());
    }

    auto* nodo = grupos.insertar_final(grupo);

    // 2. Persistencia en Supabase
    if (persistir && m_cliente && m_repo_grupos) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            dominio::Grupo creado = m_repo_grupos->crear(*grupo);
            if (creado.id.has_value()) {
                grupo->id = creado.id;
            }
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            grupos.eliminar_nodo(nodo);
            throw;
        }
    }

    // 3. Registrar en Pila de Deshacer
    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "crear",
            "grupo",
            grupo->codigo_gruplac,
            QJsonObject(),
            "Crear grupo " + grupo->nombre
        )
    );
    return grupo;
}

std::shared_ptr<dominio::Grupo> CatalogoInvestigacion::buscar_grupo(const QString& codigo_gruplac) const {
    const auto* encontrado = grupos.buscar([&codigo_gruplac](const std::shared_ptr<dominio::Grupo>& g) {
        return g && g->codigo_gruplac == codigo_gruplac;
    });
    return encontrado ? encontrado->dato : nullptr;
}


std::shared_ptr<dominio::Grupo> CatalogoInvestigacion::actualizar_grupo(
    const QString& codigo_gruplac,
    const QJsonObject& datos,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    auto grupo = buscar_grupo(codigo_gruplac);
    if (!grupo) {
        throw RecursoNoEncontrado("Grupo con código " + codigo_gruplac.toStdString() + " no encontrado");
    }

    QJsonObject valores_anteriores;
    if (datos.contains("nombre")) {
        valores_anteriores["nombre"] = grupo->nombre;
        grupo->nombre = datos["nombre"].toString();
    }
    if (datos.contains("categoria")) {
        valores_anteriores["categoria"] = grupo->categoria;
        grupo->categoria = datos["categoria"].toString();
    }
    if (datos.contains("lider")) {
        valores_anteriores["lider"] = grupo->lider;
        grupo->lider = datos["lider"].toString();
    }
    if (datos.contains("institucion_principal")) {
        valores_anteriores["institucion_principal"] = grupo->institucion_principal;
        grupo->institucion_principal = datos["institucion_principal"].toString();
    }

    if (persistir && m_cliente && m_repo_grupos) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_grupos->actualizar(codigo_gruplac, datos);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            // Compensación
            if (valores_anteriores.contains("nombre")) grupo->nombre = valores_anteriores["nombre"].toString();
            if (valores_anteriores.contains("categoria")) grupo->categoria = valores_anteriores["categoria"].toString();
            if (valores_anteriores.contains("lider")) grupo->lider = valores_anteriores["lider"].toString();
            if (valores_anteriores.contains("institucion_principal")) grupo->institucion_principal = valores_anteriores["institucion_principal"].toString();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "editar",
            "grupo",
            codigo_gruplac,
            valores_anteriores,
            "Editar grupo " + codigo_gruplac
        )
    );
    return grupo;
}

void CatalogoInvestigacion::desactivar_grupo(const QString& codigo_gruplac, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto grupo = buscar_grupo(codigo_gruplac);
    if (!grupo) {
        throw RecursoNoEncontrado("Grupo " + codigo_gruplac.toStdString() + " no encontrado");
    }

    grupo->desactivar();

    if (persistir && m_cliente && m_repo_grupos && grupo->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_grupos->desactivar(*grupo->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            grupo->activar();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "desactivar",
            "grupo",
            codigo_gruplac,
            QJsonObject(),
            "Desactivar grupo " + codigo_gruplac
        )
    );
}

void CatalogoInvestigacion::activar_grupo(const QString& codigo_gruplac, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto grupo = buscar_grupo(codigo_gruplac);
    if (!grupo) {
        throw RecursoNoEncontrado("Grupo " + codigo_gruplac.toStdString() + " no encontrado");
    }

    grupo->activar();

    if (persistir && m_cliente && m_repo_grupos) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            QJsonObject datos;
            datos["activo"] = true;
            m_repo_grupos->actualizar(codigo_gruplac, datos);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            grupo->desactivar();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "activar",
            "grupo",
            codigo_gruplac,
            QJsonObject(),
            "Activar grupo " + codigo_gruplac
        )
    );
}

std::shared_ptr<dominio::Grupo> CatalogoInvestigacion::eliminar_grupo(const QString& codigo_gruplac, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto grupo = buscar_grupo(codigo_gruplac);
    if (!grupo) {
        throw RecursoNoEncontrado("Grupo " + codigo_gruplac.toStdString() + " no encontrado");
    }

    // 1. Desenlazar productos del grupo en la Multilista
    multilista_productos.desvincular_grupo_de_todos(codigo_gruplac);

    // 2. Desvincular integrantes asociados en memoria
    while (integrantes.eliminar_por_criterio([&codigo_gruplac](const dominio::IntegranteGrupo& m) {
        return m.codigo_gruplac == codigo_gruplac;
    })) {}


    // 3. Remover de la lista de grupos
    grupos.eliminar_por_criterio([&codigo_gruplac](const std::shared_ptr<dominio::Grupo>& g) {
        return g && g->codigo_gruplac == codigo_gruplac;
    });

    // 4. Persistir eliminación remota
    if (persistir && m_cliente && m_repo_grupos && grupo->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_grupos->eliminar(*grupo->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            grupos.insertar_final(grupo);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "eliminar",
            "grupo",
            codigo_gruplac,
            grupo->aJson(),
            "Eliminar grupo " + codigo_gruplac
        )
    );
    sincronizarHipercubo();
    return grupo;
}

// ============================================================================
// GESTIÓN DE INVESTIGADORES
// ============================================================================

std::shared_ptr<dominio::Investigador> CatalogoInvestigacion::crear_investigador(
    std::shared_ptr<dominio::Investigador> inv,
    bool persistir) {
    if (!inv) return nullptr;
    verificar_autenticacion_si_aplica();

    auto* existente = investigadores.buscar([&inv](const std::shared_ptr<dominio::Investigador>& actual) {
        return actual && actual->codigo_rh == inv->codigo_rh;
    });
    if (existente) {
        throw ErrorValidacion("Ya existe un investigador con código " + inv->codigo_rh.toStdString());
    }

    auto* nodo = investigadores.insertar_final(inv);

    if (persistir && m_cliente && m_repo_investigadores) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            dominio::Investigador creado = m_repo_investigadores->crear(*inv);
            if (creado.id.has_value()) {
                inv->id = creado.id;
            }
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            investigadores.eliminar_nodo(nodo);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "crear",
            "investigador",
            inv->codigo_rh,
            QJsonObject(),
            "Crear investigador " + inv->nombre_completo
        )
    );
    return inv;
}

std::shared_ptr<dominio::Investigador> CatalogoInvestigacion::buscar_investigador(const QString& codigo_rh) const {
    const auto* encontrado = investigadores.buscar([&codigo_rh](const std::shared_ptr<dominio::Investigador>& i) {
        return i && i->codigo_rh == codigo_rh;
    });
    return encontrado ? encontrado->dato : nullptr;
}


std::shared_ptr<dominio::Investigador> CatalogoInvestigacion::actualizar_investigador(
    const QString& codigo_rh,
    const QJsonObject& datos,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    auto inv = buscar_investigador(codigo_rh);
    if (!inv) {
        throw RecursoNoEncontrado("Investigador con código " + codigo_rh.toStdString() + " no encontrado");
    }

    QJsonObject valores_anteriores;
    if (datos.contains("nombre_completo")) {
        valores_anteriores["nombre_completo"] = inv->nombre_completo;
        inv->nombre_completo = datos["nombre_completo"].toString();
    }
    if (datos.contains("categoria")) {
        valores_anteriores["categoria"] = inv->categoria;
        inv->categoria = datos["categoria"].toString();
    }
    if (datos.contains("formacion_academica")) {
        valores_anteriores["formacion_academica"] = inv->formacion_academica;
        inv->formacion_academica = datos["formacion_academica"].toString();
    }
    if (datos.contains("nacionalidad")) {
        valores_anteriores["nacionalidad"] = inv->nacionalidad;
        inv->nacionalidad = datos["nacionalidad"].toString();
    }

    if (persistir && m_cliente && m_repo_investigadores) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_investigadores->actualizar(codigo_rh, datos);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            if (valores_anteriores.contains("nombre_completo")) inv->nombre_completo = valores_anteriores["nombre_completo"].toString();
            if (valores_anteriores.contains("categoria")) inv->categoria = valores_anteriores["categoria"].toString();
            if (valores_anteriores.contains("formacion_academica")) inv->formacion_academica = valores_anteriores["formacion_academica"].toString();
            if (valores_anteriores.contains("nacionalidad")) inv->nacionalidad = valores_anteriores["nacionalidad"].toString();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "editar",
            "investigador",
            codigo_rh,
            valores_anteriores,
            "Editar investigador " + codigo_rh
        )
    );
    return inv;
}

void CatalogoInvestigacion::desactivar_investigador(const QString& codigo_rh, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto inv = buscar_investigador(codigo_rh);
    if (!inv) {
        throw RecursoNoEncontrado("Investigador " + codigo_rh.toStdString() + " no encontrado");
    }

    inv->desactivar();

    if (persistir && m_cliente && m_repo_investigadores && inv->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_investigadores->desactivar(*inv->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            inv->activar();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "desactivar",
            "investigador",
            codigo_rh,
            QJsonObject(),
            "Desactivar investigador " + codigo_rh
        )
    );
}

void CatalogoInvestigacion::activar_investigador(const QString& codigo_rh, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto inv = buscar_investigador(codigo_rh);
    if (!inv) {
        throw RecursoNoEncontrado("Investigador " + codigo_rh.toStdString() + " no encontrado");
    }

    inv->activar();

    if (persistir && m_cliente && m_repo_investigadores) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            QJsonObject datos;
            datos["activo"] = true;
            m_repo_investigadores->actualizar(codigo_rh, datos);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            inv->desactivar();
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "activar",
            "investigador",
            codigo_rh,
            QJsonObject(),
            "Activar investigador " + codigo_rh
        )
    );
}

std::shared_ptr<dominio::Investigador> CatalogoInvestigacion::eliminar_investigador(
    const QString& codigo_rh,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    auto inv = buscar_investigador(codigo_rh);
    if (!inv) {
        throw RecursoNoEncontrado("Investigador " + codigo_rh.toStdString() + " no encontrado");
    }

    // 1. Remover de listas de coautorías en la Multilista
    multilista_productos.desvincular_investigador_de_todos(codigo_rh);

    // 2. Desvincular de integrantes en memoria
    while (integrantes.eliminar_por_criterio([&codigo_rh](const dominio::IntegranteGrupo& m) {
        return m.codigo_rh == codigo_rh;
    })) {}


    // 3. Remover de la lista de investigadores
    investigadores.eliminar_por_criterio([&codigo_rh](const std::shared_ptr<dominio::Investigador>& i) {
        return i && i->codigo_rh == codigo_rh;
    });

    if (persistir && m_cliente && m_repo_investigadores && inv->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_investigadores->eliminar(*inv->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            investigadores.insertar_final(inv);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "eliminar",
            "investigador",
            codigo_rh,
            inv->aJson(),
            "Eliminar investigador " + codigo_rh
        )
    );
    sincronizarHipercubo();
    return inv;
}

// ============================================================================
// GESTIÓN DE INTEGRANTES
// ============================================================================

dominio::IntegranteGrupo CatalogoInvestigacion::vincular_integrante(
    const QString& codigo_gruplac,
    const QString& codigo_rh,
    const QString& rol,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    auto grupo = buscar_grupo(codigo_gruplac);
    if (!grupo) {
        throw RecursoNoEncontrado("Grupo " + codigo_gruplac.toStdString() + " no encontrado para vinculación");
    }
    auto inv = buscar_investigador(codigo_rh);
    if (!inv) {
        throw RecursoNoEncontrado("Investigador " + codigo_rh.toStdString() + " no encontrado para vinculación");
    }

    dominio::IntegranteGrupo integrante;
    integrante.grupo_id = grupo->id;
    integrante.codigo_gruplac = codigo_gruplac;
    integrante.investigador_id = inv->id;
    integrante.codigo_rh = codigo_rh;
    integrante.rol = rol;

    auto* nodo = integrantes.insertar_final(integrante);

    if (persistir && m_cliente && m_repo_integrantes) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            dominio::IntegranteGrupo creado = m_repo_integrantes->vincular(integrante);
            if (creado.id.has_value()) {
                integrante.id = creado.id;
                nodo->dato.id = creado.id;
            }
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            integrantes.eliminar_nodo(nodo);
            throw;
        }
    }

    return integrante;
}

void CatalogoInvestigacion::desvincular_integrante(
    const QString& codigo_gruplac,
    const QString& codigo_rh,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    const auto* nodo = integrantes.buscar([&](const dominio::IntegranteGrupo& m) {
        return m.codigo_gruplac == codigo_gruplac && m.codigo_rh == codigo_rh;
    });
    if (!nodo) {
        throw RecursoNoEncontrado("Membresía " + codigo_gruplac.toStdString() + " - " + codigo_rh.toStdString() + " no encontrada");
    }
    dominio::IntegranteGrupo respaldo = nodo->dato;
    integrantes.eliminar_por_criterio([&](const dominio::IntegranteGrupo& m) {
        return m.codigo_gruplac == codigo_gruplac && m.codigo_rh == codigo_rh;
    });

    if (persistir && m_cliente && m_repo_integrantes) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_integrantes->desvincular(codigo_gruplac, codigo_rh);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            integrantes.insertar_final(respaldo);
            throw;
        }
    }

}

// ============================================================================
// GESTIÓN DE PRODUCTOS Y MULTILISTA
// ============================================================================

std::shared_ptr<dominio::Producto> CatalogoInvestigacion::crear_producto(
    std::shared_ptr<dominio::Producto> producto,
    const QString& codigo_gruplac,
    const std::vector<QString>& codigos_rh_autores,
    bool persistir) {
    if (!producto) return nullptr;
    verificar_autenticacion_si_aplica();

    auto existente = multilista_productos.buscar_producto(producto->codigo_identificador);
    if (existente) {
        throw ErrorValidacion("Ya existe un producto con código " + producto->codigo_identificador.toStdString());
    }

    std::shared_ptr<dominio::Grupo> grupo = !codigo_gruplac.isEmpty() ? buscar_grupo(codigo_gruplac) : nullptr;
    estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>> autores;
    std::vector<qint64> inv_ids;
    for (const auto& crh : codigos_rh_autores) {
        auto inv = buscar_investigador(crh);
        if (inv) {
            autores.insertar_final(inv);
            if (inv->id.has_value()) {
                inv_ids.push_back(*inv->id);
            }
        }
    }

    // 1. Insertar en Multilista
    multilista_productos.agregar_producto(producto, grupo, autores);

    // 2. Persistir en Supabase
    if (persistir && m_cliente && m_repo_productos) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            std::optional<qint64> gid = grupo ? grupo->id : std::nullopt;
            qint64 prod_id = m_repo_productos->crear_con_rpc(
                *producto,
                gid,
                inv_ids,
                controlador_revision.revision_local()
            );
            if (prod_id > 0) {
                producto->id = prod_id;
            }
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            multilista_productos.eliminar_producto(producto->codigo_identificador);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "crear",
            "producto",
            producto->codigo_identificador,
            QJsonObject(),
            "Crear producto " + producto->titulo
        )
    );
    sincronizarHipercubo();
    return producto;
}

std::shared_ptr<dominio::Producto> CatalogoInvestigacion::buscar_producto(const QString& codigo_identificador) const {
    return multilista_productos.buscar_producto(codigo_identificador);
}

void CatalogoInvestigacion::desactivar_producto(const QString& codigo_identificador, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto prod = buscar_producto(codigo_identificador);
    if (!prod) {
        throw RecursoNoEncontrado("Producto " + codigo_identificador.toStdString() + " no encontrado");
    }

    multilista_productos.desactivar_producto(codigo_identificador);

    if (persistir && m_cliente && m_repo_productos && prod->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_productos->desactivar(*prod->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            multilista_productos.activar_producto(codigo_identificador);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "desactivar",
            "producto",
            codigo_identificador,
            QJsonObject(),
            "Desactivar producto " + codigo_identificador
        )
    );
    sincronizarHipercubo();
}

void CatalogoInvestigacion::activar_producto(const QString& codigo_identificador, bool persistir) {
    verificar_autenticacion_si_aplica();
    auto prod = buscar_producto(codigo_identificador);
    if (!prod) {
        throw RecursoNoEncontrado("Producto " + codigo_identificador.toStdString() + " no encontrado");
    }

    multilista_productos.activar_producto(codigo_identificador);

    if (persistir && m_cliente && m_repo_productos) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            QJsonObject datos;
            datos["activo"] = true;
            QString filtros = QString("codigo_identificador=eq.%1").arg(codigo_identificador);
            m_cliente->patch("productos", QJsonDocument(datos), filtros);
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            multilista_productos.desactivar_producto(codigo_identificador);
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "activar",
            "producto",
            codigo_identificador,
            QJsonObject(),
            "Activar producto " + codigo_identificador
        )
    );
    sincronizarHipercubo();
}

std::shared_ptr<dominio::Producto> CatalogoInvestigacion::eliminar_producto(
    const QString& codigo_identificador,
    bool persistir) {
    verificar_autenticacion_si_aplica();
    auto prod = buscar_producto(codigo_identificador);
    if (!prod) {
        throw RecursoNoEncontrado("Producto " + codigo_identificador.toStdString() + " no encontrado");
    }

    auto* nodo = multilista_productos.buscar_nodo(codigo_identificador);
    std::shared_ptr<dominio::Grupo> grupo_asoc = nodo ? nodo->grupo : nullptr;
    estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>> autores_asoc;
    if (nodo) {
        for (const auto& a : nodo->autores) {
            autores_asoc.insertar_final(a);
        }
    }

    auto prod_eliminado = multilista_productos.eliminar_producto(codigo_identificador);

    if (persistir && m_cliente && m_repo_productos && prod->id.has_value()) {
        try {
            controlador_revision.verificar_consistencia(*m_cliente);
            m_repo_productos->eliminar_cascada(*prod->id, controlador_revision.revision_local());
            controlador_revision.actualizar_local(controlador_revision.revision_local() + 1);
        } catch (...) {
            if (prod_eliminado) {
                multilista_productos.agregar_producto(prod_eliminado, grupo_asoc, autores_asoc);
            }
            throw;
        }
    }

    pila_deshacer.apilar(
        estructuras::ComandoInverso(
            "eliminar",
            "producto",
            codigo_identificador,
            prod->aJson(),
            "Eliminar producto " + codigo_identificador
        )
    );
    sincronizarHipercubo();
    return prod;
}

// ============================================================================
// MECANISMO DE DESHACER (UNDO LIFO)
// ============================================================================

std::optional<estructuras::ComandoInverso> CatalogoInvestigacion::deshacer(bool persistir) {
    if (pila_deshacer.esta_vacia()) {
        return std::nullopt;
    }

    estructuras::ComandoInverso cmd = pila_deshacer.desapilar();

    if (cmd.tipo_operacion == "crear") {
        if (cmd.tipo_entidad == "grupo") {
            eliminar_grupo(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "investigador") {
            eliminar_investigador(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "producto") {
            eliminar_producto(cmd.identificador, persistir);
        }
    } else if (cmd.tipo_operacion == "desactivar") {
        if (cmd.tipo_entidad == "grupo") {
            activar_grupo(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "investigador") {
            activar_investigador(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "producto") {
            activar_producto(cmd.identificador, persistir);
        }
    } else if (cmd.tipo_operacion == "activar") {
        if (cmd.tipo_entidad == "grupo") {
            desactivar_grupo(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "investigador") {
            desactivar_investigador(cmd.identificador, persistir);
        } else if (cmd.tipo_entidad == "producto") {
            desactivar_producto(cmd.identificador, persistir);
        }
    } else if (cmd.tipo_operacion == "editar") {
        if (cmd.tipo_entidad == "grupo") {
            actualizar_grupo(cmd.identificador, cmd.datos_reversion, persistir);
        } else if (cmd.tipo_entidad == "investigador") {
            actualizar_investigador(cmd.identificador, cmd.datos_reversion, persistir);
        }
    }

    // Remover el comando de reversión generado por la propia acción inversa
    if (!pila_deshacer.esta_vacia()) {
        pila_deshacer.desapilar();
    }

    sincronizarHipercubo();
    return cmd;
}

// ============================================================================
// RECARGA TOTAL Y DETECCIÓN DE CONFLICTOS
// ============================================================================

void CatalogoInvestigacion::recargar_todo() {
    if (!m_cliente) return;
    verificar_autenticacion_si_aplica();

    // 1. Limpiar estructuras en memoria
    grupos.limpiar();
    investigadores.limpiar();
    integrantes.limpiar();
    multilista_productos.limpiar();
    proyectos.limpiar();

    // 2. Cargar grupos
    if (m_repo_grupos) {
        auto grupos_remotos = m_repo_grupos->listar();
        for (const auto& g : grupos_remotos) {
            grupos.insertar_final(std::make_shared<dominio::Grupo>(g));
        }
    }

    // 3. Cargar investigadores
    if (m_repo_investigadores) {
        auto invs_remotos = m_repo_investigadores->listar();
        for (const auto& inv : invs_remotos) {
            investigadores.insertar_final(std::make_shared<dominio::Investigador>(inv));
        }
    }

    // 4. Cargar integrantes
    if (m_repo_integrantes) {
        auto ints_remotos = m_repo_integrantes->listar();
        for (const auto& m : ints_remotos) {
            integrantes.insertar_final(m);
        }
    }

    // 5. Cargar productos y relaciones
    if (m_repo_productos) {
        auto prods_remotos = m_repo_productos->listar();
        QJsonArray rels_grupos = m_repo_productos->listar_relaciones_grupos();
        QJsonArray rels_autores = m_repo_productos->listar_relaciones_autores();

        std::unordered_map<qint64, std::shared_ptr<dominio::Producto>> prod_por_id;
        for (const auto& p : prods_remotos) {
            if (p.id.has_value()) {
                prod_por_id[*p.id] = std::make_shared<dominio::Producto>(p);
            }
        }

        std::unordered_map<qint64, std::shared_ptr<dominio::Grupo>> grupo_por_id;
        for (const auto& g : grupos) {
            if (g && g->id.has_value()) {
                grupo_por_id[*g->id] = g;
            }
        }

        std::unordered_map<qint64, std::shared_ptr<dominio::Investigador>> inv_por_id;
        for (const auto& inv : investigadores) {
            if (inv && inv->id.has_value()) {
                inv_por_id[*inv->id] = inv;
            }
        }

        std::unordered_map<qint64, std::shared_ptr<dominio::Grupo>> grupo_de_prod;
        for (const auto& val : rels_grupos) {
            if (val.isObject()) {
                QJsonObject rg = val.toObject();
                qint64 pid = rg["producto_id"].toVariant().toLongLong();
                qint64 gid = rg["grupo_id"].toVariant().toLongLong();
                if (prod_por_id.count(pid) && grupo_por_id.count(gid)) {
                    grupo_de_prod[pid] = grupo_por_id[gid];
                }
            }
        }

        std::unordered_map<qint64, estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>>> autores_de_prod;
        for (const auto& val : rels_autores) {
            if (val.isObject()) {
                QJsonObject ra = val.toObject();
                qint64 pid = ra["producto_id"].toVariant().toLongLong();
                qint64 iid = ra["investigador_id"].toVariant().toLongLong();
                if (prod_por_id.count(pid) && inv_por_id.count(iid)) {
                    autores_de_prod[pid].insertar_final(inv_por_id[iid]);
                }
            }
        }

        for (const auto& p : prods_remotos) {
            if (p.id.has_value() && prod_por_id.count(*p.id)) {
                auto prod_ptr = prod_por_id[*p.id];
                std::shared_ptr<dominio::Grupo> grp = grupo_de_prod.count(*p.id) ? grupo_de_prod[*p.id] : nullptr;
                estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>> auts =
                    autores_de_prod.count(*p.id) ? autores_de_prod[*p.id] : estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>>();
                multilista_productos.agregar_producto(prod_ptr, grp, auts);
            }
        }
    }

    sincronizarHipercubo();

    // 6. Sincronizar número de revisión
    controlador_revision.sincronizar(*m_cliente);
}

bool CatalogoInvestigacion::verificar_revision() {
    if (!m_cliente) return false;
    qint64 remota = controlador_revision.consultar_remota(*m_cliente);
    return remota != controlador_revision.revision_local();
}

// ============================================================================
// RESUMEN INSTITUCIONAL Y PARIDAD JSON
// ============================================================================

QJsonObject CatalogoInvestigacion::resumen_dict() const {
    qint64 total_grupos = static_cast<qint64>(grupos.tamano());
    qint64 grupos_activos = 0;
    for (const auto& g : grupos) {
        if (g && g->activo) grupos_activos++;
    }

    qint64 total_invs = static_cast<qint64>(investigadores.tamano());
    qint64 invs_activos = 0;
    for (const auto& i : investigadores) {
        if (i && i->activo) invs_activos++;
    }

    qint64 total_prods = static_cast<qint64>(multilista_productos.tamano());
    qint64 prods_activos = 0;
    auto* actual = multilista_productos.cabeza();
    while (actual) {
        if (actual->activo()) prods_activos++;
        actual = actual->siguiente_global;
    }

    qint64 pila_tam = static_cast<qint64>(pila_deshacer.tamano());

    QJsonObject obj;
    obj["grupos_activos"] = grupos_activos;
    obj["grupos_totales"] = total_grupos;
    obj["investigadores_activos"] = invs_activos;
    obj["investigadores_totales"] = total_invs;
    obj["pila_deshacer_tamano"] = pila_tam;
    obj["productos_activos"] = prods_activos;
    obj["productos_totales"] = total_prods;
    return obj;
}

QByteArray CatalogoInvestigacion::resumen_json() const {
    QJsonObject obj = resumen_dict();
    return QJsonDocument(obj).toJson(QJsonDocument::Compact);
}

} // namespace pea::servicios
