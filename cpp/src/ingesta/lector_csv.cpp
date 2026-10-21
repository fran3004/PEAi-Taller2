#include "pea/ingesta/lector_csv.hpp"
#include <algorithm>
#include <QFile>
#include <QFileInfo>
#include <optional>

namespace pea::ingesta {
namespace {

bool leer_booleano_csv(const QString& valor, bool predeterminado = true) {
    const QString normalizado = valor.trimmed().toLower();
    if (normalizado.isEmpty()) return predeterminado;
    if (normalizado == "true" || normalizado == "1" || normalizado == "yes" ||
        normalizado == "y" || normalizado == "on" || normalizado == "si" ||
        normalizado == "sí") {
        return true;
    }
    if (normalizado == "false" || normalizado == "0" || normalizado == "no" ||
        normalizado == "n" || normalizado == "off") {
        return false;
    }
    throw std::invalid_argument("Valor booleano inválido: " + valor.toStdString());
}

std::optional<QString> valor_columna(const QStringList& fila,
                                     const QMap<QString, int>& columnas,
                                     const QString& nombre) {
    const int indice = columnas.value(nombre, -1);
    if (indice < 0 || indice >= fila.size() || fila[indice].trimmed().isEmpty()) {
        return std::nullopt;
    }
    return fila[indice].trimmed();
}

} // namespace

QChar LectorCSV::detectar_delimitador(const QString& contenido) {
    int idx_nl = contenido.indexOf(QLatin1Char('\n'));
    QString primera_linea = (idx_nl != -1) ? contenido.left(idx_nl) : contenido;

    int comas = 0;
    int puntos_coma = 0;
    bool en_comillas = false;

    for (int i = 0; i < primera_linea.size(); ++i) {
        QChar c = primera_linea[i];
        if (c == QLatin1Char('"')) {
            en_comillas = !en_comillas;
        } else if (!en_comillas) {
            if (c == QLatin1Char(',')) comas++;
            else if (c == QLatin1Char(';')) puntos_coma++;
        }
    }

    if (puntos_coma > comas) return QLatin1Char(';');
    return QLatin1Char(',');
}

QString LectorCSV::leer_texto_archivo(const QString& ruta, QString* encoding_detectada) {
    QFile file(ruta);
    if (!file.open(QIODevice::ReadOnly)) {
        throw std::runtime_error("No se pudo abrir el archivo CSV: " + ruta.toStdString());
    }

    QByteArray bytes = file.readAll();
    file.close();

    // Detección de BOM UTF-8 (\xEF\xBB\xBF)
    if (bytes.startsWith("\xEF\xBB\xBF")) {
        if (encoding_detectada) *encoding_detectada = QStringLiteral("utf-8-sig");
        return QString::fromUtf8(bytes.mid(3));
    }

    if (encoding_detectada) *encoding_detectada = QStringLiteral("utf-8");
    QString txt = QString::fromUtf8(bytes);
    if (txt.contains(QChar(0xFFFD))) {
        // Fallback a Latin1 si hubo caracteres inválidos UTF-8
        if (encoding_detectada) *encoding_detectada = QStringLiteral("latin1");
        return QString::fromLatin1(bytes);
    }
    return txt;
}

QStringList LectorCSV::parsear_linea(const QString& linea, QChar delimitador) {
    QStringList campos;
    QString campo_actual;
    bool en_comillas = false;

    for (int i = 0; i < linea.size(); ++i) {
        QChar c = linea[i];

        if (c == QLatin1Char('"')) {
            if (en_comillas && i + 1 < linea.size() && linea[i + 1] == QLatin1Char('"')) {
                // Comilla escapada ""
                campo_actual += QLatin1Char('"');
                ++i;
            } else {
                en_comillas = !en_comillas;
            }
        } else if (c == delimitador && !en_comillas) {
            campos.append(campo_actual.trimmed());
            campo_actual.clear();
        } else {
            campo_actual += c;
        }
    }
    campos.append(campo_actual.trimmed());
    return campos;
}

static QList<QStringList> parsear_csv_completo(const QString& texto, QChar delimitador) {
    QList<QStringList> filas;
    QStringList campos;
    QString campo_actual;
    bool en_comillas = false;

    for (qsizetype indice = 0; indice < texto.size(); ++indice) {
        const QChar caracter = texto[indice];
        if (caracter == QLatin1Char('"')) {
            if (en_comillas && indice + 1 < texto.size() &&
                texto[indice + 1] == QLatin1Char('"')) {
                campo_actual += QLatin1Char('"');
                ++indice;
            } else {
                en_comillas = !en_comillas;
            }
        } else if (!en_comillas && caracter == delimitador) {
            campos.append(campo_actual.trimmed());
            campo_actual.clear();
        } else if (!en_comillas &&
                   (caracter == QLatin1Char('\r') || caracter == QLatin1Char('\n'))) {
            campos.append(campo_actual.trimmed());
            campo_actual.clear();
            if (std::any_of(campos.cbegin(), campos.cend(),
                            [](const QString& campo) { return !campo.isEmpty(); })) {
                filas.append(campos);
            }
            campos.clear();
            if (caracter == QLatin1Char('\r') && indice + 1 < texto.size() &&
                texto[indice + 1] == QLatin1Char('\n')) {
                ++indice;
            }
        } else {
            campo_actual += caracter;
        }
    }

    campos.append(campo_actual.trimmed());
    if (std::any_of(campos.cbegin(), campos.cend(),
                    [](const QString& campo) { return !campo.isEmpty(); })) {
        filas.append(campos);
    }
    return filas;
}

QString LectorCSV::detectar_tipo_archivo(const QString& ruta) {
    QString contenido = leer_texto_archivo(ruta);
    QChar delim = detectar_delimitador(contenido);
    auto filas = parsear_csv_completo(contenido, delim);
    if (filas.isEmpty()) return QStringLiteral("desconocido");

    const auto& headers = filas[0];
    QSet<QString> set_headers;
    for (const auto& h : headers) {
        set_headers.insert(h.toLower().trimmed());
    }

    if (set_headers.contains(QStringLiteral("codigo_gruplac")) || set_headers.contains(QStringLiteral("codigo_minciencias"))) {
        return QStringLiteral("grupos");
    }
    if (set_headers.contains(QStringLiteral("codigo_cvlac")) || set_headers.contains(QStringLiteral("codigo_rh"))) {
        return QStringLiteral("investigadores");
    }
    if (set_headers.contains(QStringLiteral("producto_codigo")) && set_headers.contains(QStringLiteral("investigador_codigo"))) {
        return QStringLiteral("autores");
    }
    if (set_headers.contains(QStringLiteral("codigo_identificador")) || set_headers.contains(QStringLiteral("tipo_mayor")) || set_headers.contains(QStringLiteral("tipo_categoria"))) {
        return QStringLiteral("productos");
    }

    return QStringLiteral("desconocido");
}

std::pair<estructuras::ListaDoble<dominio::Grupo>, QList<QString>> LectorCSV::leer_grupos(
    const QString& ruta,
    QChar delimitador
) {
    estructuras::ListaDoble<dominio::Grupo> grupos;
    QList<QString> errores;

    QString texto = leer_texto_archivo(ruta);
    QChar delim = (delimitador != QLatin1Char('\0')) ? delimitador : detectar_delimitador(texto);
    auto filas = parsear_csv_completo(texto, delim);
    if (filas.isEmpty()) return {grupos, errores};

    const auto& headers = filas[0];
    QMap<QString, int> mapa_col;
    for (int i = 0; i < headers.size(); ++i) {
        mapa_col[headers[i].toLower().trimmed()] = i;
    }

    for (int num = 1; num < filas.size(); ++num) {
        const auto& f = filas[num];
        try {
            int idx_cod = mapa_col.value(QStringLiteral("codigo_minciencias"), mapa_col.value(QStringLiteral("codigo_gruplac"), -1));
            int idx_nom = mapa_col.value(QStringLiteral("nombre"), mapa_col.value(QStringLiteral("nombre_grupo"), -1));
            int idx_cat = mapa_col.value(QStringLiteral("clasificacion"), mapa_col.value(QStringLiteral("categoria"), -1));
            int idx_inst = mapa_col.value(QStringLiteral("institucion"), mapa_col.value(QStringLiteral("institucion_principal"), -1));
            int idx_lid = mapa_col.value(QStringLiteral("lider"), -1);

            if (idx_cod == -1 || idx_cod >= f.size() || f[idx_cod].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Código de grupo ausente o inválido").arg(num + 1));
                continue;
            }
            if (idx_nom == -1 || idx_nom >= f.size() || f[idx_nom].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Nombre de grupo ausente o inválido").arg(num + 1));
                continue;
            }

            dominio::Grupo g;
            g.codigo_gruplac = f[idx_cod].trimmed();
            g.nombre = f[idx_nom].trimmed();
            if (idx_cat != -1 && idx_cat < f.size()) g.categoria = f[idx_cat].trimmed();
            g.institucion_principal = (idx_inst != -1 && idx_inst < f.size()) ? f[idx_inst].trimmed() : QStringLiteral("Universidad Popular del Cesar");
            if (idx_lid != -1 && idx_lid < f.size()) g.lider = f[idx_lid].trimmed();
            g.pais = valor_columna(f, mapa_col, QStringLiteral("pais")).value_or(QStringLiteral("Colombia"));
            g.departamento_ciudad = valor_columna(f, mapa_col, QStringLiteral("departamento_ciudad")).value_or(QString());
            g.gran_area_ocde = valor_columna(f, mapa_col, QStringLiteral("gran_area_ocde")).value_or(QString());
            g.area_ocde = valor_columna(f, mapa_col, QStringLiteral("area_ocde")).value_or(QString());
            g.activo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("activo")).value_or(QString()));
            g.es_ejemplo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("es_ejemplo")).value_or(QString()), false);

            grupos.insertar_final(g);
        } catch (const std::exception& e) {
            errores.append(QStringLiteral("Fila %1: Error de análisis: %2").arg(num + 1).arg(e.what()));
        }
    }

    return {grupos, errores};
}

