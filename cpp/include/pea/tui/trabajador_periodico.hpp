#pragma once

#include <chrono>
#include <condition_variable>
#include <functional>
#include <mutex>
#include <string>
#include <thread>

namespace pea::tui {

class TrabajadorPeriodico {
public:
    using Tarea = std::function<void()>;
    using PrepararTarea = std::function<Tarea()>;
    using NotificarError = std::function<void(const std::string&)>;

    TrabajadorPeriodico(
        PrepararTarea preparar_tarea,
        NotificarError notificar_error,
        std::chrono::milliseconds intervalo);
    ~TrabajadorPeriodico();

    TrabajadorPeriodico(const TrabajadorPeriodico&) = delete;
    TrabajadorPeriodico& operator=(const TrabajadorPeriodico&) = delete;

    void detener();

private:
    void ejecutar();

    PrepararTarea m_preparar_tarea;
    NotificarError m_notificar_error;
    std::chrono::milliseconds m_intervalo;
    std::mutex m_mutex;
    std::condition_variable m_condicion;
    bool m_detener{false};
    std::thread m_hilo;
};

} // namespace pea::tui
