#pragma once

#include <memory>
#include <optional>
#include <vector>
#include <QByteArray>
#include <QJsonObject>
#include <QString>

#include "pea/datos/repositorios.hpp"
#include "pea/datos/revision.hpp"
#include "pea/datos/sesion.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/integrante.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/plan.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/dominio/proyecto.hpp"
#include "pea/estructuras/cola.hpp"
#include "pea/estructuras/lista_doble.hpp"
#include "pea/estructuras/multilista.hpp"
#include "pea/estructuras/pila.hpp"

namespace pea {
class ClienteHTTPSupabase;
}

namespace pea::servicios {

class CatalogoInvestigacion {
public:
    explicit CatalogoInvestigacion(ClienteHTTPSupabase* cliente = nullptr,
                                  std::shared_ptr<datos::Sesion> sesion = nullptr);

    ~CatalogoInvestigacion() = default;

    CatalogoInvestigacion(const CatalogoInvestigacion&) = delete;
    CatalogoInvestigacion& operator=(const CatalogoInvestigacion&) = delete;
    CatalogoInvestigacion(CatalogoInvestigacion&&) noexcept = default;
    CatalogoInvestigacion& operator=(CatalogoInvestigacion&&) noexcept = default;

    // Colecciones del dominio en estructuras propias hechas a mano
    estructuras::ListaDoble<std::shared_ptr<dominio::Grupo>> grupos;
    estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>> investigadores;
    estructuras::ListaDoble<dominio::IntegranteGrupo> integrantes;
    estructuras::Multilista multilista_productos;
    estructuras::ListaDoble<dominio::Proyecto> proyectos;

    // Historial e ingesta
    estructuras::Pila<estructuras::ComandoInverso> pila_deshacer;
    estructuras::Cola<estructuras::TareaIngesta> cola_importacion;

    // Sesión y control de concurrencia
    std::shared_ptr<datos::Sesion> sesion;
    datos::ControladorRevision controlador_revision;

    // Gestión de Grupos
    std::shared_ptr<dominio::Grupo> crear_grupo(std::shared_ptr<dominio::Grupo> grupo, bool persistir = true);
    [[nodiscard]] std::shared_ptr<dominio::Grupo> buscar_grupo(const QString& codigo_gruplac) const;
    std::shared_ptr<dominio::Grupo> actualizar_grupo(const QString& codigo_gruplac, const QJsonObject& datos, bool persistir = true);
    void desactivar_grupo(const QString& codigo_gruplac, bool persistir = true);
    void activar_grupo(const QString& codigo_gruplac, bool persistir = true);
    std::shared_ptr<dominio::Grupo> eliminar_grupo(const QString& codigo_gruplac, bool persistir = true);

    // Gestión de Investigadores
    std::shared_ptr<dominio::Investigador> crear_investigador(std::shared_ptr<dominio::Investigador> inv, bool persistir = true);
    [[nodiscard]] std::shared_ptr<dominio::Investigador> buscar_investigador(const QString& codigo_rh) const;
    std::shared_ptr<dominio::Investigador> actualizar_investigador(const QString& codigo_rh, const QJsonObject& datos, bool persistir = true);
    void desactivar_investigador(const QString& codigo_rh, bool persistir = true);
    void activar_investigador(const QString& codigo_rh, bool persistir = true);
    std::shared_ptr<dominio::Investigador> eliminar_investigador(const QString& codigo_rh, bool persistir = true);

    // Gestión de Integrantes (Membresías)
    dominio::IntegranteGrupo vincular_integrante(
        const QString& codigo_gruplac,
        const QString& codigo_rh,
        const QString& rol = "Investigador",
        bool persistir = true);
    void desvincular_integrante(const QString& codigo_gruplac, const QString& codigo_rh, bool persistir = true);

    // Gestión de Productos y Multilista
    std::shared_ptr<dominio::Producto> crear_producto(
        std::shared_ptr<dominio::Producto> producto,
        const QString& codigo_gruplac = QString(),
        const std::vector<QString>& codigos_rh_autores = {},
        bool persistir = true);
    [[nodiscard]] std::shared_ptr<dominio::Producto> buscar_producto(const QString& codigo_identificador) const;
    void desactivar_producto(const QString& codigo_identificador, bool persistir = true);
    void activar_producto(const QString& codigo_identificador, bool persistir = true);
    std::shared_ptr<dominio::Producto> eliminar_producto(const QString& codigo_identificador, bool persistir = true);

    // Mecanismo de Deshacer (Undo LIFO)
    std::optional<estructuras::ComandoInverso> deshacer(bool persistir = true);

    // Recarga y sincronización
    void recargar_todo();
    [[nodiscard]] bool verificar_revision();

    // Resumen institucional y paridad JSON
    [[nodiscard]] QJsonObject resumen_dict() const;
    [[nodiscard]] QByteArray resumen_json() const;

private:
    ClienteHTTPSupabase* m_cliente;
    std::unique_ptr<datos::RepositorioGrupos> m_repo_grupos;
    std::unique_ptr<datos::RepositorioInvestigadores> m_repo_investigadores;
    std::unique_ptr<datos::RepositorioIntegrantes> m_repo_integrantes;
    std::unique_ptr<datos::RepositorioProductos> m_repo_productos;
    std::unique_ptr<datos::RepositorioProyectos> m_repo_proyectos;

    void verificar_autenticacion_si_aplica();
};

} // namespace pea::servicios