std::pair<estructuras::ListaDoble<dominio::Investigador>, QList<QString>> LectorCSV::leer_investigadores(
    const QString& ruta,
    QChar delimitador
) {
    estructuras::ListaDoble<dominio::Investigador> invs;
    QList<QString> errores;

    QString texto = leer_texto_archivo(ruta);
    QChar delim = (delimitador != QLatin1Char('\0')) ? delimitador : detectar_delimitador(texto);
    auto filas = parsear_csv_completo(texto, delim);
    if (filas.isEmpty()) return {invs, errores};

    const auto& headers = filas[0];
    QMap<QString, int> mapa_col;
    for (int i = 0; i < headers.size(); ++i) {
        mapa_col[headers[i].toLower().trimmed()] = i;
    }

    for (int num = 1; num < filas.size(); ++num) {
        const auto& f = filas[num];
        try {
            int idx_rh = mapa_col.value(QStringLiteral("codigo_cvlac"), mapa_col.value(QStringLiteral("codigo_rh"), -1));
            int idx_nom = mapa_col.value(QStringLiteral("nombre_completo"), mapa_col.value(QStringLiteral("nombre"), -1));
            int idx_cat = mapa_col.value(QStringLiteral("categoria"), mapa_col.value(QStringLiteral("categoria_declarada"), -1));
            int idx_nac = mapa_col.value(QStringLiteral("nacionalidad"), -1);
            int idx_form = mapa_col.value(QStringLiteral("formacion_academica"), mapa_col.value(QStringLiteral("formacion"), -1));

            if (idx_rh == -1 || idx_rh >= f.size() || f[idx_rh].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Código CvLAC de investigador ausente o inválido").arg(num + 1));
                continue;
            }
            if (idx_nom == -1 || idx_nom >= f.size() || f[idx_nom].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Nombre de investigador ausente o inválido").arg(num + 1));
                continue;
            }

            dominio::Investigador inv;
            inv.codigo_rh = f[idx_rh].trimmed();
            inv.nombre_completo = f[idx_nom].trimmed();
            if (idx_cat != -1 && idx_cat < f.size()) inv.categoria = f[idx_cat].trimmed();
            inv.nacionalidad = (idx_nac != -1 && idx_nac < f.size() && !f[idx_nac].trimmed().isEmpty())
                                   ? f[idx_nac].trimmed()
                                   : QStringLiteral("Colombiana");
            if (idx_form != -1 && idx_form < f.size()) inv.formacion_academica = f[idx_form].trimmed();
            inv.nombre_en_citas = valor_columna(f, mapa_col, QStringLiteral("nombre_en_citas")).value_or(QString());
            inv.documento_identidad = valor_columna(f, mapa_col, QStringLiteral("documento_identidad")).value_or(QString());
            inv.sexo = valor_columna(f, mapa_col, QStringLiteral("sexo")).value_or(QString());
            inv.activo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("activo")).value_or(QString()));
            inv.es_ejemplo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("es_ejemplo")).value_or(QString()), false);

            invs.insertar_final(inv);
        } catch (const std::exception& e) {
            errores.append(QStringLiteral("Fila %1: Error de análisis: %2").arg(num + 1).arg(e.what()));
        }
    }

    return {invs, errores};
}

