#pragma once

#include <optional>
#include <QJsonArray>
#include <QJsonObject>
#include <QList>
#include <QString>

namespace pea::ingesta {

struct MetadatosOrigen {
    QString url;
    QString fecha_descarga;
    QString sha256;
    QString metodo{"requests + bs4 + lxml"};

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["url"] = url;
        obj["fecha_descarga"] = fecha_descarga;
        obj["sha256"] = sha256;
        obj["metodo"] = metodo;
        return obj;
    }
};

struct InstitucionIngesta {
    QString nombre;
    std::optional<QString> tipo{std::nullopt};

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["nombre"] = nombre;
        if (tipo.has_value()) {
            obj["tipo"] = *tipo;
        } else {
            obj["tipo"] = QJsonValue::Null;
        }
        return obj;
    }
};

struct LineaIngesta {
    QString nombre;
    bool activa{true};

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["nombre"] = nombre;
        obj["activa"] = activa;
        return obj;
    }
};

struct IntegranteIngesta {
    QString nombre;
    QString vinculacion;
    std::optional<QString> horas_dedicacion{std::nullopt};
    std::optional<QString> inicio_vinculacion{std::nullopt};
    std::optional<QString> fin_vinculacion{std::nullopt};

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["nombre"] = nombre;
        obj["vinculacion"] = vinculacion;
        obj["horas_dedicacion"] = horas_dedicacion ? QJsonValue(*horas_dedicacion) : QJsonValue::Null;
        obj["inicio_vinculacion"] = inicio_vinculacion ? QJsonValue(*inicio_vinculacion) : QJsonValue::Null;
        obj["fin_vinculacion"] = fin_vinculacion ? QJsonValue(*fin_vinculacion) : QJsonValue::Null;
        return obj;
    }
};

struct FormacionIngesta {
    QString nivel;
    QString titulo;
    QString institucion;
    std::optional<QString> periodo{std::nullopt};

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["nivel"] = nivel;
        obj["titulo"] = titulo;
        obj["institucion"] = institucion;
        obj["periodo"] = periodo ? QJsonValue(*periodo) : QJsonValue::Null;
        return obj;
    }
};

struct ProductoIngesta {
    QString tipo; // Articulo, Libro, Capitulo, Software, TrabajoDirigido, Proyecto
    QString titulo;
    std::optional<int> ano{std::nullopt};
    std::optional<QString> autores{std::nullopt};
    std::optional<QString> detalles{std::nullopt};
    std::optional<QString> doi_o_isbn{std::nullopt};
    std::optional<QString> categoria_declarada{std::nullopt};
    std::optional<QString> disponibilidad{std::nullopt};
    std::optional<QString> plataforma{std::nullopt};
    std::optional<QString> ambiente{std::nullopt};
    std::optional<QString> institucion{std::nullopt};
    std::optional<QString> persona_orientada{std::nullopt};
    std::optional<QString> rol{std::nullopt};
    std::optional<QString> tipo_trabajo{std::nullopt};
    std::optional<QString> periodo{std::nullopt};

    [[nodiscard]] QJsonObject a_json_articulo_o_libro() const {
        QJsonObject obj;
        obj["tipo"] = tipo;
        obj["titulo"] = titulo;
        obj["ano"] = ano ? QJsonValue(*ano) : QJsonValue::Null;
        obj["autores"] = autores ? QJsonValue(*autores) : QJsonValue::Null;
        obj["detalles"] = detalles ? QJsonValue(*detalles) : QJsonValue::Null;
        obj["doi_o_isbn"] = doi_o_isbn ? QJsonValue(*doi_o_isbn) : QJsonValue::Null;
        obj["categoria_declarada"] = categoria_declarada ? QJsonValue(*categoria_declarada) : QJsonValue::Null;
        return obj;
    }

    [[nodiscard]] QJsonObject a_json_software() const {
        QJsonObject obj;
        obj["titulo"] = titulo;
        obj["ano"] = ano ? QJsonValue(*ano) : QJsonValue::Null;
        obj["autores"] = autores ? QJsonValue(*autores) : QJsonValue::Null;
        obj["tipo"] = tipo.isEmpty() ? QStringLiteral("Software") : tipo;
        obj["disponibilidad"] = disponibilidad ? QJsonValue(*disponibilidad) : QJsonValue::Null;
        obj["plataforma"] = plataforma ? QJsonValue(*plataforma) : QJsonValue::Null;
        obj["ambiente"] = ambiente ? QJsonValue(*ambiente) : QJsonValue::Null;
        return obj;
    }

