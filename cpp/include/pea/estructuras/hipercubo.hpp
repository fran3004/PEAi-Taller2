#pragma once

#include <cstddef>
#include <optional>
#include <utility>
#include <QHash>
#include <QList>
#include <QMap>
#include <QPair>
#include <QSet>
#include <QString>
#include <QStringList>
#include "pea/estructuras/lista_doble.hpp"
#include "pea/estructuras/multilista.hpp"

namespace pea::estructuras {

struct Coordenada5D {
    QString grupo;
    QString investigador;
    QString categoria;
    int anio{0};
    QString validacion;

    Coordenada5D() = default;
    Coordenada5D(QString grp, QString inv, QString cat, int a, QString val)
        : grupo(std::move(grp)),
          investigador(std::move(inv)),
          categoria(std::move(cat)),
          anio(a),
          validacion(std::move(val)) {}

    bool operator==(const Coordenada5D& o) const noexcept {
        return anio == o.anio &&
               grupo == o.grupo &&
               investigador == o.investigador &&
               categoria == o.categoria &&
               validacion == o.validacion;
    }

    bool operator<(const Coordenada5D& o) const noexcept {
        if (anio != o.anio) return anio < o.anio;
        if (grupo != o.grupo) return grupo < o.grupo;
        if (investigador != o.investigador) return investigador < o.investigador;
        if (categoria != o.categoria) return categoria < o.categoria;
        return validacion < o.validacion;
    }
};

inline size_t qHash(const Coordenada5D& c, size_t seed = 0) noexcept {
    return qHashMulti(seed, c.grupo, c.investigador, c.categoria, c.anio, c.validacion);
}

class CeldaHipercubo {
public:
    Coordenada5D coordenada;
    int cantidad{0};
    double peso_ponderado{0.0};
    ListaDoble<QString> productos_ids;

    CeldaHipercubo() = default;
    explicit CeldaHipercubo(Coordenada5D coord, int cant = 0, double peso = 0.0)
        : coordenada(std::move(coord)), cantidad(cant), peso_ponderado(peso) {}

    bool agregarProductoId(const QString& pid) {
        if (pid.isEmpty()) return false;
        const auto* existe = productos_ids.buscar([&pid](const QString& p) { return p == pid; });
        if (!existe) {
            productos_ids.insertar_final(pid);
            return true;
        }
        return false;
    }

    bool removerProductoId(const QString& pid) {
        if (pid.isEmpty()) return false;
        return productos_ids.eliminar_por_criterio([&pid](const QString& p) { return p == pid; });
    }
};

class Hipercubo5D {
public:
    static constexpr const char* DIM_GRUPO = "grupo";
    static constexpr const char* DIM_INVESTIGADOR = "investigador";
    static constexpr const char* DIM_CATEGORIA = "categoria";
    static constexpr const char* DIM_ANIO = "anio";
    static constexpr const char* DIM_VALIDACION = "validacion";

    Hipercubo5D() = default;

    Hipercubo5D(const Hipercubo5D& otro) {
        copiarDesde(otro);
    }

    Hipercubo5D& operator=(const Hipercubo5D& otro) {
        if (this != &otro) {
            limpiar();
            copiarDesde(otro);
        }
        return *this;
    }

    Hipercubo5D(Hipercubo5D&& otro) noexcept = default;
    Hipercubo5D& operator=(Hipercubo5D&& otro) noexcept = default;
    ~Hipercubo5D() = default;

    [[nodiscard]] std::size_t tamano() const noexcept { return m_celdas.tamano(); }
    [[nodiscard]] bool estaVacio() const noexcept { return m_celdas.esta_vacia(); }

    void limpiar() {
        m_celdas.limpiar();
        m_indice.clear();
        m_productos_registrados.clear();
    }

