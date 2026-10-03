#include "pea/ingesta/servicio_ingesta.hpp"
#include <QUuid>
#include "pea/ingesta/lector_csv.hpp"
#include "pea/ingesta/parser_html.hpp"

namespace pea::ingesta {

ServicioIngesta::ServicioIngesta(
    std::shared_ptr<servicios::CatalogoInvestigacion> catalogo,
    std::unique_ptr<ExtractorURL> extractor
) : m_catalogo(std::move(catalogo)),
    m_extractor_url(extractor ? std::move(extractor) : std::make_unique<ExtractorURL>()) {}

estructuras::TareaIngesta ServicioIngesta::encolar_url(
    const QString& url,
    bool persistir,
    bool anonimizar,
    const QString& salida_dir
) {
    auto [tipo_fuente, _] = ExtractorURL::validar_url(url);
    QString id_tarea = QStringLiteral("URL-%1").arg(QUuid::createUuid().toString(QUuid::WithoutBraces).left(8));

    estructuras::TareaIngesta tarea;
    tarea.id_tarea = id_tarea;
    tarea.tipo_fuente = QStringLiteral("url_%1").arg(tipo_fuente);
    tarea.origen = url;
    tarea.estado = estructuras::EstadoTarea::Pendiente;

    QJsonObject det;
    det[QStringLiteral("persistir")] = persistir;
    det[QStringLiteral("anonimizar")] = anonimizar;
    det[QStringLiteral("salida_dir")] = salida_dir;
    tarea.detalles = det;

    m_catalogo->cola_importacion.encolar(tarea);
    return tarea;
}

estructuras::TareaIngesta ServicioIngesta::encolar_csv(
    const QString& ruta_csv,
    const QString& tipo_entidad,
    bool persistir
) {
    QString tipo = !tipo_entidad.isEmpty() ? tipo_entidad : LectorCSV::detectar_tipo_archivo(ruta_csv);
    QString id_tarea = QStringLiteral("CSV-%1").arg(QUuid::createUuid().toString(QUuid::WithoutBraces).left(8));

    estructuras::TareaIngesta tarea;
    tarea.id_tarea = id_tarea;
    tarea.tipo_fuente = QStringLiteral("csv_%1").arg(tipo);
    tarea.origen = ruta_csv;
    tarea.estado = estructuras::EstadoTarea::Pendiente;

    QJsonObject det;
    det[QStringLiteral("tipo_entidad")] = tipo;
    det[QStringLiteral("persistir")] = persistir;
    tarea.detalles = det;

    m_catalogo->cola_importacion.encolar(tarea);
    return tarea;
}

std::optional<InformeIngesta> ServicioIngesta::procesar_siguiente() {
    if (m_catalogo->cola_importacion.esta_vacia()) {
        return std::nullopt;
    }

    auto tarea = m_catalogo->cola_importacion.desencolar();
    tarea.estado = estructuras::EstadoTarea::Procesando;

    try {
        InformeIngesta informe;
        if (tarea.tipo_fuente.startsWith(QStringLiteral("url_"))) {
            informe = procesar_tarea_url(tarea);
        } else if (tarea.tipo_fuente.startsWith(QStringLiteral("csv_"))) {
            informe = procesar_tarea_csv(tarea);
        } else {
            throw std::runtime_error("Tipo de tarea no reconocido: " + tarea.tipo_fuente.toStdString());
        }

        tarea.estado = estructuras::EstadoTarea::Terminada;
        tarea.elementos_procesados = informe.grupos_procesados + informe.investigadores_procesados + informe.productos_procesados;
        return informe;
    } catch (const std::exception& e) {
        tarea.estado = estructuras::EstadoTarea::ConError;
        tarea.mensaje_error = QString::fromStdString(e.what());

        InformeIngesta err_inf;
        err_inf.origen = tarea.origen;
        err_inf.tipo_fuente = tarea.tipo_fuente;
        err_inf.exito = false;
        err_inf.mensaje = QStringLiteral("Error durante la ingesta: %1").arg(QString::fromStdString(e.what()));
        err_inf.advertencias.append(QString::fromStdString(e.what()));
        return err_inf;
    }
}

QList<InformeIngesta> ServicioIngesta::procesar_todas() {
    QList<InformeIngesta> resultados;
    while (!m_catalogo->cola_importacion.esta_vacia()) {
        auto inf = procesar_siguiente();
        if (inf.has_value()) {
            resultados.append(*inf);
        }
    }
    return resultados;
}

InformeIngesta ServicioIngesta::procesar_tarea_url(estructuras::TareaIngesta& tarea) {
    bool persistir = tarea.detalles.value(QStringLiteral("persistir")).toBool(false);
    bool anonimizar = tarea.detalles.value(QStringLiteral("anonimizar")).toBool(false);
    QString salida_dir = tarea.detalles.value(QStringLiteral("salida_dir")).toString(QStringLiteral("datos/fuentes/extraccion"));

    auto informe = m_extractor_url->procesar_url(tarea.origen, salida_dir, anonimizar, false);

    // Cargar en catálogo en memoria
    QString tipo = tarea.tipo_fuente.contains(QStringLiteral("gruplac")) ? QStringLiteral("gruplac") : QStringLiteral("cvlac");
    auto [bytes, meta] = m_extractor_url->descargar_o_cargar_cache(tarea.origen);
    QString html = QString::fromLatin1(bytes);

    if (tipo == QStringLiteral("gruplac")) {
        auto grupo_ing = ParserHTML::parsear_gruplac(html, meta, anonimizar);
        if (!m_catalogo->buscar_grupo(grupo_ing.codigo_gruplac)) {
            dominio::Grupo g;
            g.codigo_gruplac = grupo_ing.codigo_gruplac;
            g.nombre = grupo_ing.nombre_grupo ? *grupo_ing.nombre_grupo : QStringLiteral("Grupo %1").arg(g.codigo_gruplac);
            g.categoria = grupo_ing.clasificacion ? *grupo_ing.clasificacion : QStringLiteral("Reconocido");
            if (grupo_ing.lider) g.lider = *grupo_ing.lider;
            if (grupo_ing.departamento_ciudad) g.departamento_ciudad = *grupo_ing.departamento_ciudad;
            if (grupo_ing.area_conocimiento) g.gran_area_ocde = *grupo_ing.area_conocimiento;
            if (!grupo_ing.instituciones.isEmpty()) g.institucion_principal = grupo_ing.instituciones[0].nombre;

            m_catalogo->crear_grupo(std::make_shared<dominio::Grupo>(g), persistir);
        }

        // Cargar productos de grupo
        int prod_idx = 1;
        QList<ProductoIngesta> todos_prods;
        todos_prods.append(grupo_ing.articulos);
        todos_prods.append(grupo_ing.libros);
        todos_prods.append(grupo_ing.capitulos);
        todos_prods.append(grupo_ing.softwares);

        for (const auto& p_ing : todos_prods) {
            QString cod_prod = QStringLiteral("PROD-%1-%2").arg(grupo_ing.codigo_gruplac).arg(prod_idx++, 4, 10, QLatin1Char('0'));
            if (!m_catalogo->buscar_producto(cod_prod)) {
                dominio::Producto p;
                p.codigo_identificador = cod_prod;
                p.titulo = p_ing.titulo;
                p.tipo_mayor = p_ing.tipo.contains(QStringLiteral("Software")) ? QStringLiteral("DTI") : QStringLiteral("GNC");
                p.subtipo = p_ing.tipo;
                p.ano = p_ing.ano.value_or(2024);
                p.estado_validacion = QStringLiteral("Aprobado");
                m_catalogo->crear_producto(std::make_shared<dominio::Producto>(p), grupo_ing.codigo_gruplac, {}, persistir);
            }
        }
    } else if (tipo == QStringLiteral("cvlac")) {
        auto inv_ing = ParserHTML::parsear_cvlac(html, meta, anonimizar);
        if (!m_catalogo->buscar_investigador(inv_ing.codigo_rh)) {
            dominio::Investigador inv;
            inv.codigo_rh = inv_ing.codigo_rh;
            inv.nombre_completo = inv_ing.nombre_completo ? *inv_ing.nombre_completo : QStringLiteral("Investigador %1").arg(inv.codigo_rh);
            inv.categoria = inv_ing.categoria_declarada ? *inv_ing.categoria_declarada : QStringLiteral("Investigador");
            inv.nacionalidad = inv_ing.nacionalidad ? *inv_ing.nacionalidad : QStringLiteral("Colombiana");
            if (!inv_ing.formacion.isEmpty()) inv.formacion_academica = inv_ing.formacion[0].nivel;

            m_catalogo->crear_investigador(std::make_shared<dominio::Investigador>(inv), persistir);
        }

        int prod_idx = 1;
        QList<ProductoIngesta> todos_prods;
        todos_prods.append(inv_ing.articulos);
        todos_prods.append(inv_ing.capitulos);
        todos_prods.append(inv_ing.softwares);

        for (const auto& p_ing : todos_prods) {
            QString cod_prod = QStringLiteral("PROD-CVLAC-%1-%2").arg(inv_ing.codigo_rh).arg(prod_idx++, 4, 10, QLatin1Char('0'));
            if (!m_catalogo->buscar_producto(cod_prod)) {
                dominio::Producto p;
                p.codigo_identificador = cod_prod;
                p.titulo = p_ing.titulo;
                p.tipo_mayor = p_ing.tipo.contains(QStringLiteral("Software")) ? QStringLiteral("DTI") : QStringLiteral("GNC");
                p.subtipo = p_ing.tipo;
                p.ano = p_ing.ano.value_or(2024);
                p.estado_validacion = QStringLiteral("Aprobado");
                m_catalogo->crear_producto(std::make_shared<dominio::Producto>(p), QString(), {inv_ing.codigo_rh}, persistir);
            }
        }
    }

    return informe;
}

InformeIngesta ServicioIngesta::procesar_tarea_csv(estructuras::TareaIngesta& tarea) {
    QString tipo = tarea.detalles.value(QStringLiteral("tipo_entidad")).toString();
    if (tipo.isEmpty()) tipo = LectorCSV::detectar_tipo_archivo(tarea.origen);
    bool persistir = tarea.detalles.value(QStringLiteral("persistir")).toBool(false);

    InformeIngesta informe;
    informe.origen = tarea.origen;
    informe.tipo_fuente = QStringLiteral("csv_%1").arg(tipo);
    informe.exito = true;
    informe.mensaje = QStringLiteral("Importación CSV (%1) procesada").arg(tipo);

    if (tipo == QStringLiteral("grupos")) {
        auto [grupos, errs] = LectorCSV::leer_grupos(tarea.origen);
        for (const auto& g : grupos) {
            if (!m_catalogo->buscar_grupo(g.codigo_gruplac)) {
                m_catalogo->crear_grupo(std::make_shared<dominio::Grupo>(g), persistir);
                informe.grupos_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("investigadores")) {
        auto [invs, errs] = LectorCSV::leer_investigadores(tarea.origen);
        for (const auto& inv : invs) {
            if (!m_catalogo->buscar_investigador(inv.codigo_rh)) {
                m_catalogo->crear_investigador(std::make_shared<dominio::Investigador>(inv), persistir);
                informe.investigadores_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("productos")) {
        auto [prods, errs] = LectorCSV::leer_productos(tarea.origen);
        for (const auto& [p, grp_cod] : prods) {
            if (!m_catalogo->buscar_producto(p.codigo_identificador)) {
                m_catalogo->crear_producto(std::make_shared<dominio::Producto>(p), grp_cod, {}, persistir);
                informe.productos_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("autores")) {
        auto [autores, errs] = LectorCSV::leer_autores(tarea.origen);
        for (const auto& a : autores) {
            auto inv = m_catalogo->buscar_investigador(a.investigador_codigo);
            if (inv && m_catalogo->buscar_producto(a.producto_codigo)) {
                auto* n = m_catalogo->multilista_productos.buscar_nodo(a.producto_codigo);
                if (n) {
                    n->agregar_autor(inv);
                    informe.autores_procesados++;
                }
            }
        }
        informe.filas_erroneas.append(errs);
    }

    return informe;
}

} // namespace pea::ingesta
