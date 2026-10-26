#pragma once

#include <QJsonObject>
#include <QString>
#include <optional>

namespace pea::servicios {
QJsonObject modelo_puntajes();
QJsonObject puntaje_producto(const QJsonObject& producto);
QJsonObject calcular_indicador(const QJsonObject& datos, const QString& ambito,
                              const QString& codigo, int corte,
                              std::optional<int> desde = std::nullopt,
                              const QJsonObject& referencia = {});
}
