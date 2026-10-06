"""Pruebas de responsividad para Importar, Configuración y Acerca de."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QAbstractScrollArea, QApplication

from pea.gui.pantallas.acerca import PantallaAcerca
from pea.gui.pantallas.configuracion import PantallaConfiguracion
from pea.gui.pantallas.importar import PantallaImportar
from pea.servicios.servicio_aplicacion import ServicioAplicacion


@pytest.fixture
def servicio() -> ServicioAplicacion:
    return ServicioAplicacion()


def _mostrar(pantalla: object, qapp: QApplication, ancho: int, alto: int) -> None:
    assert hasattr(pantalla, "resize")
    pantalla.resize(QSize(ancho, alto))  # type: ignore[attr-defined]
    pantalla.show()  # type: ignore[attr-defined]
    qapp.processEvents()


def _sin_barras_horizontales(pantalla: object) -> None:
    areas = pantalla.findChildren(QAbstractScrollArea)  # type: ignore[attr-defined]
    assert all(not area.horizontalScrollBar().isVisible() for area in areas)


@pytest.mark.parametrize("ancho, alto", [(1100, 700), (1366, 768)])
def test_importar_sin_desborde_y_acciones_visibles(
    qapp: QApplication, servicio: ServicioAplicacion, ancho: int, alto: int
) -> None:
    pantalla = PantallaImportar(servicio=servicio)
    _mostrar(pantalla, qapp, ancho, alto)

    _sin_barras_horizontales(pantalla)
    assert pantalla.btn_encolar_csv.isVisible()
    assert pantalla.btn_encolar_pdf.isVisible()
    assert pantalla.btn_encolar_url.isVisible()
    assert pantalla.btn_procesar_siguiente.isVisible()


@pytest.mark.parametrize("ancho, alto", [(1100, 700), (1366, 768)])
def test_configuracion_sin_desborde_y_splitter_separado(
    qapp: QApplication, servicio: ServicioAplicacion, ancho: int, alto: int
) -> None:
    pantalla = PantallaConfiguracion(servicio=servicio)
    _mostrar(pantalla, qapp, ancho, alto)

    _sin_barras_horizontales(pantalla)
    assert pantalla.txt_url.sizePolicy().horizontalPolicy().name == "Expanding"
    assert pantalla.txt_clave.sizePolicy().horizontalPolicy().name == "Expanding"
    assert pantalla.txt_url.minimumHeight() >= 36
    assert pantalla.txt_clave.minimumHeight() >= 36
    assert pantalla.txt_correo.minimumHeight() >= 36
    assert pantalla.txt_pass.minimumHeight() >= 36
    assert pantalla.txt_url.height() >= 36
    assert pantalla.txt_clave.height() >= 36
    assert pantalla.txt_correo.height() >= 36
    assert pantalla.txt_pass.height() >= 36
    assert pantalla.splitter_verificacion.minimumHeight() >= 0
    pantalla.selector_seccion.seleccionar("cruzada")
    qapp.processEvents()
    assert pantalla.splitter_verificacion.sizes()[0] > 0
    assert pantalla.splitter_verificacion.sizes()[1] > 0


@pytest.mark.parametrize("ancho, alto", [(1100, 700), (1366, 768)])
def test_acerca_muestra_identidad_sin_desborde(
    qapp: QApplication, servicio: ServicioAplicacion, ancho: int, alto: int
) -> None:
    pantalla = PantallaAcerca(servicio=servicio)
    _mostrar(pantalla, qapp, ancho, alto)

    _sin_barras_horizontales(pantalla)
    assert pantalla.lbl_institucion.isVisible()
    assert pantalla.lbl_nombre_version.isVisible()
    assert pantalla.lbl_proposito.isVisible()