std::pair<QList<std::pair<dominio::Producto, QString>>, QList<QString>> LectorCSV::leer_productos(
    const QString& ruta,
    QChar delimitador
) {
    QList<std::pair<dominio::Producto, QString>> prods;
    QList<QString> errores;

    QString texto = leer_texto_archivo(ruta);
    QChar delim = (delimitador != QLatin1Char('\0')) ? delimitador : detectar_delimitador(texto);
    auto filas = parsear_csv_completo(texto, delim);
    if (filas.isEmpty()) return {prods, errores};

    const auto& headers = filas[0];
    QMap<QString, int> mapa_col;
    for (int i = 0; i < headers.size(); ++i) {
        mapa_col[headers[i].toLower().trimmed()] = i;
    }

    for (int num = 1; num < filas.size(); ++num) {
        const auto& f = filas[num];
        try {
            int idx_cod = mapa_col.value(QStringLiteral("codigo_identificador"), -1);
            int idx_tit = mapa_col.value(QStringLiteral("titulo"), -1);
            int idx_tipo = mapa_col.value(QStringLiteral("tipo_categoria"), mapa_col.value(QStringLiteral("tipo_mayor"), -1));
            int idx_ano = mapa_col.value(QStringLiteral("anio"), mapa_col.value(QStringLiteral("ano"), -1));
            int idx_grp = mapa_col.value(QStringLiteral("grupo_codigo"), mapa_col.value(QStringLiteral("codigo_gruplac"), -1));

            if (idx_cod == -1 || idx_cod >= f.size() || f[idx_cod].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Código identificador de producto ausente").arg(num + 1));
                continue;
            }
            if (idx_tit == -1 || idx_tit >= f.size() || f[idx_tit].trimmed().isEmpty()) {
                errores.append(QStringLiteral("Fila %1: Título del producto ausente o inválido").arg(num + 1));
                continue;
            }

            bool ok_ano = false;
            const int ano_val = (idx_ano != -1 && idx_ano < f.size())
                                    ? f[idx_ano].trimmed().toInt(&ok_ano)
                                    : 0;
            if (!ok_ano) {
                errores.append(QStringLiteral("Fila %1: Año no numérico o ausente").arg(num + 1));
                continue;
            }

            dominio::Producto p;
            p.codigo_identificador = f[idx_cod].trimmed();
            p.titulo = f[idx_tit].trimmed();
            p.tipo_mayor = (idx_tipo != -1 && idx_tipo < f.size() && !f[idx_tipo].trimmed().isEmpty())
                               ? f[idx_tipo].trimmed()
                               : QStringLiteral("GNC");
            p.ano = ano_val;
            p.subtipo = valor_columna(f, mapa_col, QStringLiteral("subtipo")).value_or(QString());
            const auto mes = valor_columna(f, mapa_col, QStringLiteral("mes"));
            if (mes) {
                bool valido = false;
                const int valor_mes = mes->toInt(&valido);
                if (!valido) throw std::invalid_argument("El mes no es numérico.");
                p.mes = valor_mes;
            }
            p.pais = valor_columna(f, mapa_col, QStringLiteral("pais")).value_or(QString());
            p.estado_validacion = valor_columna(f, mapa_col, QStringLiteral("estado_validacion"))
                                      .value_or(QStringLiteral("No avalado"));
            const auto detalles = valor_columna(f, mapa_col, QStringLiteral("detalles"));
            if (detalles) {
                const QJsonDocument documento = QJsonDocument::fromJson(detalles->toUtf8());
                if (!documento.isObject()) {
                    throw std::invalid_argument("El campo detalles debe contener un objeto JSON.");
                }
                p.detalles = documento.object();
            }
            p.activo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("activo")).value_or(QString()));
            p.es_ejemplo = leer_booleano_csv(valor_columna(f, mapa_col, QStringLiteral("es_ejemplo")).value_or(QString()), false);

            QString grp_cod = (idx_grp != -1 && idx_grp < f.size()) ? f[idx_grp].trimmed() : QString();
            prods.append({p, grp_cod});
        } catch (const std::exception& e) {
            errores.append(QStringLiteral("Fila %1: Error de análisis: %2").arg(num + 1).arg(e.what()));
        }
    }

    return {prods, errores};
}

