#pragma once
#include <QString>

namespace pea::tui {

int ejecutar(
    bool datos_demostracion = false,
    bool autoprueba = false,
    bool sin_color = false,
    bool ascii = false, const QString& archivo_local = {}, bool vacio = false);

} // namespace pea::tui
