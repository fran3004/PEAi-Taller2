#pragma once

#include <cstddef>
#include <stdexcept>
#include <utility>
#include <QJsonObject>
#include <QString>
#include "pea/estructuras/nodo.hpp"

namespace pea::estructuras {

struct ComandoInverso {
    QString tipo_operacion; // 'crear', 'editar', 'desactivar', 'activar', 'eliminar'
    QString tipo_entidad;   // 'grupo', 'investigador', 'producto', 'integrante'
    QString identificador;
    QJsonObject datos_reversion;
    QString descripcion;

    ComandoInverso() = default;
    ComandoInverso(QString op, QString entidad, QString id, QJsonObject rev = QJsonObject(), QString desc = QString())
        : tipo_operacion(std::move(op)),
          tipo_entidad(std::move(entidad)),
          identificador(std::move(id)),
          datos_reversion(std::move(rev)),
          descripcion(std::move(desc)) {}
};

template <typename T>
class Pila {
public:
    explicit Pila(std::size_t capacidad_maxima = 50)
        : m_tope(nullptr), m_tamano(0), m_capacidad_maxima(capacidad_maxima) {}

    ~Pila() {
        limpiar();
    }

    Pila(const Pila& otra)
        : m_tope(nullptr), m_tamano(0), m_capacidad_maxima(otra.m_capacidad_maxima) {
        copiar_desde(otra);
    }

    Pila& operator=(const Pila& otra) {
        if (this != &otra) {
            limpiar();
            m_capacidad_maxima = otra.m_capacidad_maxima;
            copiar_desde(otra);
        }
        return *this;
    }

    Pila(Pila&& otra) noexcept
        : m_tope(otra.m_tope),
          m_tamano(otra.m_tamano),
          m_capacidad_maxima(otra.m_capacidad_maxima) {
        otra.m_tope = nullptr;
        otra.m_tamano = 0;
    }

    Pila& operator=(Pila&& otra) noexcept {
        if (this != &otra) {
            limpiar();
            m_tope = otra.m_tope;
            m_tamano = otra.m_tamano;
            m_capacidad_maxima = otra.m_capacidad_maxima;
            otra.m_tope = nullptr;
            otra.m_tamano = 0;
        }
        return *this;
    }

    [[nodiscard]] std::size_t tamano() const noexcept { return m_tamano; }
    [[nodiscard]] bool esta_vacia() const noexcept { return m_tamano == 0; }
    [[nodiscard]] std::size_t capacidad_maxima() const noexcept { return m_capacidad_maxima; }

    void apilar(const T& valor) {
        if (m_tamano >= m_capacidad_maxima) {
            descartar_fondo();
        }
        auto* nuevo = new NodoSimple<T>(valor);
        nuevo->siguiente = m_tope;
        m_tope = nuevo;
        m_tamano++;
    }

    void apilar(T&& valor) {
        if (m_tamano >= m_capacidad_maxima) {
            descartar_fondo();
        }
        auto* nuevo = new NodoSimple<T>(std::move(valor));
        nuevo->siguiente = m_tope;
        m_tope = nuevo;
        m_tamano++;
    }

    T desapilar() {
        if (!m_tope) {
            throw std::out_of_range("No se puede desapilar de una pila vacía");
        }
        auto* nodo = m_tope;
        m_tope = nodo->siguiente;
        T valor = std::move(nodo->dato);
        delete nodo;
        m_tamano--;
        return valor;
    }

    [[nodiscard]] const T* ver_tope() const noexcept {
        return m_tope ? &(m_tope->dato) : nullptr;
    }

    [[nodiscard]] T* ver_tope() noexcept {
        return m_tope ? &(m_tope->dato) : nullptr;
    }

    void limpiar() noexcept {
        auto* actual = m_tope;
        while (actual) {
            auto* sig = actual->siguiente;
            delete actual;
            actual = sig;
        }
        m_tope = nullptr;
        m_tamano = 0;
    }

private:
    NodoSimple<T>* m_tope{nullptr};
    std::size_t m_tamano{0};
    std::size_t m_capacidad_maxima{50};

    void descartar_fondo() {
        if (!m_tope || !m_tope->siguiente) {
            limpiar();
            return;
        }
        auto* anterior = m_tope;
        auto* actual = m_tope->siguiente;
        while (actual->siguiente) {
            anterior = actual;
            actual = actual->siguiente;
        }
        delete actual;
        anterior->siguiente = nullptr;
        m_tamano--;
    }

    void copiar_desde(const Pila& otra) {
        if (!otra.m_tope) return;
        // Para preservar el orden en la pila copiada, leemos los elementos
        // y los insertamos en orden inverso
        auto* actual = otra.m_tope;
        std::size_t n = otra.m_tamano;
        if (n == 0) return;

        // Construir array temporal de punteros para invertir
        auto** nodos = new NodoSimple<T>*[n];
        std::size_t idx = 0;
        while (actual && idx < n) {
            nodos[idx++] = actual;
            actual = actual->siguiente;
        }

        // Apilar desde el fondo hasta la cima
        for (std::size_t i = idx; i > 0; --i) {
            apilar(nodos[i - 1]->dato);
        }
        delete[] nodos;
    }
};

} // namespace pea::estructuras
