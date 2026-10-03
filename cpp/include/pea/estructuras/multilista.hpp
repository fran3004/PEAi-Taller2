#pragma once

#include <cstddef>
#include <memory>
#include <QString>
#include "pea/estructuras/lista_doble.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/producto.hpp"

namespace pea::estructuras {

class NodoProductoMultilista {
public:
    std::shared_ptr<dominio::Producto> producto;
    std::shared_ptr<dominio::Grupo> grupo;
    ListaDoble<std::shared_ptr<dominio::Investigador>> autores;

    // Enlaces en la secuencia general de productos
    NodoProductoMultilista* anterior_global{nullptr};
    NodoProductoMultilista* siguiente_global{nullptr};

    // Enlaces en la secuencia de productos del mismo grupo
    NodoProductoMultilista* anterior_en_grupo{nullptr};
    NodoProductoMultilista* siguiente_en_grupo{nullptr};

    explicit NodoProductoMultilista(std::shared_ptr<dominio::Producto> prod,
                                    std::shared_ptr<dominio::Grupo> grp = nullptr)
        : producto(std::move(prod)),
          grupo(std::move(grp)) {}

    NodoProductoMultilista(const NodoProductoMultilista&) = delete;
    NodoProductoMultilista& operator=(const NodoProductoMultilista&) = delete;
    NodoProductoMultilista(NodoProductoMultilista&&) = delete;
    NodoProductoMultilista& operator=(NodoProductoMultilista&&) = delete;
    ~NodoProductoMultilista() = default;

    [[nodiscard]] QString codigo_identificador() const {
        return producto ? producto->codigo_identificador : QString();
    }

    [[nodiscard]] bool activo() const {
        return producto ? producto->activo : false;
    }

    void agregar_autor(const std::shared_ptr<dominio::Investigador>& inv) {
        if (!inv) return;
        const auto* existente = autores.buscar([&inv](const std::shared_ptr<dominio::Investigador>& actual) {
            return actual && actual->codigo_rh == inv->codigo_rh;
        });
        if (!existente) {
            autores.insertar_final(inv);
        }
    }

    bool remover_autor(const QString& codigo_rh) {
        return autores.eliminar_por_criterio([&codigo_rh](const std::shared_ptr<dominio::Investigador>& actual) {
            return actual && actual->codigo_rh == codigo_rh;
        });
    }

};

class Multilista {
public:
    Multilista() = default;

    ~Multilista() {
        limpiar();
    }

    Multilista(const Multilista&) = delete;
    Multilista& operator=(const Multilista&) = delete;

    Multilista(Multilista&& otra) noexcept
        : m_cabeza_global(otra.m_cabeza_global),
          m_cola_global(otra.m_cola_global),
          m_tamano(otra.m_tamano) {
        otra.m_cabeza_global = nullptr;
        otra.m_cola_global = nullptr;
        otra.m_tamano = 0;
    }

    Multilista& operator=(Multilista&& otra) noexcept {
        if (this != &otra) {
            limpiar();
            m_cabeza_global = otra.m_cabeza_global;
            m_cola_global = otra.m_cola_global;
            m_tamano = otra.m_tamano;
            otra.m_cabeza_global = nullptr;
            otra.m_cola_global = nullptr;
            otra.m_tamano = 0;
        }
        return *this;
    }

    [[nodiscard]] std::size_t tamano() const noexcept { return m_tamano; }
    [[nodiscard]] bool esta_vacia() const noexcept { return m_tamano == 0; }
    [[nodiscard]] NodoProductoMultilista* cabeza() const noexcept { return m_cabeza_global; }
    [[nodiscard]] NodoProductoMultilista* cola() const noexcept { return m_cola_global; }

    NodoProductoMultilista* agregar_producto(
        std::shared_ptr<dominio::Producto> prod,
        std::shared_ptr<dominio::Grupo> grp = nullptr,
        const ListaDoble<std::shared_ptr<dominio::Investigador>>& auts = {}) {
        if (!prod) return nullptr;

        NodoProductoMultilista* existente = buscar_nodo(prod->codigo_identificador);
        if (existente) {
            if (grp) existente->grupo = grp;
            for (const auto& a : auts) {
                existente->agregar_autor(a);
            }
            return existente;
        }

        auto* nodo = new NodoProductoMultilista(prod, grp);
        for (const auto& a : auts) {
            nodo->agregar_autor(a);
        }

        if (!m_cola_global) {
            m_cabeza_global = nodo;
            m_cola_global = nodo;
        } else {
            m_cola_global->siguiente_global = nodo;
            nodo->anterior_global = m_cola_global;
            m_cola_global = nodo;
        }

        m_tamano++;

        if (grp) {
            enlazar_en_grupo(nodo, grp->codigo_gruplac);
        }

        return nodo;
    }

