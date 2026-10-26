#pragma once
#include <QJsonObject>
#include <QString>
#include "pea/servicios/catalogo_investigacion.hpp"

namespace pea::datos {
QJsonObject serializar_catalogo(const servicios::CatalogoInvestigacion& catalogo);
servicios::CatalogoInvestigacion restaurar_catalogo(const QJsonObject& datos);
servicios::CatalogoInvestigacion cargar_archivo(const QString& ruta);
void guardar_archivo(const QString& ruta, const QJsonObject& datos);
}
