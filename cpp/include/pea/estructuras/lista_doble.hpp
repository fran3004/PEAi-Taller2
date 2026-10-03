#pragma once

#include <cstddef>
#include <stdexcept>
#include <utility>
#include "pea/estructuras/nodo.hpp"

namespace pea::estructuras {

template <typename T>
class ListaDoble {
public:
    class Iterador {
    public:
        using iterator_category = std::bidirectional_iterator_tag;
        using value_type = T;
        using difference_type = std::ptrdiff_t;
        using pointer = T*;
        using reference = T&;

        explicit Iterador(NodoDoble<T>* nodo) : m_nodo(nodo) {}

        reference operator*() const { return m_nodo->dato; }
        pointer operator->() const { return &(m_nodo->dato); }

        Iterador& operator++() {
            if (m_nodo) m_nodo = m_nodo->siguiente;
            return *this;
        }

        Iterador operator++(int) {
            Iterador temp = *this;
            ++(*this);
            return temp;
        }

        Iterador& operator--() {
            if (m_nodo) m_nodo = m_nodo->anterior;
            return *this;
        }

        Iterador operator--(int) {
            Iterador temp = *this;
            --(*this);
            return temp;
        }

        bool operator==(const Iterador& otro) const { return m_nodo == otro.m_nodo; }
        bool operator!=(const Iterador& otro) const { return m_nodo != otro.m_nodo; }
        NodoDoble<T>* nodo() const { return m_nodo; }

    private:
        NodoDoble<T>* m_nodo;
    };

    class IteradorConst {
    public:
        using iterator_category = std::bidirectional_iterator_tag;
        using value_type = const T;
        using difference_type = std::ptrdiff_t;
        using pointer = const T*;
        using reference = const T&;

        explicit IteradorConst(const NodoDoble<T>* nodo) : m_nodo(nodo) {}

        reference operator*() const { return m_nodo->dato; }
        pointer operator->() const { return &(m_nodo->dato); }

        IteradorConst& operator++() {
            if (m_nodo) m_nodo = m_nodo->siguiente;
            return *this;
        }

        IteradorConst operator++(int) {
            IteradorConst temp = *this;
            ++(*this);
            return temp;
        }

        IteradorConst& operator--() {
            if (m_nodo) m_nodo = m_nodo->anterior;
            return *this;
        }

        IteradorConst operator--(int) {
            IteradorConst temp = *this;
            --(*this);
            return temp;
        }

        bool operator==(const IteradorConst& otro) const { return m_nodo == otro.m_nodo; }
        bool operator!=(const IteradorConst& otro) const { return m_nodo != otro.m_nodo; }
        const NodoDoble<T>* nodo() const { return m_nodo; }

    private:
        const NodoDoble<T>* m_nodo;
    };

    ListaDoble() : m_cabeza(nullptr), m_cola(nullptr), m_tamano(0) {}

    // Regla de los cinco: Destructor
    ~ListaDoble() {
        limpiar();
    }

    // Constructor de copia
    ListaDoble(const ListaDoble& otra) : m_cabeza(nullptr), m_cola(nullptr), m_tamano(0) {
        for (const auto& elemento : otra) {
            insertarFinal(elemento);
        }
    }

    // Operador de asignación de copia
    ListaDoble& operator=(const ListaDoble& otra) {
        if (this != &otra) {
            limpiar();
            for (const auto& elemento : otra) {
                insertarFinal(elemento);
            }
        }
        return *this;
    }

    // Constructor de movimiento
    ListaDoble(ListaDoble&& otra) noexcept
        : m_cabeza(otra.m_cabeza), m_cola(otra.m_cola), m_tamano(otra.m_tamano) {
        otra.m_cabeza = nullptr;
        otra.m_cola = nullptr;
        otra.m_tamano = 0;
    }

