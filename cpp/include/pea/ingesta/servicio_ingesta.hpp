#pragma once

#include <memory>
#include <QList>
#include <QString>
#include "pea/estructuras/cola.hpp"
#include "pea/ingesta/extractor_url.hpp"
#include "pea/ingesta/modelos.hpp"
#include "pea/servicios/catalogo_investigacion.hpp"

namespace pea::ingesta {

class ServicioIngesta {
public:
    explicit ServicioIngesta(
        std::shared_ptr<servicios::CatalogoInvestigacion> catalogo,
        std::unique_ptr<ExtractorURL> extractor = nullptr
    );

    estructuras::TareaIngesta encolar_url(
        const QString& url,
        bool persistir = false,
        bool anonimizar = false,
        const QString& salida_dir = QStringLiteral("datos/fuentes/extraccion")
    );

    estructuras::TareaIngesta encolar_csv(
        const QString& ruta_csv,
        const QString& tipo_entidad = QString(),
        bool persistir = false
    );

    std::optional<InformeIngesta> procesar_siguiente();
    QList<InformeIngesta> procesar_todas();

    [[nodiscard]] estructuras::Cola<estructuras::TareaIngesta>& cola() noexcept {
        return m_catalogo->cola_importacion;
    }

private:
    std::shared_ptr<servicios::CatalogoInvestigacion> m_catalogo;
    std::unique_ptr<ExtractorURL> m_extractor_url;

    InformeIngesta procesar_tarea_url(estructuras::TareaIngesta& tarea);
    InformeIngesta procesar_tarea_csv(estructuras::TareaIngesta& tarea);
};

} // namespace pea::ingesta
