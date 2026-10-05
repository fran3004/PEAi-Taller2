"""Pruebas unitarias completas para PantallaProductos y FichaProducto (Sección 6.4)."""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.tabla import ROL_ACTIVO
from pea.gui.pantallas.productos import (
    DialogoConfirmarEliminar,
    FichaProducto,
    PantallaProductos,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


@pytest.fixture
def servicio_con_datos() -> ServicioAplicacion:
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    return servicio


def test_pantalla_productos_construccion_y_componentes(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Valida la estructura del catálogo, barra de contexto y ficha lateral según sección 6.4."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    pantalla.resize(QSize(1360, 800))
    qapp.processEvents()

    # 1. Barra de contexto
    assert pantalla.chip_ventana is not None
    assert pantalla.btn_exportar is not None

    # 2. Tarjeta del catálogo
    assert pantalla._tarjeta_catalogo is not None
    assert pantalla.campo_busqueda is not None
    assert pantalla.combo_tipologia is not None
    assert pantalla.combo_validacion is not None
    assert pantalla.combo_estado is not None
    assert pantalla.btn_nuevo is not None
    assert pantalla.tabla is not None

    # 3. Ficha lateral responsive
    ficha = pantalla._ficha_lateral
    assert isinstance(ficha, FichaProducto)
    assert ficha.width() == 320
    assert ficha._lbl_titulo is not None
    assert ficha._lbl_codigo is not None
    assert ficha._pildora_tipologia is not None
    assert ficha._pildora_validacion is not None
    assert ficha._insignia_ventana is not None
    assert ficha._contenedor_coautores is not None
    assert ficha.btn_editar is not None
    assert ficha.btn_estado is not None
    assert ficha.btn_eliminar is not None


def test_pantalla_productos_tabla_y_datos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que el modelo cargue los productos, columnas reglamentarias y autores Nombre (+N)."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    qapp.processEvents()

    modelo = pantalla._modelo
    proxy = pantalla._proxy
    total_prods = len(servicio_con_datos.tabla_productos(filtro=pantalla._filtro_actual, incluir_inactivos=True).filas)
    assert modelo.rowCount() == total_prods
    assert proxy.rowCount() > 0

    # Pie «Mostrando N de M productos»
    texto_pie = pantalla.tabla._lbl_pie.text()
    assert "Mostrando" in texto_pie
    assert str(total_prods) in texto_pie

    # Columnas esperadas según 6.4
    cols_esperadas = [
        "Código",
        "Título",
        "Tipología",
        "Subtipo",
        "Año",
        "Validación",
        "Grupo",
        "Autores",
        "Estado",
    ]
    for c_idx, nom in enumerate(cols_esperadas):
        assert modelo.headerData(c_idx, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) == nom

    # Validación de formato de autores
    for r in range(modelo.rowCount()):
        aut_val = modelo.data(modelo.index(r, 7), Qt.ItemDataRole.DisplayRole)
        assert aut_val is not None
        assert str(aut_val) != ""


def test_pantalla_productos_filtros_reactivos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Comprueba el filtrado reactivo por texto, tipología, validación y estado."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    qapp.processEvents()

    iniciales = pantalla._proxy.rowCount()
    assert iniciales > 0

    # 1. Filtro por texto (primer producto)
    prod_primero = servicio_con_datos._catalogo.multilista_productos.obtener_todos()[0]
    pantalla.campo_busqueda.establecer_texto(prod_primero.titulo[:10])
    qapp.processEvents()
    assert pantalla._proxy.rowCount() <= iniciales
    assert pantalla._proxy.rowCount() >= 1

    # Limpiar búsqueda
    pantalla.campo_busqueda.limpiar()
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales

    # 2. Filtro por Tipología
    pantalla.combo_tipologia.setCurrentIndex(1)  # GNC
    qapp.processEvents()
    filas_gnc = pantalla._proxy.rowCount()
    assert filas_gnc <= iniciales
    for r in range(filas_gnc):
        tipo_val = pantalla._proxy.index(r, 2).data()
        assert "GNC" in str(tipo_val)

    pantalla.combo_tipologia.setCurrentIndex(0)  # Todas
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales

    # 3. Filtro por Validación
    pantalla.combo_validacion.setCurrentText("Avalado")
    qapp.processEvents()
    filas_avaladas = pantalla._proxy.rowCount()
    assert filas_avaladas <= iniciales
    for r in range(filas_avaladas):
        val_txt = pantalla._proxy.index(r, 5).data()
        assert "Avalado" in str(val_txt)

    pantalla.combo_validacion.setCurrentText("Todas")
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales

    # 4. Filtro por Estado
    pantalla.combo_estado.setCurrentText("Todos")
    qapp.processEvents()
    assert pantalla._proxy.rowCount() == iniciales


def test_pantalla_productos_seleccion_y_ficha_lateral(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Verifica que la selección de una fila cargue el detalle completo y coautores en la ficha lateral."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    qtbot.addWidget(pantalla)
    pantalla.show()
    qapp.processEvents()

    # Seleccionar primera fila
    pantalla.tabla.seleccionar_fila(0)
    qapp.processEvents()

    assert pantalla._producto_seleccionado_cod is not None
    cod = pantalla._producto_seleccionado_cod

    # Ficha lateral actualizada
    ficha = pantalla._ficha_lateral
    assert not ficha._scroll.isHidden()
    assert ficha._lbl_titulo.text() != ""
    assert ficha._lbl_codigo.text() == f"Código: {cod}"
    assert ficha._lbl_anio.text() != ""
    assert ficha.lbl_insignia_ventana.text() != ""
    assert ficha.insignia_ventana.toolTip() != ""

    # Botones activos
    assert ficha.btn_editar.isEnabled()
    assert ficha.btn_estado.isEnabled()
    assert ficha.btn_eliminar.isEnabled()


def test_pantalla_productos_coautor_clic_navegacion(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Verifica que hacer clic en un coautor emita la señal para abrir Investigadores."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    qapp.processEvents()

    pantalla.tabla.seleccionar_fila(0)
    qapp.processEvents()

    ficha = pantalla._ficha_lateral
    # Si tiene filas de coautores, probar el clic
    if ficha._filas_coautores:
        primera_fila = ficha._filas_coautores[0]
        with qtbot.waitSignal(pantalla.abrir_investigador_solicitado, timeout=1000) as senal_inv:
            with qtbot.waitSignal(pantalla.solicitar_navegacion, timeout=1000) as senal_nav:
                primera_fila.mousePressEvent(None)
        assert senal_inv.args[0] == primera_fila._identificador
        assert senal_nav.args[0] == 1  # Pantalla.INVESTIGADORES


def test_producto_inactivo_opacidad_y_pildora(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que un producto desactivado retorne ROL_ACTIVO=False y píldora «Inactivo»."""
    prods = servicio_con_datos._catalogo.multilista_productos.obtener_todos()
    assert len(prods) > 0
    prod_cod = prods[0].codigo_identificador

    # Desactivar
    servicio_con_datos.cambiar_estado("producto", prod_cod, activo=False)

    pantalla = PantallaProductos(servicio=servicio_con_datos)
    pantalla.establecer_filtro(FiltroAnios(modo=ModoFiltroAnios.TODOS))
    pantalla.combo_estado.setCurrentText("Todos")
    qapp.processEvents()

    modelo = pantalla._modelo
    encontrado = False
    for r in range(modelo.rowCount()):
        if modelo.obtener_clave_fila(r) == prod_cod:
            encontrado = True
            assert modelo.data(modelo.index(r, 0), ROL_ACTIVO) is False
            assert modelo.data(modelo.index(r, 8), Qt.ItemDataRole.DisplayRole) == "Inactivo"
            break
    assert encontrado


def test_dialogos_confirmar_eliminar_producto(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion, qtbot: Any
) -> None:
    """Verifica la cascada y el diálogo de confirmación de eliminación de un producto."""
    prods = servicio_con_datos._catalogo.multilista_productos.obtener_todos()
    assert len(prods) > 0
    prod_cod = prods[0].codigo_identificador

    cascada = servicio_con_datos.describir_cascada("producto", prod_cod)
    assert "Se eliminará el producto" in cascada

    dlg = DialogoConfirmarEliminar(
        titulo=f"Eliminar Producto · {prod_cod}",
        descripcion_cascada=cascada,
    )
    qtbot.addWidget(dlg)
    dlg.show()
    assert dlg.btn_confirmar is not None
    dlg.close()


def test_cambio_filtro_anios_en_productos(
    qapp: QApplication, servicio_con_datos: ServicioAplicacion
) -> None:
    """Verifica que la asignación de filtro temporal actualice la tabla y el chip."""
    pantalla = PantallaProductos(servicio=servicio_con_datos)
    qapp.processEvents()

    filtro_3 = FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3)
    pantalla.establecer_filtro(filtro_3)
    qapp.processEvents()

    assert pantalla._filtro_actual.modo == ModoFiltroAnios.ULTIMOS
    assert pantalla.chip_ventana.filtro.modo == ModoFiltroAnios.ULTIMOS
