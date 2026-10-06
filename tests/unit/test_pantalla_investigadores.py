"""Pruebas unitarias completas para PantallaInvestigadores (Sección 6.2)."""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.tabla import ROL_ACTIVO
from pea.gui.pantallas.investigadores import (
    DialogoConfirmarEliminar,
    DialogoFichaCompletaInvestigador,
    PantallaInvestigadores,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


@pytest.fixture
def servicio_con_datos() -> ServicioAplicacion:
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    return servicio


def test_pantalla_investigadores_construccion_y_componentes(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Valida la estructura de directorio, barra de contexto y ficha lateral según sección 6.2."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    pantalla.resize(QSize(1360, 800))
    qapp.processEvents()

    # 1. Barra de contexto
    assert pantalla._chip_ventana is not None
    assert pantalla._btn_exportar is not None

    # 2. Tarjeta del directorio
    assert pantalla._tarjeta_directorio is not None
    assert pantalla.campo_busqueda is not None
    assert pantalla.combo_grupo is not None
    assert pantalla.combo_categoria is not None
    assert pantalla.combo_estado is not None
    assert pantalla.btn_nuevo is not None
    assert pantalla.tabla is not None

    # 3. Ficha lateral
    ficha = pantalla._ficha_lateral
    assert ficha is not None
    assert ficha.width() == 320
    assert pantalla.kpi_productos is not None
    assert pantalla.kpi_grupos is not None
    assert pantalla.kpi_coautores is not None
    assert pantalla.kpi_anios is not None
    assert pantalla.grafico_serie is not None
    assert pantalla.barras_tipologia is not None
    assert ficha.btn_editar is not None
    assert ficha.btn_estado is not None
    assert ficha.btn_eliminar is not None
    assert ficha.btn_ver_completa is not None
    assert ficha.btn_ver_productos is not None


@pytest.mark.parametrize(("ancho", "alto", "ancho_ficha"), [(1100, 700, 320), (1366, 768, 380), (1920, 1080, 440)])
def test_pantalla_investigadores_responsive(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, ancho: int, alto: int, ancho_ficha: int
) -> None:
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    pantalla.resize(ancho, alto)
    pantalla.show()
    qapp.processEvents()

    assert not pantalla.tabla.vista.horizontalScrollBar().isVisible()
    assert pantalla._ficha_lateral.width() == ancho_ficha
    assert pantalla._ficha_lateral.geometry().right() <= pantalla._splitter.width()
    assert pantalla.btn_nuevo.isVisible()
    assert pantalla.grafico_serie.minimumHeight() == (120 if alto < 760 else 140)


def test_pantalla_investigadores_tabla_y_datos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el modelo cargue investigadores, columnas y conteo en el pie."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qapp.processEvents()

    # Modelo y proxy
    modelo = pantalla._modelo
    proxy = pantalla._proxy
    total_inv = len(servicio_con_datos._catalogo.investigadores)
    assert modelo.rowCount() == total_inv
    assert proxy.rowCount() > 0

    # Pie «Mostrando N de M»
    texto_pie = pantalla.tabla._lbl_pie.text()
    assert "Mostrando" in texto_pie
    assert str(total_inv) in texto_pie

    # Columnas esperadas
    cols_esperadas = ["Nombre", "Grupo(s)", "Categoría", "Formación", "Productos", "Código CvLAC"]
    for c_idx, nom in enumerate(cols_esperadas):
        assert modelo.headerData(c_idx, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == nom

    # Datos de la primera fila
    assert modelo.data(modelo.index(0, 0), Qt.ItemDataRole.DisplayRole) != ""
    assert modelo.data(modelo.index(0, 5), Qt.ItemDataRole.DisplayRole) != ""


def test_pantalla_investigadores_filtros_reactivos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Comprueba el filtrado interactivo por texto, grupo, categoría y estado."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qapp.processEvents()

    iniciales = pantalla._proxy.rowCount()
    assert iniciales > 0

    # 1. Filtro por texto
    pantalla.campo_busqueda.establecer_texto("Ficticia")
    qapp.processEvents()
    assert pantalla._proxy.rowCount() <= iniciales
    assert pantalla._proxy.rowCount() >= 1

    # Limpiar búsqueda
    pantalla.campo_busqueda.limpiar()
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales

    # 2. Filtro por categoría
    pantalla.combo_categoria.setCurrentText("Senior")
    qapp.processEvents()
    filas_senior = pantalla._proxy.rowCount()
    assert filas_senior <= iniciales
    for r in range(filas_senior):
        cat_val = pantalla._proxy.index(r, 2).data()
        assert "Senior" in str(cat_val)

    pantalla.combo_categoria.setCurrentText("Todas las categorías")
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales

    # 3. Filtro por Estado (Activos / Todos)
    pantalla.combo_estado.setCurrentText("Todos")
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == len(servicio_con_datos._catalogo.investigadores)


def test_pantalla_investigadores_seleccion_y_ficha_lateral(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Verifica la carga de detalles, KPIs y gráficos en la ficha lateral al seleccionar fila."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qtbot.addWidget(pantalla)
    pantalla.show()
    qapp.processEvents()

    # Seleccionar primera fila
    pantalla.tabla.seleccionar_fila(0)
    qapp.processEvents()

    assert pantalla._investigador_seleccionado_cod is not None
    cod = pantalla._investigador_seleccionado_cod

    # Ficha lateral poblada
    ficha = pantalla._ficha_lateral
    assert not ficha._scroll.isHidden()
    assert ficha._lbl_nombre.text() != ""
    assert pantalla._investigador_seleccionado_nom in ficha._lbl_nombre.text()

    # KPIs actualizados
    val_prod = int(pantalla.kpi_productos.lbl_valor.text().replace(".", ""))
    assert val_prod >= 0

    # Gráfico de serie anual actualizado
    assert not pantalla.grafico_serie.esta_vacio()

    # Cambiar de fila programáticamente
    if pantalla._proxy.rowCount() > 1:
        pantalla.tabla.seleccionar_fila(1)
        qapp.processEvents()
        assert pantalla._investigador_seleccionado_cod != cod


def test_pantalla_investigadores_navegacion_ver_productos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Prueba que el botón «Ver productos» emita la señal con el nombre y navegue a Productos."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qapp.processEvents()

    pantalla.tabla.seleccionar_fila(0)
    qapp.processEvents()

    with qtbot.waitSignal(pantalla.ver_productos_solicitado, timeout=1000) as senal_prod:
        with qtbot.waitSignal(pantalla.solicitar_navegacion, timeout=1000) as senal_nav:
            pantalla._ficha_lateral.btn_ver_productos.click()

    assert senal_prod.args[0] == pantalla._investigador_seleccionado_nom
    assert senal_nav.args[0] == 3  # Pantalla.PRODUCTOS


def test_investigador_inactivo_opacidad_y_pildora(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que un investigador inactivo retorne ROL_ACTIVO=False y píldora «Inactivo»."""
    # Desactivar primer investigador
    inv_cod = servicio_con_datos._catalogo.investigadores[0].codigo_rh
    servicio_con_datos.cambiar_estado("investigador", inv_cod, activo=False)

    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    # Seleccionar opción Todos para ver al inactivo
    pantalla.combo_estado.setCurrentText("Todos")
    qapp.processEvents()

    modelo = pantalla._modelo
    # Buscar el registro inactivo
    encontrado = False
    for r in range(modelo.rowCount()):
        if modelo.obtener_clave_fila(r) == inv_cod:
            encontrado = True
            # ROL_ACTIVO debe ser False
            assert modelo.data(modelo.index(r, 0), ROL_ACTIVO) is False
            # Columna Categoría debe decir «Inactivo»
            assert modelo.data(modelo.index(r, 2), Qt.ItemDataRole.DisplayRole) == "Inactivo"
            break
    assert encontrado


def test_dialogos_ficha_completa_y_confirmar_eliminar(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Valida la instanciación de DialogoFichaCompletaInvestigador y DialogoConfirmarEliminar."""
    cod = servicio_con_datos._catalogo.investigadores[0].codigo_rh
    vista = servicio_con_datos.vista_investigador(cod, FiltroAnios())

    # Diálogo Ficha Completa
    dlg_ficha = DialogoFichaCompletaInvestigador(vista, servicio_con_datos)
    qtbot.addWidget(dlg_ficha)
    dlg_ficha.show()
    assert dlg_ficha.pestanas.count() == 3
    assert dlg_ficha.pestanas.tabText(0) == "Aporte a Grupos de Investigación"
    assert dlg_ficha.pestanas.tabText(1) == "Membresías Registradas"
    assert dlg_ficha.pestanas.tabText(2) == "Productos Autorados en Multilista"
    dlg_ficha.close()

    # Diálogo Confirmar Eliminación
    cascada = servicio_con_datos.describir_cascada("investigador", cod)
    dlg_elim = DialogoConfirmarEliminar("Confirmar", cascada)
    qtbot.addWidget(dlg_elim)
    dlg_elim.show()
    assert "Se eliminará el investigador" in cascada
    dlg_elim.close()


def test_cambio_filtro_anios_en_investigadores(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el cambio de filtro actualice el conteo y la vista del investigador."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qapp.processEvents()

    filtro_3 = FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3)
    pantalla.establecer_filtro(filtro_3)
    qapp.processEvents()

    assert pantalla._filtro_actual.modo == ModoFiltroAnios.ULTIMOS
    assert pantalla._chip_ventana.filtro.modo == ModoFiltroAnios.ULTIMOS


def test_pantalla_investigadores_tabla_responsive_y_elipsis(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Verifica que en 1100x700 Nombre conserve un ancho útil >= 240 px, sin desborde ni recorte de cabecera."""
    pantalla = PantallaInvestigadores(servicio=servicio_con_datos)
    qtbot.addWidget(pantalla)

    # 1. Modo compacto (1100x700)
    pantalla.resize(1100, 700)
    pantalla.show()
    qapp.processEvents()

    vista = pantalla.tabla.vista
    assert not vista.horizontalScrollBar().isVisible()
    ancho_nombre = vista.columnWidth(0)
    assert ancho_nombre >= 240
    # En 1100x700 Nombre tiene ~329 px y no queda como «Nor» o «Nomb-»
    assert ancho_nombre >= 300

    # Columnas secundarias ocultadas antes de comprimir la columna principal Nombre
    assert vista.isColumnHidden(3)  # Formación oculta
    assert vista.isColumnHidden(5)  # Código CvLAC oculto
    assert not vista.isColumnHidden(0)  # Nombre visible
    assert not vista.isColumnHidden(1)  # Grupo(s) visible
    assert not vista.isColumnHidden(2)  # Categoría visible
    assert not vista.isColumnHidden(4)  # Productos visible

    # 2. Modos amplios (1366x768 y 1920x1080)
    for ancho, alto in [(1366, 768), (1920, 1080)]:
        pantalla.resize(ancho, alto)
        qapp.processEvents()
        assert not vista.horizontalScrollBar().isVisible()
        # Todas las columnas visibles en resoluciones grandes
        for col_idx in range(6):
            assert not vista.isColumnHidden(col_idx)
        assert vista.columnWidth(0) >= 300

    # 3. Tooltips disponibles en modelo y cabeceras
    idx_0 = vista.model().index(0, 0)
    tooltip_nombre = vista.model().data(idx_0, Qt.ItemDataRole.ToolTipRole)
    assert bool(tooltip_nombre)
    assert tooltip_nombre == vista.model().data(idx_0, Qt.ItemDataRole.DisplayRole)
    assert vista.model().headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole) == "Nombre"

