#include <doctest/doctest.h>
#include "pea/estructuras/hipercubo.hpp"
#include "pea/servicios/servicio_estadisticas.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

using namespace pea;

TEST_CASE("Hipercubo C++: Estado vacio y metricas sin division por cero") {
    estructuras::Hipercubo5D cubo;
    CHECK(cubo.estaVacio());
    CHECK(cubo.tamano() == 0);
    CHECK(cubo.medidaTotal() == 0);
    CHECK(cubo.totalProductosUnicos() == 0);

    servicios::ServicioEstadisticas stats(&cubo);
    CHECK(stats.productosPorAnio().isEmpty());

    auto cats = stats.productosPorCategoria();
    CHECK(cats["GNC"] == 0);
    CHECK(cats["DTI"] == 0);

    auto vals = stats.productosPorValidacion();
    CHECK(vals["Avalado"] == 0);

    CHECK(stats.promedioPorInvestigador() == 0.0);
    CHECK(stats.top5Investigadores().isEmpty());
    CHECK(stats.top5Grupos().isEmpty());

    auto pctCats = stats.porcentajesPorCategoria();
    for (auto it = pctCats.constBegin(); it != pctCats.constEnd(); ++it) {
        CHECK(it.value() == 0.0);
    }

    // Tres vistas vacias
    QJsonObject vInst = stats.obtenerVistaInstitucional();
    CHECK(vInst["total_productos"].toInt() == 0);

    QJsonObject vGrp = stats.obtenerVistaGrupo("GRP-INEXISTENTE");
    CHECK(vGrp["total_productos"].toInt() == 0);

    QJsonObject vInv = stats.obtenerVistaInvestigador("INV-INEXISTENTE");
    CHECK(vInv["total_productos"].toInt() == 0);
}

TEST_CASE("Hipercubo C++: Un producto activo y calculo de porcentajes") {
    estructuras::Hipercubo5D cubo;
    cubo.acumular("GRP-01", "INV-01", "GNC", 2023, "Avalado", "PRD-01", 1.0);

    CHECK_FALSE(cubo.estaVacio());
    CHECK(cubo.medidaTotal() == 1);
    CHECK(cubo.totalProductosUnicos() == 1);

    servicios::ServicioEstadisticas stats(&cubo);
    auto anios = stats.productosPorAnio();
    CHECK(anios.value(2023) == 1);

    auto pctCat = stats.porcentajesPorCategoria();
    CHECK(pctCat.value("GNC") == 100.0);
    CHECK(pctCat.value("DTI") == 0.0);

    auto pctVal = stats.porcentajesPorValidacion();
    CHECK(pctVal.value("Avalado") == 100.0);

    auto topInv = stats.top5Investigadores();
    REQUIRE(topInv.size() == 1);
    CHECK(topInv[0].first == "INV-01");
    CHECK(topInv[0].second == 1);

    CHECK(stats.promedioPorInvestigador() == 1.0);
}

TEST_CASE("Hipercubo C++: Desactivacion y reactivacion en Catalogo") {
    servicios::CatalogoInvestigacion catalogo;
    auto g = std::make_shared<dominio::Grupo>("GRP-A", "Grupo Alfa");
    catalogo.crear_grupo(g, false);

    auto inv = std::make_shared<dominio::Investigador>("INV-100", "Dra. Lopez");
    catalogo.crear_investigador(inv, false);

    auto prod = std::make_shared<dominio::Producto>(
        "P-100", "Paper IA", "GNC", "ART_A1", 2022, "Avalado", false
    );
    catalogo.crear_producto(prod, g->codigo_gruplac, {inv->codigo_rh}, false);

    // Debe estar indexado y medido
    CHECK(catalogo.hipercubo.totalProductosUnicos() == 1);
    CHECK(catalogo.estadisticas.productosPorCategoria().value("GNC") == 1);

    // Desactivar
    catalogo.desactivar_producto("P-100", false);
    CHECK_FALSE(prod->activo);
    CHECK(catalogo.hipercubo.medidaTotal() == 0);
    CHECK(catalogo.hipercubo.totalProductosUnicos() == 0);
    CHECK(catalogo.estadisticas.productosPorCategoria().value("GNC") == 0);

    // Reactivar
    catalogo.activar_producto("P-100", false);
    CHECK(prod->activo);
    CHECK(catalogo.hipercubo.totalProductosUnicos() == 1);
    CHECK(catalogo.estadisticas.productosPorCategoria().value("GNC") == 1);
}

