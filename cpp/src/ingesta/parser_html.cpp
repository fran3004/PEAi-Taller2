#include "pea/ingesta/parser_html.hpp"
#include <QRegularExpression>
#include <QRegularExpressionMatch>

namespace pea::ingesta {

QString ParserHTML::decodificar_entidades(const QString& texto) {
    QString res = texto;
    res.replace(QStringLiteral("&aacute;"), QStringLiteral("á"));
    res.replace(QStringLiteral("&eacute;"), QStringLiteral("é"));
    res.replace(QStringLiteral("&iacute;"), QStringLiteral("í"));
    res.replace(QStringLiteral("&oacute;"), QStringLiteral("ó"));
    res.replace(QStringLiteral("&uacute;"), QStringLiteral("ú"));
    res.replace(QStringLiteral("&ntilde;"), QStringLiteral("ñ"));
    res.replace(QStringLiteral("&Aacute;"), QStringLiteral("Á"));
    res.replace(QStringLiteral("&Eacute;"), QStringLiteral("É"));
    res.replace(QStringLiteral("&Iacute;"), QStringLiteral("Í"));
    res.replace(QStringLiteral("&Oacute;"), QStringLiteral("Ó"));
    res.replace(QStringLiteral("&Uacute;"), QStringLiteral("Ú"));
    res.replace(QStringLiteral("&Ntilde;"), QStringLiteral("Ñ"));
    res.replace(QStringLiteral("&uuml;"), QStringLiteral("ü"));
    res.replace(QStringLiteral("&Uuml;"), QStringLiteral("Ü"));
    res.replace(QStringLiteral("&nbsp;"), QStringLiteral(" "));
    res.replace(QStringLiteral("&quot;"), QStringLiteral("\""));
    res.replace(QStringLiteral("&apos;"), QStringLiteral("'"));
    res.replace(QStringLiteral("&#39;"), QStringLiteral("'"));
    res.replace(QStringLiteral("&lt;"), QStringLiteral("<"));
    res.replace(QStringLiteral("&gt;"), QStringLiteral(">"));
    res.replace(QStringLiteral("&amp;"), QStringLiteral("&"));

    // Entidades numéricas decimales: &#(\d+);
    static const QRegularExpression num_ent(QStringLiteral("&#(\\d+);"));
    auto it = num_ent.globalMatch(res);
    while (it.hasNext()) {
        auto m = it.next();
        bool ok = false;
        int cp = m.captured(1).toInt(&ok);
        if (ok && cp > 0 && cp <= 0xFFFF) {
            res.replace(m.captured(0), QString(QChar(static_cast<ushort>(cp))));
        }
    }

    // Entidades numéricas hexadecimales: &#x([0-9a-fA-F]+);
    static const QRegularExpression hex_ent(QStringLiteral("&#x([0-9a-fA-F]+);"), QRegularExpression::CaseInsensitiveOption);
    auto it_hex = hex_ent.globalMatch(res);
    while (it_hex.hasNext()) {
        auto m = it_hex.next();
        bool ok = false;
        int cp = m.captured(1).toInt(&ok, 16);
        if (ok && cp > 0 && cp <= 0xFFFF) {
            res.replace(m.captured(0), QString(QChar(static_cast<ushort>(cp))));
        }
    }

    return res;
}

QString ParserHTML::limpiar_texto(const QString& fragmento_html) {
    if (fragmento_html.isEmpty()) return {};

    QString s = fragmento_html;

    // 1. Reemplazar tags de bloque por un espacio para no juntar palabras
    static const QRegularExpression block_tags(
        QStringLiteral("<(?:br|p|div|tr|td|th)\\b[^>]*>"),
        QRegularExpression::CaseInsensitiveOption
    );
    s.replace(block_tags, QStringLiteral(" "));

    // 2. Eliminar tags restantes (inline como strong, a, b, i, span, font, etc.)
    static const QRegularExpression remaining_tags(QStringLiteral("<[^>]+>"));
    s.replace(remaining_tags, QStringLiteral(""));

    // 3. Decodificar entidades HTML
    s = decodificar_entidades(s);

    // 4. Colapsar espacios múltiples y recortar
    static const QRegularExpression whitespace_re(QStringLiteral("\\s+"));
    s.replace(whitespace_re, QStringLiteral(" "));
    return s.trimmed();
}

static QList<QString> extraer_tablas(const QString& html) {
    QList<QString> tablas;
    static const QRegularExpression table_start_re(QStringLiteral("<table\\b"), QRegularExpression::CaseInsensitiveOption);
    auto it = table_start_re.globalMatch(html);

    while (it.hasNext()) {
        auto m = it.next();
        int start = static_cast<int>(m.capturedStart());

        int depth = 0;
        static const QRegularExpression table_tag_re(QStringLiteral("</?table\\b"), QRegularExpression::CaseInsensitiveOption);
        auto it_inner = table_tag_re.globalMatch(html, start);
        int end = -1;

        while (it_inner.hasNext()) {
            auto m_inner = it_inner.next();
            QString tag = m_inner.captured(0).toLower();
            if (tag.startsWith(QStringLiteral("<table"))) {
                depth++;
            } else if (tag.startsWith(QStringLiteral("</table"))) {
                depth--;
                if (depth == 0) {
                    int close_tag = html.indexOf(QLatin1Char('>'), static_cast<int>(m_inner.capturedEnd()) - 1);
                    end = (close_tag != -1) ? close_tag + 1 : static_cast<int>(m_inner.capturedEnd());
                    break;
                }
            }
        }

        if (end != -1 && end > start) {
            tablas.append(html.mid(start, end - start));
        } else {
            tablas.append(html.mid(start));
        }
    }
    return tablas;
}

static QList<QString> extraer_filas(const QString& tabla_html) {
    QList<QString> filas;
    static const QRegularExpression tr_re(QStringLiteral("<tr\\b"), QRegularExpression::CaseInsensitiveOption);
    auto it = tr_re.globalMatch(tabla_html);

    QList<int> posiciones;
    while (it.hasNext()) {
        posiciones.append(static_cast<int>(it.next().capturedStart()));
    }
    if (posiciones.isEmpty()) return filas;
    posiciones.append(static_cast<int>(tabla_html.size()));

    for (int i = 0; i < posiciones.size() - 1; ++i) {
        int start = posiciones[i];
        int next_start = posiciones[i + 1];
        QString chunk = tabla_html.mid(start, next_start - start);
        int end_idx = chunk.indexOf(QStringLiteral("</tr>"), 0, Qt::CaseInsensitive);
        if (end_idx != -1) {
            chunk = chunk.left(end_idx + 5);
        }
        filas.append(chunk);
    }
    return filas;
}

static QList<QString> extraer_celdas(const QString& fila_html) {
    QList<QString> celdas;
    static const QRegularExpression td_re(QStringLiteral("<t[dh]\\b"), QRegularExpression::CaseInsensitiveOption);
    auto it = td_re.globalMatch(fila_html);

    QList<int> posiciones;
    while (it.hasNext()) {
        posiciones.append(static_cast<int>(it.next().capturedStart()));
    }
    if (posiciones.isEmpty()) return celdas;
    posiciones.append(static_cast<int>(fila_html.size()));

    for (int i = 0; i < posiciones.size() - 1; ++i) {
        int start = posiciones[i];
        int next_start = posiciones[i + 1];
        QString chunk = fila_html.mid(start, next_start - start);
        static const QRegularExpression end_td(QStringLiteral("</t[dh]>"), QRegularExpression::CaseInsensitiveOption);
        auto m_end = end_td.match(chunk);
        if (m_end.hasMatch()) {
            chunk = chunk.left(static_cast<int>(m_end.capturedEnd()));
        }
        celdas.append(chunk);
    }
    return celdas;
}

static QString extraer_primer_td_texto(const QString& tabla_html) {
    static const QRegularExpression first_td_re(
        QStringLiteral("<t[dh]\\b[^>]*>"),
        QRegularExpression::CaseInsensitiveOption
    );
    auto m = first_td_re.match(tabla_html);
    if (!m.hasMatch()) return {};
    int start = static_cast<int>(m.capturedEnd());

    static const QRegularExpression end_re(
        QStringLiteral("</t[dh]>|<t[dh]\\b|<tr\\b"),
        QRegularExpression::CaseInsensitiveOption
    );
    auto m_end = end_re.match(tabla_html, start);
    int end = m_end.hasMatch() ? static_cast<int>(m_end.capturedStart()) : static_cast<int>(tabla_html.size());
    return ParserHTML::limpiar_texto(tabla_html.mid(start, end - start));
}

GrupoIngesta ParserHTML::parsear_gruplac(
    const QString& html,
    const QJsonObject& meta,
    bool /*anonimizar*/
) {
    GrupoIngesta grupo;
    QString url = meta.value(QStringLiteral("url")).toString();
    QString alias = meta.value(QStringLiteral("alias")).toString();

    // Extraer código de la query o del alias
    QString codigo_gruplac;
    int idx_nro = url.indexOf(QStringLiteral("nro="));
    if (idx_nro != -1) {
        int fin = url.indexOf(QLatin1Char('&'), idx_nro);
        if (fin == -1) fin = static_cast<int>(url.size());
        codigo_gruplac = url.mid(idx_nro + 4, fin - (idx_nro + 4));
    } else if (!alias.isEmpty()) {
        codigo_gruplac = alias;
        codigo_gruplac.remove(QStringLiteral("gruplac_"));
    }
    grupo.codigo_gruplac = codigo_gruplac;

    grupo.origen.url = url;
    grupo.origen.fecha_descarga = meta.value(QStringLiteral("fecha_descarga")).toString();
    grupo.origen.sha256 = meta.value(QStringLiteral("sha256")).toString();
    grupo.origen.metodo = QStringLiteral("requests + bs4 + lxml");

    auto tablas = extraer_tablas(html);
    if (tablas.isEmpty()) return grupo;

    static const QRegularExpression re_header(
        QStringLiteral("<td\\b[^>]*class=[\"'][^\"']*celdaEncabezado[^\"']*[\"'][^>]*>(.*?)</td>"),
        QRegularExpression::CaseInsensitiveOption | QRegularExpression::DotMatchesEverythingOption
    );
    static const QRegularExpression ano_re(QStringLiteral("\\b(19\\d{2}|20\\d{2})\\b"));

    for (int idx = 0; idx < tablas.size(); ++idx) {
        const QString& tbl = tablas[idx];
        auto m_enc = re_header.match(tbl);
        QString sec_title = m_enc.hasMatch() ? limpiar_texto(m_enc.captured(1)) : QStringLiteral("Sección %1").arg(idx);

        auto rows = extraer_filas(tbl);
        if (rows.size() <= 1) continue;

        if (sec_title.contains(QStringLiteral("Datos básicos")) || sec_title.contains(QStringLiteral("Datos bsicos"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                if (tds.size() >= 2) {
                    QString k = limpiar_texto(tds[0]);
                    QString v = limpiar_texto(tds[1]);

                    if (k.contains(QStringLiteral("Año y mes")) || k.contains(QStringLiteral("Ao y mes"))) {
                        grupo.ano_mes_formacion = v;
                    } else if (k.contains(QStringLiteral("Departamento"))) {
                        grupo.departamento_ciudad = v;
                    } else if (k.contains(QStringLiteral("Líder")) || k.contains(QStringLiteral("Lder"))) {
                        grupo.lider = v;
                    } else if (k.contains(QStringLiteral("certificad"), Qt::CaseInsensitive)) {
                        grupo.certificacion = v;
                    } else if (k.contains(QStringLiteral("Página web")) || k.contains(QStringLiteral("Pgina web"))) {
                        grupo.pagina_web = v;
                    } else if (k.contains(QStringLiteral("E-mail"))) {
                        grupo.email = v;
                    } else if (k.contains(QStringLiteral("Clasificación")) || k.contains(QStringLiteral("Clasificacin"))) {
                        grupo.clasificacion = v;
                    } else if (k.contains(QStringLiteral("Área de conocimiento")) || k.contains(QStringLiteral("rea de conocimiento"))) {
                        grupo.area_conocimiento = v;
                    } else if (k.contains(QStringLiteral("Programa nacional"))) {
                        grupo.programa_nacional = v;
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Instituciones"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString inst = limpiar_texto(td);
                    if (!inst.isEmpty() && inst != QStringLiteral("Instituciones")) {
                        InstitucionIngesta ii;
                        ii.nombre = inst;
                        grupo.instituciones.append(ii);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Integrantes del grupo"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                if (tds.size() >= 4) {
                    QString nom = limpiar_texto(tds[0]);
                    if (nom == QStringLiteral("Nombre")) continue;
                    QString vinc = limpiar_texto(tds[1]);
                    QString hrs = limpiar_texto(tds[2]);
                    QString per = limpiar_texto(tds[3]);

                    auto partes_per = per.split(QStringLiteral(" - "));
                    std::optional<QString> ini = !partes_per.isEmpty() ? std::make_optional(partes_per[0].trimmed()) : std::nullopt;
                    std::optional<QString> fin = (partes_per.size() > 1) ? std::make_optional(partes_per[1].trimmed()) : std::nullopt;

                    IntegranteIngesta int_ing;
                    int_ing.nombre = nom;
                    int_ing.vinculacion = vinc;
                    int_ing.horas_dedicacion = hrs;
                    int_ing.inicio_vinculacion = ini;
                    int_ing.fin_vinculacion = fin;
                    grupo.integrantes.append(int_ing);
                }
            }
        } else if (sec_title.contains(QStringLiteral("Líneas de investigación")) || sec_title.contains(QStringLiteral("Lneas de investigacin"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString linea = limpiar_texto(td);
                    if (!linea.isEmpty() && !linea.contains(QStringLiteral("Líneas de investigación")) && !linea.contains(QStringLiteral("Lneas de investigacin"))) {
                        LineaIngesta li;
                        li.nombre = linea;
                        li.activa = true;
                        grupo.lineas_investigacion.append(li);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Artículos publicados")) || sec_title.contains(QStringLiteral("Artculos publicados"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Artículos publicados")) && !txt.contains(QStringLiteral("Artculos publicados"))) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Articulo");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.detalles = txt;
                        grupo.articulos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Libros publicados"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Libros publicados"))) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Libro");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.detalles = txt;
                        grupo.libros.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Capítulos de libro")) || sec_title.contains(QStringLiteral("Captulos de libro"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Capítulos de libro")) && !txt.contains(QStringLiteral("Captulos de libro"))) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Capitulo");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.detalles = txt;
                        grupo.capitulos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Softwares"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Softwares"))) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Software");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.disponibilidad = txt;
                        grupo.softwares.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Trabajos dirigidos"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Trabajos dirigidos"))) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo_trabajo = QStringLiteral("Tesis/Trabajo");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.persona_orientada = txt;
                        grupo.trabajos_dirigidos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Proyectos"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Proyectos"))) {
                        ProductoIngesta prod;
                        prod.titulo = txt.left(150);
                        prod.tipo = txt;
                        prod.detalles = txt;
                        grupo.proyectos.append(prod);
                    }
                }
            }
        }
    }

    return grupo;
}

