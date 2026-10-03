#pragma once

#include <stdexcept>
#include <string>

namespace pea {

class ErrorPEA : public std::runtime_error {
public:
    explicit ErrorPEA(const std::string& mensaje, const std::string& detalle = "")
        : std::runtime_error(detalle.empty() ? mensaje : mensaje + " - Detalle: " + detalle),
          m_mensaje(mensaje),
          m_detalle(detalle) {}

    const std::string& mensaje() const noexcept { return m_mensaje; }
    const std::string& detalle() const noexcept { return m_detalle; }

private:
    std::string m_mensaje;
    std::string m_detalle;
};

class ErrorConexion : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class ErrorAutenticacion : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class ErrorAutorizacion : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class RecursoNoEncontrado : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class ConflictoRevision : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class ErrorValidacion : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

class ErrorServidor : public ErrorPEA {
public:
    using ErrorPEA::ErrorPEA;
};

} // namespace pea
