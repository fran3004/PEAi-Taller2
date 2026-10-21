#pragma once

#include <array>
#include <QString>

namespace pea::servicios {
class CatalogoInvestigacion;
}

namespace pea::datos {

[[nodiscard]] std::array<QString, 3> serializar_catalogo_csv(
    const servicios::CatalogoInvestigacion& catalogo);

[[nodiscard]] bool guardar_csv_atomico(
    const QString& ruta,
    const QString& contenido,
    QString& error);

} // namespace pea::datos