InvestigadorIngesta ParserHTML::parsear_cvlac(
    const QString& html,
    const QJsonObject& meta,
    bool /*anonimizar*/
) {
    InvestigadorIngesta inv;
    QString url = meta.value(QStringLiteral("url")).toString();
    QString alias = meta.value(QStringLiteral("alias")).toString();

    QString codigo_rh;
    int idx_rh = url.indexOf(QStringLiteral("cod_rh="));
    if (idx_rh != -1) {
        int fin = url.indexOf(QLatin1Char('&'), idx_rh);
        if (fin == -1) fin = static_cast<int>(url.size());
        codigo_rh = url.mid(idx_rh + 7, fin - (idx_rh + 7));
    } else if (!alias.isEmpty()) {
        codigo_rh = alias;
        codigo_rh.remove(QStringLiteral("cvlac_"));
    }
    inv.codigo_rh = codigo_rh;

    inv.origen.url = url;
    inv.origen.fecha_descarga = meta.value(QStringLiteral("fecha_descarga")).toString();
    inv.origen.sha256 = meta.value(QStringLiteral("sha256")).toString();
    inv.origen.metodo = QStringLiteral("requests + bs4 + lxml");

    auto tablas = extraer_tablas(html);
    if (tablas.isEmpty()) return inv;

    static const QRegularExpression ano_re(QStringLiteral("\\b(19\\d{2}|20\\d{2})\\b"));

    for (int idx = 0; idx < tablas.size(); ++idx) {
        const QString& tbl = tablas[idx];
        auto rows = extraer_filas(tbl);
        if (rows.isEmpty()) continue;

        QString sec_title = extraer_primer_td_texto(tbl);
        if (sec_title.isEmpty()) {
            sec_title = QStringLiteral("Bloque %1").arg(idx);
        }
        if (sec_title.size() > 60) {
            sec_title = sec_title.left(60) + QStringLiteral("...");
        }

        if (rows.size() <= 1 && idx != 0) continue;

        if (sec_title.contains(QStringLiteral("Hoja de vida")) || idx == 0) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                if (tds.size() >= 2) {
                    QString k = limpiar_texto(tds[0]);
                    QString v = limpiar_texto(tds[1]);

                    if (k == QStringLiteral("Nombre")) {
                        inv.nombre_completo = v;
                    } else if (k.contains(QStringLiteral("citaciones"))) {
                        inv.nombre_citaciones = v;
                    } else if (k == QStringLiteral("Nacionalidad")) {
                        inv.nacionalidad = v;
                    } else if (k == QStringLiteral("Sexo")) {
                        inv.sexo = v;
                    } else if (k.contains(QStringLiteral("Categoría")) || k.contains(QStringLiteral("Categoria"))) {
                        inv.categoria_declarada = v;
                    } else if (k.contains(QStringLiteral("Par evaluador"))) {
                        inv.par_evaluador = true;
                    }
                } else if (tds.size() == 1) {
                    QString k = limpiar_texto(tds[0]);
                    if (k.contains(QStringLiteral("Par evaluador"))) {
                        inv.par_evaluador = true;
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Formación Académica")) || sec_title.contains(QStringLiteral("Formacion Academica"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                QStringList partes_celdas;
                for (const auto& td : tds) {
                    QString t = limpiar_texto(td);
                    if (!t.isEmpty()) partes_celdas.append(t);
                }
                QString txt_row = partes_celdas.join(QLatin1Char(' ')).trimmed();
                if (!txt_row.isEmpty() && !txt_row.contains(QStringLiteral("Formación Académica")) && !txt_row.contains(QStringLiteral("Formacion Academica")) && txt_row.size() > 10) {
                    QString nivel = QStringLiteral("Formación");
                    QString lower = txt_row.toLower();
                    if (lower.contains(QStringLiteral("doctorado"))) {
                        nivel = QStringLiteral("Doctorado");
                    } else if (lower.contains(QStringLiteral("maestr"))) {
                        nivel = QStringLiteral("Maestría");
                    } else if (lower.contains(QStringLiteral("pregrado"))) {
                        nivel = QStringLiteral("Pregrado");
                    } else if (lower.contains(QStringLiteral("perfeccionamiento"))) {
                        nivel = QStringLiteral("Perfeccionamiento");
                    }

                    FormacionIngesta fi;
                    fi.nivel = nivel;
                    fi.titulo = txt_row.left(100);
                    fi.institucion = txt_row;
                    inv.formacion.append(fi);
                }
            }
        } else if (sec_title.contains(QStringLiteral("Áreas de actuación")) || sec_title.contains(QStringLiteral("reas de actuacin"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Áreas de actuación")) && !txt.contains(QStringLiteral("reas de actuacin"))) {
                        inv.areas_actuacion.append(txt);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Líneas de investigación")) || sec_title.contains(QStringLiteral("Lneas de investigacin"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Líneas de investigación")) && !txt.contains(QStringLiteral("Lneas de investigacin"))) {
                        inv.lineas_investigacion.append(txt);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Artículos")) || sec_title.contains(QStringLiteral("Artculos"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Artículos")) && !txt.contains(QStringLiteral("Artculos")) && txt.size() > 20) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Articulo");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.detalles = txt;
                        inv.articulos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Capitulos de libro")) || sec_title.contains(QStringLiteral("Captulos de libro"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Capitulos de libro")) && !txt.contains(QStringLiteral("Captulos de libro")) && txt.size() > 20) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Capitulo");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.detalles = txt;
                        inv.capitulos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Softwares"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Softwares")) && txt.size() > 20) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo = QStringLiteral("Software");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.disponibilidad = txt;
                        inv.softwares.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Trabajos dirigidos/tutorías")) || sec_title.contains(QStringLiteral("Trabajos dirigidos/tutoras"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Trabajos dirigidos")) && txt.size() > 20) {
                        auto m_ano = ano_re.match(txt);
                        std::optional<int> ano_val = m_ano.hasMatch() ? std::make_optional(m_ano.captured(1).toInt()) : std::nullopt;

                        ProductoIngesta prod;
                        prod.tipo_trabajo = QStringLiteral("Tutoría/Trabajo de Grado");
                        prod.titulo = txt.left(150);
                        prod.ano = ano_val;
                        prod.persona_orientada = txt;
                        inv.trabajos_dirigidos.append(prod);
                    }
                }
            }
        } else if (sec_title.contains(QStringLiteral("Proyectos"))) {
            for (const auto& tr : rows) {
                auto tds = extraer_celdas(tr);
                for (const auto& td : tds) {
                    QString txt = limpiar_texto(td);
                    if (!txt.isEmpty() && !txt.contains(QStringLiteral("Proyectos")) && txt.size() > 20) {
                        ProductoIngesta prod;
                        prod.titulo = txt.left(150);
                        prod.tipo = txt;
                        prod.detalles = txt;
                        inv.proyectos.append(prod);
                    }
                }
            }
        }
    }

    return inv;
}

