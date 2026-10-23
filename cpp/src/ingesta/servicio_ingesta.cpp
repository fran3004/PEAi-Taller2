#include "pea/ingesta/servicio_ingesta.hpp"
#include "pea/excepciones.hpp"
#include <QDate>
#include <QDateTime>
#include <QRegularExpression>
#include <QStringList>
#include <chrono>
#include <stdexcept>
#include <thread>
#include <utility>
#include <QUuid>
#include "pea/ingesta/lector_csv.hpp"
#include "pea/ingesta/parser_html.hpp"

namespace pea::ingesta {
namespace {

QString normalizar_categoria_cvlac(const std::optional<QString>& declarada) {
    const QString texto = declarada.value_or(QString()).toLower();
    if (texto.contains(QStringLiteral("emerit"))) return QStringLiteral("Investigador Emérito");
    if (texto.contains(QStringLiteral("senior"))) return QStringLiteral("Investigador Senior");
    if (texto.contains(QStringLiteral("asociado"))) return QStringLiteral("Investigador Asociado");
    if (texto.contains(QStringLiteral("junior"))) return QStringLiteral("Investigador Junior");
    return QStringLiteral("Sin categoría / Vinculado");
}

QString normalizar_formacion_cvlac(const QList<FormacionIngesta>& formacion) {
    if (formacion.isEmpty()) return QStringLiteral("Pregrado");
    const QString nivel = formacion[0].nivel.toLower();
    if (nivel.contains(QStringLiteral("doctor"))) return QStringLiteral("Doctorado");
    if (nivel.contains(QStringLiteral("maestr"))) return QStringLiteral("Maestría");
    if (nivel.contains(QStringLiteral("especial"))) return QStringLiteral("Especialización");
    return QStringLiteral("Pregrado");
}

template <typename Operacion>
auto ejecutar_con_reintento_revision(
    servicios::CatalogoInvestigacion& catalogo,
    Operacion&& operacion
) -> decltype(operacion()) {
    constexpr int max_intentos = 5;
    for (int intento = 0; intento < max_intentos; ++intento) {
        try {
            return operacion();
        } catch (const ConflictoRevision& error) {
            if (error.mensaje() != "La base de datos cambió" || intento == max_intentos - 1) {
                throw;
            }
            catalogo.sincronizar_revision();
            std::this_thread::sleep_for(std::chrono::milliseconds(50 * (1 << intento)));
        }
    }
    throw std::runtime_error("La mutación de ingesta terminó sin resultado.");
}

} // namespace

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
    if (tipo != QStringLiteral("grupos") &&
        tipo != QStringLiteral("investigadores") &&
        tipo != QStringLiteral("productos") &&
        tipo != QStringLiteral("autores")) {
        throw std::invalid_argument(
            "Tipo de CSV no reconocido; use grupos, investigadores, productos o autores.");
    }
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