    // Operador de asignación de movimiento
    ListaDoble& operator=(ListaDoble&& otra) noexcept {
        if (this != &otra) {
            limpiar();
            m_cabeza = otra.m_cabeza;
            m_cola = otra.m_cola;
            m_tamano = otra.m_tamano;
            otra.m_cabeza = nullptr;
            otra.m_cola = nullptr;
            otra.m_tamano = 0;
        }
        return *this;
    }

    size_t tamano() const noexcept { return m_tamano; }
    bool estaVacia() const noexcept { return m_tamano == 0; }

    Iterador begin() noexcept { return Iterador(m_cabeza); }
    Iterador end() noexcept { return Iterador(nullptr); }
    IteradorConst begin() const noexcept { return IteradorConst(m_cabeza); }
    IteradorConst end() const noexcept { return IteradorConst(nullptr); }
    IteradorConst cbegin() const noexcept { return IteradorConst(m_cabeza); }
    IteradorConst cend() const noexcept { return IteradorConst(nullptr); }

    NodoDoble<T>* cabeza() const noexcept { return m_cabeza; }
    NodoDoble<T>* cola() const noexcept { return m_cola; }

    NodoDoble<T>* insertarInicio(const T& valor) {
        auto* nuevo = new NodoDoble<T>(valor);
        if (!m_cabeza) {
            m_cabeza = nuevo;
            m_cola = nuevo;
        } else {
            nuevo->siguiente = m_cabeza;
            m_cabeza->anterior = nuevo;
            m_cabeza = nuevo;
        }
        ++m_tamano;
        return nuevo;
    }

    NodoDoble<T>* insertarInicio(T&& valor) {
        auto* nuevo = new NodoDoble<T>(std::move(valor));
        if (!m_cabeza) {
            m_cabeza = nuevo;
            m_cola = nuevo;
        } else {
            nuevo->siguiente = m_cabeza;
            m_cabeza->anterior = nuevo;
            m_cabeza = nuevo;
        }
        ++m_tamano;
        return nuevo;
    }

    NodoDoble<T>* insertarFinal(const T& valor) {
        auto* nuevo = new NodoDoble<T>(valor);
        if (!m_cola) {
            m_cabeza = nuevo;
            m_cola = nuevo;
        } else {
            m_cola->siguiente = nuevo;
            nuevo->anterior = m_cola;
            m_cola = nuevo;
        }
        ++m_tamano;
        return nuevo;
    }

    NodoDoble<T>* insertarFinal(T&& valor) {
        auto* nuevo = new NodoDoble<T>(std::move(valor));
        if (!m_cola) {
            m_cabeza = nuevo;
            m_cola = nuevo;
        } else {
            m_cola->siguiente = nuevo;
            nuevo->anterior = m_cola;
            m_cola = nuevo;
        }
        ++m_tamano;
        return nuevo;
    }

    NodoDoble<T>* insertarEn(size_t indice, const T& valor) {
        if (indice > m_tamano) {
            throw std::out_of_range("Índice fuera de rango en ListaDoble::insertarEn");
        }
        if (indice == 0) return insertarInicio(valor);
        if (indice == m_tamano) return insertarFinal(valor);

        NodoDoble<T>* actual = nodoEn(indice);
        auto* nuevo = new NodoDoble<T>(valor);
        NodoDoble<T>* predecesor = actual->anterior;

        if (predecesor) {
            predecesor->siguiente = nuevo;
            nuevo->anterior = predecesor;
        }
        nuevo->siguiente = actual;
        actual->anterior = nuevo;
        ++m_tamano;
        return nuevo;
    }

    T eliminarNodo(NodoDoble<T>* nodo) {
        if (!nodo) {
            throw std::invalid_argument("El nodo a eliminar no puede ser nulo");
        }

        if (nodo == m_cabeza) {
            m_cabeza = nodo->siguiente;
        }
        if (nodo->anterior) {
            nodo->anterior->siguiente = nodo->siguiente;
        }

        if (nodo == m_cola) {
            m_cola = nodo->anterior;
        }
        if (nodo->siguiente) {
            nodo->siguiente->anterior = nodo->anterior;
        }

        T valor = std::move(nodo->dato);
        delete nodo;
        --m_tamano;
        return valor;
    }