    void acumular(
        const QString& grupo,
        const QString& investigador,
        const QString& categoria,
        int anio,
        const QString& validacion,
        const QString& productoId = "",
        double peso = 1.0
    ) {
        QString grp = grupo.isEmpty() ? "SIN_GRUPO" : grupo;
        QString inv = investigador.isEmpty() ? "SIN_INVESTIGADOR" : investigador;
        QString cat = categoria.isEmpty() ? "GNC" : categoria;
        QString val = validacion.isEmpty() ? "No avalado" : validacion;
        QString pid = productoId.trimmed();

        Coordenada5D coord(grp, inv, cat, anio, val);

        if (!pid.isEmpty()) {
            QString claveReg = pid + "|" + grp + "|" + inv + "|" + cat + "|" + QString::number(anio) + "|" + val;
            if (m_productos_registrados.contains(claveReg)) {
                return;
            }
            m_productos_registrados.insert(claveReg);
        }

        auto it = m_indice.find(coord);
        if (it == m_indice.end()) {
            CeldaHipercubo celda(coord, 1, peso);
            if (!pid.isEmpty()) {
                celda.agregarProductoId(pid);
            }
            auto* nodo = m_celdas.insertar_final(std::move(celda));
            m_indice.insert(coord, &(nodo->dato));
        } else {
            CeldaHipercubo* celdaPtr = it.value();
            celdaPtr->cantidad++;
            celdaPtr->peso_ponderado += peso;
            if (!pid.isEmpty()) {
                celdaPtr->agregarProductoId(pid);
            }
        }
    }

    bool desacumular(
        const QString& grupo,
        const QString& investigador,
        const QString& categoria,
        int anio,
        const QString& validacion,
        const QString& productoId = "",
        double peso = 1.0
    ) {
        QString grp = grupo.isEmpty() ? "SIN_GRUPO" : grupo;
        QString inv = investigador.isEmpty() ? "SIN_INVESTIGADOR" : investigador;
        QString cat = categoria.isEmpty() ? "GNC" : categoria;
        QString val = validacion.isEmpty() ? "No avalado" : validacion;
        QString pid = productoId.trimmed();

        Coordenada5D coord(grp, inv, cat, anio, val);

        if (!pid.isEmpty()) {
            QString claveReg = pid + "|" + grp + "|" + inv + "|" + cat + "|" + QString::number(anio) + "|" + val;
            m_productos_registrados.remove(claveReg);
        }

        auto it = m_indice.find(coord);
        if (it == m_indice.end()) {
            return false;
        }

        CeldaHipercubo* celdaPtr = it.value();
        celdaPtr->cantidad--;
        celdaPtr->peso_ponderado = std::max(0.0, celdaPtr->peso_ponderado - peso);
        if (!pid.isEmpty()) {
            celdaPtr->removerProductoId(pid);
        }

        if (celdaPtr->cantidad <= 0) {
            m_indice.erase(it);
            m_celdas.eliminar_por_criterio([&coord](const CeldaHipercubo& c) {
                return c.coordenada == coord;
            });
        }

        return true;
    }

    [[nodiscard]] int medidaTotal() const noexcept {
        int total = 0;
        for (const auto& celda : m_celdas) {
            total += celda.cantidad;
        }
        return total;
    }

    [[nodiscard]] int totalProductosUnicos() const noexcept {
        QSet<QString> unicos;
        for (const auto& celda : m_celdas) {
            for (const auto& pid : celda.productos_ids) {
                unicos.insert(pid);
            }
        }
        if (unicos.isEmpty()) {
            return medidaTotal();
        }
        return static_cast<int>(unicos.size());
    }

