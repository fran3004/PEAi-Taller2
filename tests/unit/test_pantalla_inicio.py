"""Pruebas unitarias completas para PantallaInicio (Sección 6.1 y 11)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from pea.gui.pantallas.inicio import FilaRanking, PantallaInicio
from pea.gui.ventana_principal import Pantalla
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


@pytest.fixture
def servicio_con_datos() -> ServicioAplicacion:
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    return servicio


@pytest.fixture
def servicio_vacio() -> ServicioAplicacion:
    return ServicioAplicacion()


def test_fila_ranking(qapp: QApplication) -> None:
    """Verifica el componente de filas de ranking Top 5."""
    fila = FilaRanking(puesto=1, titulo="Dr. Ficticio", subtitulo="", valor=15, max_valor=20)
    assert fila.height() == 48


def test_pantalla_inicio_modo_institucion(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Valida la visualización institucional de Inicio con datos de demostración."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    pantalla.resize(QSize(1400, 900))
    qapp.processEvents()

    # Estado de contenido activo
    assert pantalla._apilador_estado.currentIndex() == 1

    # 1. Ámbito Institución
    assert "Universidad Popular del Cesar" in pantalla._lbl_titulo_ambito.text()
    assert pantalla._avatar_ambito.nombre == "Universidad Popular del Cesar"
    assert pantalla._combo_grupos.isHidden()

    # 6 Fichas KPI presentes y actualizadas
    assert int(pantalla._kpi_1.lbl_valor.text().replace(".", "")) > 0
    assert int(pantalla._kpi_2.lbl_valor.text().replace(".", "")) > 0
    assert int(pantalla._kpi_3.lbl_valor.text().replace(".", "")) > 0
    assert pantalla._kpi_3.minigrafico is not None
    assert not pantalla._kpi_3.minigrafico.esta_vacio()

    # Gráficos poblados
    assert not pantalla._grafico_dona.esta_vacio()
    assert not pantalla._mini_red.esta_vacio()

    # Rankings poblados
    assert pantalla._layout_ranking_1.count() > 0
    assert pantalla._layout_ranking_2.count() > 0


def test_pantalla_inicio_modo_grupo(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Valida el cambio a modo Grupo y actualización de sus componentes."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    pantalla.resize(QSize(1400, 900))
    pantalla.show()
    qapp.processEvents()

    # Cambiar a modo grupo
    pantalla._selector_ambito.seleccionar("grupo")
    qapp.processEvents()

    assert not pantalla._combo_grupos.isHidden()
    assert pantalla._combo_grupos.count() > 0
    assert "Grupo de Investigación" in pantalla._lbl_titulo_ambito.text()

    # KPI 1 debe ser Integrantes en modo grupo
    assert pantalla._kpi_1.lbl_titulo.text() == "Integrantes"
    assert pantalla._kpi_2.lbl_titulo.text() == "Estudiantes"
    assert pantalla._kpi_6.lbl_titulo.text() == "Aporte a la institución"


def test_pantalla_inicio_detalles_desplegables(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el botón de detalles despliegue y oculte el panel."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    pantalla.show()
    qapp.processEvents()
    assert not pantalla._panel_detalles.isVisible()

    pantalla._btn_detalles.click()
    assert pantalla._panel_detalles.isVisible()
    assert "Ocultar detalles" in pantalla._btn_detalles.text()

    pantalla._btn_detalles.click()
    assert not pantalla._panel_detalles.isVisible()
    assert "Ver más detalles" in pantalla._btn_detalles.text()


def test_pantalla_inicio_navegacion_red(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el enlace de abrir red emita la señal a Pantalla.REDES."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    destinos: list[int] = []
    pantalla.solicitar_navegacion.connect(destinos.append)

    pantalla._al_abrir_red_completa()
    assert destinos == [int(Pantalla.REDES)]


def test_pantalla_inicio_filtro_anios(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica la propagación y recálculo ante cambios de filtro de años."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    filtros_emitidos: list[FiltroAnios] = []
    pantalla.filtro_cambiado.connect(filtros_emitidos.append)

    nuevo_filtro = FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3)
    pantalla.establecer_filtro(nuevo_filtro)
    qapp.processEvents()

    assert pantalla._filtro_actual.modo == ModoFiltroAnios.ULTIMOS


def test_pantalla_inicio_estado_vacio(
    qapp: QApplication, servicio_vacio: ServicioAplicacion
) -> None:
    """Verifica que sin datos se muestre el EstadoVacio con sus dos acciones."""
    pantalla = PantallaInicio(servicio=servicio_vacio)
    qapp.processEvents()

    assert pantalla._apilador_estado.currentIndex() == 2

    # Cargar demostración desde el botón
    pantalla._estado_vacio.accion_secundaria_pulsada.emit()
    qapp.processEvents()

    assert pantalla._apilador_estado.currentIndex() == 1
    assert "Universidad Popular del Cesar" in pantalla._lbl_titulo_ambito.text()


def test_pantalla_inicio_responsividad_rejilla(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica la conmutación entre 4 columnas (>=1500 px) y 2x2 (<1500 px)."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)

    # ≥ 1500 px
    pantalla.resize(QSize(1600, 900))
    pantalla._reorganizar_rejilla(1600)
    assert pantalla._es_cuatro_columnas is True

    # < 1360 px
    pantalla.resize(QSize(1100, 700))
    pantalla._reorganizar_rejilla(1100)
    assert pantalla._es_cuatro_columnas is False


@pytest.mark.parametrize(
    ("ancho", "alto", "cuatro_columnas", "minimo_combo"),
    [
        (1100, 700, False, 200),
        (1366, 768, False, 280),
        (1920, 1080, True, 280),
    ],
)
def test_pantalla_inicio_sin_desborde_horizontal(
    qapp: QApplication,
    servicio_con_datos: ServicioAplicacion,
    ancho: int,
    alto: int,
    cuatro_columnas: bool,
    minimo_combo: int,
) -> None:
    """Comprueba que Inicio conserva su rejilla sin barra horizontal."""
    pantalla = PantallaInicio(servicio=servicio_con_datos)
    pantalla.resize(QSize(ancho, alto))
    pantalla.show()
    qapp.processEvents()

    assert not pantalla._scroll_contenido.horizontalScrollBar().isVisible()
    assert pantalla._es_cuatro_columnas is cuatro_columnas
    assert pantalla._combo_grupos.minimumWidth() == minimo_combo
