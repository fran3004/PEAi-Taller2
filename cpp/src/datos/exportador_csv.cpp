#include "pea/datos/exportador_csv.hpp"

#include "pea/datos/serializador_csv.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

#include <QSaveFile>

namespace pea::datos {

std::array<QString, 3> serializar_catalogo_csv(
    const servicios::CatalogoInvestigacion& catalogo) {
    QString grupos;
    grupos += serializar_fila_csv(
        {"codigo_gruplac", "nombre", "categoria", "lider", "institucion_principal", "activo"});
    for (const auto& grupo : catalogo.grupos) {
        if (!grupo) continue;
        grupos += serializar_fila_csv(
            {grupo->codigo_gruplac, grupo->nombre, grupo->categoria, grupo->lider,
             grupo->institucion_principal, grupo->activo ? "True" : "False"});
    }

    QString investigadores;
    investigadores += serializar_fila_csv(
        {"codigo_rh", "nombre_completo", "categoria", "formacion_academica", "nacionalidad", "activo"});
    for (const auto& investigador : catalogo.investigadores) {
        if (!investigador) continue;
        investigadores += serializar_fila_csv(
            {investigador->codigo_rh, investigador->nombre_completo, investigador->categoria,
             investigador->formacion_academica, investigador->nacionalidad,
             investigador->activo ? "True" : "False"});
    }

    QString productos;
    productos += serializar_fila_csv(
        {"codigo_identificador", "titulo", "tipo_mayor", "subtipo", "ano",
         "estado_validacion", "activo"});
    for (auto* nodo = catalogo.multilista_productos.cabeza(); nodo != nullptr;
         nodo = nodo->siguiente_global) {
        if (!nodo->producto) continue;
        const auto& producto = *nodo->producto;
        productos += serializar_fila_csv(
            {producto.codigo_identificador, producto.titulo, producto.tipo_mayor,
             producto.subtipo, QString::number(producto.ano), producto.estado_validacion,
             producto.activo ? "True" : "False"});
    }

    return {grupos, investigadores, productos};
}

bool guardar_csv_atomico(
    const QString& ruta,
    const QString& contenido,
    QString& error) {
    error.clear();
    QSaveFile archivo(ruta);
    if (!archivo.open(QIODevice::WriteOnly)) {
        error = archivo.errorString();
        return false;
    }
    const QByteArray bytes = contenido.toUtf8();
    if (archivo.write(bytes) != bytes.size()) {
        error = archivo.errorString();
        archivo.cancelWriting();
        return false;
    }
    if (!archivo.commit()) {
        error = archivo.errorString();
        return false;
    }
    return true;
}

} // namespace pea::datos
