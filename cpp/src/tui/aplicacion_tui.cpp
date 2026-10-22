#include "pea/tui/aplicacion_tui.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

#include <ftxui/component/component.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include <ftxui/dom/elements.hpp>
#include <ftxui/screen/screen.hpp>
#include <ftxui/screen/string.hpp>
#include <ftxui/screen/terminal.hpp>

#include <QDir>
#include <QFile>
#include <QDate>
#include <QJsonArray>
#include <QJsonDocument>
#include <QMap>
#include <QSet>
#include <QStringList>

#include "pea/cliente_http.hpp"
#include "pea/datos/sesion.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/datos/configuracion_conexion.hpp"
#include "pea/ingesta/servicio_ingesta.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"
#include "pea/tui/trabajador_periodico.hpp"
#include "pea/version.hpp"

namespace pea::tui {
namespace {

using namespace ftxui;

constexpr std::array<const char*, 8> PESTANAS{
    "Inicio", "Investigadores", "Grupos", "Productos",
    "Análisis de redes", "Importar", "Configuración", "Acerca de"
};
constexpr std::array<const char*, 8> ARCHIVOS_PANTALLA{
    "inicio", "investigadores", "grupos", "productos",
    "analisis-redes", "importar", "configuracion", "acerca-de"
};
constexpr std::array<const char*, 9> ACCIONES_FORMULARIO{
    "", "Crear", "Editar", "Activar / desactivar", "Eliminar", "Ver ficha",
    "Importar CSV", "Importar URL SCIENTI", "Configurar rango anual"
};
constexpr int FILAS_POR_PAGINA = 12;

std::vector<std::string> campos_formulario(int entidad, int accion) {
    if (accion == 6) return {"Ruta al archivo CSV", "Tipo: auto/grupos/investigadores/productos/autores"};
    if (accion == 7) return {"URL SCIENTI (HTTPS)", "Anonimizar datos personales (si/no)"};
    if (accion == 8) return {"Año desde (opcional)", "Año hasta (opcional)"};
    if (accion == 1) {
        if (entidad == 1) return {"Código RH", "Nombre completo", "Categoría", "Formación académica"};
        if (entidad == 2) return {"Código GrupLAC", "Nombre", "Categoría", "Líder"};
        return {"Código", "Título", "Tipo mayor (GNC/DTI/ASC/FRH)", "Subtipo",
                "Año (1970-" + std::to_string(QDate::currentDate().year()) + ")",
                "Validación", "Código GrupLAC (opcional)",
                "Códigos RH autores separados por ; (opcional)"};
    }
    if (accion == 2) {
        if (entidad == 1) return {"Código RH", "Nombre completo nuevo", "Categoría nueva", "Formación nueva"};
        if (entidad == 2) return {"Código GrupLAC", "Nombre nuevo", "Categoría nueva", "Líder nuevo"};
        return {"Código", "Título nuevo", "Tipo mayor nuevo", "Subtipo nuevo",
                "Año nuevo (1970-" + std::to_string(QDate::currentDate().year()) + ")",
                "Validación nueva", "Código GrupLAC nuevo (opcional)",
                "Quitar grupo actual (sí/no)"};
    }
    if (accion == 3) return {entidad == 1 ? "Código RH" : entidad == 2 ? "Código GrupLAC" : "Código producto"};
    if (accion == 4) {
        return {entidad == 1 ? "Código RH" : entidad == 2 ? "Código GrupLAC" : "Código producto",
                "Escriba ELIMINAR para confirmar"};
    }
    if (accion == 5) {
        return {entidad == 1 ? "Código RH" : entidad == 2 ? "Código GrupLAC" : "Código producto"};
    }
    return {};
}

QString campo_qstring(const std::vector<std::string>& campos, std::size_t indice) {
    return indice < campos.size() ? QString::fromUtf8(campos[indice].c_str()) : QString();
}

QString etiqueta_entidad(int entidad) {
    if (entidad == 1) return "investigador";
    if (entidad == 2) return "grupo";
    return "producto";
}

QString texto_valor_json(const QJsonValue& valor) {
    if (valor.isObject()) {
        return QString::fromUtf8(QJsonDocument(valor.toObject()).toJson(QJsonDocument::Compact));
    }
    if (valor.isArray()) {
        return QString::fromUtf8(QJsonDocument(valor.toArray()).toJson(QJsonDocument::Compact));
    }
    return valor.toVariant().toString();
}

bool coincide_campos(const QJsonObject& campos, const QString& filtro) {
    if (filtro.isEmpty()) return true;

    const qsizetype separador = filtro.indexOf(':');
    if (separador > 0) {
        const QString nombre_campo = filtro.left(separador).trimmed();
        const QString valor_busqueda = filtro.mid(separador + 1).trimmed();
        if (nombre_campo.isEmpty() || valor_busqueda.isEmpty()) return false;
        for (auto campo = campos.constBegin(); campo != campos.constEnd(); ++campo) {
            if (campo.key().compare(nombre_campo, Qt::CaseInsensitive) == 0) {
                return texto_valor_json(campo.value()).contains(valor_busqueda, Qt::CaseInsensitive);
            }
        }
        return false;
    }

    for (auto campo = campos.constBegin(); campo != campos.constEnd(); ++campo) {
        if (texto_valor_json(campo.value()).contains(filtro, Qt::CaseInsensitive)) return true;
    }
    return false;
}

void agregar_pagina(Elements& filas, const std::vector<std::string>& resultados, int pagina) {
    const int paginas = std::max(
        1, static_cast<int>((resultados.size() + FILAS_POR_PAGINA - 1) / FILAS_POR_PAGINA));
    const int pagina_visible = std::clamp(pagina, 0, paginas - 1);
    const auto inicio = static_cast<std::size_t>(pagina_visible * FILAS_POR_PAGINA);
    const auto fin = std::min(inicio + FILAS_POR_PAGINA, resultados.size());
    for (auto indice = inicio; indice < fin; ++indice) {
        filas.push_back(text(resultados[indice]));
    }
    filas.push_back(text(
        "Página " + std::to_string(pagina_visible + 1) + " de " + std::to_string(paginas) +
        " · " + std::to_string(resultados.size()) +
        " registros  [: anterior · ]: siguiente"));
}

int ultima_pagina(int indice, const servicios::CatalogoInvestigacion& catalogo,
                  const QString& filtro) {
    std::size_t coincidencias = 0;
    if (indice == 1) {
        for (const auto& investigador : catalogo.investigadores) {
            if (investigador && coincide_campos(investigador->aJson(), filtro)) ++coincidencias;
        }
    } else if (indice == 2) {
        for (const auto& grupo : catalogo.grupos) {
            if (grupo && coincide_campos(grupo->aJson(), filtro)) ++coincidencias;
        }
    } else if (indice == 3) {
        for (auto* nodo = catalogo.multilista_productos.cabeza(); nodo != nullptr;
             nodo = nodo->siguiente_global) {
            if (nodo->producto && coincide_campos(nodo->producto->aJson(), filtro)) {
                ++coincidencias;
            }
        }
    }
    if (coincidencias == 0) return 0;
    return static_cast<int>((coincidencias - 1) / FILAS_POR_PAGINA);
}

void borrar_ultimo_caracter_utf8(std::string& texto) {
    if (texto.empty()) return;
    std::size_t posicion = texto.size() - 1;
    while (posicion > 0 &&
           (static_cast<unsigned char>(texto[posicion]) & 0xC0) == 0x80) {
        --posicion;
    }
    texto.erase(posicion);
}

std::string texto_cantidad(int cantidad) {
    return std::to_string(cantidad);
}

std::string quitar_secuencias_ansi(const std::string& entrada) {
    std::string salida;
    salida.reserve(entrada.size());
    for (std::size_t indice = 0; indice < entrada.size(); ++indice) {
        if (entrada[indice] != '\x1b' || indice + 1 >= entrada.size() ||
            entrada[indice + 1] != '[') {
            salida.push_back(entrada[indice]);
            continue;
        }
        indice += 2;
        while (indice < entrada.size() &&
               !(entrada[indice] >= '@' && entrada[indice] <= '~')) {
            ++indice;
        }
    }
    return salida;
}

Element color_si(Element elemento, Color tono, bool habilitado) {
    return habilitado ? elemento | color(tono) : elemento;
}

Element separador(bool ascii) {
    return ascii ? separatorCharacter("-") : separator();
}

Element marco(Element elemento, bool ascii) {
    if (!ascii) {
        return elemento | border;
    }
    const auto linea = [] {
        return hbox({text("+"), separatorCharacter("-") | flex, text("+")});
    };
    return vbox({
        linea(),
        hbox({text("|"), elemento | flex, text("|")}),
        linea(),
    });
}

Element tarjeta(std::string titulo, std::string valor, Color tono, bool color_activo, bool ascii) {
    auto contenido = vbox({
        color_si(text(std::move(titulo)), Color::GrayLight, color_activo),
        color_si(text(std::move(valor)) | bold, tono, color_activo),
    });
    return marco(contenido, ascii) |
           size(WIDTH, GREATER_THAN, 18) |
           size(HEIGHT, GREATER_THAN, 3);
}

void cargar_datos_demostracion(servicios::CatalogoInvestigacion& catalogo) {
    auto grupo = std::make_shared<dominio::Grupo>(
        "PRUEBA-GRUPO-001", "Grupo de demostración", "A1", QString(), true);
    auto investigador = std::make_shared<dominio::Investigador>(
        "PRUEBA-RH-001", "Investigador de demostración", "Junior", "Maestría", true);
    auto coautor = std::make_shared<dominio::Investigador>(
        "PRUEBA-RH-002", "Coautor de demostración", "Junior", "Maestría", true);
    auto producto = std::make_shared<dominio::Producto>(
        "PRUEBA-PROD-001", "Producto de demostración", "GNC", "Artículo", 2024, "Avalado", true);
    catalogo.crear_grupo(grupo, false);
    catalogo.crear_investigador(investigador, false);
    catalogo.crear_investigador(coautor, false);
    catalogo.crear_producto(producto, grupo->codigo_gruplac,
                             {investigador->codigo_rh, coautor->codigo_rh}, false);
}

Element tabla_resumen(const QJsonObject& resumen, bool ascii) {
    auto fila = [](std::string etiqueta, int total, int activos) {
        return hbox({
            text(std::move(etiqueta)) | size(WIDTH, EQUAL, 24),
            text(texto_cantidad(total)) | size(WIDTH, EQUAL, 10),
            text(texto_cantidad(activos)) | size(WIDTH, EQUAL, 10),
        });
    };

    return marco(vbox({
               hbox({
                   text("Entidad") | bold | size(WIDTH, EQUAL, 24),
                   text("Total") | bold | size(WIDTH, EQUAL, 10),
                   text("Activos") | bold | size(WIDTH, EQUAL, 10),
               }),
               separador(ascii),
               fila("Grupos", resumen["grupos_totales"].toInt(), resumen["grupos_activos"].toInt()),
               fila("Investigadores", resumen["investigadores_totales"].toInt(),
                    resumen["investigadores_activos"].toInt()),
               fila("Productos", resumen["productos_totales"].toInt(),
                    resumen["productos_activos"].toInt()),
           }), ascii);
}

Element panel_contenido(
    int indice,
    const QJsonObject& resumen,
    const servicios::CatalogoInvestigacion& catalogo,
    bool datos_demostracion,
    bool conectado,
    const std::string& mensaje_conexion,
    const QString& filtro,
    bool filtro_activo,
    int accion_formulario,
    const std::vector<std::string>& valores_formulario,
    std::size_t campo_activo,
    const std::string& mensaje_estado,
    const std::string& ficha_detalle,
    bool color_activo,
    bool ascii,
    int ancho,
    const servicios::FiltroAnios& filtro_anios,
    int pagina_actual) {
    const std::string origen = datos_demostracion
                                   ? "Datos de demostración (solo memoria)"
                                   : (conectado ? "Datos de Supabase" : "Sin datos");
    const auto estadisticas = catalogo.estadisticas.obtenerVistaInstitucional();
    const QString texto_filtro = filtro_activo
                                     ? QString("Filtro: %1  (texto o campo:valor · Enter aplicar · Esc limpiar)")
                                           .arg(filtro)
                                     : (filtro.isEmpty()
                                            ? QString("Presione / para buscar por texto o campo:valor")
                                            : QString("Filtro: %1  (/ editar · Esc limpiar)")
                                                  .arg(filtro));
    if (!ficha_detalle.empty() && indice >= 1 && indice <= 3) {
        return vbox({
                   color_si(text("Ficha de " + etiqueta_entidad(indice).toStdString()) | bold,
                            Color::Cyan, color_activo),
                   text("Escape: regresar al directorio"),
                   separador(ascii),
                   paragraph(ficha_detalle),
               }) |
               flex;
    }
    if (accion_formulario > 0) {
        const auto campos = campos_formulario(indice, accion_formulario);
        const std::string titulo_formulario = accion_formulario >= 6
                                                  ? ACCIONES_FORMULARIO[static_cast<std::size_t>(accion_formulario)]
                                                  : std::string(ACCIONES_FORMULARIO[static_cast<std::size_t>(accion_formulario)]) +
                                                        " " + etiqueta_entidad(indice).toStdString();
        Elements contenido{
            color_si(text(titulo_formulario) | bold, Color::Cyan, color_activo),
            text("Escriba en el campo activo · Tab: siguiente campo · Enter: guardar · Esc: cancelar"),
            separador(ascii),
        };
        for (std::size_t campo = 0; campo < campos.size(); ++campo) {
            const std::string valor = campo < valores_formulario.size()
                                          ? valores_formulario[campo]
                                          : std::string();
            const std::string linea = (campo == campo_activo ? "> " : "  ") +
                                      campos[campo] + ": " + valor;
            contenido.push_back(campo == campo_activo
                                    ? color_si(text(linea), Color::Yellow, color_activo)
                                    : text(linea));
        }
        contenido.push_back(separador(ascii));
        if (!mensaje_estado.empty()) {
            contenido.push_back(color_si(text(mensaje_estado), Color::Red, color_activo));
        }
        return vbox(std::move(contenido)) | flex;
    }

    switch (indice) {
        case 0: {
            const int productos = resumen["productos_activos"].toInt();
            const int grupos = resumen["grupos_activos"].toInt();
            const int investigadores = resumen["investigadores_activos"].toInt();
            const int avalados = estadisticas["productos_por_validacion"].toObject()["Avalado"].toInt();
            const auto kpi_grupos = tarjeta("Grupos activos", texto_cantidad(grupos),
                                            Color::Cyan, color_activo, ascii);
            const auto kpi_investigadores = tarjeta("Investigadores activos",
                                                    texto_cantidad(investigadores),
                                                    Color::Green, color_activo, ascii);
            const auto kpi_productos = tarjeta("Productos activos", texto_cantidad(productos),
                                               Color::Yellow, color_activo, ascii);
            const auto kpi_avalados = tarjeta("Productos avalados", texto_cantidad(avalados),
                                              Color::Green, color_activo, ascii);
            const auto kpis = ancho < 100
                                  ? vbox({
                                        hbox({kpi_grupos, kpi_investigadores}),
                                        hbox({kpi_productos, kpi_avalados}),
                                    })
                                  : hbox({
                                        kpi_grupos, kpi_investigadores, kpi_productos, kpi_avalados,
                                    });
            if (ancho < 100) {
                return vbox({
                           color_si(text("Resumen institucional") | bold, Color::Cyan, color_activo),
                           text("Origen: " + origen),
                           (!datos_demostracion && !conectado)
                               ? text("No conectado. Sin datos actuales.")
                               : text(""),
                           kpis,
                       }) |
                       flex;
            }
            return vbox({
                       color_si(text("Resumen institucional") | bold, Color::Cyan, color_activo),
                       text("Origen: " + origen),
                       (!datos_demostracion && !conectado)
                           ? text(mensaje_conexion.empty()
                                      ? "Conecte Supabase o inicie con --demo para ver datos de demostración."
                                      : mensaje_conexion)
                           : text(""),
                       separador(ascii),
                       kpis,
                       separador(ascii),
                       text("Producción por año") | bold,
                       text(productos == 0 ? "Aún no hay productos en el catálogo." :
                                             "Las estadísticas se calculan desde el hipercubo local."),
                       separador(ascii),
                       text("Resumen del catálogo") | bold,
                       tabla_resumen(resumen, ascii),
                   }) |
                   flex;
        }
        case 1: {
            Elements filas{color_si(text("Directorio de investigadores") | bold, Color::Cyan, color_activo),
                           text("Código · nombre · categoría · estado"),
                           text("n/e/t/x: gestionar · v: ficha · /: buscar · [: anterior · ]: siguiente"),
                           text(texto_filtro.toStdString()),
                           separador(ascii)};
            std::vector<std::string> resultados;
            for (const auto& investigador : catalogo.investigadores) {
                if (!investigador) {
                    continue;
                }
                const QString linea = investigador->codigo_rh + " · " +
                                      investigador->nombre_completo.left(38) + " · " +
                                      investigador->categoria + (investigador->activo ? "" : " · Inactivo");
                if (!coincide_campos(investigador->aJson(), filtro)) {
                    continue;
                }
                resultados.push_back(linea.toStdString());
            }
            if (resultados.empty()) {
                filas.push_back(text(filtro.isEmpty() ? "No hay investigadores cargados."
                                                      : "No hay coincidencias para el filtro."));
            } else {
                agregar_pagina(filas, resultados, pagina_actual);
            }
            return vbox(std::move(filas)) | flex;
        }
        case 2: {
            Elements filas{color_si(text("Directorio de grupos") | bold, Color::Cyan, color_activo),
                           text("Código GrupLAC · nombre · categoría · estado"),
                           text("n/e/t/x: gestionar · v: ficha · /: buscar · [: anterior · ]: siguiente"),
                           text(texto_filtro.toStdString()),
                           separador(ascii)};
            std::vector<std::string> resultados;
            for (const auto& grupo : catalogo.grupos) {
                if (!grupo) {
                    continue;
                }
                const QString linea = grupo->codigo_gruplac + " · " + grupo->nombre.left(42) +
                                      " · " + grupo->categoria + (grupo->activo ? "" : " · Inactivo");
                if (!coincide_campos(grupo->aJson(), filtro)) {
                    continue;
                }
                resultados.push_back(linea.toStdString());
            }
            if (resultados.empty()) {
                filas.push_back(text(filtro.isEmpty() ? "No hay grupos cargados."
                                                      : "No hay coincidencias para el filtro."));
            } else {
                agregar_pagina(filas, resultados, pagina_actual);
            }
            return vbox(std::move(filas)) | flex;
        }
        case 3: {
            Elements filas{color_si(text("Catálogo de productos") | bold, Color::Cyan, color_activo),
                           text("Código · año · tipología · título · validación"),
                           text("n/e/t/x: gestionar · v: ficha · /: buscar · [: anterior · ]: siguiente"),
                           text(texto_filtro.toStdString()),
                           separador(ascii)};
            std::vector<std::string> resultados;
            for (auto* nodo = catalogo.multilista_productos.cabeza(); nodo != nullptr;
                 nodo = nodo->siguiente_global) {
                if (!nodo->producto) {
                    continue;
                }
                const auto& producto = *nodo->producto;
                const QString linea = producto.codigo_identificador + " · " +
                                      QString::number(producto.ano) + " · " + producto.tipo_mayor +
                                      " · " + producto.titulo.left(34) + " · " +
                                      producto.estado_validacion +
                                      (producto.activo ? "" : " · Inactivo");
                if (!coincide_campos(producto.aJson(), filtro)) {
                    continue;
                }
                resultados.push_back(linea.toStdString());
            }
            if (resultados.empty()) {
                filas.push_back(text(filtro.isEmpty() ? "No hay productos cargados."
                                                      : "No hay coincidencias para el filtro."));
            } else {
                agregar_pagina(filas, resultados, pagina_actual);
            }
            return vbox(std::move(filas)) | flex;
        }
        case 4: {
            Elements filas{
                color_si(text("Análisis institucional y red de coautoría") | bold,
                         Color::Cyan, color_activo),
                text("Cálculos desde el hipercubo y las relaciones de la multilista."),
                text(QString("Filtro temporal: %1  (f: cambiar · g: rango)")
                         .arg(filtro_anios.descripcion(QDate::currentDate().year()))
                         .toStdString()),
                separador(ascii),
            };
            const auto cubo_filtrado = catalogo.estadisticas.aplicarFiltro(
                filtro_anios, QDate::currentDate().year());
            const auto anios = catalogo.estadisticas.productosPorAnio(&cubo_filtrado);
            int maximo_anual = 0;
            for (auto it = anios.constBegin(); it != anios.constEnd(); ++it) {
                maximo_anual = std::max(maximo_anual, it.value());
            }
            filas.push_back(text("Productos por año") | bold);
            int anios_mostrados = 0;
            for (auto it = anios.constBegin(); it != anios.constEnd() && anios_mostrados < 6;
                 ++it, ++anios_mostrados) {
                const int longitud = maximo_anual == 0
                                         ? 0
                                         : std::min(28, it.value() * 28 / maximo_anual);
                const std::string barra(longitud, ascii ? '#' : '*');
                filas.push_back(text(QString("%1  %2  %3")
                                         .arg(it.key())
                                         .arg(barra.c_str())
                                         .arg(it.value())
                                         .toStdString()));
            }
            if (anios.isEmpty()) filas.push_back(text("No hay productos activos con año registrado."));

            QMap<QString, int> pares;
            QMap<QString, int> grados;
            int productos_con_coautoria = 0;
            const auto rango = filtro_anios.resolver(QDate::currentDate().year());
            for (auto* nodo = catalogo.multilista_productos.cabeza(); nodo != nullptr;
                 nodo = nodo->siguiente_global) {
                if (!nodo->producto || !nodo->producto->activo) continue;
                const int anio_producto = nodo->producto->ano;
                if (rango.modelo_2024) {
                    if (anio_producto > 2023) continue;
                    const bool ventana_ampliada =
                        nodo->producto->subtipo.contains("LIB", Qt::CaseInsensitive) ||
                        nodo->producto->subtipo.contains("PATENTE", Qt::CaseInsensitive) ||
                        nodo->producto->subtipo.contains("VARIEDAD", Qt::CaseInsensitive);
                    if (anio_producto < (ventana_ampliada ? 2014 : 2019)) continue;
                } else if ((rango.inicio.has_value() && anio_producto < *rango.inicio) ||
                           (rango.fin.has_value() && anio_producto > *rango.fin)) {
                    continue;
                }
                QStringList autores;
                for (const auto& autor : nodo->autores) {
                    if (autor && autor->activo && !autores.contains(autor->codigo_rh)) {
                        autores.push_back(autor->codigo_rh);
                    }
                }
                std::sort(autores.begin(), autores.end());
                if (autores.size() > 1) ++productos_con_coautoria;
                for (qsizetype i = 0; i < autores.size(); ++i) {
                    for (qsizetype j = i + 1; j < autores.size(); ++j) {
                        const QString clave = autores[i] + " · " + autores[j];
                        ++pares[clave];
                        ++grados[autores[i]];
                        ++grados[autores[j]];
                    }
                }
            }
            filas.push_back(separador(ascii));
            filas.push_back(text(QString("Coautoría · %1 nodos · %2 pares · %3 productos")
                                     .arg(grados.size())
                                     .arg(pares.size())
                                     .arg(productos_con_coautoria)
                                     .toStdString()) |
                            bold);
            if (pares.isEmpty()) {
                filas.push_back(text("No hay productos con dos o más autores activos."));
            } else {
                std::vector<std::pair<QString, int>> ranking;
                ranking.reserve(static_cast<std::size_t>(pares.size()));
                for (auto it = pares.constBegin(); it != pares.constEnd(); ++it) {
                    ranking.emplace_back(it.key(), it.value());
                }
                std::sort(ranking.begin(), ranking.end(), [](const auto& izquierda, const auto& derecha) {
                    return izquierda.second == derecha.second
                               ? izquierda.first < derecha.first
                               : izquierda.second > derecha.second;
                });
                filas.push_back(text("Pares de coautoría más frecuentes") | bold);
                for (std::size_t i = 0; i < ranking.size() && i < 8; ++i) {
                    filas.push_back(text(QString("%1 · %2 producto(s)")
                                             .arg(ranking[i].first)
                                             .arg(ranking[i].second)
                                             .toStdString()));
                }
                std::vector<std::pair<QString, int>> nodos;
                nodos.reserve(static_cast<std::size_t>(grados.size()));
                for (auto it = grados.constBegin(); it != grados.constEnd(); ++it) {
                    nodos.emplace_back(it.key(), it.value());
                }
                std::sort(nodos.begin(), nodos.end(), [](const auto& izquierda, const auto& derecha) {
                    return izquierda.second == derecha.second
                               ? izquierda.first < derecha.first
                               : izquierda.second > derecha.second;
                });
                filas.push_back(text("Investigadores con mayor número de vínculos") | bold);
                for (std::size_t i = 0; i < nodos.size() && i < 5; ++i) {
                    filas.push_back(text(QString("%1 · %2 vínculo(s)")
                                             .arg(nodos[i].first)
                                             .arg(nodos[i].second)
                                             .toStdString()));
                }
            }
            return vbox(std::move(filas)) | flex;
        }
        case 5:
            return vbox({
                       color_si(text("Importación") | bold, Color::Cyan, color_activo),
                       separador(ascii),
                       text("Formatos disponibles: CSV y URL SCIENTI."),
                       text("La importación desde PDF debe realizarse desde la versión Python."),
                       text(conectado
                                ? "Presione i para CSV o w para URL; solo se importa con conexión autenticada."
                                : "La importación requiere sesión remota autenticada; demo y modo sin conexión están bloqueados."),
                       text("Tareas en cola: " + texto_cantidad(static_cast<int>(catalogo.cola_importacion.tamano()))),
                   }) |
                   flex;
        case 6:
            return vbox({
                       color_si(text("Configuración") | bold, Color::Cyan, color_activo),
                       separador(ascii),
                       text("Origen de datos: " + origen),
                       text(conectado ? "Conexión remota verificada."
                                      : (mensaje_conexion.empty()
                                             ? "Sin conexión a Supabase."
                                             : mensaje_conexion)),
                       text("Tema: oscuro"),
                       text("Ventana de años: " +
                            filtro_anios.descripcion(QDate::currentDate().year()).toStdString()),
                   }) |
                   flex;
        default:
            return vbox({
                       color_si(text("Acerca de PEA-i") | bold, Color::Cyan, color_activo),
                       separador(ascii),
                       text(std::string(APP_NAME) + " · " + APP_VERSION),
                       text("Universidad Popular del Cesar · Ingeniería de Sistemas"),
                       text("Estructura de Datos · Taller 2 · Grupo 8"),
                       text("Terminal interactiva C++17 con Qt Core/Network y FTXUI."),
                   }) |
                   flex;
    }
}

Element renderizar_pantalla(
    int indice,
    const QJsonObject& resumen,
    const servicios::CatalogoInvestigacion& catalogo,
    bool datos_demostracion,
    bool conectado,
    const std::string& mensaje_conexion,
    const QString& filtro,
    bool filtro_activo,
    int accion_formulario,
    const std::vector<std::string>& valores_formulario,
    std::size_t campo_activo,
    const std::string& mensaje_estado,
    const std::string& ficha_detalle,
    const std::vector<Component>& botones,
    bool color_activo,
    bool ascii,
    int ancho,
    const servicios::FiltroAnios& filtro_anios = {},
    int pagina_actual = 0) {
    Elements pestanas;
    for (std::size_t i = 0; i < botones.size(); ++i) {
        auto render = ascii
                          ? text((static_cast<int>(i) == indice ? "> " : "  ") +
                                 std::to_string(i + 1) + " " + PESTANAS[i])
                          : botones[i]->Render();
        if (color_activo) {
            render = render | color(static_cast<int>(i) == indice ? Color::GreenLight : Color::GrayLight);
            if (static_cast<int>(i) == indice) {
                render = render | bold;
            }
        }
        pestanas.push_back(std::move(render));
    }
    Elements fila_superior;
    Elements fila_inferior;
    for (std::size_t i = 0; i < pestanas.size(); ++i) {
        (i < 4 ? fila_superior : fila_inferior).push_back(std::move(pestanas[i]));
    }

    auto titulo = text(" PEA-i ") | bold;
    const std::string nombre_programa = ancho < 100
                                            ? "  Terminal de análisis de investigación"
                                            : "  Programa Estadístico de Análisis de Investigación";
    auto estado = text(datos_demostracion
                           ? "[ DEMOSTRACIÓN ]"
                           : (conectado ? "[ SUPABASE ]" : "[ SIN DATOS ]"));
    if (color_activo) {
        titulo = titulo | color(Color::White) | bgcolor(Color::RGB(18, 39, 67));
        estado = estado | color(datos_demostracion ? Color::Yellow
                                                   : (conectado ? Color::GreenLight : Color::GrayLight));
    }
    const std::string texto_pie =
        accion_formulario > 0
            ? "Tab: siguiente campo  Enter: ejecutar  Esc: cancelar"
            : (!mensaje_estado.empty()
                   ? mensaje_estado
                   : (indice == 4
                          ? "f: cambiar filtro temporal  g: configurar rango  q: salir"
                          : (indice == 5
                                 ? "i: importar CSV  w: importar URL SCIENTI  q: salir"
                                 : (ancho < 100
                                        ? "1–8 pestañas · n/e/t/x gestión · v ficha · u deshacer · q salir"
                                        : "1–8 pestañas  n/e/t/x gestión  v ficha  u deshacer  q salir"))));
    auto pie = text(texto_pie);
    if (color_activo) {
        pie = pie | color(Color::GrayLight);
    }
    const auto contador = text("Deshacer: " + texto_cantidad(static_cast<int>(catalogo.pila_deshacer.tamano())) +
                               "  Importación: " +
                               texto_cantidad(static_cast<int>(catalogo.cola_importacion.tamano())));
    const auto pie_completo = ancho < 100
                                  ? hbox({pie})
                                  : hbox({pie, filler(), contador});
    auto pantalla = vbox({
               hbox({
                   titulo,
                   text(nombre_programa) | bold,
                   filler(),
                   estado,
               }),
               vbox({
                   hbox(std::move(fila_superior)),
                   hbox(std::move(fila_inferior)),
               }),
               marco(panel_contenido(indice, resumen, catalogo, datos_demostracion, conectado,
                                     mensaje_conexion, filtro, filtro_activo, accion_formulario,
                                     valores_formulario, campo_activo, mensaje_estado, ficha_detalle,
                                     color_activo, ascii, ancho, filtro_anios,
                                     pagina_actual) | flex,
                     ascii),
               pie_completo,
           });
    return pantalla | flex;
}

int autoprueba() {
    servicios::CatalogoInvestigacion catalogo;
    cargar_datos_demostracion(catalogo);
    const QJsonObject resumen = catalogo.resumen_dict();
    std::vector<Component> botones;
    for (std::size_t indice = 0; indice < PESTANAS.size(); ++indice) {
        botones.push_back(Button(
            std::to_string(indice + 1) + " " + PESTANAS[indice],
            [] {}));
    }
    const QString directorio_capturas =
        QDir::current().filePath(QStringLiteral("datos/capturas/terminal"));
    if (!QDir().mkpath(directorio_capturas)) {
        std::cerr << "No se pudo crear el directorio de capturas de terminal.\n";
        return 1;
    }
    const std::array<std::pair<int, int>, 4> tamanos{{
        {80, 24}, {100, 28}, {120, 35}, {160, 50},
    }};
    const std::array<const char*, 8> titulos_vista{
        "Resumen institucional", "Directorio de investigadores", "Directorio de grupos",
        "Catálogo de productos", "Análisis de redes", "Importación", "Configuración",
        "Acerca de PEA-i"
    };
    int hallazgos = 0;
    std::cout << "Pantalla             Tamaño   Hallazgos\n";
    std::cout << "----------------------------------------\n";
    for (std::size_t indice = 0; indice < PESTANAS.size(); ++indice) {
        for (const auto& [ancho, alto] : tamanos) {
            Screen screen = Screen::Create(Dimension::Fixed(ancho), Dimension::Fixed(alto));
            Render(screen, renderizar_pantalla(
                               static_cast<int>(indice), resumen, catalogo, true, false, {},
                               {}, false, 0, {}, 0, {}, {}, botones, false, true, ancho));
            const std::string salida = quitar_secuencias_ansi(screen.ToString());
            bool reemplazo = false;
            bool excede_ancho = false;
            for (int y = 0; y < screen.dimy(); ++y) {
                int ancho_fila = 0;
                for (int x = 0; x < screen.dimx(); ++x) {
                    const auto& caracter = screen.PixelAt(x, y).character;
                    reemplazo = reemplazo || caracter == "\xEF\xBF\xBD";
                    if (string_width(caracter) == 2) {
                        ancho_fila += 2;
                        ++x;
                    } else {
                        ancho_fila += string_width(caracter);
                    }
                }
                excede_ancho = excede_ancho || ancho_fila > ancho;
            }
            const QString ruta_captura = QDir(directorio_capturas).filePath(
                QStringLiteral("%1-%2x%3.txt")
                    .arg(QString::fromLatin1(ARCHIVOS_PANTALLA[indice]))
                    .arg(ancho)
                    .arg(alto));
            QFile captura(ruta_captura);
            const QByteArray contenido = QByteArray::fromStdString(salida);
            const bool captura_guardada =
                captura.open(QIODevice::WriteOnly | QIODevice::Truncate) &&
                captura.write(contenido) == contenido.size();
            const bool tiene_borde_unicode =
                salida.find("┌") != std::string::npos || salida.find("┐") != std::string::npos ||
                salida.find("└") != std::string::npos || salida.find("┘") != std::string::npos ||
                salida.find("─") != std::string::npos || salida.find("│") != std::string::npos;
            const bool hallazgo = reemplazo || excede_ancho || salida.empty() ||
                                   salida.find('\x1b') != std::string::npos || !captura_guardada ||
                                   salida.find(titulos_vista[indice]) == std::string::npos ||
                                   salida.find('+') == std::string::npos ||
                                   salida.find('-') == std::string::npos ||
                                   salida.find('|') == std::string::npos ||
                                   tiene_borde_unicode ||
                                   std::any_of(PESTANAS.begin(), PESTANAS.end(),
                                               [&salida](const char* pestana) {
                                                   return salida.find(pestana) == std::string::npos;
                                               }) ||
                                   (ancho == 80 && indice == 0 &&
                                    (salida.find("Grupos activos") == std::string::npos ||
                                     salida.find("Investigadores activos") == std::string::npos ||
                                     salida.find("Productos activos") == std::string::npos ||
                                     salida.find("Productos avalados") == std::string::npos));
            if (hallazgo) {
                ++hallazgos;
            }
            std::cout << PESTANAS[indice] << "  " << ancho << "x" << alto << "  "
                      << (hallazgo ? "1" : "0")
                      << "\n";
        }
    }
    struct CasoFiltro {
        int pantalla;
        const char* consulta;
        const char* codigo_esperado;
    };
    const std::array<CasoFiltro, 6> casos_filtro{{
        {1, "prueba-rh-001", "PRUEBA-RH-001"},
        {2, "prueba-grupo-001", "PRUEBA-GRUPO-001"},
        {3, "prueba-prod-001", "PRUEBA-PROD-001"},
        {1, "formacion_academica:Maestría", "PRUEBA-RH-001"},
        {2, "categoria:A1", "PRUEBA-GRUPO-001"},
        {3, "estado_validacion:Avalado", "PRUEBA-PROD-001"},
    }};
    for (const auto& caso : casos_filtro) {
        Screen screen = Screen::Create(Dimension::Fixed(80), Dimension::Fixed(24));
        Render(screen, renderizar_pantalla(
                           caso.pantalla, resumen, catalogo, true, false, {},
                           QString::fromUtf8(caso.consulta), false, 0, {}, 0, {},
                           {}, botones, false, true, 80));
        const std::string salida = quitar_secuencias_ansi(screen.ToString());
        const bool hallazgo =
            salida.find(caso.codigo_esperado) == std::string::npos;
        hallazgos += hallazgo ? 1 : 0;
        std::cout << "Filtro " << PESTANAS[static_cast<std::size_t>(caso.pantalla)] << "  "
                  << (hallazgo ? "1" : "0") << "\n";
    }
    servicios::CatalogoInvestigacion catalogo_paginado;
    for (int indice = 1; indice <= FILAS_POR_PAGINA + 1; ++indice) {
        auto grupo = std::make_shared<dominio::Grupo>();
        grupo->codigo_gruplac = QString("PAGINA-GRP-%1").arg(indice, 2, 10, QChar('0'));
        grupo->nombre = QString("Grupo de página %1").arg(indice);
        grupo->categoria = "A";
        catalogo_paginado.crear_grupo(grupo, false);
    }
    Screen pagina_grupos = Screen::Create(Dimension::Fixed(80), Dimension::Fixed(24));
    Render(pagina_grupos, renderizar_pantalla(
                              2, catalogo_paginado.resumen_dict(), catalogo_paginado,
                              true, false, {}, {}, false, 0, {}, 0, {}, {}, botones,
                              false, true, 80, {}, 1));
    const std::string salida_pagina = quitar_secuencias_ansi(pagina_grupos.ToString());
    const bool hallazgo_paginacion =
        salida_pagina.find("Página 2 de 2") == std::string::npos ||
        salida_pagina.find("PAGINA-GRP-13") == std::string::npos ||
        salida_pagina.find("PAGINA-GRP-01") != std::string::npos;
    hallazgos += hallazgo_paginacion ? 1 : 0;
    std::cout << "Paginación directorio de grupos  "
              << (hallazgo_paginacion ? "1" : "0") << "\n";

    for (int entidad = 1; entidad <= 3; ++entidad) {
        for (int accion = 1; accion <= 5; ++accion) {
            Screen screen = Screen::Create(Dimension::Fixed(120), Dimension::Fixed(40));
            Render(screen, renderizar_pantalla(
                               entidad, resumen, catalogo, true, false, {}, {}, false,
                               accion, std::vector<std::string>(8), 0, {}, {}, botones,
                               false, true, 120));
            const std::string salida = quitar_secuencias_ansi(screen.ToString());
            const std::string titulo = std::string(ACCIONES_FORMULARIO[static_cast<std::size_t>(accion)]) +
                                       " " + etiqueta_entidad(entidad).toStdString();
            bool hallazgo = salida.find(titulo) == std::string::npos;
            const auto campos = campos_formulario(entidad, accion);
            for (const auto& campo : campos) {
                hallazgo = hallazgo || salida.find(campo + ":") == std::string::npos;
            }
            hallazgos += hallazgo ? 1 : 0;
            std::cout << "Formulario " << etiqueta_entidad(entidad).toStdString() << " "
                      << ACCIONES_FORMULARIO[static_cast<std::size_t>(accion)] << "  "
                      << (hallazgo ? "1" : "0") << "\n";
        }
    }
    for (int accion = 6; accion <= 8; ++accion) {
        const int pantalla = accion == 8 ? 4 : 5;
        Screen screen = Screen::Create(Dimension::Fixed(120), Dimension::Fixed(40));
        Render(screen, renderizar_pantalla(
                           pantalla, resumen, catalogo, false, true, {}, {}, false, accion,
                           std::vector<std::string>(8), 0, {}, {}, botones, false,
                           true, 120));
        const std::string salida = quitar_secuencias_ansi(screen.ToString());
        bool hallazgo = salida.find(ACCIONES_FORMULARIO[static_cast<std::size_t>(accion)]) ==
                        std::string::npos;
        for (const auto& campo : campos_formulario(pantalla, accion)) {
            hallazgo = hallazgo || salida.find(campo + ":") == std::string::npos;
        }
        hallazgos += hallazgo ? 1 : 0;
        std::cout << (accion == 8 ? "Formulario filtro " : "Formulario importación ")
                  << ACCIONES_FORMULARIO[static_cast<std::size_t>(accion)] << "  "
                  << (hallazgo ? "1" : "0") << "\n";
    }
    servicios::FiltroAnios filtro_modelo;
    filtro_modelo.modo = servicios::ModoFiltroAnios::MODELO_2024;
    Screen modelo = Screen::Create(Dimension::Fixed(160), Dimension::Fixed(50));
    Render(modelo, renderizar_pantalla(
                       4, resumen, catalogo, true, false, {}, {}, false, 0, {}, 0,
                       {}, {}, botones, false, true, 160, filtro_modelo));
    const std::string salida_modelo = quitar_secuencias_ansi(modelo.ToString());
    const bool hallazgo_filtro_modelo =
        salida_modelo.find("No hay productos activos con año registrado.") == std::string::npos ||
        salida_modelo.find("Ventana del Modelo 2024") == std::string::npos;
    hallazgos += hallazgo_filtro_modelo ? 1 : 0;
    std::cout << "Filtro temporal Modelo 2024  "
              << (hallazgo_filtro_modelo ? "1" : "0") << "\n";
    Screen red = Screen::Create(Dimension::Fixed(160), Dimension::Fixed(50));
    Render(red, renderizar_pantalla(
                    4, resumen, catalogo, true, false, {}, {}, false, 0, {}, 0, {}, {},
                    botones, false, true, 160));
    const std::string salida_red = quitar_secuencias_ansi(red.ToString());
    const bool hallazgo_red = salida_red.find("PRUEBA-RH-001") == std::string::npos ||
                              salida_red.find("PRUEBA-RH-002") == std::string::npos ||
                              salida_red.find("2024") == std::string::npos ||
                              salida_red.find("Coautoría") == std::string::npos;
    hallazgos += hallazgo_red ? 1 : 0;
    std::cout << "Análisis y coautoría  " << (hallazgo_red ? "1" : "0") << "\n";
    return hallazgos == 0 ? 0 : 1;
}

} // namespace

int ejecutar(bool datos_demostracion, bool ejecutar_autoprueba, bool sin_color, bool ascii) {
    if (ejecutar_autoprueba) {
        return autoprueba();
    }

#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    HANDLE salida = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD modo = 0;
    if (salida != INVALID_HANDLE_VALUE && GetConsoleMode(salida, &modo)) {
        SetConsoleMode(salida, modo | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
    }
#endif
    const bool color_activo = !sin_color && std::getenv("NO_COLOR") == nullptr;

    servicios::CatalogoInvestigacion catalogo;
    std::unique_ptr<ClienteHTTPSupabase> cliente;
    std::shared_ptr<datos::Sesion> sesion;
    bool conectado = false;
    std::string mensaje_conexion;
    if (datos_demostracion) {
        cargar_datos_demostracion(catalogo);
    } else {
        try {
            cliente = datos::crear_cliente_configurado(nullptr, &sesion);
            if (cliente) {
                catalogo = servicios::CatalogoInvestigacion(cliente.get(), sesion);
                catalogo.recargar_todo();
                conectado = true;
            }
        } catch (const std::exception& error) {
            mensaje_conexion = std::string("No se pudo conectar a Supabase: ") + error.what();
            std::cerr << mensaje_conexion << '\n';
        }
    }

    std::vector<Component> botones;
    int seleccion = 0;
    int pagina_actual = 0;
    QString filtro;
    bool filtro_activo = false;
    servicios::FiltroAnios filtro_anios;
    int accion_formulario = 0;
    std::vector<std::string> valores_formulario(8);
    std::size_t campo_activo = 0;
    std::string mensaje_estado;
    std::string ficha_detalle;
    for (std::size_t i = 0; i < PESTANAS.size(); ++i) {
        botones.push_back(Button(
            std::to_string(i + 1) + " " + PESTANAS[i],
            [i, &seleccion] { seleccion = static_cast<int>(i); }));
    }

    const auto abrir_formulario = [&](int accion) {
        if (accion == 6 || accion == 7) {
            if (seleccion != 5) {
                mensaje_estado = "Abra Importación para iniciar una tarea.";
                return;
            }
            if (datos_demostracion || !conectado) {
                mensaje_estado = "Importación bloqueada: requiere un catálogo remoto autenticado.";
                return;
            }
        } else if (accion == 8) {
            if (seleccion != 4) {
                mensaje_estado = "Abra Análisis de redes para configurar el rango temporal.";
                return;
            }
        } else if (seleccion < 1 || seleccion > 3) {
            mensaje_estado = "Abra un directorio para ejecutar esta acción.";
            return;
        }
        if (accion <= 5 && !datos_demostracion && !conectado) {
            mensaje_estado = "Acción bloqueada: no hay catálogo remoto disponible.";
            return;
        }
        accion_formulario = accion;
        std::fill(valores_formulario.begin(), valores_formulario.end(), std::string());
        campo_activo = 0;
        mensaje_estado.clear();
        ficha_detalle.clear();
        filtro_activo = false;
    };
    const auto guardar_formulario = [&] {
        if (accion_formulario == 8) {
            const auto parsear_anio = [&valores_formulario](std::size_t indice,
                                                            const char* etiqueta)
                -> std::optional<int> {
                const QString valor = campo_qstring(valores_formulario, indice).trimmed();
                if (valor.isEmpty()) return std::nullopt;
                bool valido = false;
                const int anio = valor.toInt(&valido);
                if (!valido || anio < 1 || anio > 9999) {
                    throw std::invalid_argument(std::string(etiqueta) +
                                                " debe ser un año entre 1 y 9999.");
                }
                return anio;
            };
            try {
                const auto desde = parsear_anio(0, "El año inicial");
                const auto hasta = parsear_anio(1, "El año final");
                if (!desde && !hasta) {
                    throw std::invalid_argument("Indique al menos un límite del rango.");
                }
                filtro_anios.modo = servicios::ModoFiltroAnios::RANGO;
                filtro_anios.desde = desde;
                filtro_anios.hasta = hasta;
                mensaje_estado =
                    "Filtro aplicado: " +
                    filtro_anios.descripcion(QDate::currentDate().year()).toStdString();
                accion_formulario = 0;
            } catch (const std::exception& error) {
                mensaje_estado = std::string("No se aplicó el filtro: ") + error.what();
            }
            return;
        }
        if (accion_formulario == 6 || accion_formulario == 7) {
            const auto valor_importacion = [&valores_formulario](std::size_t indice) {
                return campo_qstring(valores_formulario, indice).trimmed();
            };
            try {
                if (datos_demostracion || !conectado || !cliente) {
                    throw std::runtime_error("La importación requiere sesión remota autenticada.");
                }
                auto catalogo_compartido = std::shared_ptr<servicios::CatalogoInvestigacion>(
                    &catalogo, [](servicios::CatalogoInvestigacion*) {});
                ingesta::ServicioIngesta servicio(catalogo_compartido);
                QList<ingesta::InformeIngesta> informes;
                if (accion_formulario == 6) {
                    const QString ruta = valor_importacion(0);
                    QString tipo = valor_importacion(1).toLower();
                    if (ruta.isEmpty()) {
                        throw std::invalid_argument("Indique la ruta del archivo CSV.");
                    }
                    if (tipo == "auto") tipo.clear();
                    if (!tipo.isEmpty() && tipo != "grupos" && tipo != "investigadores" &&
                        tipo != "productos" && tipo != "autores") {
                        throw std::invalid_argument(
                            "El tipo debe ser auto, grupos, investigadores, productos o autores.");
                    }
                    servicio.encolar_csv(ruta, tipo, true);
                    const auto informe = servicio.procesar_siguiente();
                    if (informe) informes.push_back(*informe);
                } else {
                    const QString url = valor_importacion(0);
                    const QString anonimizar_texto = valor_importacion(1).toLower();
                    if (url.isEmpty()) {
                        throw std::invalid_argument("Indique una URL SCIENTI.");
                    }
                    if (anonimizar_texto != "si" && anonimizar_texto != "sí" &&
                        anonimizar_texto != "no") {
                        throw std::invalid_argument("Indique si o no para anonimizar datos personales.");
                    }
                    servicio.encolar_url(url, true, anonimizar_texto != "no");
                    informes = servicio.procesar_todas();
                }
                if (informes.isEmpty()) {
                    throw std::runtime_error("No se recibió ningún informe de ingesta.");
                }
                int procesados = 0;
                int errores = 0;
                int filas_erroneas = 0;
                bool con_advertencias = false;
                bool requiere_recarga = false;
                for (const auto& informe : informes) {
                    if (!informe.exito) ++errores;
                    requiere_recarga = requiere_recarga || informe.requiere_recarga;
                    procesados += informe.grupos_procesados +
                                  informe.investigadores_procesados +
                                  informe.productos_procesados +
                                  informe.autores_procesados;
                    filas_erroneas += informe.filas_erroneas.size();
                    con_advertencias = con_advertencias || !informe.advertencias.isEmpty();
                }
                mensaje_estado = "Importación completada: " + std::to_string(procesados) +
                                 " registro(s) en " + std::to_string(informes.size()) +
                                 " tarea(s).";
                if (errores > 0) {
                    mensaje_estado += " Tareas con error: " + std::to_string(errores) + ".";
                }
                if (filas_erroneas > 0) {
                    mensaje_estado += " Filas con errores: " +
                                      std::to_string(filas_erroneas) + ".";
                }
                if (con_advertencias) {
                    mensaje_estado += " Revise las advertencias del informe.";
                }
                if (errores > 0) {
                    mensaje_estado = "Importación parcial. " + mensaje_estado;
                }
                if (requiere_recarga) {
                    mensaje_estado +=
                        " Presione r para recargar y vuelva a encolar la tarea interrumpida.";
                }
                accion_formulario = 0;
            } catch (const std::exception& error) {
                mensaje_estado = std::string("No se completó la importación: ") + error.what();
            }
            return;
        }
        const int entidad = seleccion;
        const bool persistir = conectado;
        const bool es_ejemplo = datos_demostracion;
        const QString codigo = campo_qstring(valores_formulario, 0).trimmed();
        const auto valor = [&valores_formulario](std::size_t indice) {
            return campo_qstring(valores_formulario, indice).trimmed();
        };
        const auto tiene_valor = [&valores_formulario](std::size_t indice) {
            return !campo_qstring(valores_formulario, indice).trimmed().isEmpty();
        };
        try {
            if (codigo.isEmpty()) {
                throw std::invalid_argument("El código es obligatorio.");
            }
            if (accion_formulario == 1) {
                if (entidad == 1) {
                    if (valor(1).isEmpty()) throw std::invalid_argument("El nombre del investigador es obligatorio.");
                    catalogo.crear_investigador(std::make_shared<dominio::Investigador>(
                        codigo, valor(1), valor(2), valor(3), es_ejemplo), persistir);
                } else if (entidad == 2) {
                    if (valor(1).isEmpty()) throw std::invalid_argument("El nombre del grupo es obligatorio.");
                    catalogo.crear_grupo(std::make_shared<dominio::Grupo>(
                        codigo, valor(1), valor(2), valor(3), es_ejemplo), persistir);
                } else {
                    if (valor(1).isEmpty()) throw std::invalid_argument("El título del producto es obligatorio.");
                    bool anio_valido = false;
                    const int anio = valor(4).toInt(&anio_valido);
                    if (!anio_valido) {
                        throw std::invalid_argument("El año del producto debe ser numérico.");
                    }
                    const QString tipo = valor(2).toUpper();
                    if (tipo != "GNC" && tipo != "DTI" && tipo != "ASC" && tipo != "FRH") {
                        throw std::invalid_argument("El tipo mayor debe ser GNC, DTI, ASC o FRH.");
                    }
                    const QString validacion = valor(5).isEmpty()
                                                   ? "No avalado"
                                                   : valor(5);
                    if (validacion != "Avalado" && validacion != "Con soporte" &&
                        validacion != "No avalado") {
                        throw std::invalid_argument("La validación debe ser Avalado, Con soporte o No avalado.");
                    }
                    auto autores_texto = campo_qstring(valores_formulario, 7)
                                             .split(';', Qt::SkipEmptyParts);
                    std::vector<QString> autores;
                    for (const auto& autor : autores_texto) {
                        if (autor.trimmed().isEmpty()) continue;
                        const QString codigo_autor = autor.trimmed();
                        if (!catalogo.buscar_investigador(codigo_autor)) {
                            throw std::invalid_argument("No existe el investigador autor " +
                                                        codigo_autor.toStdString() + ".");
                        }
                        autores.push_back(codigo_autor);
                    }
                    const QString codigo_grupo = valor(6);
                    if (!codigo_grupo.isEmpty() && !catalogo.buscar_grupo(codigo_grupo)) {
                        throw std::invalid_argument("No existe el grupo indicado.");
                    }
                    catalogo.crear_producto(std::make_shared<dominio::Producto>(
                        codigo, valor(1), tipo, valor(3), anio, validacion, es_ejemplo),
                        codigo_grupo, autores, persistir);
                }
            } else if (accion_formulario == 2) {
                QJsonObject cambios;
                if (entidad == 1) {
                    if (tiene_valor(1)) cambios["nombre_completo"] = valor(1);
                    if (tiene_valor(2)) cambios["categoria"] = valor(2);
                    if (tiene_valor(3)) cambios["formacion_academica"] = valor(3);
                    if (cambios.isEmpty()) throw std::invalid_argument("Indique al menos un campo para actualizar.");
                    catalogo.actualizar_investigador(codigo, cambios, persistir);
                } else if (entidad == 2) {
                    if (tiene_valor(1)) cambios["nombre"] = valor(1);
                    if (tiene_valor(2)) cambios["categoria"] = valor(2);
                    if (tiene_valor(3)) cambios["lider"] = valor(3);
                    if (cambios.isEmpty()) throw std::invalid_argument("Indique al menos un campo para actualizar.");
                    catalogo.actualizar_grupo(codigo, cambios, persistir);
                } else {
                    if (tiene_valor(1)) cambios["titulo"] = valor(1);
                    if (tiene_valor(2)) {
                        const QString tipo = valor(2).toUpper();
                        if (tipo != "GNC" && tipo != "DTI" && tipo != "ASC" && tipo != "FRH") {
                            throw std::invalid_argument("El tipo mayor debe ser GNC, DTI, ASC o FRH.");
                        }
                        cambios["tipo_mayor"] = tipo;
                    }
                    if (tiene_valor(3)) cambios["subtipo"] = valor(3);
                    if (tiene_valor(4)) {
                        bool anio_valido = false;
                        const int anio = valor(4).toInt(&anio_valido);
                        if (!anio_valido) {
                            throw std::invalid_argument("El año del producto debe ser numérico.");
                        }
                        cambios["ano"] = anio;
                    }
                    if (tiene_valor(5)) {
                        const QString validacion = valor(5);
                        if (validacion != "Avalado" && validacion != "Con soporte" &&
                            validacion != "No avalado") {
                            throw std::invalid_argument("La validación debe ser Avalado, Con soporte o No avalado.");
                        }
                        cambios["estado_validacion"] = validacion;
                    }
                    const QString codigo_grupo = valor(6).trimmed();
                    if (!codigo_grupo.isEmpty()) {
                        if (!catalogo.buscar_grupo(codigo_grupo)) {
                            throw std::invalid_argument("No existe el grupo indicado.");
                        }
                        cambios["codigo_grupo"] = codigo_grupo;
                    }
                    const QString quitar_grupo = valor(7).trimmed().toLower();
                    if (!quitar_grupo.isEmpty() && quitar_grupo != "si" &&
                        quitar_grupo != "sí" &&
                        quitar_grupo != "no") {
                        throw std::invalid_argument(
                            "Para quitar el grupo, escriba sí o no.");
                    }
                    if (quitar_grupo == "si" || quitar_grupo == "sí") {
                        if (!codigo_grupo.isEmpty()) {
                            throw std::invalid_argument(
                                "Indique un grupo nuevo o quite el grupo actual, no ambas acciones.");
                        }
                        cambios["codigo_grupo"] = QJsonValue(QJsonValue::Null);
                    }
                    if (cambios.isEmpty()) throw std::invalid_argument("Indique al menos un campo para actualizar.");
                    catalogo.actualizar_producto(codigo, cambios, persistir);
                }
            } else if (accion_formulario == 3) {
                if (entidad == 1) {
                    const auto registro = catalogo.buscar_investigador(codigo);
                    if (!registro) throw std::invalid_argument("No existe el investigador indicado.");
                    registro->activo ? catalogo.desactivar_investigador(codigo, persistir)
                                     : catalogo.activar_investigador(codigo, persistir);
                } else if (entidad == 2) {
                    const auto registro = catalogo.buscar_grupo(codigo);
                    if (!registro) throw std::invalid_argument("No existe el grupo indicado.");
                    registro->activo ? catalogo.desactivar_grupo(codigo, persistir)
                                     : catalogo.activar_grupo(codigo, persistir);
                } else {
                    const auto registro = catalogo.buscar_producto(codigo);
                    if (!registro) throw std::invalid_argument("No existe el producto indicado.");
                    registro->activo ? catalogo.desactivar_producto(codigo, persistir)
                                     : catalogo.activar_producto(codigo, persistir);
                }
            } else if (accion_formulario == 4) {
                if (campo_qstring(valores_formulario, 1) != "ELIMINAR") {
                    throw std::invalid_argument("La confirmación debe ser exactamente ELIMINAR.");
                }
                if (entidad == 1) catalogo.eliminar_investigador(codigo, persistir);
                else if (entidad == 2) catalogo.eliminar_grupo(codigo, persistir);
                else catalogo.eliminar_producto(codigo, persistir);
            } else if (accion_formulario == 5) {
                QJsonObject detalle;
                if (entidad == 1) {
                    const auto registro = catalogo.buscar_investigador(codigo);
                    if (!registro) throw std::invalid_argument("No existe el investigador indicado.");
                    detalle = registro->aJson();
                } else if (entidad == 2) {
                    const auto registro = catalogo.buscar_grupo(codigo);
                    if (!registro) throw std::invalid_argument("No existe el grupo indicado.");
                    detalle = registro->aJson();
                } else {
                    const auto registro = catalogo.buscar_producto(codigo);
                    if (!registro) throw std::invalid_argument("No existe el producto indicado.");
                    detalle = registro->aJson();
                    const auto* nodo = catalogo.multilista_productos.buscar_nodo(codigo);
                    if (nodo && nodo->grupo) {
                        detalle["grupo"] = nodo->grupo->codigo_gruplac;
                    }
                    if (nodo) {
                        QJsonArray autores;
                        for (const auto& autor : nodo->autores) {
                            if (autor) autores.append(autor->codigo_rh);
                        }
                        detalle["autores"] = autores;
                    }
                }
                ficha_detalle = QJsonDocument(detalle).toJson(QJsonDocument::Indented).toStdString();
                accion_formulario = 0;
                mensaje_estado = "Ficha cargada; Escape vuelve al directorio.";
                return;
            }
            mensaje_estado = "Acción completada para " + etiqueta_entidad(entidad).toStdString() + " " +
                             codigo.toStdString() + ".";
            accion_formulario = 0;
        } catch (const std::exception& error) {
            mensaje_estado = std::string("No se aplicó el cambio: ") + error.what();
        }
    };

    auto barra = Container::Horizontal(botones);
    auto contenido = Renderer(barra, [&] {
        const auto dimensiones = Terminal::Size();
        return renderizar_pantalla(
            seleccion, catalogo.resumen_dict(), catalogo, datos_demostracion, conectado,
            mensaje_conexion, filtro, filtro_activo, accion_formulario, valores_formulario,
            campo_activo, mensaje_estado, ficha_detalle, botones, color_activo, ascii,
            dimensiones.dimx, filtro_anios, pagina_actual);
    });
    auto pantalla = ScreenInteractive::Fullscreen();
    auto salir = pantalla.ExitLoopClosure();
    std::mutex mutex_revision;
    std::optional<qint64> revision_remota_recibida;
    std::string error_revision;
    std::unique_ptr<TrabajadorPeriodico> trabajador_revision;
    if (conectado && cliente) {
        const QString url_supabase = cliente->baseUrl();
        const QString clave_publicable = cliente->anonKey();
        try {
            const auto notificar_error =
                [&pantalla, &mutex_revision, &revision_remota_recibida,
                 &error_revision](const std::string& error) {
                    {
                        std::lock_guard<std::mutex> bloqueo(mutex_revision);
                        revision_remota_recibida.reset();
                        error_revision = error;
                    }
                    pantalla.PostEvent(Event::Custom);
                };
            const auto preparar_tarea =
                [url_supabase, clave_publicable, &pantalla,
                 &mutex_revision, &revision_remota_recibida,
                 &error_revision]() -> TrabajadorPeriodico::Tarea {
                    auto cliente_revision = std::make_shared<ClienteHTTPSupabase>(
                        url_supabase, clave_publicable);
                    // meta.revision es publica; no copiar una sesion que pueda caducar.
                    return [cliente_revision, &pantalla, &mutex_revision,
                            &revision_remota_recibida, &error_revision] {
                        datos::ControladorRevision lector_revision;
                        const qint64 revision =
                            lector_revision.consultar_remota(*cliente_revision);
                        {
                            std::lock_guard<std::mutex> bloqueo(mutex_revision);
                            revision_remota_recibida = revision;
                            error_revision.clear();
                        }
                        pantalla.PostEvent(Event::Custom);
                    };
                };
            trabajador_revision = std::make_unique<TrabajadorPeriodico>(
                preparar_tarea, notificar_error, std::chrono::seconds(30));
        } catch (const std::exception& error) {
            mensaje_estado = std::string("No se pudo iniciar la revisión periódica: ") +
                             error.what();
        }
    }
    auto aplicacion = CatchEvent(contenido, [&seleccion, &filtro, &filtro_activo,
                                             &filtro_anios,
                                             &pagina_actual,
                                             &accion_formulario, &valores_formulario,
                                             &campo_activo, &mensaje_estado, &abrir_formulario,
                                             &guardar_formulario, &catalogo, &conectado,
                                             &ficha_detalle,
                                             &mutex_revision, &revision_remota_recibida,
                                             &error_revision,
                                             salir](const Event& evento) {
        if (evento == Event::Custom) {
            std::optional<qint64> revision_remota;
            std::string error;
            {
                std::lock_guard<std::mutex> bloqueo(mutex_revision);
                revision_remota = revision_remota_recibida;
                error = error_revision;
            }
            if (!error.empty()) {
                mensaje_estado = "No se pudo verificar la revisión remota: " + error;
            } else if (revision_remota &&
                       *revision_remota != catalogo.controlador_revision.revision_local()) {
                mensaje_estado = "La base de datos cambió; presione r para recargar antes de editar.";
            } else if (mensaje_estado.rfind("La base de datos cambió", 0) == 0 ||
                       mensaje_estado.rfind("No se pudo verificar la revisión remota:", 0) == 0) {
                mensaje_estado = "Revisión remota verificada; no hay cambios pendientes de recarga.";
            }
            return true;
        }
        if (accion_formulario > 0) {
            const auto campos = campos_formulario(seleccion, accion_formulario);
            if (evento == Event::Escape) {
                accion_formulario = 0;
                mensaje_estado = "Acción cancelada.";
                return true;
            }
            if (evento == Event::Tab) {
                if (!campos.empty()) campo_activo = (campo_activo + 1) % campos.size();
                return true;
            }
            if (evento == Event::Backspace) {
                if (campo_activo < valores_formulario.size()) {
                    borrar_ultimo_caracter_utf8(valores_formulario[campo_activo]);
                }
                return true;
            }
            if (evento == Event::Return) {
                guardar_formulario();
                return true;
            }
            if (evento.is_character() && campo_activo < valores_formulario.size()) {
                valores_formulario[campo_activo] += evento.character();
                return true;
            }
            return true;
        }
        if (filtro_activo) {
            if (evento == Event::Return) {
                filtro_activo = false;
                return true;
            }
            if (evento == Event::Escape) {
                filtro.clear();
                filtro_activo = false;
                return true;
            }
            if (evento == Event::Backspace) {
                if (!filtro.isEmpty()) {
                    filtro.chop(1);
                }
                return true;
            }
            if (evento.is_character()) {
                const auto caracter = evento.character();
                filtro += QString::fromUtf8(caracter.c_str());
                return true;
            }
            return true;
        }
        if (evento == Event::Character("/") &&
            (seleccion == 1 || seleccion == 2 || seleccion == 3)) {
            filtro_activo = true;
            pagina_actual = 0;
            return true;
        }
        if (evento == Event::Escape && !ficha_detalle.empty()) {
            ficha_detalle.clear();
            return true;
        }
        if (evento == Event::Escape && !filtro.isEmpty()) {
            filtro.clear();
            pagina_actual = 0;
            return true;
        }
        if ((seleccion == 1 || seleccion == 2 || seleccion == 3) &&
            (evento == Event::Character("[") || evento == Event::Character("]"))) {
            const int ultima = ultima_pagina(seleccion, catalogo, filtro);
            pagina_actual = evento == Event::Character("[")
                                ? std::max(0, pagina_actual - 1)
                                : std::min(ultima, pagina_actual + 1);
            return true;
        }
        if (evento == Event::Character("n")) {
            abrir_formulario(1);
            return true;
        }
        if (evento == Event::Character("e")) {
            abrir_formulario(2);
            return true;
        }
        if (evento == Event::Character("t")) {
            abrir_formulario(3);
            return true;
        }
        if (evento == Event::Character("x")) {
            abrir_formulario(4);
            return true;
        }
        if (evento == Event::Character("v")) {
            abrir_formulario(5);
            return true;
        }
        if (evento == Event::Character("i")) {
            abrir_formulario(6);
            return true;
        }
        if (evento == Event::Character("w")) {
            abrir_formulario(7);
            return true;
        }
        if (evento == Event::Character("f") && seleccion == 4) {
            switch (filtro_anios.modo) {
            case servicios::ModoFiltroAnios::TODOS:
                filtro_anios.modo = servicios::ModoFiltroAnios::ULTIMOS;
                filtro_anios.ultimos_n = 5;
                break;
            case servicios::ModoFiltroAnios::ULTIMOS:
                filtro_anios.modo = servicios::ModoFiltroAnios::MODELO_2024;
                break;
            case servicios::ModoFiltroAnios::MODELO_2024:
            case servicios::ModoFiltroAnios::RANGO:
                filtro_anios = {};
                break;
            }
            mensaje_estado =
                "Filtro: " + filtro_anios.descripcion(QDate::currentDate().year()).toStdString();
            return true;
        }
        if (evento == Event::Character("g") && seleccion == 4) {
            abrir_formulario(8);
            return true;
        }
        if (evento == Event::Character("r")) {
            if (!conectado) {
                mensaje_estado = "No se puede recargar: Supabase no está conectado.";
                return true;
            }
            try {
                catalogo.recargar_todo();
                mensaje_estado = "Catálogo remoto recargado.";
            } catch (const std::exception& error) {
                mensaje_estado = std::string("No se pudo recargar el catálogo: ") + error.what();
            }
            return true;
        }
        if (evento == Event::Character("u")) {
            try {
                const auto deshecho = catalogo.deshacer(conectado);
                mensaje_estado = deshecho
                                     ? "Deshecho: " + deshecho->descripcion.toStdString()
                                     : "No hay operaciones para deshacer.";
            } catch (const std::exception& error) {
                mensaje_estado = std::string("No se pudo deshacer: ") + error.what();
            }
            return true;
        }
        if (evento == Event::Character("q") || evento == Event::Escape) {
            salir();
            return true;
        }
        if (evento == Event::ArrowRight) {
            seleccion = (seleccion + 1) % static_cast<int>(PESTANAS.size());
            pagina_actual = 0;
            return true;
        }
        if (evento == Event::ArrowLeft) {
            seleccion = (seleccion + static_cast<int>(PESTANAS.size()) - 1) %
                        static_cast<int>(PESTANAS.size());
            pagina_actual = 0;
            return true;
        }
        for (std::size_t i = 0; i < PESTANAS.size(); ++i) {
            if (evento == Event::Character(std::to_string(i + 1))) {
                seleccion = static_cast<int>(i);
                pagina_actual = 0;
                return true;
            }
        }
        return false;
    });

    pantalla.Loop(aplicacion);
    if (trabajador_revision) {
        trabajador_revision->detener();
    }
    return 0;
}

} // namespace pea::tui
