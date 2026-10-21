#pragma once

#include <memory>

#include <QString>

namespace pea::datos {
class Sesion;
}

namespace pea {
class ClienteHTTPSupabase;
}

namespace pea::datos {

struct ConfiguracionConexion {
    QString url;
    QString clave_publicable;
    QString correo;
    bool url_configurada{false};
    bool clave_configurada{false};
    bool acceso_evaluacion{false};
};

[[nodiscard]] ConfiguracionConexion leer_configuracion_conexion();
[[nodiscard]] QString leer_clave_usuario();
void validar_configuracion_conexion(const ConfiguracionConexion& configuracion);
[[nodiscard]] std::unique_ptr<ClienteHTTPSupabase> crear_cliente_configurado(
    QString* correo = nullptr,
    std::shared_ptr<Sesion>* sesion = nullptr);

} // namespace pea::datos