TEST_CASE("Hipercubo C++: Ventanas temporales (Filtro interfaz vs Modelo 2024)") {
    estructuras::Hipercubo5D cubo;
    cubo.acumular("G1", "I1", "GNC", 2013, "Avalado", "P-2013-LIBRO");
    cubo.acumular("G1", "I1", "GNC_LIBRO", 2015, "Avalado", "P-2015-LIBRO");
    cubo.acumular("G1", "I2", "GNC", 2018, "Avalado", "P-2018-ART");
    cubo.acumular("G1", "I1", "GNC", 2020, "Avalado", "P-2020-ART");
    cubo.acumular("G2", "I3", "DTI", 2021, "Con soporte", "P-2021-SW");
    cubo.acumular("G2", "I3", "ASC", 2023, "Avalado", "P-2023-EVT");
    cubo.acumular("G1", "I2", "FRH", 2024, "Avalado", "P-2024-TESIS");

    // 1. Filtro generico de interfaz: rango 2020..2022
    estructuras::Hipercubo5D subInterfaz = cubo.subcuboPorVentana(2020, 2022);
    auto aniosInter = subInterfaz.enrollarAnio();
    CHECK(aniosInter.contains(2020));
    CHECK(aniosInter.contains(2021));
    CHECK_FALSE(aniosInter.contains(2013));
    CHECK_FALSE(aniosInter.contains(2015));
    CHECK_FALSE(aniosInter.contains(2024));

    // 2. Ventana del Modelo 2024 (corte 2023):
    // 5 anios (2019-2023) para articulos, 10 anios (2014-2023) para libros/patentes
    estructuras::Hipercubo5D subModelo = cubo.subcuboModelo2024(2023);
    auto aniosModelo = subModelo.enrollarAnio();

    // El libro de 2015 entra en los 10 anios
    CHECK(aniosModelo.contains(2015));
    // El libro de 2013 queda por fuera (>10 anios)
    CHECK_FALSE(aniosModelo.contains(2013));
    // La tesis de 2024 queda por fuera (>2023)
    CHECK_FALSE(aniosModelo.contains(2024));
}

TEST_CASE("Hipercubo C++: Desempate determinista y redondeo a 2 decimales") {
    estructuras::Hipercubo5D cubo;
    // Tres investigadores con exactamente 2 productos cada uno
    cubo.acumular("G1", "INV_CARLOS", "GNC", 2022, "Avalado", "P1");
    cubo.acumular("G1", "INV_CARLOS", "GNC", 2023, "Avalado", "P2");
    cubo.acumular("G1", "INV_ANDRES", "GNC", 2022, "Avalado", "P3");
    cubo.acumular("G1", "INV_ANDRES", "GNC", 2023, "Avalado", "P4");
    cubo.acumular("G1", "INV_BERNARDO", "GNC", 2022, "Avalado", "P5");
    cubo.acumular("G1", "INV_BERNARDO", "GNC", 2023, "Avalado", "P6");

    servicios::ServicioEstadisticas stats(&cubo);
    auto top = stats.top5Investigadores();

    REQUIRE(top.size() == 3);
    CHECK(top[0].first == "INV_ANDRES");
    CHECK(top[1].first == "INV_BERNARDO");
    CHECK(top[2].first == "INV_CARLOS");

    // Redondeo exacto: 1 GNC, 2 DTI -> GNC 33.33%, DTI 66.67%
    estructuras::Hipercubo5D cubo2;
    cubo2.acumular("G1", "I1", "GNC", 2023, "Avalado", "P1");
    cubo2.acumular("G1", "I2", "DTI", 2023, "Avalado", "P2");
    cubo2.acumular("G1", "I2", "DTI", 2023, "Avalado", "P3");

    servicios::ServicioEstadisticas stats2(&cubo2);
    auto pct = stats2.porcentajesPorCategoria();
    CHECK(pct["GNC"] == 33.33);
    CHECK(pct["DTI"] == 66.67);
    CHECK(stats2.promedioPorInvestigador() == 1.5);
}

