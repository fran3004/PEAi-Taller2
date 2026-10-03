#include <doctest/doctest.h>
#include <QApplication>
#include <QCoreApplication>
#include "pea/gui/ventana_principal.hpp"

TEST_CASE("VentanaPrincipal - Inicialización y propiedades básicas") {
    int argc = 1;
    char arg0[] = "pruebas_cpp";
    char* argv[] = { arg0, nullptr };

    qputenv("QT_QPA_PLATFORM", "offscreen");

    std::unique_ptr<QApplication> appProvisional;
    if (!QCoreApplication::instance()) {
        appProvisional = std::make_unique<QApplication>(argc, argv);
    }

    pea::gui::VentanaPrincipal ventana;
    CHECK(ventana.windowTitle().contains("PEA-i"));
    CHECK(ventana.minimumWidth() >= 960);
    CHECK(ventana.minimumHeight() >= 540);
    CHECK(ventana.centralWidget() != nullptr);
}
