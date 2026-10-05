"""Pruebas unitarias para el módulo de análisis de redes y PantallaRedes (Sección 6.5 y ADR-0015)."""

from __future__ import annotations

import math
from typing import Any

import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from pea.gui.pantallas.redes import PantallaRedes
from pea.gui.red.arista import AristaGrafoItem
from pea.gui.red.disposicion import calcular_disposicion_fuerzas
from pea.gui.red.nodo import NodoGrafoItem
from pea.gui.red.vista_red import VistaRed
from pea.servicios.servicio_aplicacion import ServicioAplicacion


@pytest.fixture
def servicio_con_datos() -> ServicioAplicacion:
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    return servicio


# ---------------------------------------------------------------------------
# 1. Disposición por fuerzas determinista (ADR-0015)
# ---------------------------------------------------------------------------


def test_disposicion_fuerzas_determinista() -> None:
    """Verifica que calcular_disposicion_fuerzas es 100% determinista con semilla fija."""
    nodos = [
        {"id": "INV-01", "grado": 5},
        {"id": "INV-02", "grado": 3},
        {"id": "INV-03", "grado": 2},
        {"id": "INV-04", "grado": 1},
    ]
    aristas = [
        {"origen": "INV-01", "destino": "INV-02", "peso": 4},
        {"origen": "INV-01", "destino": "INV-03", "peso": 2},
        {"origen": "INV-02", "destino": "INV-04", "peso": 1},
    ]

    # Ejecución 1 con semilla fija 42
    pos1 = calcular_disposicion_fuerzas(nodos, aristas, ancho=1000, alto=700, semilla=42)
    # Ejecución 2 con semilla fija 42
    pos2 = calcular_disposicion_fuerzas(nodos, aristas, ancho=1000, alto=700, semilla=42)

    assert set(pos1.keys()) == {"INV-01", "INV-02", "INV-03", "INV-04"}
    for nid in pos1:
        x1, y1 = pos1[nid]
        x2, y2 = pos2[nid]
        assert math.isclose(x1, x2, abs_tol=1e-9), f"Diferencia en x para nodo {nid}"
        assert math.isclose(y1, y2, abs_tol=1e-9), f"Diferencia en y para nodo {nid}"


def test_calculo_geometria_nodos_y_aristas() -> None:
    """Verifica fórmulas reglamentarias: r = 8 + 2.5*sqrt(grado) y grosor = 1 + log2(peso)."""
    nodo = NodoGrafoItem(
        codigo="INV-TEST",
        nombre="Juan Pérez",
        categoria="Investigador Senior (IS)",
        grado=16,
        intermediacion=0.25,
    )
    radio_esperado = 8.0 + 2.5 * math.sqrt(16)  # 8 + 2.5*4 = 18.0
    assert math.isclose(nodo.radio, radio_esperado, abs_tol=1e-4)
    assert nodo.nombre_abreviado == "J. Pérez"

    arista = AristaGrafoItem(
        nodo_origen=nodo,
        nodo_destino=nodo,
        peso=4,
    )
    grosor_esperado = 1.0 + math.log2(4)  # 1 + 2 = 3.0
    assert math.isclose(arista.grosor, grosor_esperado, abs_tol=1e-4)


# ---------------------------------------------------------------------------
# 2. Construcción de PantallaRedes y sus componentes
# ---------------------------------------------------------------------------


