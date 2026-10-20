#include <doctest/doctest.h>

#include "pea/servicios/filtro_anios.hpp"
#include "pea/servicios/servicio_estadisticas.hpp"

using namespace pea::servicios;

TEST_CASE("FiltroAnios conserva los cuatro modos y normaliza rangos") {
    FiltroAnios todos;
    CHECK(todos.descripcion(2026) == "Todos los años");
    CHECK_FALSE(todos.resolver(2026).inicio.has_value());
    CHECK_FALSE(todos.resolver(2026).fin.has_value());

    FiltroAnios ultimos;
    ultimos.modo = ModoFiltroAnios::ULTIMOS;
    ultimos.ultimos_n = 5;
    const auto ultimos_rango = ultimos.resolver(2026);
    REQUIRE(ultimos_rango.inicio.has_value());
    REQUIRE(ultimos_rango.fin.has_value());
    CHECK(*ultimos_rango.inicio == 2022);
    CHECK(*ultimos_rango.fin == 2026);
    CHECK(ultimos.descripcion(2026) == "Últimos 5 años (2022–2026)");

    FiltroAnios rango;
    rango.modo = ModoFiltroAnios::RANGO;
    rango.desde = 2025;
    rango.hasta = 2020;
    const auto rango_resuelto = rango.resolver(2026);
    REQUIRE(rango_resuelto.inicio.has_value());
    REQUIRE(rango_resuelto.fin.has_value());
    CHECK(*rango_resuelto.inicio == 2020);
    CHECK(*rango_resuelto.fin == 2025);
    CHECK(rango.descripcion(2026) == "Años 2020–2025");

    FiltroAnios modelo;
    modelo.modo = ModoFiltroAnios::MODELO_2024;
    CHECK(modelo.resolver(2026).modelo_2024);
    CHECK(modelo.descripcion(2026) ==
          "Ventana del Modelo 2024 (5 años; 10 para libros y patentes; corte 2023)");
}

TEST_CASE("Estadísticas construyen la serie anual por categoría y los histogramas") {
    pea::estructuras::Hipercubo5D cubo;
    cubo.acumular("G1", "I1", "GNC", 2022, "Avalado", "P1");
    cubo.acumular("G1", "I1", "DTI", 2022, "Avalado", "P2");
    cubo.acumular("G1", "I2", "ASC", 2023, "Con soporte", "P3");
    cubo.acumular("G1", "I2", "FRH", 2023, "No avalado", "P4");
    ServicioEstadisticas estadisticas(&cubo);

    const auto serie = estadisticas.serieAnualPorCategoria();
    REQUIRE(serie.size() == 2);
    CHECK(serie[2022]["GNC"] == 1);
    CHECK(serie[2022]["DTI"] == 1);
    CHECK(serie[2023]["ASC"] == 1);
    CHECK(serie[2023]["FRH"] == 1);

    const auto por_anio = estadisticas.distribucionProductosPorAnio();
    CHECK(por_anio.value("2022") == 2);
    CHECK(por_anio.value("2023") == 2);

    QSet<QString> investigadores{"I0", "I1", "I2", "I3"};
    const auto histograma = estadisticas.distribucionProductosPorInvestigador(investigadores);
    CHECK(histograma.value("0") == 2);
    CHECK(histograma.value("1–2") == 2);
    CHECK(histograma.value("3–5") == 0);
    CHECK(histograma.value("6–10") == 0);
    CHECK(histograma.value("11+") == 0);
}

TEST_CASE("FiltroAnios aplica rangos generales y ventana normativa desde el hipercubo") {
    pea::estructuras::Hipercubo5D cubo;
    cubo.acumular("G1", "I1", "GNC", 2013, "Avalado", "P2013");
    cubo.acumular("G1", "I1", "GNC_LIBRO", 2015, "Avalado", "P2015");
    cubo.acumular("G1", "I1", "GNC", 2019, "Avalado", "P2019");
    cubo.acumular("G1", "I1", "DTI", 2023, "Avalado", "P2023");
    cubo.acumular("G1", "I1", "DTI", 2024, "Avalado", "P2024");
    ServicioEstadisticas estadisticas(&cubo);

    FiltroAnios rango;
    rango.modo = ModoFiltroAnios::RANGO;
    rango.desde = 2024;
    rango.hasta = 2023;
    CHECK(estadisticas.aplicarFiltro(rango, 2026).totalProductosUnicos() == 2);

    FiltroAnios modelo;
    modelo.modo = ModoFiltroAnios::MODELO_2024;
    const auto cubo_modelo = estadisticas.aplicarFiltro(modelo, 2026);
    CHECK(cubo_modelo.totalProductosUnicos() == 3);
    CHECK_FALSE(cubo_modelo.enrollarAnio().contains(2024));
    CHECK(cubo_modelo.enrollarAnio().contains(2015));
}