    [[nodiscard]] QJsonObject a_json_trabajo_dirigido() const {
        QJsonObject obj;
        obj["tipo_trabajo"] = tipo_trabajo ? *tipo_trabajo : QStringLiteral("Tesis/Trabajo");
        obj["titulo"] = titulo;
        obj["ano"] = ano ? QJsonValue(*ano) : QJsonValue::Null;
        obj["institucion"] = institucion ? QJsonValue(*institucion) : QJsonValue::Null;
        obj["persona_orientada"] = persona_orientada ? QJsonValue(*persona_orientada) : QJsonValue::Null;
        obj["rol"] = rol ? QJsonValue(*rol) : QJsonValue::Null;
        return obj;
    }

    [[nodiscard]] QJsonObject a_json_proyecto() const {
        QJsonObject obj;
        obj["titulo"] = titulo;
        obj["tipo"] = detalles ? *detalles : tipo;
        obj["periodo"] = periodo ? QJsonValue(*periodo) : QJsonValue::Null;
        obj["institucion"] = institucion ? QJsonValue(*institucion) : QJsonValue::Null;
        return obj;
    }
};

struct GrupoIngesta {
    QString codigo_gruplac;
    std::optional<QString> nombre_grupo{std::nullopt};
    std::optional<QString> ano_mes_formacion{std::nullopt};
    std::optional<QString> departamento_ciudad{std::nullopt};
    std::optional<QString> lider{std::nullopt};
    std::optional<QString> certificacion{std::nullopt};
    std::optional<QString> pagina_web{std::nullopt};
    std::optional<QString> email{std::nullopt};
    std::optional<QString> clasificacion{std::nullopt};
    std::optional<QString> area_conocimiento{std::nullopt};
    std::optional<QString> programa_nacional{std::nullopt};

    QList<InstitucionIngesta> instituciones;
    QList<LineaIngesta> lineas_investigacion;
    QList<IntegranteIngesta> integrantes;
    QList<ProductoIngesta> articulos;
    QList<ProductoIngesta> libros;
    QList<ProductoIngesta> capitulos;
    QList<ProductoIngesta> softwares;
    QList<ProductoIngesta> trabajos_dirigidos;
    QList<ProductoIngesta> proyectos;
    MetadatosOrigen origen;

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["codigo_gruplac"] = codigo_gruplac;
        obj["nombre_grupo"] = nombre_grupo ? QJsonValue(*nombre_grupo) : QJsonValue::Null;
        obj["ano_mes_formacion"] = ano_mes_formacion ? QJsonValue(*ano_mes_formacion) : QJsonValue::Null;
        obj["departamento_ciudad"] = departamento_ciudad ? QJsonValue(*departamento_ciudad) : QJsonValue::Null;
        obj["lider"] = lider ? QJsonValue(*lider) : QJsonValue::Null;
        obj["certificacion"] = certificacion ? QJsonValue(*certificacion) : QJsonValue::Null;
        obj["pagina_web"] = pagina_web ? QJsonValue(*pagina_web) : QJsonValue::Null;
        obj["email"] = email ? QJsonValue(*email) : QJsonValue::Null;
        obj["clasificacion"] = clasificacion ? QJsonValue(*clasificacion) : QJsonValue::Null;
        obj["area_conocimiento"] = area_conocimiento ? QJsonValue(*area_conocimiento) : QJsonValue::Null;
        obj["programa_nacional"] = programa_nacional ? QJsonValue(*programa_nacional) : QJsonValue::Null;

        QJsonArray arr_inst;
        for (const auto& i : instituciones) arr_inst.append(i.a_json());
        obj["instituciones"] = arr_inst;

        QJsonArray arr_lin;
        for (const auto& l : lineas_investigacion) arr_lin.append(l.a_json());
        obj["lineas_investigacion"] = arr_lin;

        QJsonArray arr_int;
        for (const auto& in : integrantes) arr_int.append(in.a_json());
        obj["integrantes"] = arr_int;

        QJsonArray arr_art;
        for (const auto& a : articulos) arr_art.append(a.a_json_articulo_o_libro());
        obj["articulos"] = arr_art;

        QJsonArray arr_lib;
        for (const auto& l : libros) arr_lib.append(l.a_json_articulo_o_libro());
        obj["libros"] = arr_lib;

