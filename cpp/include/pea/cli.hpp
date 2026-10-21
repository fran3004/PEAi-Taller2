#pragma once

#include <functional>

#include <QStringList>

namespace pea::servicios {
class CatalogoInvestigacion;
}

namespace pea::cli {

using CargadorCatalogoCsv =
    std::function<void(servicios::CatalogoInvestigacion&)>;

int ejecutar(const QStringList& argumentos);
int ejecutar(
    const QStringList& argumentos,
    const CargadorCatalogoCsv& cargar_catalogo_csv);

} // namespace pea::cli
