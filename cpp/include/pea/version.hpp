#pragma once

#include <string>

namespace pea {

constexpr const char* APP_NAME = "PEA-i";
constexpr const char* APP_VERSION = "0.1.0";
constexpr const char* INSTITUCION = "Universidad Popular del Cesar";

inline std::string obtener_version() {
    return std::string(APP_NAME) + " versión " + APP_VERSION + " (" + INSTITUCION + ")";
}

} // namespace pea
