#pragma once

#include <utility>

namespace pea::estructuras {

template <typename T>
class NodoDoble {
public:
    T dato;
    NodoDoble<T>* anterior;
    NodoDoble<T>* siguiente;

    explicit NodoDoble(const T& valor)
        : dato(valor), anterior(nullptr), siguiente(nullptr) {}

    explicit NodoDoble(T&& valor)
        : dato(std::move(valor)), anterior(nullptr), siguiente(nullptr) {}

    // Prohibir copia y movimiento directo del nodo (propiedad gestionada por la lista)
    NodoDoble(const NodoDoble&) = delete;
    NodoDoble& operator=(const NodoDoble&) = delete;
    NodoDoble(NodoDoble&&) = delete;
    NodoDoble& operator=(NodoDoble&&) = delete;
    ~NodoDoble() = default;
};

template <typename T>
class NodoSimple {
public:
    T dato;
    NodoSimple<T>* siguiente;

    explicit NodoSimple(const T& valor)
        : dato(valor), siguiente(nullptr) {}

    explicit NodoSimple(T&& valor)
        : dato(std::move(valor)), siguiente(nullptr) {}

    NodoSimple(const NodoSimple&) = delete;
    NodoSimple& operator=(const NodoSimple&) = delete;
    NodoSimple(NodoSimple&&) = delete;
    NodoSimple& operator=(NodoSimple&&) = delete;
    ~NodoSimple() = default;
};

} // namespace pea::estructuras
