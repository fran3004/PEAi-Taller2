#pragma once

#include <cstddef>
#include <stdexcept>
#include <utility>
#include <QJsonObject>
#include <QString>
#include "pea/estructuras/nodo.hpp"

namespace pea::estructuras {

enum class EstadoTarea {
    Pendiente,
    Procesando,
    Terminada,
    ConError
};

struct TareaIngesta {
    QString id_tarea;
    QString tipo_fuente; // 'url_gruplac', 'url_cvlac', 'archivo_csv'
    QString origen;
    EstadoTarea estado{EstadoTarea::Pendiente};
    QString mensaje_error;
    int elementos_procesados{0};
    QJsonObject detalles;

    TareaIngesta() = default;
    TareaIngesta(QString id, QString tipo, QString orig)
        : id_tarea(std::move(id)),
          tipo_fuente(std::move(tipo)),
          origen(std::move(orig)) {}
};

template <typename T>
class Cola {
public:
    Cola() : m_frente(nullptr), m_final(nullptr), m_tamano(0) {}

    ~Cola() {
        limpiar();
    }

    Cola(const Cola& otra)
        : m_frente(nullptr), m_final(nullptr), m_tamano(0) {
        copiar_desde(otra);
    }

    Cola& operator=(const Cola& otra) {
        if (this != &otra) {
            limpiar();
            copiar_desde(otra);
        }
        return *this;
    }

    Cola(Cola&& otra) noexcept
        : m_frente(otra.m_frente),
          m_final(otra.m_final),
          m_tamano(otra.m_tamano) {
        otra.m_frente = nullptr;
        otra.m_final = nullptr;
        otra.m_tamano = 0;
    }

    Cola& operator=(Cola&& otra) noexcept {
        if (this != &otra) {
            limpiar();
            m_frente = otra.m_frente;
            m_final = otra.m_final;
            m_tamano = otra.m_tamano;
            otra.m_frente = nullptr;
            otra.m_final = nullptr;
            otra.m_tamano = 0;
        }
        return *this;
    }

    [[nodiscard]] std::size_t tamano() const noexcept { return m_tamano; }
    [[nodiscard]] bool esta_vacia() const noexcept { return m_tamano == 0; }

    void encolar(const T& valor) {
        auto* nuevo = new NodoSimple<T>(valor);
        if (!m_final) {
            m_frente = nuevo;
            m_final = nuevo;
        } else {
            m_final->siguiente = nuevo;
            m_final = nuevo;
        }
        m_tamano++;
    }

    void encolar(T&& valor) {
        auto* nuevo = new NodoSimple<T>(std::move(valor));
        if (!m_final) {
            m_frente = nuevo;
            m_final = nuevo;
        } else {
            m_final->siguiente = nuevo;
            m_final = nuevo;
        }
        m_tamano++;
    }

    T desencolar() {
        if (!m_frente) {
            throw std::out_of_range("No se puede desencolar de una cola vacía");
        }
        auto* nodo = m_frente;
        m_frente = nodo->siguiente;
        if (!m_frente) {
            m_final = nullptr;
        }
        T valor = std::move(nodo->dato);
        delete nodo;
        m_tamano--;
        return valor;
    }

    [[nodiscard]] const T* ver_frente() const noexcept {
        return m_frente ? &(m_frente->dato) : nullptr;
    }

    [[nodiscard]] T* ver_frente() noexcept {
        return m_frente ? &(m_frente->dato) : nullptr;
    }

    void limpiar() noexcept {
        auto* actual = m_frente;
        while (actual) {
            auto* sig = actual->siguiente;
            delete actual;
            actual = sig;
        }
        m_frente = nullptr;
        m_final = nullptr;
        m_tamano = 0;
    }

private:
    NodoSimple<T>* m_frente{nullptr};
    NodoSimple<T>* m_final{nullptr};
    std::size_t m_tamano{0};

    void copiar_desde(const Cola& otra) {
        auto* actual = otra.m_frente;
        while (actual) {
            encolar(actual->dato);
            actual = actual->siguiente;
        }
    }
};

} // namespace pea::estructuras