QString ParserHTML::generar_markdown_gruplac(
    const GrupoIngesta& grupo,
    const QJsonObject& meta,
    bool /*anonimizar*/
) {
    QStringList md;
    md.append(QStringLiteral("# Transcripción Integral GrupLAC · %1\n").arg(grupo.codigo_gruplac));
    md.append(QStringLiteral("- **URL:** `%1`").arg(meta.value(QStringLiteral("url")).toString()));
    md.append(QStringLiteral("- **Fecha Descarga:** `%1`").arg(meta.value(QStringLiteral("fecha_descarga")).toString()));
    md.append(QStringLiteral("- **SHA256:** `%1`\n").arg(meta.value(QStringLiteral("sha256")).toString()));
    md.append(QStringLiteral("---\n"));

    md.append(QStringLiteral("## Datos básicos\n"));
    md.append(QStringLiteral("| Campo | Valor |"));
    md.append(QStringLiteral("|---|---|"));
    if (grupo.ano_mes_formacion) md.append(QStringLiteral("| Año y mes de formación | %1 |").arg(*grupo.ano_mes_formacion));
    if (grupo.departamento_ciudad) md.append(QStringLiteral("| Departamento - Ciudad | %1 |").arg(*grupo.departamento_ciudad));
    if (grupo.lider) md.append(QStringLiteral("| Líder | %1 |").arg(*grupo.lider));
    if (grupo.clasificacion) md.append(QStringLiteral("| Clasificación | %1 |").arg(*grupo.clasificacion));
    if (grupo.area_conocimiento) md.append(QStringLiteral("| Área de conocimiento | %1 |").arg(*grupo.area_conocimiento));
    md.append(QStringLiteral(""));

    return md.join(QLatin1Char('\n'));
}

