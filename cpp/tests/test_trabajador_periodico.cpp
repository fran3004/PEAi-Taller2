#include <doctest/doctest.h>

#include "pea/tui/trabajador_periodico.hpp"

#include <atomic>
#include <condition_variable>
#include <mutex>
#include <stdexcept>
#include <thread>

using pea::tui::TrabajadorPeriodico;
using namespace std::chrono_literals;

TEST_CASE("Trabajador periódico ejecuta la primera tarea en un hilo propio") {
    std::mutex mutex;
    std::condition_variable condicion;
    std::atomic<int> llamadas{0};
    std::thread::id hilo_tarea;
    const auto hilo_principal = std::this_thread::get_id();

    TrabajadorPeriodico trabajador(
        [&] {
            return TrabajadorPeriodico::Tarea([&] {
                {
                    std::lock_guard<std::mutex> bloqueo(mutex);
                    hilo_tarea = std::this_thread::get_id();
                }
                ++llamadas;
                condicion.notify_all();
            });
        },
        [](const std::string&) {},
        30s);

    std::unique_lock<std::mutex> bloqueo(mutex);
    REQUIRE(condicion.wait_for(
        bloqueo, 1s, [&] { return llamadas.load() == 1; }));
    const bool hilo_separado = hilo_tarea != hilo_principal;
    CHECK(hilo_separado);
    bloqueo.unlock();

    trabajador.detener();
    trabajador.detener();
    CHECK(llamadas.load() == 1);
}

TEST_CASE("Trabajador periódico repite la tarea y se detiene durante la espera") {
    std::mutex mutex;
    std::condition_variable condicion;
    std::atomic<int> llamadas{0};

    TrabajadorPeriodico trabajador(
        [&] {
            return TrabajadorPeriodico::Tarea([&] {
                ++llamadas;
                condicion.notify_all();
            });
        },
        [](const std::string&) {},
        5ms);

    std::unique_lock<std::mutex> bloqueo(mutex);
    REQUIRE(condicion.wait_for(
        bloqueo, 1s, [&] { return llamadas.load() >= 3; }));
    bloqueo.unlock();

    trabajador.detener();
    const int llamadas_al_detener = llamadas.load();
    std::this_thread::sleep_for(20ms);
    CHECK(llamadas.load() == llamadas_al_detener);
}

TEST_CASE("Trabajador periódico comunica los errores de su tarea") {
    std::mutex mutex;
    std::condition_variable condicion;
    std::string error_recibido;

    TrabajadorPeriodico trabajador(
        [] {
            return TrabajadorPeriodico::Tarea(
                [] { throw std::runtime_error("fallo de prueba"); });
        },
        [&](const std::string& error) {
            {
                std::lock_guard<std::mutex> bloqueo(mutex);
                error_recibido = error;
            }
            condicion.notify_all();
        },
        30s);

    std::unique_lock<std::mutex> bloqueo(mutex);
    REQUIRE(condicion.wait_for(
        bloqueo, 1s, [&] { return !error_recibido.empty(); }));
    CHECK(error_recibido == "fallo de prueba");
    bloqueo.unlock();
    trabajador.detener();
}

TEST_CASE("Trabajador periódico rechaza configuración incompleta") {
    CHECK_THROWS_AS(
        TrabajadorPeriodico({}, [](const std::string&) {}, 1s),
        std::invalid_argument);
    CHECK_THROWS_AS(TrabajadorPeriodico([] { return TrabajadorPeriodico::Tarea{}; }, {}, 1s),
        std::invalid_argument);
    CHECK_THROWS_AS(
        TrabajadorPeriodico([] { return TrabajadorPeriodico::Tarea{}; },
                            [](const std::string&) {}, 0ms),
        std::invalid_argument);
}

TEST_CASE("Trabajador periódico reporta un error al preparar el cliente") {
    std::mutex mutex;
    std::condition_variable condicion;
    std::string error_recibido;

    TrabajadorPeriodico trabajador(
        []() -> TrabajadorPeriodico::Tarea {
            throw std::runtime_error("no se pudo preparar");
        },
        [&](const std::string& error) {
            {
                std::lock_guard<std::mutex> bloqueo(mutex);
                error_recibido = error;
            }
            condicion.notify_all();
        },
        30s);

    std::unique_lock<std::mutex> bloqueo(mutex);
    REQUIRE(condicion.wait_for(
        bloqueo, 1s, [&] { return !error_recibido.empty(); }));
    CHECK(error_recibido == "no se pudo preparar");
    bloqueo.unlock();
    trabajador.detener();
}

TEST_CASE("Trabajador periódico informa si la tarea preparada está vacía") {
    std::mutex mutex;
    std::condition_variable condicion;
    std::string error_recibido;

    TrabajadorPeriodico trabajador(
        [] { return TrabajadorPeriodico::Tarea{}; },
        [&](const std::string& error) {
            {
                std::lock_guard<std::mutex> bloqueo(mutex);
                error_recibido = error;
            }
            condicion.notify_all();
        },
        30s);

    std::unique_lock<std::mutex> bloqueo(mutex);
    REQUIRE(condicion.wait_for(
        bloqueo, 1s, [&] { return !error_recibido.empty(); }));
    CHECK(error_recibido == "La tarea preparada para el trabajador está vacía.");
    bloqueo.unlock();
    trabajador.detener();
}
