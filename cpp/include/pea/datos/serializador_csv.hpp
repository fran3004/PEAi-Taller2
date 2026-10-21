#pragma once

#include <QString>
#include <QStringList>

namespace pea::datos {

inline QString escapar_celda_csv(const QString& valor) {
    QString escapado = valor;
    escapado.replace("\"", "\"\"");
    if (valor.contains(',') || valor.contains('"') || valor.contains('\n') ||
        valor.contains('\r')) {
        return "\"" + escapado + "\"";
    }
    return escapado;
}

inline QString serializar_fila_csv(const QStringList& valores) {
    QStringList celdas;
    celdas.reserve(valores.size());
    for (const auto& valor : valores) {
        celdas.push_back(escapar_celda_csv(valor));
    }
    return celdas.join(',') + "\r\n";
}

} // namespace pea::datos
