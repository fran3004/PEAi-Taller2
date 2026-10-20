"""Pruebas unitarias para CLI y GUI de Python."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pea.cli import main as cli_main
from pea.gui import VentanaPrincipal
from pea.gui import main as gui_main
from pea.gui.ventana_principal import (
    _textos_elididos_sin_tooltip,
    _widget_alcanzable_con_scroll,
    _widgets_fuera_de_ventana,
)
from pea.version import APP_NAME, APP_VERSION, INSTITUCION, obtener_version


def test_version_e_identidad() -> None:
    cadena = obtener_version()
    assert APP_NAME in cadena
    assert APP_VERSION in cadena
    assert INSTITUCION in cadena


def test_cli_info(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = cli_main(["info"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert APP_NAME in captura.out
    assert APP_VERSION in captura.out


def test_cli_ping_sin_credenciales(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = cli_main(["ping"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert "Aviso" in captura.out


def test_gui_ventana_principal(qapp: QApplication) -> None:
    ventana = VentanaPrincipal()
    assert APP_NAME in ventana.windowTitle()
    assert ventana.minimumWidth() >= 960
    assert ventana.minimumHeight() >= 540
    assert ventana.centralWidget() is not None


def test_gui_autoprueba(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = gui_main(["--autoprueba"])
    assert codigo == 0
    captura = capsys.readouterr()
    assert "Cero hallazgos en las 24 combinaciones" in captura.out
    assert "Autoprueba de GUI Python completada exitosamente." in captura.out
    assert "FALLA" not in captura.out


def test_gui_autoprueba_propaga_fallo(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import pea.gui as modulo_gui

    monkeypatch.setattr(modulo_gui, "VentanaPrincipal", lambda: object())
    monkeypatch.setattr(modulo_gui, "ejecutar_autoprueba", lambda app, ventana: 3)

    assert gui_main(["--autoprueba"]) == 3
    captura = capsys.readouterr()
    assert "Autoprueba de GUI Python fallida" in captura.out
    assert "completada exitosamente" not in captura.out


def test_autoprueba_ignora_widgets_alcanzables_con_desplazamiento(qapp: QApplication) -> None:
    ventana = QWidget()
    ventana.resize(240, 140)

    scroll = QScrollArea(ventana)
    scroll.setGeometry(0, 0, 180, 100)
    contenido = QWidget()
    contenido.setObjectName("contenido_desplazable")
    contenido.setMinimumSize(160, 320)
    layout = QVBoxLayout(contenido)
    filas = []
    for indice in range(10):
        fila = QLabel(f"Fila {indice}", contenido)
        fila.setMinimumHeight(28)
        if indice == 9:
            fila.setObjectName("fila_desplazable")
        filas.append(fila)
        layout.addWidget(fila)
    scroll.setWidget(contenido)

    fuera = QLabel("Fuera", ventana)
    fuera.setObjectName("fuera_de_ventana")
    fuera.setGeometry(220, 10, 60, 24)

    ventana.show()
    qapp.processEvents()

    assert _widget_alcanzable_con_scroll(filas[-1], ventana)
    widgets_fuera = _widgets_fuera_de_ventana(ventana)
    assert "fuera_de_ventana" in widgets_fuera
    assert "fila_desplazable" not in widgets_fuera
    assert "contenido_desplazable" not in widgets_fuera


def test_autoprueba_detecta_elipsis_sin_tooltip_en_label_boton_y_encabezado(
    qapp: QApplication,
) -> None:
    ventana = QWidget()
    ventana.resize(420, 240)

    etiqueta = QLabel("Etiqueta demasiado larga", ventana)
    etiqueta.setObjectName("etiqueta_prueba")
    etiqueta.setGeometry(0, 0, 30, 24)

    boton = QPushButton("Botón demasiado largo", ventana)
    boton.setObjectName("boton_prueba")
    boton.setGeometry(0, 32, 30, 24)

    modelo = QStandardItemModel(1, 1, ventana)
    modelo.setHeaderData(0, Qt.Orientation.Horizontal, "Encabezado de columna demasiado largo")
    tabla = QTableView(ventana)
    tabla.setGeometry(160, 70, 120, 100)
    tabla.setModel(modelo)
    encabezado = tabla.horizontalHeader()
    encabezado.setObjectName("encabezado_prueba")
    encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    encabezado.resizeSection(0, 24)

    ventana.show()
    qapp.processEvents()

    hallazgos = _textos_elididos_sin_tooltip(ventana)
    assert any("etiqueta_prueba" in hallazgo for hallazgo in hallazgos)
    assert any("boton_prueba" in hallazgo for hallazgo in hallazgos)
    assert any("encabezado_prueba" in hallazgo for hallazgo in hallazgos)

    etiqueta.setToolTip("Etiqueta demasiado larga")
    boton.setToolTip("Botón demasiado largo")
    modelo.setHeaderData(
        0,
        Qt.Orientation.Horizontal,
        "Encabezado de columna demasiado largo",
        Qt.ItemDataRole.ToolTipRole,
    )
    assert _textos_elididos_sin_tooltip(ventana) == []