    [[nodiscard]] NodoProductoMultilista* buscar_nodo(const QString& codigo_identificador) const {
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual->codigo_identificador() == codigo_identificador) {
                return actual;
            }
            actual = actual->siguiente_global;
        }
        return nullptr;
    }

    [[nodiscard]] std::shared_ptr<dominio::Producto> buscar_producto(const QString& codigo_identificador) const {
        auto* nodo = buscar_nodo(codigo_identificador);
        return nodo ? nodo->producto : nullptr;
    }

    [[nodiscard]] ListaDoble<std::shared_ptr<dominio::Producto>> obtener_productos_grupo(const QString& codigo_gruplac) const {
        ListaDoble<std::shared_ptr<dominio::Producto>> resultado;
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual->grupo && actual->grupo->codigo_gruplac == codigo_gruplac && actual->producto) {
                resultado.insertar_final(actual->producto);
            }
            actual = actual->siguiente_global;
        }
        return resultado;
    }

    [[nodiscard]] ListaDoble<std::shared_ptr<dominio::Producto>> obtener_productos_investigador(const QString& codigo_rh) const {
        ListaDoble<std::shared_ptr<dominio::Producto>> resultado;
        auto* actual = m_cabeza_global;
        while (actual) {
            const auto* es_autor = actual->autores.buscar([&codigo_rh](const std::shared_ptr<dominio::Investigador>& inv) {
                return inv && inv->codigo_rh == codigo_rh;
            });
            if (es_autor && actual->producto) {
                resultado.insertar_final(actual->producto);
            }
            actual = actual->siguiente_global;
        }
        return resultado;
    }

    [[nodiscard]] ListaDoble<std::shared_ptr<dominio::Producto>> obtener_todos() const {
        ListaDoble<std::shared_ptr<dominio::Producto>> resultado;
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual->producto) {
                resultado.insertar_final(actual->producto);
            }
            actual = actual->siguiente_global;
        }
        return resultado;
    }

    std::shared_ptr<dominio::Producto> eliminar_producto(const QString& codigo_identificador) {
        auto* nodo = buscar_nodo(codigo_identificador);
        if (!nodo) return nullptr;

        // 1. Desenlazar de lista global
        if (nodo == m_cabeza_global) {
            m_cabeza_global = nodo->siguiente_global;
        }
        if (nodo->anterior_global) {
            nodo->anterior_global->siguiente_global = nodo->siguiente_global;
        }

        if (nodo == m_cola_global) {
            m_cola_global = nodo->anterior_global;
        }
        if (nodo->siguiente_global) {
            nodo->siguiente_global->anterior_global = nodo->anterior_global;
        }

        // 2. Desenlazar de lista del grupo
        if (nodo->anterior_en_grupo) {
            nodo->anterior_en_grupo->siguiente_en_grupo = nodo->siguiente_en_grupo;
        }
        if (nodo->siguiente_en_grupo) {
            nodo->siguiente_en_grupo->anterior_en_grupo = nodo->anterior_en_grupo;
        }

        std::shared_ptr<dominio::Producto> prod = nodo->producto;
        delete nodo;
        m_tamano--;
        return prod;
    }

    bool desactivar_producto(const QString& codigo_identificador) {
        auto* nodo = buscar_nodo(codigo_identificador);
        if (nodo && nodo->producto) {
            nodo->producto->desactivar();
            return true;
        }
        return false;
    }

    bool activar_producto(const QString& codigo_identificador) {
        auto* nodo = buscar_nodo(codigo_identificador);
        if (nodo && nodo->producto) {
            nodo->producto->activar();
            return true;
        }
        return false;
    }

    int desvincular_investigador_de_todos(const QString& codigo_rh) {
        int contador = 0;
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual->remover_autor(codigo_rh)) {
                contador++;
            }
            actual = actual->siguiente_global;
        }
        return contador;
    }

    int desvincular_grupo_de_todos(const QString& codigo_gruplac) {
        int contador = 0;
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual->grupo && actual->grupo->codigo_gruplac == codigo_gruplac) {
                actual->grupo = nullptr;
                actual->anterior_en_grupo = nullptr;
                actual->siguiente_en_grupo = nullptr;
                contador++;
            }
            actual = actual->siguiente_global;
        }
        return contador;
    }

    void limpiar() noexcept {
        auto* actual = m_cabeza_global;
        while (actual) {
            auto* sig = actual->siguiente_global;
            delete actual;
            actual = sig;
        }
        m_cabeza_global = nullptr;
        m_cola_global = nullptr;
        m_tamano = 0;
    }

private:
    NodoProductoMultilista* m_cabeza_global{nullptr};
    NodoProductoMultilista* m_cola_global{nullptr};
    std::size_t m_tamano{0};

    void enlazar_en_grupo(NodoProductoMultilista* nodo, const QString& codigo_gruplac) {
        NodoProductoMultilista* ultimo = nullptr;
        auto* actual = m_cabeza_global;
        while (actual) {
            if (actual != nodo && actual->grupo && actual->grupo->codigo_gruplac == codigo_gruplac) {
                ultimo = actual;
            }
            actual = actual->siguiente_global;
        }
        if (ultimo) {
            ultimo->siguiente_en_grupo = nodo;
            nodo->anterior_en_grupo = ultimo;
        }
    }
};

} // namespace pea::estructuras
