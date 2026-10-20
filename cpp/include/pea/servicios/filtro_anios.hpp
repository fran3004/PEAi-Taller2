#pragma once

#include <algorithm>
#include <optional>

#include <QString>

namespace pea::servicios {

enum class ModoFiltroAnios {
    TODOS,
    ULTIMOS,
    RANGO,
    MODELO_2024,
};

struct RangoAnios {
    std::optional<int> inicio;
    std::optional<int> fin;
    bool modelo_2024{false};
};

struct FiltroAnios {
    ModoFiltroAnios modo{ModoFiltroAnios::TODOS};
    int ultimos_n{5};
    std::optional<int> desde;
    std::optional<int> hasta;

    [[nodiscard]] RangoAnios resolver(int anio_actual) const {
        if (modo == ModoFiltroAnios::MODELO_2024) {
            return {std::nullopt, std::nullopt, true};
        }
        if (modo == ModoFiltroAnios::ULTIMOS) {
            const int cantidad = std::max(1, ultimos_n);
            return {anio_actual - cantidad + 1, anio_actual, false};
        }
        if (modo == ModoFiltroAnios::RANGO) {
            auto inicio = desde;
            auto fin = hasta;
            if (inicio.has_value() && fin.has_value() && *inicio > *fin) {
                std::swap(inicio, fin);
            }
            return {inicio, fin, false};
        }
        return {};
    }

    [[nodiscard]] QString descripcion(int anio_actual) const {
        if (modo == ModoFiltroAnios::MODELO_2024) {
            return QStringLiteral("Ventana del Modelo 2024 (5 años; 10 para libros y patentes; corte 2023)");
        }
        const auto rango = resolver(anio_actual);
        if (modo == ModoFiltroAnios::ULTIMOS) {
            return QStringLiteral("Últimos %1 años (%2–%3)")
                .arg(std::max(1, ultimos_n))
                .arg(*rango.inicio)
                .arg(*rango.fin);
        }
        if (modo == ModoFiltroAnios::RANGO) {
            const QString inicio = rango.inicio.has_value()
                                       ? QString::number(*rango.inicio)
                                       : QStringLiteral("…");
            const QString fin = rango.fin.has_value()
                                    ? QString::number(*rango.fin)
                                    : QStringLiteral("…");
            return QStringLiteral("Años %1–%2").arg(inicio, fin);
        }
        return QStringLiteral("Todos los años");
    }
};

} // namespace pea::servicios
