#include "pea/servicios/parcial_cli.hpp"
#include "pea/servicios/indicadores.hpp"
#include "pea/datos/archivo_local.hpp"
#include "pea/datos/configuracion_conexion.hpp"
#include "pea/cliente_http.hpp"
#include "pea/ingesta/servicio_ingesta.hpp"
#include <QDate>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonParseError>
#include <QUrl>
#include <QUrlQuery>
#include <array>
#include <iostream>
#include <tuple>
#include <stdexcept>

namespace pea::cli {
namespace {
void imprimir_resultado(const QJsonObject& r, const QString& etiqueta) {
    std::cout << etiqueta.toStdString() << " · " << r["nombre"].toString().toStdString()
              << (r["completo"].toBool() ? " · Indicador: " : " · Indicador parcial: ") << r["indicador"].toDouble() << "\n";
    std::cout << "  Componente | Bruto | Máximo | Índice | Coef. | Aporte\n";
    for (const auto& v : r["componentes"].toArray()) {
        const auto c = v.toObject();
        std::cout << "  " << c["componente"].toString().toStdString() << " | " << c["bruto"].toDouble() << " | " << c["maximo"].toDouble()
                  << " | " << c["indice"].toDouble() << " | " << c["coeficiente"].toDouble() << " | " << c["aporte"].toDouble() << "\n";
    }
    std::cout << "  Incluidos: " << r["incluidos"].toArray().size() << " · excluidos: " << r["excluidos"].toArray().size()
              << " · estimados: " << r["estimadas"].toArray().size() << "\n";
}

// Respuestas del PARCIAL 1 y 2: descarga las URL del enunciado y calcula ambos indicadores.
int ejecutar_respuestas(const QStringList& args) {
    int corte = 2023;
    for (int i = 1; i < args.size(); ++i) {
        bool ok = false;
        if (args[i] == "--corte" && i + 1 < args.size()) corte = args[++i].toInt(&ok); else ok = false;
        if (!ok) throw std::invalid_argument("Uso: respuestas-parcial [--corte <año>]");
    }
    const std::array<std::tuple<QString, QString, QString>, 2> casos{{
        {"grupo", "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099", "00000000002099"},
        {"investigador", "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917", "0000494917"}}};
    for (const auto& [ambito, url, codigo] : casos) {
        std::cout << "Descargando " << url.toStdString() << "\n";
        auto cat = std::make_shared<servicios::CatalogoInvestigacion>();
        ingesta::ServicioIngesta ingesta(cat);
        ingesta.encolar_url(url, false);
        const auto informes = ingesta.procesar_todas();
        if (informes.isEmpty()) throw std::runtime_error("La URL no devolvió resultados.");
        for (const auto& i : informes) if (!i.exito) throw std::runtime_error(i.mensaje.toStdString());
        const auto datos = datos::serializar_catalogo(*cat);
        for (const bool estimar : {false, true}) {
            const QString modo = estimar ? "estimado (categoría base)" : "estricto (solo categorías publicadas)";
            imprimir_resultado(servicios::calcular_indicador(datos, ambito, codigo, corte, std::nullopt, {}, estimar),
                               ambito.left(1).toUpper() + ambito.mid(1) + " " + modo);
        }
    }
    return 0;
}
}  // namespace

int ejecutar_parcial(const QStringList& args) {
    if (args[0] == "respuestas-parcial") return ejecutar_respuestas(args);
    QMap<QString, QString> opciones;
    bool json = false, estimar = false;
    const QSet<QString> admitidas{"--archivo", "--url", "--ambito", "--codigo", "--corte", "--desde", "--referencia", "--salida", "--guardar-catalogo"};
    for (int i = 1; i < args.size(); ++i) {
        if (args[i] == "--json") { json = true; continue; }
        if (args[i] == "--estimar-categorias") { estimar = true; continue; }
        if (!admitidas.contains(args[i]) || i + 1 >= args.size() || opciones.contains(args[i]))
            throw std::invalid_argument("Opción desconocida, repetida o sin valor en indicador/guardar-local.");
        const auto clave = args[i]; opciones[clave] = args[++i];
    }
    if (opciones.contains("--archivo") && opciones.contains("--url")) throw std::invalid_argument("Elija archivo o URL.");
    const auto entero = [&opciones](const QString& clave, int defecto) {
        if (!opciones.contains(clave)) return defecto;
        bool ok = false; auto n = opciones[clave].toInt(&ok);
        if (!ok) throw std::invalid_argument("Los años deben ser números enteros.");
        return n;
    };
    auto codigo = opciones["--codigo"];
    auto ambito = opciones["--ambito"];
    std::unique_ptr<ClienteHTTPSupabase> cliente;
    auto cat = std::make_shared<servicios::CatalogoInvestigacion>();
    if (opciones.contains("--archivo")) *cat = datos::cargar_archivo(opciones["--archivo"]);
    else if (opciones.contains("--url")) {
        const auto url = opciones["--url"];
        ingesta::ServicioIngesta ingesta(cat);
        ingesta.encolar_url(url, false);
        const auto informes = ingesta.procesar_todas();
        if (informes.isEmpty()) throw std::runtime_error("La URL no devolvió resultados.");
        for (const auto& i : informes) if (!i.exito) throw std::runtime_error(i.mensaje.toStdString());
        if (codigo.isEmpty()) codigo = QUrlQuery(QUrl(url)).queryItemValue(ambito == "grupo" ? "nro" : "cod_rh");
    } else {
        cliente = datos::crear_cliente_configurado();
        if (!cliente) throw std::invalid_argument("Indique un archivo, una URL o configure Supabase.");
        *cat = servicios::CatalogoInvestigacion(cliente.get());
        cat->recargar_todo();
    }
    const auto snapshot = datos::serializar_catalogo(*cat);
    if (args[0] == "guardar-local") {
        if (opciones["--salida"].isEmpty()) throw std::invalid_argument("Falta --salida.");
        datos::guardar_archivo(opciones["--salida"], snapshot);
        std::cout << "Catálogo local guardado.\n";
        return 0;
    }
    if (codigo.isEmpty()) throw std::invalid_argument("Falta --codigo o una URL del ámbito elegido.");
    QJsonObject referencia;
    if (opciones.contains("--referencia")) {
        QFile f(opciones["--referencia"]);
        if (!f.open(QIODevice::ReadOnly)) throw std::runtime_error("No se pudo abrir la referencia.");
        QJsonParseError error;
        auto doc = QJsonDocument::fromJson(f.readAll(), &error);
        if (error.error != QJsonParseError::NoError || !doc.isObject() || doc.object().isEmpty()) throw std::invalid_argument("Referencia JSON inválida.");
        referencia = doc.object();
    }
    auto resultado = servicios::calcular_indicador(snapshot, ambito, codigo, entero("--corte", 2023),
        opciones.contains("--desde") ? std::optional<int>(entero("--desde", 1970)) : std::nullopt, referencia, estimar);
    if (opciones.contains("--guardar-catalogo")) datos::guardar_archivo(opciones["--guardar-catalogo"], snapshot);
    if (opciones.contains("--salida")) datos::guardar_archivo(opciones["--salida"], resultado);
    if (json) std::cout << QJsonDocument(resultado).toJson().toStdString();
    else {
        std::cout << resultado["nombre"].toString().toStdString() << (resultado["completo"].toBool() ? " · Indicador: " : " · Indicador parcial: ") << resultado["indicador"].toDouble() << "\n";
        std::cout << resultado["referencia"].toString().toStdString() << "\n";
        std::cout << "Componente | Indicador bruto | Máximo | Índice | Coeficiente | Aporte\n";
        for (const auto& v : resultado["componentes"].toArray()) {
            auto c = v.toObject();
            std::cout << c["componente"].toString().toStdString() << " | " << c["bruto"].toDouble() << " | " << c["maximo"].toDouble()
                      << " | " << c["indice"].toDouble() << " | " << c["coeficiente"].toDouble() << " | " << c["aporte"].toDouble() << "\n";
        }
        for (const auto& a : resultado["avisos"].toArray()) std::cout << "Aviso: " << a.toString().toStdString() << "\n";
        for (const auto& v : resultado["estimadas"].toArray()) {
            auto e = v.toObject();
            std::cout << "Estimado " << e["codigo"].toString().toStdString() << ": " << e["categoria"].toString().toStdString()
                      << " · " << e["regla"].toString().toStdString() << "\n";
        }
        for (const auto& v : resultado["excluidos"].toArray()) {
            auto p = v.toObject();
            std::cout << "Excluido " << p["codigo"].toString().toStdString() << ": " << p["motivo"].toString().toStdString() << "\n";
        }
    }
    return 0;
}
}
