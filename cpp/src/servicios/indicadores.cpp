#include "pea/servicios/indicadores.hpp"
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QRegularExpression>
#include <QSet>
#include <QMap>
#include <cmath>
#include <algorithm>
#include <stdexcept>

// La referencia explícita fuerza la inclusión del recurso en la biblioteca estática.
static void iniciar_recurso_modelo() { Q_INIT_RESOURCE(modelo); }

namespace pea::servicios {
namespace {
const QStringList CLAVES{"Nc.Top", "Nc.A", "Nc.B", "AP", "DPC", "Fr.A", "Fr.B", "Cohe", "Coop"};
QString normalizar(QString texto) {
    QString limpio;
    for (auto c : texto.toUpper().normalized(QString::NormalizationForm_D))
        if (c.category() != QChar::Mark_NonSpacing) limpio += c;
    limpio.replace(QRegularExpression("[^A-Z0-9]+"), "_");
    limpio.remove(QRegularExpression("^_+|_+$"));
    return limpio;
}
QJsonObject categoria(const QJsonObject& p) {
    QString codigo = p["detalles"].toObject()["categoria_minciencias"].toString();
    if (codigo.isEmpty()) codigo = p["subtipo"].toString();
    codigo = normalizar(codigo);
    codigo.replace(QRegularExpression("^ARTICULO(?:_DE_INVESTIGACION)?(?:_TIPO)?_"), "ART_");
    for (const auto& v : modelo_puntajes()["categorias"].toArray())
        if (v.toObject()["codigo"] == codigo) return v.toObject();
    return {};
}
// Año de una fecha AAAA o AAAA-MM; «Actual» o vacío no son años.
std::optional<int> anio_de(const QString& valor) {
    const auto texto = valor.left(4);
    bool ok = false;
    const int anio = texto.toInt(&ok);
    return (texto.size() == 4 && ok) ? std::optional<int>(anio) : std::nullopt;
}
bool vinculado(const QJsonObject& m, int anio) {
    const auto inicio = anio_de(m["fecha_inicio"].toString());
    const auto fin = anio_de(m["fecha_fin"].toString());
    return (!inicio || *inicio <= anio) && (!fin || *fin >= anio) && (m["activo"].toBool(true) || fin.has_value());
}
// Supuesto conservador y declarado: sin calidad publicada se usa la categoría de
// menor peso de la tipología. Nunca sustituye una categoría informada.
using Supuesta = std::pair<QString, QString>;
std::optional<Supuesta> categoria_estimada(const QJsonObject& p) {
    if (!categoria(p).isEmpty()) return std::nullopt;
    auto subtipo = normalizar(p["subtipo"].toString());
    if (subtipo == "TRABAJODIRIGIDO") subtipo = "TRABAJO_DIRIGIDO";  // etiqueta de catálogos antiguos
    if (subtipo == "ARTICULO") return Supuesta{"ART_D", "Artículo sin cuartil publicado: categoría base ART_D."};
    if (subtipo == "LIBRO") return Supuesta{"LIB_C", "Libro sin calidad publicada: categoría base LIB_C."};
    if (subtipo == "CAPITULO") return Supuesta{"CAP_LIB_C", "Capítulo sin calidad publicada: categoría base CAP_LIB_C."};
    if (subtipo == "SOFTWARE") return Supuesta{"SF", "Software sin registro verificable: categoría base SF."};
    if (subtipo == "TRABAJO_DIRIGIDO") {
        const auto texto = normalizar(p["detalles"].toObject()["referencia_original"].toString() + " " + p["titulo"].toString());
        if (texto.contains("EN_CURSO") || texto.contains("EN_EJECUCION")) return std::nullopt;
        if (texto.contains("DOCTORA")) return Supuesta{"TD_B", "Tesis doctoral sin calificación: categoría base TD_B."};
        if (texto.contains("MAESTRIA") || texto.contains("MAGISTER"))
            return Supuesta{"TM_B", "Trabajo de maestría sin calificación: categoría base TM_B."};
        return Supuesta{"TP_B", "Trabajo de grado sin calificación: categoría base TP_B."};
    }
    return std::nullopt;
}
QJsonObject aplicar_estimacion(const QJsonObject& datos, QJsonArray& estimadas) {
    QJsonArray productos;
    for (const auto& v : datos["productos"].toArray()) {
        auto p = v.toObject();
        if (auto supuesta = categoria_estimada(p)) {
            auto detalles = p["detalles"].toObject();
            detalles["categoria_minciencias"] = supuesta->first;
            detalles["categoria_estimada"] = true;
            p["detalles"] = detalles;
            estimadas.append(QJsonObject{{"codigo", p["codigo_identificador"]}, {"categoria", supuesta->first},
                                         {"regla", supuesta->second}});
        }
        productos.append(p);
    }
    auto copia = datos;
    copia["productos"] = productos;
    return copia;
}
QJsonObject componentes(const QJsonObject& datos, const QString& ambito, const QString& codigo,
                       int corte, std::optional<int> desde) {
    QJsonObject brutos;
    for (const auto& k : CLAVES) brutos[k] = 0.0;
    QJsonObject entidad;
    for (const auto& v : datos[ambito == "grupo" ? "grupos" : "investigadores"].toArray())
        if (v.toObject()[ambito == "grupo" ? "codigo_gruplac" : "codigo_rh"] == codigo) entidad = v.toObject();
    if (entidad.isEmpty()) throw std::invalid_argument("No existe el grupo o investigador solicitado.");
    int edad = 0;
    if (ambito == "grupo" && !entidad["fecha_creacion"].toString().isEmpty()) {
        edad = corte - entidad["fecha_creacion"].toString().left(4).toInt() + 1;
        if (edad <= 0) throw std::invalid_argument("El corte precede a la creación del grupo.");
    }
    QMap<QString, QJsonObject> relaciones;
    for (const auto& r : datos["relaciones"].toArray()) relaciones[r.toObject()["codigo_identificador"].toString()] = r.toObject();
    QMap<QString, int> conteos, periodos;
    QJsonArray incluidos, excluidos, por_subtipo;
    int autores_total = 0, grupos_total = 0, productos_colab = 0;
    bool completa = true;
    QMap<QString, QJsonObject> productos;
    for (const auto& v : datos["productos"].toArray()) productos[v.toObject()["codigo_identificador"].toString()] = v.toObject();
    for (const auto& p : productos) {
        auto rel = relaciones[p["codigo_identificador"].toString()];
        QSet<QString> autores;
        for (const auto& a : rel["autores"].toArray()) autores.insert(a.toString());
        if ((ambito == "grupo" && rel["grupo"] != codigo) || (ambito == "investigador" && !autores.contains(codigo))) continue;
        const int anio = p["ano"].toInt();
        if (!p["activo"].toBool(true) || anio > corte || (desde && anio < *desde)) continue;
        auto regla = categoria(p);
        auto puntos = puntaje_producto(p);
        auto motivo = puntos["motivo"].toString();
        if (p["estado_validacion"] != "Avalado") motivo = "El producto no está avalado.";
        int periodo = 0;
        if (!regla.isEmpty()) {
            periodo = std::min({regla["ventana"].toInt(), desde ? corte - *desde + 1 : regla["ventana"].toInt(), edad ? edad : regla["ventana"].toInt()});
            if (anio < corte - periodo + 1) continue;
        }
        if (!motivo.isEmpty()) {
            excluidos.append(QJsonObject{{"codigo", p["codigo_identificador"]}, {"titulo", p["titulo"]}, {"motivo", motivo}});
            continue;
        }
        const auto cat = regla["codigo"].toString();
        conteos[cat]++;
        periodos[cat] = periodo;
        puntos["codigo"] = p["codigo_identificador"]; puntos["titulo"] = p["titulo"]; puntos["periodo"] = periodo;
        incluidos.append(puntos);
        if (p["tipo_mayor"] == "GNC" || p["tipo_mayor"] == "DTI") {
            productos_colab++;
            QSet<QString> miembros, grupos;
            for (const auto& v : datos["integrantes"].toArray()) {
                auto m = v.toObject();
                if (!vinculado(m, anio)) continue;
                if (m["codigo_gruplac"] == rel["grupo"]) miembros.insert(m["codigo_rh"].toString());
                if (autores.contains(m["codigo_rh"].toString())) grupos.insert(m["codigo_gruplac"].toString());
            }
            if (!rel["grupo"].toString().isEmpty()) grupos.insert(rel["grupo"].toString());
            auto internos = ambito == "grupo" ? (autores & miembros) : autores;
            if (internos.isEmpty() || grupos.isEmpty()) completa = false;
            autores_total += internos.size(); grupos_total += grupos.size();
        }
    }
    for (auto it = conteos.cbegin(); it != conteos.cend(); ++it) {
        auto regla = categoria(QJsonObject{{"subtipo", it.key()}});
        auto peso = regla["peso_base"].toDouble() * regla["peso_relativo"].toDouble();
        auto valor = std::log1p(static_cast<double>(it.value()) / periodos[it.key()]) * peso;
        const auto clase = regla["clase"].toString();
        brutos[clase] = brutos[clase].toDouble() + valor;
        por_subtipo.append(QJsonObject{{"categoria", it.key()}, {"cantidad", it.value()}, {"periodo", periodos[it.key()]},
                                      {"peso_relativo", regla["peso_relativo"]}, {"puntaje_unitario", peso}, {"indicador", valor}});
    }
    if (productos_colab) {
        brutos["Cohe"] = std::max(0.0, static_cast<double>(autores_total) / productos_colab - 1);
        brutos["Coop"] = std::max(0.0, static_cast<double>(grupos_total) / productos_colab - 1);
    }
    return {{"codigo", codigo}, {"nombre", entidad["nombre"].toString(entidad["nombre_completo"].toString(codigo))},
            {"periodo_completo", ambito != "grupo" || edad > 0},
            {"area", entidad.contains("gran_area_ocde") ? entidad["gran_area_ocde"] : QJsonValue(QJsonValue::Null)}, {"brutos", brutos}, {"por_subtipo", por_subtipo},
            {"incluidos", incluidos}, {"excluidos", excluidos}, {"colaboracion_completa", completa}};
}
}

QJsonObject modelo_puntajes() {
    static QJsonObject modelo = [] {
        iniciar_recurso_modelo();
        QFile f(":/pea/modelo_2024.json");
        if (!f.open(QIODevice::ReadOnly)) throw std::runtime_error("Falta el catálogo del Modelo 2024.");
        auto obj = QJsonDocument::fromJson(f.readAll()).object();
        if (obj.isEmpty()) throw std::runtime_error("Catálogo del Modelo inválido.");
        return obj;
    }();
    return modelo;
}

QJsonObject puntaje_producto(const QJsonObject& p) {
    auto r = categoria(p);
    if (r.isEmpty()) return {{"categoria", QJsonValue::Null}, {"peso_relativo", QJsonValue::Null},
                            {"puntaje", QJsonValue::Null}, {"clase", QJsonValue::Null}, {"motivo", "Falta una categoría de calidad del Modelo 2024."}};
    if (p["tipo_mayor"] != r["tipo_mayor"]) return {{"categoria", r["codigo"]}, {"peso_relativo", QJsonValue::Null},
        {"puntaje", QJsonValue::Null}, {"clase", QJsonValue::Null}, {"motivo", "La categoría de calidad contradice la tipología mayor."}};
    return {{"categoria", r["codigo"]}, {"peso_relativo", r["peso_relativo"]},
            {"puntaje", r["peso_base"].toDouble() * r["peso_relativo"].toDouble()}, {"clase", r["clase"]}, {"motivo", ""}};
}

QJsonObject calcular_indicador(const QJsonObject& datos_originales, const QString& ambito, const QString& codigo,
                              int corte, std::optional<int> desde, const QJsonObject& referencia, bool estimar) {
    if (ambito != "grupo" && ambito != "investigador") throw std::invalid_argument("Ámbito inválido.");
    if (corte < 1970 || corte > 2100 || (desde && (*desde < 1970 || *desde > corte))) throw std::invalid_argument("Rango inválido.");
    QJsonArray estimadas_todas;
    const QJsonObject datos = estimar ? aplicar_estimacion(datos_originales, estimadas_todas) : datos_originales;
    auto resultado = componentes(datos, ambito, codigo, corte, desde);
    QJsonObject maximos;
    QString procedencia;
    if (referencia.isEmpty()) {
        QSet<QString> codigos{codigo};
        auto area = resultado["area"].toString();
        for (const auto& v : datos[ambito == "grupo" ? "grupos" : "investigadores"].toArray()) {
            auto e = v.toObject();
            if (e["activo"].toBool(true) && (ambito != "grupo" || e["fecha_creacion"].toString().isEmpty() || e["fecha_creacion"].toString().left(4).toInt() <= corte) &&
                (ambito != "grupo" || area.isEmpty() || e["gran_area_ocde"] == area))
                codigos.insert(e[ambito == "grupo" ? "codigo_gruplac" : "codigo_rh"].toString());
        }
        for (const auto& c : codigos) {
            auto brutos = componentes(datos, ambito, c, corte, desde)["brutos"].toObject();
            for (const auto& k : CLAVES) maximos[k] = std::max(maximos[k].toDouble(), brutos[k].toDouble());
        }
        procedencia = QString("Catálogo local: %1 %2(s)").arg(codigos.size()).arg(ambito);
        if (!area.isEmpty()) procedencia += "; área " + area;
    } else {
        maximos = referencia["maximos"].toObject();
        if (maximos.size() != CLAVES.size() || referencia["fuente"].toString().trimmed().isEmpty())
            throw std::invalid_argument("La referencia requiere fuente y los nueve máximos.");
        if (referencia["corte"].toInt() != corte || (desde ? referencia["desde"].toInt(-1) != *desde : !referencia["desde"].isNull()))
            throw std::invalid_argument("La referencia no corresponde al rango temporal.");
        procedencia = referencia["fuente"].toString();
    }
    QJsonArray filas, avisos;
    auto coefs = modelo_puntajes()["coeficientes"].toObject();
    double total = 0;
    for (const auto& k : CLAVES) {
        auto m = maximos[k];
        auto bruto = resultado["brutos"].toObject()[k].toDouble();
        if (!m.isDouble() || !std::isfinite(m.toDouble()) || m.toDouble() < 0 || m.toDouble() + 1e-9 < bruto)
            throw std::invalid_argument("Máximo de referencia inválido o menor que el indicador observado.");
        auto indice = m.toDouble() ? bruto / m.toDouble() : 0.0;
        auto aporte = indice * coefs[k].toDouble(); total += aporte;
        filas.append(QJsonObject{{"componente", k}, {"bruto", bruto}, {"maximo", m}, {"indice", indice}, {"coeficiente", coefs[k]}, {"aporte", aporte}});
    }
    QSet<QString> usadas;
    for (const auto& v : resultado["incluidos"].toArray()) usadas.insert(v.toObject()["codigo"].toString());
    QJsonArray estimadas;
    for (const auto& v : estimadas_todas)
        if (usadas.contains(v.toObject()["codigo"].toString())) estimadas.append(v);
    if (!estimadas.isEmpty())
        avisos.append(QString("%1 productos puntuados con categoría estimada (la de menor peso de su tipología); "
                              "el cuartil o nivel real exige los soportes del Modelo.").arg(estimadas.size()));
    const auto n = resultado["excluidos"].toArray().size();
    if (n) avisos.append(QString("%1 productos excluidos por categoría o validación insuficientes.").arg(n));
    if (!resultado["colaboracion_completa"].toBool()) avisos.append("Faltan autorías o vínculos históricos para completar cohesión/cooperación.");
    if (!resultado["periodo_completo"].toBool()) avisos.append("Se desconoce la antigüedad del grupo: cálculo parcial con la ventana de cada subtipo.");
    if (referencia.isEmpty()) avisos.append("Comparación del catálogo cargado; no representa la clasificación nacional de Minciencias.");
    if (ambito == "investigador") avisos.append("Adaptación del parcial: misma fórmula sobre sus productos; cohesión usa todos sus coautores.");
    resultado["ambito"] = ambito; resultado["corte"] = corte; resultado["desde"] = desde ? QJsonValue(*desde) : QJsonValue(QJsonValue::Null);
    resultado["modelo"] = modelo_puntajes()["version"]; resultado["referencia"] = procedencia;
    resultado["maximos"] = maximos; resultado["componentes"] = filas; resultado["indicador"] = total;
    resultado["estimado"] = !estimadas.isEmpty(); resultado["estimadas"] = estimadas;
    resultado["completo"] = !n && estimadas.isEmpty() && resultado["colaboracion_completa"].toBool() && resultado["periodo_completo"].toBool(); resultado["avisos"] = avisos;
    return resultado;
}
}