def test_pantalla_redes_construccion_y_componentes(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica la existencia y dimensiones de todos los componentes de la Sección 6.5."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    pantalla.resize(QSize(1360, 800))
    qapp.processEvents()

    # Barra superior de contexto
    assert pantalla.chip_ventana is not None
    assert pantalla.btn_exportar_png is not None

    # Fila de controles
    assert pantalla.combo_grupo is not None
    assert pantalla.combo_min_coautorias is not None
    assert pantalla.campo_busqueda is not None
    assert pantalla.btn_reordenar is not None
    assert pantalla.btn_zoom_mas is not None
    assert pantalla.btn_zoom_menos is not None
    assert pantalla.btn_zoom_ajustar is not None

    # Canvas del grafo y leyenda
    assert isinstance(pantalla.vista_red, VistaRed)
    assert pantalla.vista_red.leyenda is not None

    # Panel lateral de métricas flexible
    assert pantalla.panel_metricas is not None
    assert 280 <= pantalla.panel_metricas.width() <= 340
    assert pantalla.lbl_titulo_metricas.text() == "Métricas de centralidad"


def test_pantalla_redes_reencuadra_grafo_y_pliega_panel(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Comprueba el reencuadre completo y el lienzo ampliado a 1100x700."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    pantalla.resize(QSize(1100, 700))
    pantalla.show()
    qapp.processEvents()
    qapp.processEvents()

    viewport = pantalla.vista_red.viewport().rect()
    for nodo in pantalla.vista_red.items_nodos.values():
        recto = nodo.sceneBoundingRect()
        for esquina in (recto.topLeft(), recto.topRight(), recto.bottomLeft(), recto.bottomRight()):
            punto = pantalla.vista_red.mapFromScene(esquina)
            assert viewport.contains(punto), f"Nodo fuera del viewport: {punto}"

    assert not pantalla.vista_red.horizontalScrollBar().isVisible()
    assert not pantalla._scroll_panel.horizontalScrollBar().isVisible()
    pantalla.btn_alternar_panel.click()
    qapp.processEvents()
    assert pantalla.panel_metricas.isHidden()
    assert pantalla.vista_red.width() > 700
    assert pantalla.btn_alternar_panel.toolTip() == "Muestra el panel de métricas"


# ---------------------------------------------------------------------------
# 3. Carga de red y estado vacío vs seleccionado en panel de métricas
# ---------------------------------------------------------------------------


def test_pantalla_redes_carga_y_metricas_estado_inicial(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el grafo cargue nodos y aristas, y el panel muestre el estado inicial con Top 5."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    pantalla.show()
    qapp.processEvents()

    # Comprobar que hay nodos en la vista
    items_nodos = pantalla.vista_red.items_nodos
    assert len(items_nodos) > 0, "Debe haber nodos en el grafo de demostración"

    # En estado inicial, el panel de métricas está en modo resumen (no hay nodo seleccionado)
    assert not pantalla.widget_estado_vacio.isHidden()
    assert pantalla.widget_estado_seleccionado.isHidden()

    # El resumen de red muestra nodos, enlaces y densidad
    resumen_txt = pantalla.lbl_resumen_red.text()
    assert "Investigadores:" in resumen_txt
    assert "Enlaces de coautoría:" in resumen_txt
    assert "Densidad:" in resumen_txt

    # Hay elementos en el contenedor del Top 5
    assert pantalla.contenedor_top5.count() > 0


def test_pantalla_redes_seleccion_nodo_actualiza_panel(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que seleccionar un nodo actualice el panel de métricas a estado seleccionado."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    pantalla.show()
    qapp.processEvents()

    # Obtener el primer nodo disponible
    nodo_codigo = next(iter(pantalla.vista_red.items_nodos.keys()))
    nodo_item = pantalla.vista_red.items_nodos[nodo_codigo]

    # Seleccionar el nodo mediante API
    pantalla.seleccionar_nodo(nodo_codigo)
    qapp.processEvents()

    # Verificar que el estado seleccionado sea visible
    assert pantalla.widget_estado_vacio.isHidden()
    assert not pantalla.widget_estado_seleccionado.isHidden()

    # Verificar que los datos del nodo aparezcan en el panel
    assert pantalla.lbl_nombre_inv.text() == nodo_item.nombre
    assert nodo_item.codigo in pantalla.lbl_cvlac_inv.text()
    assert str(nodo_item.grado) in pantalla.kpi_grado.lbl_valor.text()

    # Verificar botón deseleccionar
    pantalla.btn_deseleccionar.click()
    qapp.processEvents()

    # Al deseleccionar vuelve al estado inicial
    assert not pantalla.widget_estado_vacio.isHidden()
    assert pantalla.widget_estado_seleccionado.isHidden()


# ---------------------------------------------------------------------------
# 4. Navegación y emisión de señales
# ---------------------------------------------------------------------------


def test_pantalla_redes_navegacion_investigador_solicitada(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el botón «Ver ficha de investigador →» emita la señal abrir_investigador_solicitado."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    qapp.processEvents()

    nodo_codigo = next(iter(pantalla.vista_red.items_nodos.keys()))
    pantalla.seleccionar_nodo(nodo_codigo)
    qapp.processEvents()

    codigos_emitidos: list[str] = []
    pantalla.abrir_investigador_solicitado.connect(codigos_emitidos.append)

    # Clic en «Ver ficha de investigador →»
    pantalla.btn_ver_ficha.click()
    assert len(codigos_emitidos) == 1
    assert codigos_emitidos[0] == nodo_codigo


# ---------------------------------------------------------------------------
# 5. Filtros reactivos (combo grupo, min coautorías, búsqueda)
# ---------------------------------------------------------------------------


def test_pantalla_redes_filtros_reactivos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que los combos de grupo y coautorías filtren reactivamente el grafo."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    qapp.processEvents()

    total_inicial = len(pantalla.vista_red.items_nodos)

    # Subir mínimo de coautorías a 5
    idx_5 = pantalla.combo_min_coautorias.findData(5)
    if idx_5 >= 0:
        pantalla.combo_min_coautorias.setCurrentIndex(idx_5)
        qapp.processEvents()
        # El número de nodos o enlaces debe ser menor o igual al inicial
        assert len(pantalla.vista_red.items_nodos) <= total_inicial

    # Buscar por texto
    nodo_codigo = next(iter(pantalla.vista_red.items_nodos.keys()))
    nodo_item = pantalla.vista_red.items_nodos[nodo_codigo]
    pantalla._al_buscar_investigador(nodo_item.nombre[:5])
    qapp.processEvents()

    # Debe haber seleccionado o encontrado el nodo
    assert pantalla._investigador_seleccionado_cod is not None


# ---------------------------------------------------------------------------
# 6. Aviso de límite de 400 nodos
# ---------------------------------------------------------------------------


def test_pantalla_redes_banner_limite_400(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que si la red tiene más de 400 nodos, se muestre el banner reglamentario."""
    pantalla = PantallaRedes(servicio=servicio_con_datos)
    qapp.processEvents()

    # Simular una red con 450 nodos
    nodos_ficticios = [{"codigo": f"INV-{i}", "nombre": f"Inv {i}", "grado": 1, "intermediacion": 0.0} for i in range(450)]
    aristas_ficticias: list[dict[str, Any]] = []
    red_ficticia = {
        "nodos": nodos_ficticios,
        "aristas": aristas_ficticias,
        "resumen": {
            "investigadores": 450,
            "vinculos": 0,
            "densidad": 0.01,
        },
    }

    pantalla._al_grafo_cargado(red_ficticia)
    qapp.processEvents()

    assert not pantalla.banner_limite.isHidden()
    assert "400" in pantalla.lbl_texto_banner.text()
    # Los nodos mostrados en el canvas están recortados a 400
    assert len(pantalla.vista_red.items_nodos) == 400