TEST_CASE("Hipercubo C++: Verificacion contra GROUP BY relacional") {
    struct RegistroPlano {
        QString id;
        QString grupo;
        QString inv;
        QString cat;
        int ano;
        QString val;
    };

    QList<RegistroPlano> datos = {
        {"P1", "GRP-A", "I1", "GNC", 2021, "Avalado"},
        {"P2", "GRP-A", "I1", "GNC", 2022, "Avalado"},
        {"P3", "GRP-A", "I2", "DTI", 2021, "Con soporte"},
        {"P4", "GRP-B", "I3", "ASC", 2020, "Avalado"},
        {"P5", "GRP-B", "I3", "FRH", 2023, "No avalado"},
        {"P6", "GRP-C", "I4", "GNC", 2023, "Avalado"},
        {"P7", "GRP-C", "I4", "DTI", 2022, "Avalado"},
        {"P8", "GRP-A", "I2", "GNC", 2023, "Avalado"},
    };

    // Oraculo relacional simulado
    QMap<int, int> sqlAnio;
    QMap<QString, int> sqlCat;
    QMap<QString, int> sqlGrp;

    for (const auto& r : datos) {
        sqlAnio[r.ano]++;
        sqlCat[r.cat]++;
        sqlGrp[r.grupo]++;
    }

    estructuras::Hipercubo5D cubo;
    for (const auto& r : datos) {
        cubo.acumular(r.grupo, r.inv, r.cat, r.ano, r.val, r.id);
    }

    CHECK(cubo.enrollarAnio() == sqlAnio);
    CHECK(cubo.enrollar(estructuras::Hipercubo5D::DIM_CATEGORIA) == sqlCat);
    CHECK(cubo.enrollar(estructuras::Hipercubo5D::DIM_GRUPO) == sqlGrp);
}

TEST_CASE("Hipercubo C++: Tres vistas analiticas") {
    estructuras::Hipercubo5D cubo;
    cubo.acumular("G1", "I1", "GNC", 2023, "Avalado", "P1");
    cubo.acumular("G1", "I2", "GNC", 2023, "Avalado", "P2");
    cubo.acumular("G2", "I1", "DTI", 2022, "Con soporte", "P3");

    servicios::ServicioEstadisticas stats(&cubo);

    // 1. Vista Institucional
    QJsonObject vInst = stats.obtenerVistaInstitucional();
    CHECK(vInst["tipo_vista"].toString() == "institucional");
    CHECK(vInst["total_productos"].toInt() == 3);

    // 2. Vista Grupo
    QJsonObject vGrp = stats.obtenerVistaGrupo("G1");
    CHECK(vGrp["tipo_vista"].toString() == "grupo");
    CHECK(vGrp["id_grupo"].toString() == "G1");
    CHECK(vGrp["total_productos"].toInt() == 2);
    CHECK(vGrp["porcentaje_sobre_institucion"].toDouble() == 66.67);

    // 3. Vista Investigador
    QJsonObject vInv = stats.obtenerVistaInvestigador("I1");
    CHECK(vInv["tipo_vista"].toString() == "investigador");
    CHECK(vInv["id_investigador"].toString() == "I1");
    CHECK(vInv["total_productos"].toInt() == 2);
}