std::pair<QList<FilaAutorCSV>, QList<QString>> LectorCSV::leer_autores(
    const QString& ruta,
    QChar delimitador
) {
    QList<FilaAutorCSV> autores;
    QList<QString> errores;

    QString texto = leer_texto_archivo(ruta);
    QChar delim = (delimitador != QLatin1Char('\0')) ? delimitador : detectar_delimitador(texto);
    auto filas = parsear_csv_completo(texto, delim);
    if (filas.isEmpty()) return {autores, errores};

    const auto& headers = filas[0];
    QMap<QString, int> mapa_col;
    for (int i = 0; i < headers.size(); ++i) {
        mapa_col[headers[i].toLower().trimmed()] = i;
    }

    for (int num = 1; num < filas.size(); ++num) {
        const auto& f = filas[num];
        try {
            int idx_prod = mapa_col.value(QStringLiteral("producto_codigo"), -1);
            int idx_inv = mapa_col.value(QStringLiteral("investigador_codigo"), -1);
            int idx_ord = mapa_col.value(QStringLiteral("orden_autoria"), -1);

            if (idx_prod == -1 || idx_prod >= f.size() || idx_inv == -1 || idx_inv >= f.size()) {
                errores.append(QStringLiteral("Fila %1: Campos producto_codigo o investigador_codigo ausentes").arg(num + 1));
                continue;
            }

            int orden = 1;
            if (idx_ord != -1 && idx_ord < f.size()) {
                bool ok = false;
                int val = f[idx_ord].trimmed().toInt(&ok);
                if (ok && val > 0) orden = val;
            }

            FilaAutorCSV fa;
            fa.producto_codigo = f[idx_prod].trimmed();
            fa.investigador_codigo = f[idx_inv].trimmed();
            fa.orden_autoria = orden;
            autores.append(fa);
        } catch (const std::exception& e) {
            errores.append(QStringLiteral("Fila %1: Error de análisis: %2").arg(num + 1).arg(e.what()));
        }
    }

    return {autores, errores};
}

} // namespace pea::ingesta
