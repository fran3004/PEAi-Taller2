#pragma once

#include <QMainWindow>

namespace pea::gui {

class VentanaPrincipal : public QMainWindow {
    Q_OBJECT

public:
    explicit VentanaPrincipal(QWidget* parent = nullptr);
    ~VentanaPrincipal() override = default;

private:
    void configurarEstilo();
    void construirUi();
};

} // namespace pea::gui
