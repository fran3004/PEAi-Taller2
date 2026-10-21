#include "pea/tui/trabajador_periodico.hpp"

#include <stdexcept>
#include <utility>

namespace pea::tui {

TrabajadorPeriodico::TrabajadorPeriodico(
    PrepararTarea preparar_tarea,
    NotificarError notificar_error,
    std::chrono::milliseconds intervalo)
    : m_preparar_tarea(std::move(preparar_tarea)),
      m_notificar_error(std::move(notificar_error)),
      m_intervalo(intervalo) {
    if (!m_preparar_tarea || !m_notificar_error) {
        throw std::invalid_argument(
            "El trabajador periódico requiere una tarea y un notificador.");
    }
    if (m_intervalo.count() <= 0) {
        throw std::invalid_argument(
            "El intervalo del trabajador periódico debe ser positivo.");
    }
    m_hilo = std::thread(&TrabajadorPeriodico::ejecutar, this);
}

TrabajadorPeriodico::~TrabajadorPeriodico() {
    detener();
}

void TrabajadorPeriodico::detener() {
    {
        std::lock_guard<std::mutex> bloqueo(m_mutex);
        m_detener = true;
    }
    m_condicion.notify_all();
    if (m_hilo.joinable()) {
        m_hilo.join();
    }
}

void TrabajadorPeriodico::ejecutar() {
    Tarea tarea;
    try {
        tarea = m_preparar_tarea();
        if (!tarea) {
            m_notificar_error(
                "La tarea preparada para el trabajador está vacía.");
            return;
        }
    } catch (const std::exception& error) {
        m_notificar_error(error.what());
        return;
    } catch (...) {
        m_notificar_error(
            "Error desconocido al preparar el trabajador periódico.");
        return;
    }

    while (true) {
        try {
            tarea();
        } catch (const std::exception& error) {
            m_notificar_error(error.what());
        } catch (...) {
            m_notificar_error("Error desconocido en el trabajador periódico.");
        }

        std::unique_lock<std::mutex> bloqueo(m_mutex);
        if (m_condicion.wait_for(
                bloqueo, m_intervalo, [this] { return m_detener; })) {
            return;
        }
    }
}

} // namespace pea::tui
