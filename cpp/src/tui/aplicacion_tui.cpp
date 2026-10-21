#include "pea/tui/aplicacion_tui.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
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

#include "pea/cliente_http.hpp"
#include "pea/datos/sesion.hpp"
#include "pea/dominio/grupo.hpp"
#include "pea/dominio/investigador.hpp"
#include "pea/dominio/producto.hpp"
#include "pea/datos/configuracion_conexion.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"
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

Element marco(Element elemento, bool ascii) {
    if (!ascii) {
        return elemento | border;
    }
    Pixel borde_ascii;
    borde_ascii.character = "+";
    return elemento | borderWith(borde_ascii);
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
    auto producto = std::make_shared<dominio::Producto>(
        "PRUEBA-PROD-001", "Producto de demostración", "GNC", "Artículo", 2024, "Avalado", true);
    catalogo.crear_grupo(grupo, false);
    catalogo.crear_investigador(investigador, false);
    catalogo.crear_producto(producto, grupo->codigo_gruplac, {investigador->codigo_rh}, false);
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
               separator(),
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
    bool color_activo,
    bool ascii,
    int ancho) {
    const std::string origen = datos_demostracion
                                   ? "Datos de demostración (solo memoria)"
                                   : (conectado ? "Datos de Supabase" : "Sin datos");
    const auto estadisticas = catalogo.estadisticas.obtenerVistaInstitucional();
    const auto coincide = [&filtro](const QString& texto) {
        return filtro.isEmpty() || texto.contains(filtro, Qt::CaseInsensitive);
    };
    const QString texto_filtro = filtro_activo
                                     ? QString("Filtro: %1  (Enter: aplicar · Esc: limpiar)")
                                           .arg(filtro)
                                     : (filtro.isEmpty()
                                            ? QString("Presione / para buscar")
                                            : QString("Filtro: %1  (/ para editar · Esc para limpiar)")
                                                  .arg(filtro));

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
                       separator(),
                       kpis,
                       separator(),
                       text("Producción por año") | bold,
                       text(productos == 0 ? "Aún no hay productos en el catálogo." :
                                             "Las estadísticas se calculan desde el hipercubo local."),
                       separator(),
                       text("Resumen del catálogo") | bold,
                       tabla_resumen(resumen, ascii),
                   }) |
                   flex;
        }
        case 1: {
            Elements filas{color_si(text("Directorio de investigadores") | bold, Color::Cyan, color_activo),
                           text("Código · nombre · categoría · estado"),
                           text(texto_filtro.toStdString()),
                           separator()};
            int mostrados = 0;
            for (const auto& investigador : catalogo.investigadores) {
                if (!investigador) {
                    continue;
                }
                const QString linea = investigador->codigo_rh + " · " +
                                      investigador->nombre_completo.left(38) + " · " +
                                      investigador->categoria + (investigador->activo ? "" : " · Inactivo");
                if (!coincide(linea)) {
                    continue;
                }
                if (mostrados == 12) {
                    filas.push_back(text("… y más investigadores"));
                    break;
                }
                ++mostrados;
                filas.push_back(text(linea.toStdString()));
            }
            if (mostrados == 0) {
                filas.push_back(text(filtro.isEmpty() ? "No hay investigadores cargados."
                                                      : "No hay coincidencias para el filtro."));
            }
            return vbox(std::move(filas)) | flex;
        }
        case 2: {
            Elements filas{color_si(text("Directorio de grupos") | bold, Color::Cyan, color_activo),
                           text("Código GrupLAC · nombre · categoría · estado"),
                           text(texto_filtro.toStdString()),
                           separator()};
            int mostrados = 0;
            for (const auto& grupo : catalogo.grupos) {
                if (!grupo) {
                    continue;
                }
                const QString linea = grupo->codigo_gruplac + " · " + grupo->nombre.left(42) +
                                      " · " + grupo->categoria + (grupo->activo ? "" : " · Inactivo");
                if (!coincide(linea)) {
                    continue;
                }
                if (mostrados == 12) {
                    filas.push_back(text("… y más grupos"));
                    break;
                }
                ++mostrados;
                filas.push_back(text(linea.toStdString()));
            }
            if (mostrados == 0) {
                filas.push_back(text(filtro.isEmpty() ? "No hay grupos cargados."
                                                      : "No hay coincidencias para el filtro."));
            }
            return vbox(std::move(filas)) | flex;
        }
        case 3: {
            Elements filas{color_si(text("Catálogo de productos") | bold, Color::Cyan, color_activo),
                           text("Código · año · tipología · título · validación"),
                           text(texto_filtro.toStdString()),
                           separator()};
            int mostrados = 0;
            for (auto* nodo = catalogo.multilista_productos.cabeza(); nodo != nullptr;
                 nodo = nodo->siguiente_global) {
                if (!nodo->producto) {
                    continue;
                }
                if (mostrados++ == 12) {
                    filas.push_back(text("… y más productos"));
                    break;
                }
                const auto& producto = *nodo->producto;
                const QString linea = producto.codigo_identificador + " · " +
                                      QString::number(producto.ano) + " · " + producto.tipo_mayor +
                                      " · " + producto.titulo.left(34) + " · " +
                                      producto.estado_validacion +
                                      (producto.activo ? "" : " · Inactivo");
                if (!coincide(linea)) {
                    continue;
                }
                if (mostrados == 12) {
                    filas.push_back(text("… y más productos"));
                    break;
                }
                ++mostrados;
                filas.push_back(text(linea.toStdString()));
            }
            if (mostrados == 0) {
                filas.push_back(text(filtro.isEmpty() ? "No hay productos cargados."
                                                      : "No hay coincidencias para el filtro."));
            }
            return vbox(std::move(filas)) | flex;
        }
        case 4:
            return vbox({
                       color_si(text("Análisis de redes") | bold, Color::Cyan, color_activo),
                       separator(),
                       text("El grafo de coautoría aparecerá cuando haya relaciones cargadas."),
                       text("Sin datos, no se muestran métricas ni nodos ficticios."),
                   }) |
                   flex;
        case 5:
            return vbox({
                       color_si(text("Importación") | bold, Color::Cyan, color_activo),
                       separator(),
                       text("Formatos disponibles: CSV y URL SCIENTI."),
                       text("La importación desde PDF debe realizarse desde la versión Python."),
                       text("Tareas en cola: " + texto_cantidad(static_cast<int>(catalogo.cola_importacion.tamano()))),
                   }) |
                   flex;
        case 6:
            return vbox({
                       color_si(text("Configuración") | bold, Color::Cyan, color_activo),
                       separator(),
                       text("Origen de datos: " + origen),
                       text(conectado ? "Conexión remota verificada."
                                      : (mensaje_conexion.empty()
                                             ? "Sin conexión a Supabase."
                                             : mensaje_conexion)),
                       text("Tema: oscuro"),
                       text("Ventana de años: todos los años"),
                   }) |
                   flex;
        default:
            return vbox({
                       color_si(text("Acerca de PEA-i") | bold, Color::Cyan, color_activo),
                       separator(),
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
    const std::vector<Component>& botones,
    bool color_activo,
    bool ascii,
    int ancho) {
    Elements pestanas;
    for (std::size_t i = 0; i < botones.size(); ++i) {
        auto render = botones[i]->Render();
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
    auto pie = text("1–8: pestañas  ←/→: cambiar  ?: ayuda  q: salir");
    if (color_activo) {
        pie = pie | color(Color::GrayLight);
    }
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
                                     mensaje_conexion, filtro, filtro_activo,
                                     color_activo, ascii, ancho) | flex,
                     ascii),
               hbox({
                   pie,
                   filler(),
                   text("Deshacer: " + texto_cantidad(static_cast<int>(catalogo.pila_deshacer.tamano())) +
                        "  Importación: " +
                        texto_cantidad(static_cast<int>(catalogo.cola_importacion.tamano()))),
               }),
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
                               {}, false, botones, false, true, ancho));
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
            const bool hallazgo = reemplazo || excede_ancho || salida.empty() ||
                                   salida.find('\x1b') != std::string::npos || !captura_guardada ||
                                   salida.find(titulos_vista[indice]) == std::string::npos ||
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
    const std::array<std::pair<int, std::string>, 3> casos_filtro{{
        {1, "prueba-rh-001"},
        {2, "prueba-grupo-001"},
        {3, "prueba-prod-001"},
    }};
    for (const auto& [indice, consulta] : casos_filtro) {
        Screen screen = Screen::Create(Dimension::Fixed(80), Dimension::Fixed(24));
        Render(screen, renderizar_pantalla(
                           indice, resumen, catalogo, true, false, {},
                           QString::fromStdString(consulta), false, botones, false, true, 80));
        const std::string salida = quitar_secuencias_ansi(screen.ToString());
        const QString codigo_esperado = indice == 1
                                            ? "PRUEBA-RH-001"
                                            : (indice == 2 ? "PRUEBA-GRUPO-001" : "PRUEBA-PROD-001");
        const bool hallazgo = salida.find(codigo_esperado.toStdString()) == std::string::npos;
        hallazgos += hallazgo ? 1 : 0;
        std::cout << "Filtro " << PESTANAS[static_cast<std::size_t>(indice)] << "  "
                  << (hallazgo ? "1" : "0") << "\n";
    }
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
    QString filtro;
    bool filtro_activo = false;
    for (std::size_t i = 0; i < PESTANAS.size(); ++i) {
        botones.push_back(Button(
            std::to_string(i + 1) + " " + PESTANAS[i],
            [i, &seleccion] { seleccion = static_cast<int>(i); }));
    }

    auto barra = Container::Horizontal(botones);
    auto contenido = Renderer(barra, [&] {
        const auto dimensiones = Terminal::Size();
        return renderizar_pantalla(
            seleccion, catalogo.resumen_dict(), catalogo, datos_demostracion, conectado,
            mensaje_conexion, filtro, filtro_activo, botones, color_activo, ascii,
            dimensiones.dimx);
    });
    auto pantalla = ScreenInteractive::Fullscreen();
    auto salir = pantalla.ExitLoopClosure();
    auto aplicacion = CatchEvent(contenido, [&seleccion, &filtro, &filtro_activo, salir](const Event& evento) {
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
            return true;
        }
        if (evento == Event::Escape && !filtro.isEmpty()) {
            filtro.clear();
            return true;
        }
        if (evento == Event::Character("q") || evento == Event::Escape) {
            salir();
            return true;
        }
        if (evento == Event::ArrowRight) {
            seleccion = (seleccion + 1) % static_cast<int>(PESTANAS.size());
            return true;
        }
        if (evento == Event::ArrowLeft) {
            seleccion = (seleccion + static_cast<int>(PESTANAS.size()) - 1) %
                        static_cast<int>(PESTANAS.size());
            return true;
        }
        for (std::size_t i = 0; i < PESTANAS.size(); ++i) {
            if (evento == Event::Character(std::to_string(i + 1))) {
                seleccion = static_cast<int>(i);
                return true;
            }
        }
        return false;
    });

    pantalla.Loop(aplicacion);
    return 0;
}

} // namespace pea::tui