        tarea.estado = informe.exito ? estructuras::EstadoTarea::Terminada : estructuras::EstadoTarea::ConError;
        if (!informe.exito) tarea.mensaje_error = informe.mensaje;
        tarea.elementos_procesados = informe.grupos_procesados + informe.investigadores_procesados +
                                    informe.productos_procesados + informe.autores_procesados;
        return informe;
    } catch (const std::exception& e) {
        tarea.estado = estructuras::EstadoTarea::ConError;
        tarea.mensaje_error = QString::fromStdString(e.what());

        InformeIngesta err_inf;
        err_inf.origen = tarea.origen;
        err_inf.tipo_fuente = tarea.tipo_fuente;
        err_inf.fecha = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
        err_inf.exito = false;
        err_inf.mensaje = QStringLiteral("Error durante la ingesta: %1").arg(QString::fromStdString(e.what()));
        err_inf.requiere_recarga = dynamic_cast<const ConflictoRevision*>(&e) != nullptr;
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
            if (inf->requiere_recarga) {
                break;
            }
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
            const QString clasificacion = grupo_ing.clasificacion.value_or(QString());
            static const QRegularExpression categoria_re(QStringLiteral("\\b(A1|A|B|C)\\b"), QRegularExpression::CaseInsensitiveOption);
            const auto categoria_match = categoria_re.match(clasificacion);
            g.categoria = categoria_match.hasMatch()
                ? categoria_match.captured(1).toUpper()
                : QStringLiteral("Reconocido");
            g.fecha_creacion = QDate::currentDate().toString(QStringLiteral("yyyy-MM-dd"));
            if (grupo_ing.ano_mes_formacion) {
                static const QRegularExpression formacion_re(QStringLiteral("\\b(19\\d{2}|20\\d{2})\\s*-\\s*(\\d{1,2})\\b"));
                const auto formacion_match = formacion_re.match(*grupo_ing.ano_mes_formacion);
                if (formacion_match.hasMatch()) {
                    const int anio = formacion_match.captured(1).toInt();
                    const int mes = formacion_match.captured(2).toInt();
                    const QDate fecha(anio, mes, 1);
                    if (fecha.isValid()) g.fecha_creacion = fecha.toString(QStringLiteral("yyyy-MM-dd"));
                }
            }
            g.lider = grupo_ing.lider.value_or(QStringLiteral("Sin información"));
            g.departamento_ciudad = grupo_ing.departamento_ciudad.value_or(QStringLiteral("Sin información"));
            g.gran_area_ocde = grupo_ing.area_conocimiento.value_or(QStringLiteral("Sin información"));
            g.area_ocde = grupo_ing.area_conocimiento.value_or(QStringLiteral("Sin información"));
            if (!grupo_ing.instituciones.isEmpty()) g.institucion_principal = grupo_ing.instituciones[0].nombre;
            g.detalles = grupo_ing.a_json();

            ejecutar_con_reintento_revision(*m_catalogo, [&] {
                return m_catalogo->crear_grupo(std::make_shared<dominio::Grupo>(g), persistir);
            });
        } else {
            QJsonObject cambios;
            cambios[QStringLiteral("detalles")] = grupo_ing.a_json();
            ejecutar_con_reintento_revision(*m_catalogo, [&] {
                return m_catalogo->actualizar_grupo(grupo_ing.codigo_gruplac, cambios, persistir);
            });
        }

        const QString fecha_grupo = m_catalogo->buscar_grupo(grupo_ing.codigo_gruplac)->fecha_creacion;
        QStringList urls_cvlac_encoladas;
        for (const auto& integrante : grupo_ing.integrantes) {
            if (integrante.codigo_rh.isEmpty()) {
                informe.advertencias.append(
                    QStringLiteral("No se pudo crear el vínculo de %1: GrupLAC no informa su código CvLAC.")
                        .arg(integrante.nombre));
                continue;
            }
            const QString url_cvlac = integrante.url_cvlac.isEmpty()
                ? QStringLiteral("https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=%1")
                    .arg(integrante.codigo_rh)
                : integrante.url_cvlac;
            if (!urls_cvlac_encoladas.contains(url_cvlac)) {
                encolar_url(url_cvlac, persistir, anonimizar, salida_dir);
                urls_cvlac_encoladas.append(url_cvlac);
            }
            auto investigador = m_catalogo->buscar_investigador(integrante.codigo_rh);
            if (!investigador) {
                investigador = std::make_shared<dominio::Investigador>();
                investigador->codigo_rh = integrante.codigo_rh;
                investigador->nombre_completo = integrante.nombre;
                investigador->nacionalidad = QStringLiteral("Colombiana");
                investigador->sexo = QStringLiteral("No especificado");
                investigador->categoria = QStringLiteral("Sin categoría / Vinculado");
                investigador->formacion_academica = QStringLiteral("Pregrado");
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_investigador(investigador, persistir);
                });
            }
            const QString vinculacion = integrante.vinculacion;
            const QString vinculacion_lower = vinculacion.toLower();
            const QString rol = vinculacion_lower.contains(QStringLiteral("lider"))
                    || vinculacion_lower.contains(QStringLiteral("líder"))
                ? QStringLiteral("Lider")
                : (vinculacion_lower.contains(QStringLiteral("estudiante"))
                    ? QStringLiteral("Estudiante")
                    : QStringLiteral("Investigador"));
            bool ya_vinculado = false;
            for (const auto& actual : m_catalogo->integrantes) {
                if (actual.codigo_gruplac == grupo_ing.codigo_gruplac
                    && actual.codigo_rh == integrante.codigo_rh) {
                    ya_vinculado = true;
                    break;
                }
            }
            if (!urls_cvlac_encoladas.isEmpty()) {
                informe.mensaje += QStringLiteral(" Se encolaron %1 perfiles CvLAC enlazados.")
                    .arg(urls_cvlac_encoladas.size());
            }
            if (!ya_vinculado) {
                bool ok = false;
                const int horas = integrante.horas_dedicacion.value_or(QString()).toInt(&ok);
                QJsonObject detalles;
                detalles[QStringLiteral("url_cvlac")] = integrante.url_cvlac;
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->vincular_integrante(
                        grupo_ing.codigo_gruplac,
                        integrante.codigo_rh,
                        rol,
                        persistir,
                        integrante.inicio_vinculacion.value_or(fecha_grupo),
                        integrante.fin_vinculacion.value_or(QString()),
                        vinculacion,
                        ok ? horas : 0,
                        detalles);
                });
            }
        }

        // Cargar productos de grupo
        int prod_idx = 1;
        QList<ProductoIngesta> todos_prods;
        todos_prods.append(grupo_ing.articulos);
        todos_prods.append(grupo_ing.libros);
        todos_prods.append(grupo_ing.capitulos);
        todos_prods.append(grupo_ing.softwares);
        todos_prods.append(grupo_ing.trabajos_dirigidos);
        todos_prods.append(grupo_ing.proyectos);

        for (const auto& p_ing : todos_prods) {
            if (!p_ing.ano.has_value()) {
                informe.advertencias.append(
                    QStringLiteral("Se omitió el producto GrupLAC #%1: la fuente no informa el año.")
                        .arg(prod_idx));
                ++prod_idx;
                continue;
            }
            QString cod_prod = QStringLiteral("PROD-%1-%2").arg(grupo_ing.codigo_gruplac).arg(prod_idx++, 4, 10, QLatin1Char('0'));
            if (!m_catalogo->buscar_producto(cod_prod)) {
                dominio::Producto p;
                p.codigo_identificador = cod_prod;
                p.titulo = p_ing.titulo;
                p.tipo_mayor = p_ing.tipo.contains(QStringLiteral("Software")) ? QStringLiteral("DTI") : QStringLiteral("GNC");
                p.subtipo = p_ing.tipo.isEmpty() ? QStringLiteral("Producto GrupLAC") : p_ing.tipo.left(100);
                p.ano = *p_ing.ano;
                p.estado_validacion = QStringLiteral("Avalado");
                p.detalles[QStringLiteral("fuente")] = tarea.origen;
                p.detalles[QStringLiteral("referencia_original")] = p_ing.detalles.value_or(QString());
                if (p_ing.autores) p.detalles[QStringLiteral("autores")] = *p_ing.autores;
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_producto(
                        std::make_shared<dominio::Producto>(p),
                        grupo_ing.codigo_gruplac,
                        {},
                        persistir);
                });
            }
        }
    } else if (tipo == QStringLiteral("cvlac")) {
        auto inv_ing = ParserHTML::parsear_cvlac(html, meta, anonimizar);
        const auto investigador_existente = m_catalogo->buscar_investigador(inv_ing.codigo_rh);
        QJsonObject cambios_investigador;
        cambios_investigador[QStringLiteral("nombre_completo")] =
            inv_ing.nombre_completo.value_or(
                investigador_existente ? investigador_existente->nombre_completo
                                       : QStringLiteral("Investigador %1").arg(inv_ing.codigo_rh));
        cambios_investigador[QStringLiteral("nombre_en_citas")] =
            inv_ing.nombre_citaciones.value_or(QString());
        cambios_investigador[QStringLiteral("nacionalidad")] =
            inv_ing.nacionalidad.value_or(QStringLiteral("Colombiana"));
        cambios_investigador[QStringLiteral("sexo")] =
            inv_ing.sexo.value_or(QStringLiteral("No especificado"));
        cambios_investigador[QStringLiteral("categoria")] =
            normalizar_categoria_cvlac(inv_ing.categoria_declarada);
        cambios_investigador[QStringLiteral("formacion_academica")] =
            normalizar_formacion_cvlac(inv_ing.formacion);
        cambios_investigador[QStringLiteral("par_evaluador")] = inv_ing.par_evaluador;
        cambios_investigador[QStringLiteral("detalles")] = inv_ing.a_json();

        if (investigador_existente) {
            ejecutar_con_reintento_revision(*m_catalogo, [&] {
                return m_catalogo->actualizar_investigador(
                    inv_ing.codigo_rh,
                    cambios_investigador,
                    persistir);
            });
        } else {
            auto investigador = std::make_shared<dominio::Investigador>();
            investigador->codigo_rh = inv_ing.codigo_rh;
            investigador->nombre_completo = cambios_investigador[QStringLiteral("nombre_completo")].toString();
            investigador->nombre_en_citas = inv_ing.nombre_citaciones.value_or(QString());
            investigador->nacionalidad = cambios_investigador[QStringLiteral("nacionalidad")].toString();
            investigador->sexo = cambios_investigador[QStringLiteral("sexo")].toString();
            investigador->categoria = cambios_investigador[QStringLiteral("categoria")].toString();
            investigador->formacion_academica = cambios_investigador[QStringLiteral("formacion_academica")].toString();
            investigador->par_evaluador = inv_ing.par_evaluador;
            investigador->detalles = inv_ing.a_json();
            ejecutar_con_reintento_revision(*m_catalogo, [&] {
                return m_catalogo->crear_investigador(investigador, persistir);
            });
        }

        int prod_idx = 1;
        QList<ProductoIngesta> todos_prods;
        todos_prods.append(inv_ing.articulos);
        todos_prods.append(inv_ing.libros);
        todos_prods.append(inv_ing.capitulos);
        todos_prods.append(inv_ing.softwares);
        todos_prods.append(inv_ing.trabajos_dirigidos);
        todos_prods.append(inv_ing.proyectos);

        for (const auto& p_ing : todos_prods) {
            if (!p_ing.ano.has_value()) {
                informe.advertencias.append(
                    QStringLiteral("Se omitió el producto CvLAC #%1: la fuente no informa el año.")
                        .arg(prod_idx));
                ++prod_idx;
                continue;
            }
            QString cod_prod = QStringLiteral("PROD-CVLAC-%1-%2").arg(inv_ing.codigo_rh).arg(prod_idx++, 4, 10, QLatin1Char('0'));
            if (!m_catalogo->buscar_producto(cod_prod)) {
                dominio::Producto p;
                p.codigo_identificador = cod_prod;
                p.titulo = p_ing.titulo;
                p.tipo_mayor = p_ing.tipo.contains(QStringLiteral("Software")) ? QStringLiteral("DTI") : QStringLiteral("GNC");
                p.subtipo = p_ing.tipo.left(100);
                p.ano = *p_ing.ano;
                p.estado_validacion = QStringLiteral("Avalado");
                p.detalles[QStringLiteral("fuente")] = tarea.origen;
                p.detalles[QStringLiteral("referencia_original")] = p_ing.detalles.value_or(QString());
                if (p_ing.autores) p.detalles[QStringLiteral("autores")] = *p_ing.autores;
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_producto(
                        std::make_shared<dominio::Producto>(p),
                        QString(),
                        {inv_ing.codigo_rh},
                        persistir);
                });
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
    informe.fecha = QDateTime::currentDateTimeUtc().toString(Qt::ISODate);
    informe.exito = true;
    informe.mensaje = QStringLiteral("Importación de CSV tipo '%1' procesada").arg(tipo);

    if (tipo == QStringLiteral("grupos")) {
        auto [grupos, errs] = LectorCSV::leer_grupos(tarea.origen);
        for (const auto& g : grupos) {
            if (!m_catalogo->buscar_grupo(g.codigo_gruplac)) {
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_grupo(std::make_shared<dominio::Grupo>(g), persistir);
                });
                informe.grupos_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("investigadores")) {
        auto [invs, errs] = LectorCSV::leer_investigadores(tarea.origen);
        for (const auto& inv : invs) {
            if (!m_catalogo->buscar_investigador(inv.codigo_rh)) {
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_investigador(
                        std::make_shared<dominio::Investigador>(inv),
                        persistir);
                });
                informe.investigadores_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("productos")) {
        auto [prods, errs] = LectorCSV::leer_productos(tarea.origen);
        for (const auto& [p, grp_cod] : prods) {
            if (!m_catalogo->buscar_producto(p.codigo_identificador)) {
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    return m_catalogo->crear_producto(
                        std::make_shared<dominio::Producto>(p),
                        grp_cod,
                        {},
                        persistir);
                });
                informe.productos_procesados++;
            }
        }
        informe.filas_erroneas.append(errs);
    } else if (tipo == QStringLiteral("autores")) {
        auto [autores, errs] = LectorCSV::leer_autores(tarea.origen);
        informe.filas_erroneas.append(errs);
        for (const auto& a : autores) {
            if (!persistir && (!m_catalogo->buscar_investigador(a.investigador_codigo) ||
                              !m_catalogo->buscar_producto(a.producto_codigo))) continue;
            try {
                ejecutar_con_reintento_revision(*m_catalogo, [&] {
                    m_catalogo->asociar_autor_producto(a.producto_codigo, a.investigador_codigo,
                                                     a.orden_autoria, persistir);
                });
                ++informe.autores_procesados;
            } catch (const ErrorPEA& error) {
                informe.filas_erroneas.append(QStringLiteral("Fila %1: %2").arg(a.fila).arg(error.what()));
                if (dynamic_cast<const ConflictoRevision*>(&error) && error.mensaje() == "La base de datos cambió")
                    informe.requiere_recarga = true;
            }
        }
        if (persistir) {
            const auto total = autores.size() + errs.size();
            informe.exito = informe.autores_procesados > 0 || total == 0;
            informe.mensaje = QStringLiteral("%1 de %2 relaciones guardadas").arg(informe.autores_procesados).arg(total);
            informe.advertencias.append(informe.filas_erroneas);
        }
    }

    return informe;
}

} // namespace pea::ingesta