    T eliminarInicio() {
        if (!m_cabeza) {
            throw std::out_of_range("No se puede eliminar de una lista vacía");
        }
        return eliminarNodo(m_cabeza);
    }

    T eliminarFinal() {
        if (!m_cola) {
            throw std::out_of_range("No se puede eliminar de una lista vacía");
        }
        return eliminarNodo(m_cola);
    }

    T eliminarEn(size_t indice) {
        return eliminarNodo(nodoEn(indice));
    }


    template <typename Predicado>
    bool eliminarPorCriterio(Predicado pred) {
        NodoDoble<T>* actual = m_cabeza;
        while (actual) {
            if (pred(actual->dato)) {
                eliminarNodo(actual);
                return true;
            }
            actual = actual->siguiente;
        }
        return false;
    }

    template <typename Predicado>
    NodoDoble<T>* buscar(Predicado pred) const {
        NodoDoble<T>* actual = m_cabeza;
        while (actual) {
            if (pred(actual->dato)) {
                return actual;
            }
            actual = actual->siguiente;
        }
        return nullptr;
    }

    template <typename Predicado>
    const T* buscarDato(Predicado pred) const {
        NodoDoble<T>* n = buscar(pred);
        return n ? &(n->dato) : nullptr;
    }

    template <typename Predicado>
    T* buscarDato(Predicado pred) {
        NodoDoble<T>* n = buscar(pred);
        return n ? &(n->dato) : nullptr;
    }

    T& obtener(size_t indice) {
        return nodoEn(indice)->dato;
    }

    const T& obtener(size_t indice) const {
        return nodoEn(indice)->dato;
    }

    T& operator[](size_t indice) { return obtener(indice); }
    const T& operator[](size_t indice) const { return obtener(indice); }

    void limpiar() noexcept {
        NodoDoble<T>* actual = m_cabeza;
        while (actual) {
            NodoDoble<T>* siguiente = actual->siguiente;
            delete actual;
            actual = siguiente;
        }
        m_cabeza = nullptr;
        m_cola = nullptr;
        m_tamano = 0;
    }

    // Alias en snake_case para compatibilidad total de contrato
    bool esta_vacia() const noexcept { return estaVacia(); }
    NodoDoble<T>* insertar_inicio(const T& valor) { return insertarInicio(valor); }
    NodoDoble<T>* insertar_inicio(T&& valor) { return insertarInicio(std::move(valor)); }
    NodoDoble<T>* insertar_final(const T& valor) { return insertarFinal(valor); }
    NodoDoble<T>* insertar_final(T&& valor) { return insertarFinal(std::move(valor)); }
    T eliminar_inicio() { return eliminarInicio(); }
    T eliminar_final() { return eliminarFinal(); }
    T eliminar_nodo(NodoDoble<T>* nodo) { return eliminarNodo(nodo); }

    template <typename Predicado>
    bool eliminar_por_criterio(Predicado pred) {
        return eliminarPorCriterio(pred);
    }

    template <typename Predicado>
    const T* buscar_dato(Predicado pred) const {
        return buscarDato(pred);
    }

    template <typename Predicado>
    T* buscar_dato(Predicado pred) {
        return buscarDato(pred);
    }


private:
    NodoDoble<T>* nodoEn(size_t indice) const {
        if (indice >= m_tamano) {
            throw std::out_of_range("Índice fuera de rango en ListaDoble");
        }

        if (indice < m_tamano / 2) {
            NodoDoble<T>* actual = m_cabeza;
            for (size_t i = 0; i < indice; ++i) {
                actual = actual->siguiente;
            }
            return actual;
        } else {
            NodoDoble<T>* actual = m_cola;
            for (size_t i = m_tamano - 1; i > indice; --i) {
                actual = actual->anterior;
            }
            return actual;
        }
    }

    NodoDoble<T>* m_cabeza;
    NodoDoble<T>* m_cola;
    size_t m_tamano;
};

} // namespace pea::estructuras
