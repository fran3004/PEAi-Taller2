#pragma once

#include <cmath>
#include <optional>
#include <QJsonArray>
#include <QJsonObject>
#include <QList>
#include <QMap>
#include <QPair>
#include <QString>
#include "pea/estructuras/hipercubo.hpp"

namespace pea::servicios {

class ServicioEstadisticas {
public:
    explicit ServicioEstadisticas(estructuras::Hipercubo5D* cubo = nullptr)
        : m_hipercubo(cubo) {}

    void setHipercubo(estructuras::Hipercubo5D* cubo) noexcept {
        m_hipercubo = cubo;
    }

    [[nodiscard]] estructuras::Hipercubo5D* hipercubo() const noexcept {
        return m_hipercubo;
    }

    [[nodiscard]] QMap<int, int> productosPorAnio(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, int> productosPorCategoria(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, int> productosPorValidacion(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, int> productosPorGrupo(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, int> productosPorInvestigador(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] double promedioPorInvestigador(const QString& idGrupo = "", const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QList<QPair<QString, int>> top5Investigadores(const QString& idGrupo = "", const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QList<QPair<QString, int>> top5Grupos(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, double> porcentajesPorCategoria(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QMap<QString, double> porcentajesPorValidacion(const estructuras::Hipercubo5D* cubo = nullptr) const;

    [[nodiscard]] QJsonObject obtenerVistaInstitucional(std::optional<int> ventanaAnios = std::nullopt, bool modelo2024 = false) const;

    [[nodiscard]] QJsonObject obtenerVistaGrupo(const QString& idGrupo, std::optional<int> ventanaAnios = std::nullopt, bool modelo2024 = false) const;

    [[nodiscard]] QJsonObject obtenerVistaInvestigador(const QString& idInvestigador, std::optional<int> ventanaAnios = std::nullopt, bool modelo2024 = false) const;

private:
    estructuras::Hipercubo5D* m_hipercubo{nullptr};

    [[nodiscard]] estructuras::Hipercubo5D resolverCubo(
        const estructuras::Hipercubo5D* cubo,
        std::optional<int> ventanaAnios,
        bool modelo2024,
        int anioReferencia = 2024
    ) const;
};

} // namespace pea::servicios