    [[nodiscard]] Hipercubo5D rebanada(const QString& dimension, const QString& valor) const {
        Hipercubo5D nuevo;
        QString dim = dimension.toLower().trimmed();

        for (const auto& celda : m_celdas) {
            const auto& c = celda.coordenada;
            bool coincide = false;

            if (dim == DIM_GRUPO && c.grupo == valor) coincide = true;
            else if (dim == DIM_INVESTIGADOR && c.investigador == valor) coincide = true;
            else if (dim == DIM_CATEGORIA && c.categoria == valor) coincide = true;
            else if (dim == DIM_ANIO && QString::number(c.anio) == valor) coincide = true;
            else if (dim == DIM_VALIDACION && c.validacion == valor) coincide = true;

            if (coincide) {
                double pesoUnitario = (celda.cantidad > 0) ? (celda.peso_ponderado / celda.cantidad) : 1.0;
                if (celda.productos_ids.tamano() > 0) {
                    for (const auto& pid : celda.productos_ids) {
                        nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, pid, pesoUnitario);
                    }
                } else {
                    for (int i = 0; i < celda.cantidad; ++i) {
                        nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, "", pesoUnitario);
                    }
                }
            }
        }
        return nuevo;
    }

    [[nodiscard]] Hipercubo5D subcuboPorVentana(
        std::optional<int> anioInicio,
        std::optional<int> anioFin,
        const QStringList& cats = {},
        const QStringList& grupos = {},
        const QStringList& invs = {},
        const QStringList& vals = {}
    ) const {
        Hipercubo5D nuevo;
        QSet<QString> setCats(cats.begin(), cats.end());
        QSet<QString> setGrps(grupos.begin(), grupos.end());
        QSet<QString> setInvs(invs.begin(), invs.end());
        QSet<QString> setVals(vals.begin(), vals.end());

        for (const auto& celda : m_celdas) {
            const auto& c = celda.coordenada;

            if (anioInicio.has_value() && c.anio < *anioInicio) continue;
            if (anioFin.has_value() && c.anio > *anioFin) continue;
            if (!setCats.isEmpty() && !setCats.contains(c.categoria)) continue;
            if (!setGrps.isEmpty() && !setGrps.contains(c.grupo)) continue;
            if (!setInvs.isEmpty() && !setInvs.contains(c.investigador)) continue;
            if (!setVals.isEmpty() && !setVals.contains(c.validacion)) continue;

            double pesoUnitario = (celda.cantidad > 0) ? (celda.peso_ponderado / celda.cantidad) : 1.0;
            if (celda.productos_ids.tamano() > 0) {
                for (const auto& pid : celda.productos_ids) {
                    nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, pid, pesoUnitario);
                }
            } else {
                for (int i = 0; i < celda.cantidad; ++i) {
                    nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, "", pesoUnitario);
                }
            }
        }
        return nuevo;
    }

    [[nodiscard]] Hipercubo5D subcuboModelo2024(int anioCorte = 2023) const {
        int inicio5 = anioCorte - 4;
        int inicio10 = anioCorte - 9;
        Hipercubo5D nuevo;

        for (const auto& celda : m_celdas) {
            const auto& c = celda.coordenada;
            if (c.anio > anioCorte) continue;

            bool esAmpliada = false;
            QString catUpper = c.categoria.toUpper();
            if (catUpper.contains("LIBRO") || catUpper.contains("PATENTE") || catUpper.contains("VARIEDAD")) {
                esAmpliada = true;
            }

            int inicioVigente = esAmpliada ? inicio10 : inicio5;
            if (c.anio < inicioVigente) continue;

            double pesoUnitario = (celda.cantidad > 0) ? (celda.peso_ponderado / celda.cantidad) : 1.0;
            if (celda.productos_ids.tamano() > 0) {
                for (const auto& pid : celda.productos_ids) {
                    nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, pid, pesoUnitario);
                }
            } else {
                for (int i = 0; i < celda.cantidad; ++i) {
                    nuevo.acumular(c.grupo, c.investigador, c.categoria, c.anio, c.validacion, "", pesoUnitario);
                }
            }
        }
        return nuevo;
    }

    [[nodiscard]] QMap<QString, int> enrollar(const QString& dimension) const {
        QString dim = dimension.toLower().trimmed();
        QMap<QString, QSet<QString>> agrupacionIds;
        QMap<QString, int> conteoSinId;

        for (const auto& celda : m_celdas) {
            const auto& c = celda.coordenada;
            QString clave;
            if (dim == DIM_GRUPO) clave = c.grupo;
            else if (dim == DIM_INVESTIGADOR) clave = c.investigador;
            else if (dim == DIM_CATEGORIA) clave = c.categoria;
            else if (dim == DIM_ANIO) clave = QString::number(c.anio);
            else if (dim == DIM_VALIDACION) clave = c.validacion;
            else clave = "TODOS";

            if (celda.productos_ids.tamano() > 0) {
                for (const auto& pid : celda.productos_ids) {
                    agrupacionIds[clave].insert(pid);
                }
            } else {
                conteoSinId[clave] += celda.cantidad;
            }
        }

        QMap<QString, int> resultado;
        QSet<QString> todasLasClaves;
        for (auto it = agrupacionIds.keyBegin(); it != agrupacionIds.keyEnd(); ++it) {
            todasLasClaves.insert(*it);
        }
        for (auto it = conteoSinId.keyBegin(); it != conteoSinId.keyEnd(); ++it) {
            todasLasClaves.insert(*it);
        }

        for (const auto& k : todasLasClaves) {
            int cnt = agrupacionIds.contains(k) ? static_cast<int>(agrupacionIds[k].size()) : 0;
            cnt += conteoSinId.value(k, 0);
            resultado.insert(k, cnt);
        }
        return resultado;
    }

    [[nodiscard]] QMap<int, int> enrollarAnio() const {
        QMap<int, QSet<QString>> agrupacionIds;
        QMap<int, int> conteoSinId;

        for (const auto& celda : m_celdas) {
            int anio = celda.coordenada.anio;
            if (celda.productos_ids.tamano() > 0) {
                for (const auto& pid : celda.productos_ids) {
                    agrupacionIds[anio].insert(pid);
                }
            } else {
                conteoSinId[anio] += celda.cantidad;
            }
        }

        QMap<int, int> resultado;
        QSet<int> anios;
        for (auto it = agrupacionIds.keyBegin(); it != agrupacionIds.keyEnd(); ++it) anios.insert(*it);
        for (auto it = conteoSinId.keyBegin(); it != conteoSinId.keyEnd(); ++it) anios.insert(*it);

        for (int a : anios) {
            int cnt = agrupacionIds.contains(a) ? static_cast<int>(agrupacionIds[a].size()) : 0;
            cnt += conteoSinId.value(a, 0);
            resultado.insert(a, cnt);
        }
        return resultado;
    }

    void poblarDesdeMultilista(const Multilista& multilista) {
        limpiar();

        for (const auto* nodo = multilista.cabeza(); nodo != nullptr; nodo = nodo->siguiente_global) {
            if (!nodo->activo() || !nodo->producto) continue;

            QString grp = nodo->grupo ? nodo->grupo->codigo_gruplac : "SIN_GRUPO";
            QString cat = nodo->producto->tipo_mayor.isEmpty() ? "GNC" : nodo->producto->tipo_mayor;
            QString sub = nodo->producto->subtipo;
            int anio = nodo->producto->ano;
            QString val = nodo->producto->estado_validacion.isEmpty() ? "No avalado" : nodo->producto->estado_validacion;
            QString pid = nodo->producto->codigo_identificador;

            QString catCubo = cat;
            if (sub.contains("LIB", Qt::CaseInsensitive)) {
                catCubo = "GNC_LIBRO";
            } else if (sub.contains("PA", Qt::CaseInsensitive) || sub.contains("PATENTE", Qt::CaseInsensitive)) {
                catCubo = "GNC_PATENTE";
            }

            if (nodo->autores.tamano() > 0) {
                for (const auto& autor : nodo->autores) {
                    QString inv = autor ? autor->codigo_rh : "SIN_INVESTIGADOR";
                    acumular(grp, inv, catCubo, anio, val, pid, 1.0);
                }
            } else {
                acumular(grp, "SIN_INVESTIGADOR", catCubo, anio, val, pid, 1.0);
            }
        }
    }

private:
    ListaDoble<CeldaHipercubo> m_celdas;
    QHash<Coordenada5D, CeldaHipercubo*> m_indice;
    QSet<QString> m_productos_registrados;

    void copiarDesde(const Hipercubo5D& otro) {
        for (const auto& celda : otro.m_celdas) {
            double pesoUnitario = (celda.cantidad > 0) ? (celda.peso_ponderado / celda.cantidad) : 1.0;
            if (celda.productos_ids.tamano() > 0) {
                for (const auto& pid : celda.productos_ids) {
                    acumular(celda.coordenada.grupo, celda.coordenada.investigador,
                             celda.coordenada.categoria, celda.coordenada.anio,
                             celda.coordenada.validacion, pid, pesoUnitario);
                }
            } else {
                for (int i = 0; i < celda.cantidad; ++i) {
                    acumular(celda.coordenada.grupo, celda.coordenada.investigador,
                             celda.coordenada.categoria, celda.coordenada.anio,
                             celda.coordenada.validacion, "", pesoUnitario);
                }
            }
        }
    }
};

} // namespace pea::estructuras