        QJsonArray arr_cap;
        for (const auto& c : capitulos) arr_cap.append(c.a_json_articulo_o_libro());
        obj["capitulos"] = arr_cap;

        QJsonArray arr_soft;
        for (const auto& s : softwares) arr_soft.append(s.a_json_software());
        obj["softwares"] = arr_soft;

        QJsonArray arr_td;
        for (const auto& td : trabajos_dirigidos) arr_td.append(td.a_json_trabajo_dirigido());
        obj["trabajos_dirigidos"] = arr_td;

        QJsonArray arr_proy;
        for (const auto& pr : proyectos) arr_proy.append(pr.a_json_proyecto());
        obj["proyectos"] = arr_proy;

        obj["origen"] = origen.a_json();
        return obj;
    }
};

struct InvestigadorIngesta {
    QString codigo_rh;
    std::optional<QString> nombre_completo{std::nullopt};
    std::optional<QString> nombre_citaciones{std::nullopt};
    std::optional<QString> nacionalidad{QStringLiteral("Colombiana")};
    std::optional<QString> sexo{std::nullopt};
    std::optional<QString> categoria_declarada{std::nullopt};
    bool par_evaluador{false};

    QList<QString> areas_actuacion;
    QList<QString> lineas_investigacion;
    QList<FormacionIngesta> formacion;
    QList<ProductoIngesta> articulos;
    QList<ProductoIngesta> libros;
    QList<ProductoIngesta> capitulos;
    QList<ProductoIngesta> softwares;
    QList<ProductoIngesta> trabajos_dirigidos;
    QList<ProductoIngesta> proyectos;
    MetadatosOrigen origen;

    [[nodiscard]] QJsonObject a_json() const {
        QJsonObject obj;
        obj["codigo_rh"] = codigo_rh;
        obj["nombre_completo"] = nombre_completo ? QJsonValue(*nombre_completo) : QJsonValue::Null;
        obj["nombre_citaciones"] = nombre_citaciones ? QJsonValue(*nombre_citaciones) : QJsonValue::Null;
        obj["nacionalidad"] = nacionalidad ? QJsonValue(*nacionalidad) : QJsonValue::Null;
        obj["sexo"] = sexo ? QJsonValue(*sexo) : QJsonValue::Null;
        obj["categoria_declarada"] = categoria_declarada ? QJsonValue(*categoria_declarada) : QJsonValue::Null;
        obj["par_evaluador"] = par_evaluador;

        QJsonArray arr_act;
        for (const auto& a : areas_actuacion) arr_act.append(a);
        obj["areas_actuacion"] = arr_act;

        QJsonArray arr_lin;
        for (const auto& l : lineas_investigacion) arr_lin.append(l);
        obj["lineas_investigacion"] = arr_lin;

        QJsonArray arr_form;
        for (const auto& f : formacion) arr_form.append(f.a_json());
        obj["formacion"] = arr_form;

        QJsonArray arr_art;
        for (const auto& a : articulos) arr_art.append(a.a_json_articulo_o_libro());
        obj["articulos"] = arr_art;

        QJsonArray arr_cap;
        for (const auto& c : capitulos) arr_cap.append(c.a_json_articulo_o_libro());
        obj["capitulos"] = arr_cap;

        QJsonArray arr_soft;
        for (const auto& s : softwares) arr_soft.append(s.a_json_software());
        obj["softwares"] = arr_soft;

        QJsonArray arr_td;
        for (const auto& td : trabajos_dirigidos) arr_td.append(td.a_json_trabajo_dirigido());
        obj["trabajos_dirigidos"] = arr_td;

        QJsonArray arr_proy;
        for (const auto& pr : proyectos) arr_proy.append(pr.a_json_proyecto());
        obj["proyectos"] = arr_proy;

        obj["origen"] = origen.a_json();
        return obj;
    }
};

struct FilaAutorCSV {
    QString producto_codigo;
    QString investigador_codigo;
    int orden_autoria{1};
};

struct InformeIngesta {
    QString origen;
    QString tipo_fuente;
    QString fecha;
    bool exito{true};
    QString mensaje;
    int grupos_procesados{0};
    int investigadores_procesados{0};
    int productos_procesados{0};
    int autores_procesados{0};
    QList<QString> filas_erroneas;
    QList<QString> advertencias;
    QJsonObject archivos_generados;
};

} // namespace pea::ingesta
