#include "pea/gui/ventana_principal.hpp"
#include "pea/version.hpp"
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QStatusBar>
#include <QFrame>

namespace pea::gui {

VentanaPrincipal::VentanaPrincipal(QWidget* parent)
    : QMainWindow(parent) {
    setWindowTitle(QString::fromStdString(std::string(APP_NAME) + " - Programa Estadístico de Análisis de Investigación (UPC)"));
    resize(1280, 720);
    setMinimumSize(960, 540);

    configurarEstilo();
    construirUi();
}

void VentanaPrincipal::configurarEstilo() {
    QString estilo = R"(
        QMainWindow {
            background-color: #F8F9FA;
        }
        QStatusBar {
            background-color: #003366;
            color: #FFFFFF;
            font-size: 12px;
            padding: 4px;
        }
        QStatusBar QLabel {
            color: #FFFFFF;
        }
    )";
    setStyleSheet(estilo);
}

void VentanaPrincipal::construirUi() {
    auto* widgetCentral = new QWidget(this);
    setCentralWidget(widgetCentral);

    auto* layoutPrincipal = new QVBoxLayout(widgetCentral);
    layoutPrincipal->setContentsMargins(24, 24, 24, 24);
    layoutPrincipal->setSpacing(20);

    // Cabecera institucional
    auto* frameCabecera = new QFrame(this);
    frameCabecera->setStyleSheet("background-color: #003366; border-radius: 8px; padding: 16px;");
    auto* layoutCabecera = new QVBoxLayout(frameCabecera);

    auto* lblTitulo = new QLabel("PEA-i · Programa Estadístico de Análisis de Investigación", frameCabecera);
    lblTitulo->setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;");
    layoutCabecera->addWidget(lblTitulo);

    auto* lblSubtitulo = new QLabel(QString("Universidad Popular del Cesar · Versión %1 (C++17 / Qt 6)").arg(APP_VERSION), frameCabecera);
    lblSubtitulo->setStyleSheet("color: #E2E8F0; font-size: 13px;");
    layoutCabecera->addWidget(lblSubtitulo);

    layoutPrincipal->addWidget(frameCabecera);

    // Contenido informativo central
    auto* frameContenido = new QFrame(this);
    frameContenido->setStyleSheet("background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 24px;");
    auto* layoutContenido = new QVBoxLayout(frameContenido);

    auto* lblEstado = new QLabel("Esqueleto operativo C++ / Qt 6 Widgets listo para integración.", frameContenido);
    lblEstado->setStyleSheet("color: #2D3748; font-size: 15px; font-weight: bold;");
    layoutContenido->addWidget(lblEstado);

    auto* lblDetalle = new QLabel(
        "Módulos arquitectónicos verificados:\n"
        " • Interfaz Gráfica de Usuario (Qt 6 Widgets / QMainWindow)\n"
        " • Cliente HTTPS / REST / RPC Supabase (QNetworkAccessManager + TLS)\n"
        " • Gestión segura de credenciales en memoria volátil\n"
        " • Pruebas unitarias doctest",
        frameContenido
    );
    lblDetalle->setStyleSheet("color: #4A5568; font-size: 13px; line-height: 1.6;");
    layoutContenido->addWidget(lblDetalle);

    layoutContenido->addStretch();
    layoutPrincipal->addWidget(frameContenido);

    // Barra de estado
    auto* status = statusBar();
    status->showMessage("Listo · Universidad Popular del Cesar");
}

} // namespace pea::gui
