#include "pea/ingesta/lector_csv.hpp"
#include <QFile>
#include <QFileInfo>
#include <QRegularExpression>

namespace pea::ingesta {

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
    QStringList lineas = texto.split(QRegularExpression(QStringLiteral("[\r\n]+")), Qt::SkipEmptyParts);

    for (const auto& l : lineas) {
        if (l.trimmed().isEmpty()) continue;
        filas.append(LectorCSV::parsear_linea(l, delimitador));
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

            dominio::Grupo g;
            g.codigo_gruplac = f[idx_cod].trimmed();
            g.nombre = (idx_nom != -1 && idx_nom < f.size()) ? f[idx_nom].trimmed() : QStringLiteral("Grupo %1").arg(g.codigo_gruplac);
            g.categoria = (idx_cat != -1 && idx_cat < f.size()) ? f[idx_cat].trimmed() : QStringLiteral("Reconocido");
            g.institucion_principal = (idx_inst != -1 && idx_inst < f.size()) ? f[idx_inst].trimmed() : QStringLiteral("Universidad Popular del Cesar");
            if (idx_lid != -1 && idx_lid < f.size()) g.lider = f[idx_lid].trimmed();

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

            dominio::Investigador inv;
            inv.codigo_rh = f[idx_rh].trimmed();
            inv.nombre_completo = (idx_nom != -1 && idx_nom < f.size()) ? f[idx_nom].trimmed() : QStringLiteral("Investigador %1").arg(inv.codigo_rh);
            inv.categoria = (idx_cat != -1 && idx_cat < f.size()) ? f[idx_cat].trimmed() : QStringLiteral("Investigador");
            inv.nacionalidad = (idx_nac != -1 && idx_nac < f.size()) ? f[idx_nac].trimmed() : QStringLiteral("Colombiana");
            if (idx_form != -1 && idx_form < f.size()) inv.formacion_academica = f[idx_form].trimmed();

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

            bool ok_ano = false;
            int ano_val = (idx_ano != -1 && idx_ano < f.size()) ? f[idx_ano].trimmed().toInt(&ok_ano) : 2024;
            if (idx_ano != -1 && !ok_ano) {
                errores.append(QStringLiteral("Fila %1: Año no numérico o inválido: '%2'").arg(num + 1).arg(f[idx_ano]));
                continue;
            }

            dominio::Producto p;
            p.codigo_identificador = f[idx_cod].trimmed();
            p.titulo = (idx_tit != -1 && idx_tit < f.size()) ? f[idx_tit].trimmed() : QStringLiteral("Producto %1").arg(p.codigo_identificador);
            p.tipo_mayor = (idx_tipo != -1 && idx_tipo < f.size()) ? f[idx_tipo].trimmed() : QStringLiteral("GNC");
            p.ano = ano_val;
            p.estado_validacion = QStringLiteral("Aprobado");

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