QString ParserHTML::generar_markdown_cvlac(
    const InvestigadorIngesta& inv,
    const QJsonObject& meta,
    bool /*anonimizar*/
) {
    QStringList md;
    md.append(QStringLiteral("# Transcripción Integral CvLAC · %1\n").arg(inv.codigo_rh));
    md.append(QStringLiteral("- **URL:** `%1`").arg(meta.value(QStringLiteral("url")).toString()));
    md.append(QStringLiteral("- **Fecha Descarga:** `%1`").arg(meta.value(QStringLiteral("fecha_descarga")).toString()));
    md.append(QStringLiteral("- **SHA256:** `%1`\n").arg(meta.value(QStringLiteral("sha256")).toString()));
    md.append(QStringLiteral("---\n"));

    md.append(QStringLiteral("## Hoja de vida\n"));
    md.append(QStringLiteral("| Atributo | Detalle |"));
    md.append(QStringLiteral("|---|---|"));
    if (inv.nombre_completo) md.append(QStringLiteral("| Nombre | %1 |").arg(*inv.nombre_completo));
    if (inv.categoria_declarada) md.append(QStringLiteral("| Categoría | %1 |").arg(*inv.categoria_declarada));
    md.append(QStringLiteral(""));

    return md.join(QLatin1Char('\n'));
}

} // namespace pea::ingesta
