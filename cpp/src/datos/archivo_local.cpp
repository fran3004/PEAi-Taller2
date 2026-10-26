#include "pea/datos/archivo_local.hpp"
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QSaveFile>
#include <QSet>
#include <QRegularExpression>
#include <stdexcept>

namespace pea::datos {
namespace {
// SCIENTI publica AAAA/M o AAAA-MM además de fechas ISO; «Actual» marca un vínculo vigente.
bool fecha_vinculo_valida(const QString& fecha) {
    static const QRegularExpression patron(
        QStringLiteral("^(?:\\d{4}(?:[-/]\\d{1,2}(?:[-/]\\d{1,2})?)?|actual)$"),
        QRegularExpression::CaseInsensitiveOption);
    return patron.match(fecha.trimmed()).hasMatch();
}
}  // namespace

QJsonObject serializar_catalogo(const servicios::CatalogoInvestigacion& cat) {
    QJsonArray grupos, investigadores, integrantes, productos, relaciones;
    for (const auto& g : cat.grupos) grupos.append(g->aJson());
    for (const auto& i : cat.investigadores) investigadores.append(i->aJson());
    for (const auto& m : cat.integrantes) integrantes.append(m.aJson());
    for (auto* n = cat.multilista_productos.cabeza(); n; n = n->siguiente_global) {
        productos.append(n->producto->aJson());
        QJsonArray autores;
        for (const auto& a : n->autores) autores.append(a->codigo_rh);
        relaciones.append(QJsonObject{{"codigo_identificador", n->producto->codigo_identificador},
                                     {"grupo", n->grupo ? QJsonValue(n->grupo->codigo_gruplac) : QJsonValue(QJsonValue::Null)},
                                     {"autores", autores}});
    }
    return {{"formato", "pea-catalogo"}, {"version", 1}, {"grupos", grupos},
            {"investigadores", investigadores}, {"integrantes", integrantes},
            {"productos", productos}, {"relaciones", relaciones}};
}

servicios::CatalogoInvestigacion restaurar_catalogo(const QJsonObject& datos) {
    if (datos["formato"] != "pea-catalogo" || datos["version"] != 1)
        throw std::invalid_argument("Formato o versión de archivo local no admitidos.");
    for (const auto* k : {"grupos", "investigadores", "integrantes", "productos", "relaciones"})
        if (!datos[k].isArray()) throw std::invalid_argument("Faltan colecciones del archivo local.");
    servicios::CatalogoInvestigacion cat;
    for (const auto& v : datos["grupos"].toArray()) {
        auto g = std::make_shared<dominio::Grupo>(dominio::Grupo::desdeJson(v.toObject()));
        if (g->codigo_gruplac.isEmpty() || g->nombre.isEmpty() || cat.buscar_grupo(g->codigo_gruplac))
            throw std::invalid_argument("Grupo inválido o duplicado.");
        cat.grupos.insertar_final(g);
    }
    for (const auto& v : datos["investigadores"].toArray()) {
        auto i = std::make_shared<dominio::Investigador>(dominio::Investigador::desdeJson(v.toObject()));
        if (i->codigo_rh.isEmpty() || i->nombre_completo.isEmpty() || cat.buscar_investigador(i->codigo_rh))
            throw std::invalid_argument("Investigador inválido o duplicado.");
        cat.investigadores.insertar_final(i);
    }
    QSet<QString> miembros;
    for (const auto& v : datos["integrantes"].toArray()) {
        auto m = dominio::IntegranteGrupo::desdeJson(v.toObject());
        auto clave = m.codigo_gruplac + "\n" + m.codigo_rh;
        if (!cat.buscar_grupo(m.codigo_gruplac) || !cat.buscar_investigador(m.codigo_rh) || miembros.contains(clave))
            throw std::invalid_argument("Membresía inexistente o duplicada.");
        for (const auto& f : {m.fecha_inicio, m.fecha_fin})
            if (!f.isEmpty() && !fecha_vinculo_valida(f))
                throw std::invalid_argument("Fecha de membresía inválida.");
        miembros.insert(clave);
        cat.integrantes.insertar_final(m);
    }
    QMap<QString, QJsonObject> relaciones;
    for (const auto& v : datos["relaciones"].toArray()) {
        const auto r = v.toObject();
        const auto codigo = r["codigo_identificador"].toString();
        if (codigo.isEmpty() || relaciones.contains(codigo)) throw std::invalid_argument("Relación duplicada o inválida.");
        relaciones[codigo] = r;
    }
    if (relaciones.size() != datos["productos"].toArray().size())
        throw std::invalid_argument("Relaciones de producto incompletas.");
    for (const auto& v : datos["productos"].toArray()) {
        auto p = std::make_shared<dominio::Producto>(dominio::Producto::desdeJson(v.toObject()));
        if (p->codigo_identificador.isEmpty() || p->titulo.isEmpty() || p->ano < 1970 || p->ano > 2100 ||
            cat.buscar_producto(p->codigo_identificador) || !relaciones.contains(p->codigo_identificador))
            throw std::invalid_argument("Producto inválido, duplicado o sin relación.");
        const auto r = relaciones[p->codigo_identificador];
        const auto grupo = r["grupo"].toString();
        if (!grupo.isEmpty() && !cat.buscar_grupo(grupo)) throw std::invalid_argument("Grupo de producto inexistente.");
        estructuras::ListaDoble<std::shared_ptr<dominio::Investigador>> autores;
        QSet<QString> vistos;
        for (const auto& a : r["autores"].toArray()) {
            const auto codigo = a.toString();
            auto autor = cat.buscar_investigador(codigo);
            if (!autor || vistos.contains(codigo)) throw std::invalid_argument("Autor inexistente o duplicado.");
            vistos.insert(codigo);
            autores.insertar_final(autor);
        }
        cat.multilista_productos.agregar_producto(p, cat.buscar_grupo(grupo), autores);
    }
    cat.sincronizarHipercubo();
    return cat;
}

servicios::CatalogoInvestigacion cargar_archivo(const QString& ruta) {
    QFile archivo(ruta);
    if (!archivo.open(QIODevice::ReadOnly)) throw std::runtime_error("No se pudo abrir el archivo local.");
    QJsonParseError error;
    auto doc = QJsonDocument::fromJson(archivo.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject()) throw std::invalid_argument("JSON local inválido.");
    return restaurar_catalogo(doc.object());
}

void guardar_archivo(const QString& ruta, const QJsonObject& datos) {
    QSaveFile archivo(ruta);
    const auto contenido = QJsonDocument(datos).toJson(QJsonDocument::Indented);
    if (!archivo.open(QIODevice::WriteOnly) || archivo.write(contenido) != contenido.size() || !archivo.commit())
        throw std::runtime_error("No se pudo guardar el archivo local de forma atómica.");
}
}
