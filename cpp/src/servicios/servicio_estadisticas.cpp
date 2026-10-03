#include "pea/servicios/servicio_estadisticas.hpp"
#include <algorithm>

namespace pea::servicios {

static inline double redondear2(double valor) noexcept {
    return std::round(valor * 100.0) / 100.0;
}

estructuras::Hipercubo5D ServicioEstadisticas::resolverCubo(
    const estructuras::Hipercubo5D* cubo,
    std::optional<int> ventanaAnios,
    bool modelo2024,
    int anioReferencia
) const {
    const estructuras::Hipercubo5D* base = cubo ? cubo : m_hipercubo;
    if (!base) return estructuras::Hipercubo5D();

    if (modelo2024) {
        return base->subcuboModelo2024(2023);
    }
    if (ventanaAnios.has_value() && *ventanaAnios > 0) {
        int inicio = anioReferencia - *ventanaAnios + 1;
        return base->subcuboPorVentana(inicio, anioReferencia);
    }
    return *base;
}

QMap<int, int> ServicioEstadisticas::productosPorAnio(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return {};
    return c->enrollarAnio();
}

QMap<QString, int> ServicioEstadisticas::productosPorCategoria(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    QMap<QString, int> resultado;
    resultado["GNC"] = 0;
    resultado["DTI"] = 0;
    resultado["ASC"] = 0;
    resultado["FRH"] = 0;

    if (!c) return resultado;

    QMap<QString, int> bruto = c->enrollar(estructuras::Hipercubo5D::DIM_CATEGORIA);
    for (auto it = bruto.constBegin(); it != bruto.constEnd(); ++it) {
        QString catUpper = it.key().toUpper();
        if (resultado.contains(catUpper)) {
            resultado[catUpper] += it.value();
        } else if (catUpper.contains("GNC") || catUpper.contains("LIBRO") || catUpper.contains("PATENTE")) {
            resultado["GNC"] += it.value();
        } else {
            resultado[it.key()] = it.value();
        }
    }
    return resultado;
}

QMap<QString, int> ServicioEstadisticas::productosPorValidacion(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    QMap<QString, int> resultado;
    resultado["Avalado"] = 0;
    resultado["Con soporte"] = 0;
    resultado["No avalado"] = 0;

    if (!c) return resultado;

    QMap<QString, int> bruto = c->enrollar(estructuras::Hipercubo5D::DIM_VALIDACION);
    for (auto it = bruto.constBegin(); it != bruto.constEnd(); ++it) {
        resultado[it.key()] = it.value();
    }
    return resultado;
}

QMap<QString, int> ServicioEstadisticas::productosPorGrupo(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return {};
    return c->enrollar(estructuras::Hipercubo5D::DIM_GRUPO);
}

QMap<QString, int> ServicioEstadisticas::productosPorInvestigador(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return {};
    return c->enrollar(estructuras::Hipercubo5D::DIM_INVESTIGADOR);
}

double ServicioEstadisticas::promedioPorInvestigador(const QString& idGrupo, const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return 0.0;

    estructuras::Hipercubo5D temporal;
    if (!idGrupo.isEmpty()) {
        temporal = c->rebanada(estructuras::Hipercubo5D::DIM_GRUPO, idGrupo);
        c = &temporal;
    }

    QMap<QString, int> conteoInv = c->enrollar(estructuras::Hipercubo5D::DIM_INVESTIGADOR);
    int invsReales = 0;
    for (auto it = conteoInv.constBegin(); it != conteoInv.constEnd(); ++it) {
        if (it.key() != "SIN_INVESTIGADOR") {
            invsReales++;
        }
    }

    if (invsReales == 0) return 0.0;
    int totalProds = c->totalProductosUnicos();
    return redondear2(static_cast<double>(totalProds) / invsReales);
}

QList<QPair<QString, int>> ServicioEstadisticas::top5Investigadores(const QString& idGrupo, const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return {};

    estructuras::Hipercubo5D temporal;
    if (!idGrupo.isEmpty()) {
        temporal = c->rebanada(estructuras::Hipercubo5D::DIM_GRUPO, idGrupo);
        c = &temporal;
    }

    QMap<QString, int> conteoInv = c->enrollar(estructuras::Hipercubo5D::DIM_INVESTIGADOR);
    QList<QPair<QString, int>> lista;
    for (auto it = conteoInv.constBegin(); it != conteoInv.constEnd(); ++it) {
        if (it.key() != "SIN_INVESTIGADOR") {
            lista.append(qMakePair(it.key(), it.value()));
        }
    }

    std::sort(lista.begin(), lista.end(), [](const QPair<QString, int>& a, const QPair<QString, int>& b) {
        if (a.second != b.second) return a.second > b.second;
        return a.first < b.first;
    });

    if (lista.size() > 5) {
        return lista.mid(0, 5);
    }
    return lista;
}

QList<QPair<QString, int>> ServicioEstadisticas::top5Grupos(const estructuras::Hipercubo5D* cubo) const {
    const estructuras::Hipercubo5D* c = cubo ? cubo : m_hipercubo;
    if (!c) return {};

    QMap<QString, int> conteoGrp = c->enrollar(estructuras::Hipercubo5D::DIM_GRUPO);
    QList<QPair<QString, int>> lista;
    for (auto it = conteoGrp.constBegin(); it != conteoGrp.constEnd(); ++it) {
        if (it.key() != "SIN_GRUPO") {
            lista.append(qMakePair(it.key(), it.value()));
        }
    }

    std::sort(lista.begin(), lista.end(), [](const QPair<QString, int>& a, const QPair<QString, int>& b) {
        if (a.second != b.second) return a.second > b.second;
        return a.first < b.first;
    });

    if (lista.size() > 5) {
        return lista.mid(0, 5);
    }
    return lista;
}

QMap<QString, double> ServicioEstadisticas::porcentajesPorCategoria(const estructuras::Hipercubo5D* cubo) const {
    QMap<QString, int> conteo = productosPorCategoria(cubo);
    int total = 0;
    for (int cnt : conteo) total += cnt;

    QMap<QString, double> resultado;
    for (auto it = conteo.constBegin(); it != conteo.constEnd(); ++it) {
        if (total == 0) {
            resultado.insert(it.key(), 0.0);
        } else {
            resultado.insert(it.key(), redondear2(it.value() * 100.0 / total));
        }
    }
    return resultado;
}

QMap<QString, double> ServicioEstadisticas::porcentajesPorValidacion(const estructuras::Hipercubo5D* cubo) const {
    QMap<QString, int> conteo = productosPorValidacion(cubo);
    int total = 0;
    for (int cnt : conteo) total += cnt;

    QMap<QString, double> resultado;
    for (auto it = conteo.constBegin(); it != conteo.constEnd(); ++it) {
        if (total == 0) {
            resultado.insert(it.key(), 0.0);
        } else {
            resultado.insert(it.key(), redondear2(it.value() * 100.0 / total));
        }
    }
    return resultado;
}

QJsonObject ServicioEstadisticas::obtenerVistaInstitucional(std::optional<int> ventanaAnios, bool modelo2024) const {
    estructuras::Hipercubo5D c = resolverCubo(nullptr, ventanaAnios, modelo2024);
    QJsonObject obj;
    obj["tipo_vista"] = "institucional";
    obj["total_productos"] = c.totalProductosUnicos();

    QJsonObject aniosObj;
    QMap<int, int> anios = productosPorAnio(&c);
    for (auto it = anios.constBegin(); it != anios.constEnd(); ++it) {
        aniosObj[QString::number(it.key())] = it.value();
    }
    obj["productos_por_anio"] = aniosObj;

    QJsonObject catObj;
    QMap<QString, int> cats = productosPorCategoria(&c);
    for (auto it = cats.constBegin(); it != cats.constEnd(); ++it) {
        catObj[it.key()] = it.value();
    }
    obj["productos_por_categoria"] = catObj;

    QJsonObject pctCatObj;
    QMap<QString, double> pctCats = porcentajesPorCategoria(&c);
    for (auto it = pctCats.constBegin(); it != pctCats.constEnd(); ++it) {
        pctCatObj[it.key()] = it.value();
    }
    obj["porcentajes_categoria"] = pctCatObj;

    QJsonObject valObj;
    QMap<QString, int> vals = productosPorValidacion(&c);
    for (auto it = vals.constBegin(); it != vals.constEnd(); ++it) {
        valObj[it.key()] = it.value();
    }
    obj["productos_por_validacion"] = valObj;

    QJsonObject pctValObj;
    QMap<QString, double> pctVals = porcentajesPorValidacion(&c);
    for (auto it = pctVals.constBegin(); it != pctVals.constEnd(); ++it) {
        pctValObj[it.key()] = it.value();
    }
    obj["porcentajes_validacion"] = pctValObj;

    QJsonArray topInvArr;
    for (const auto& par : top5Investigadores("", &c)) {
        QJsonObject invItem;
        invItem["investigador"] = par.first;
        invItem["cantidad"] = par.second;
        topInvArr.append(invItem);
    }
    obj["top_5_investigadores"] = topInvArr;

    QJsonArray topGrpArr;
    for (const auto& par : top5Grupos(&c)) {
        QJsonObject grpItem;
        grpItem["grupo"] = par.first;
        grpItem["cantidad"] = par.second;
        topGrpArr.append(grpItem);
    }
    obj["top_5_grupos"] = topGrpArr;
    obj["promedio_por_investigador"] = promedioPorInvestigador("", &c);

    return obj;
}

QJsonObject ServicioEstadisticas::obtenerVistaGrupo(const QString& idGrupo, std::optional<int> ventanaAnios, bool modelo2024) const {
    estructuras::Hipercubo5D cInst = resolverCubo(nullptr, ventanaAnios, modelo2024);
    estructuras::Hipercubo5D cGrp = cInst.rebanada(estructuras::Hipercubo5D::DIM_GRUPO, idGrupo);

    int totGrp = cGrp.totalProductosUnicos();
    int totInst = cInst.totalProductosUnicos();
    double pctInst = totInst > 0 ? redondear2(totGrp * 100.0 / totInst) : 0.0;

    QJsonObject obj;
    obj["tipo_vista"] = "grupo";
    obj["id_grupo"] = idGrupo;
    obj["total_productos"] = totGrp;
    obj["porcentaje_sobre_institucion"] = pctInst;

    QJsonObject aniosObj;
    QMap<int, int> anios = productosPorAnio(&cGrp);
    for (auto it = anios.constBegin(); it != anios.constEnd(); ++it) {
        aniosObj[QString::number(it.key())] = it.value();
    }
    obj["productos_por_anio"] = aniosObj;

    QJsonObject catObj;
    QMap<QString, int> cats = productosPorCategoria(&cGrp);
    for (auto it = cats.constBegin(); it != cats.constEnd(); ++it) {
        catObj[it.key()] = it.value();
    }
    obj["productos_por_categoria"] = catObj;

    QJsonObject pctCatObj;
    QMap<QString, double> pctCats = porcentajesPorCategoria(&cGrp);
    for (auto it = pctCats.constBegin(); it != pctCats.constEnd(); ++it) {
        pctCatObj[it.key()] = it.value();
    }
    obj["porcentajes_categoria"] = pctCatObj;

    QJsonObject valObj;
    QMap<QString, int> vals = productosPorValidacion(&cGrp);
    for (auto it = vals.constBegin(); it != vals.constEnd(); ++it) {
        valObj[it.key()] = it.value();
    }
    obj["productos_por_validacion"] = valObj;

    QJsonObject pctValObj;
    QMap<QString, double> pctVals = porcentajesPorValidacion(&cGrp);
    for (auto it = pctVals.constBegin(); it != pctVals.constEnd(); ++it) {
        pctValObj[it.key()] = it.value();
    }
    obj["porcentajes_validacion"] = pctValObj;

    QJsonArray topInvArr;
    for (const auto& par : top5Investigadores(idGrupo, &cGrp)) {
        QJsonObject invItem;
        invItem["investigador"] = par.first;
        invItem["cantidad"] = par.second;
        topInvArr.append(invItem);
    }
    obj["top_5_investigadores"] = topInvArr;
    obj["promedio_por_investigador"] = promedioPorInvestigador(idGrupo, &cGrp);

    QJsonObject invsObj;
    QMap<QString, int> invs = productosPorInvestigador(&cGrp);
    for (auto it = invs.constBegin(); it != invs.constEnd(); ++it) {
        invsObj[it.key()] = it.value();
    }
    obj["investigadores"] = invsObj;

    return obj;
}

QJsonObject ServicioEstadisticas::obtenerVistaInvestigador(const QString& idInvestigador, std::optional<int> ventanaAnios, bool modelo2024) const {
    estructuras::Hipercubo5D cInst = resolverCubo(nullptr, ventanaAnios, modelo2024);
    estructuras::Hipercubo5D cInv = cInst.rebanada(estructuras::Hipercubo5D::DIM_INVESTIGADOR, idInvestigador);

    int totInv = cInv.totalProductosUnicos();
    QJsonObject obj;
    obj["tipo_vista"] = "investigador";
    obj["id_investigador"] = idInvestigador;
    obj["total_productos"] = totInv;

    QJsonObject aniosObj;
    QMap<int, int> anios = productosPorAnio(&cInv);
    for (auto it = anios.constBegin(); it != anios.constEnd(); ++it) {
        aniosObj[QString::number(it.key())] = it.value();
    }
    obj["productos_por_anio"] = aniosObj;

    QJsonObject catObj;
    QMap<QString, int> cats = productosPorCategoria(&cInv);
    for (auto it = cats.constBegin(); it != cats.constEnd(); ++it) {
        catObj[it.key()] = it.value();
    }
    obj["productos_por_categoria"] = catObj;

    QJsonObject pctCatObj;
    QMap<QString, double> pctCats = porcentajesPorCategoria(&cInv);
    for (auto it = pctCats.constBegin(); it != pctCats.constEnd(); ++it) {
        pctCatObj[it.key()] = it.value();
    }
    obj["porcentajes_categoria"] = pctCatObj;

    QJsonObject valObj;
    QMap<QString, int> vals = productosPorValidacion(&cInv);
    for (auto it = vals.constBegin(); it != vals.constEnd(); ++it) {
        valObj[it.key()] = it.value();
    }
    obj["productos_por_validacion"] = valObj;

    QJsonObject pctValObj;
    QMap<QString, double> pctVals = porcentajesPorValidacion(&cInv);
    for (auto it = pctVals.constBegin(); it != pctVals.constEnd(); ++it) {
        pctValObj[it.key()] = it.value();
    }
    obj["porcentajes_validacion"] = pctValObj;

    QJsonObject grpObj;
    QMap<QString, int> grps = cInv.enrollar(estructuras::Hipercubo5D::DIM_GRUPO);
    QJsonObject contribObj;

    for (auto it = grps.constBegin(); it != grps.constEnd(); ++it) {
        grpObj[it.key()] = it.value();
        if (it.key() != "SIN_GRUPO") {
            estructuras::Hipercubo5D cGrupo = cInst.rebanada(estructuras::Hipercubo5D::DIM_GRUPO, it.key());
            int totGrupo = cGrupo.totalProductosUnicos();
            double pct = totGrupo > 0 ? redondear2(it.value() * 100.0 / totGrupo) : 0.0;

            QJsonObject cItem;
            cItem["productos_propios_en_grupo"] = it.value();
            cItem["total_productos_grupo"] = totGrupo;
            cItem["porcentaje_aporte"] = pct;
            contribObj[it.key()] = cItem;
        }
    }
    obj["grupos_participacion"] = grpObj;
    obj["contribuciones_grupos"] = contribObj;

    return obj;
}

} // namespace pea::servicios
