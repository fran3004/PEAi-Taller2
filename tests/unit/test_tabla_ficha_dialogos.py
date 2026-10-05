"""Pruebas unitarias para TablaEstilizada, FichaLateral, Dialogos y PopoverHistorial."""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QApplication, QLabel

from pea.gui.componentes.ficha_lateral import FichaLateral
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.popover_historial import PopoverHistorial
from pea.gui.componentes.tabla import (
    ColumnSpecification,
    TablaEstilizada,
)
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.dialogos import (
    DialogoEditarProducto,
    DialogoGrupo,
    DialogoInvestigador,
    DialogoProducto,
)
from pea.servicios.vistas import TablaDatos


def test_tabla_estilizada_y_delegados(qapp: QApplication, qtbot: Any) -> None:
    """Verifica filas de 48 px, pie Mostrando N de M, seleccion y delegados."""
    tabla_widget = TablaEstilizada()
    qtbot.addWidget(tabla_widget)
    tabla_widget.resize(800, 400)
    tabla_widget.show()

    # Altura de filas
    assert tabla_widget.vista.verticalHeader().defaultSectionSize() == 48

    # Cargar datos
    datos = TablaDatos(
        columnas=("Nombre", "Código", "Categoría", "Productos"),
        filas=(
            ("Wilman Orozco Cotes", "0000123456", "Senior", 42),
            ("Adith Pérez Orozco", "0000789012", "Asociado", 28),
            ("Emiro De la Hoz", "0000345678", "Junior", 15),
        ),
        claves=("INV-01", "INV-02", "INV-03"),
    )
    modelo = ModeloTabla(datos)
    tabla_widget.establecer_modelo(modelo)

    # Configurar delegados
    tabla_widget.establecer_delegado_columna(0, tabla_widget.delegado_avatar)
    tabla_widget.establecer_delegado_columna(1, tabla_widget.delegado_enlace)
    tabla_widget.establecer_delegado_columna(2, tabla_widget.delegado_pildora)
    tabla_widget.establecer_delegado_columna(3, tabla_widget.delegado_numero)

    # Verificar pie inicial
    assert "Mostrando 3 de 3" in tabla_widget._lbl_pie.text()

    # Seleccionar fila 1
    with qtbot.waitSignal(tabla_widget.fila_seleccionada, timeout=1000) as bloque_fila:
        with qtbot.waitSignal(tabla_widget.clave_seleccionada, timeout=1000) as bloque_clave:
            tabla_widget.seleccionar_fila(1)

    assert bloque_fila.args == [1]
    assert bloque_clave.args == ["INV-02"]
    assert tabla_widget.fila_seleccionada_actual() == 1

    # Probar ordenamiento mediante el proxy
    tabla_widget.proxy.sort(3, Qt.SortOrder.DescendingOrder)
    assert tabla_widget.proxy.rowCount() == 3

    # Probar copia de enlace al portapapeles
    delegado_enlace = tabla_widget.delegado_enlace
    idx_enlace = tabla_widget.proxy.index(0, 1)
    with qtbot.waitSignal(delegado_enlace.copiado, timeout=1000) as bloque_copia:
        qtbot.mouseClick(tabla_widget.vista.viewport(), Qt.MouseButton.LeftButton, pos=tabla_widget.vista.visualRect(idx_enlace).center())

    assert len(bloque_copia.args) == 1


@pytest.mark.parametrize(("ancho", "ancho_ficha"), [(1100, 320), (1366, 380), (1920, 440)])
def test_responsividad_tabla_y_ficha(
    qapp: QApplication, qtbot: Any, ancho: int, ancho_ficha: int
) -> None:
    """Comprueba el contrato responsive en las tres resoluciones de aceptación."""
    tabla_widget = TablaEstilizada()
    qtbot.addWidget(tabla_widget)
    modelo = QStandardItemModel(2, 4, tabla_widget)
    tabla_widget.establecer_modelo(modelo)
    tabla_widget.configurar_columnas([
        ColumnSpecification("estirar", 200, 1),
        ColumnSpecification("fijo", 120, 2),
        ColumnSpecification("contenido", 100, 3),
        ColumnSpecification("contenido", 100, 3),
    ])
    tabla_widget.resize(max(400, ancho - ancho_ficha - 40), 400)
    tabla_widget.show()
    qapp.processEvents()

    assert not tabla_widget.vista.horizontalScrollBar().isVisible()
    assert tabla_widget.vista.columnWidth(0) >= 200

    ficha = FichaLateral()
    qtbot.addWidget(ficha)
    ficha.ajustar_ancho_ficha(ancho)
    assert ficha.width() == ancho_ficha


def test_ficha_lateral_base(qapp: QApplication, qtbot: Any) -> None:
    """Verifica el ancho mínimo responsive y las zonas de la ficha."""
    ficha = FichaLateral()
    qtbot.addWidget(ficha)
    ficha.show()

    assert ficha.width() == 320
    ficha.ajustar_ancho_ficha(1366)
    assert ficha.width() == 380
    ficha.ajustar_ancho_ficha(1920)
    assert ficha.width() == 440

    # Estado inicial: vacío
    assert ficha._lbl_vacio.isVisible()
    assert not ficha._scroll.isVisible()

    # Configurar cabecera
    ficha.establecer_cabecera(
        nombre="Marly Celina Beleño Díaz",
        subtitulo="Grupo de Investigación en Telecomunicaciones · Senior",
        pildoras=[("Activo", "exito"), ("Senior", "info")],
    )

    assert not ficha._lbl_vacio.isVisible()
    assert ficha._scroll.isVisible()
    assert ficha._lbl_nombre.text() == "Marly Celina Beleño Díaz"

    # Agregar KPI
    kpi = FichaKPI(titulo="Productos", valor_inicial="48")
    ficha.agregar_kpi(kpi, 0, 0)
    assert ficha._layout_kpi.count() == 1

    # Agregar contenido libre
    lbl_nota = QLabel("Línea de investigación principal: IA")
    ficha.agregar_contenido(lbl_nota)
    assert ficha._layout_contenido.count() == 1

    # Cambiar estado del botón
    ficha.configurar_estado_activo(activo=False)
    assert ficha.btn_estado.text() == "Activar"
    ficha.configurar_estado_activo(activo=True)
    assert ficha.btn_estado.text() == "Desactivar"

    # Probar emisión de señales de acción
    with qtbot.waitSignal(ficha.editar_solicitado, timeout=1000):
        ficha.btn_editar.click()

    with qtbot.waitSignal(ficha.cambiar_estado_solicitado, timeout=1000):
        ficha.btn_estado.click()

    with qtbot.waitSignal(ficha.eliminar_solicitado, timeout=1000):
        ficha.btn_eliminar.click()

    with qtbot.waitSignal(ficha.ver_completa_solicitado, timeout=1000):
        ficha.btn_ver_completa.click()


def test_dialogos_validacion_y_datos(qapp: QApplication, qtbot: Any) -> None:
    """Verifica que los diálogos muestren errores y extraigan datos validados."""
    # 1. DialogoGrupo: falla validación si está vacío
    dlg_grupo = DialogoGrupo()
    qtbot.addWidget(dlg_grupo)
    dlg_grupo.show()
    assert not dlg_grupo.validar()
    assert not dlg_grupo._err_codigo.isHidden()
    assert not dlg_grupo._err_nombre.isHidden()

    dlg_grupo.txt_codigo.setText("COL0009999")
    dlg_grupo.txt_nombre.setText("Grupo Inteligencia Artificial")
    assert dlg_grupo.validar()
    assert dlg_grupo._err_codigo.isHidden()
    datos_g = dlg_grupo.obtener_datos()
    assert datos_g["codigo_gruplac"] == "COL0009999"
    assert datos_g["nombre"] == "Grupo Inteligencia Artificial"

    # 2. DialogoInvestigador
    dlg_inv = DialogoInvestigador()
    qtbot.addWidget(dlg_inv)
    dlg_inv.show()
    assert not dlg_inv.validar()
    assert not dlg_inv._err_codigo.isHidden()

    dlg_inv.txt_codigo.setText("0000987654")
    dlg_inv.txt_nombre.setText("Investigador de Prueba")
    assert dlg_inv.validar()
    datos_i = dlg_inv.obtener_datos()
    assert datos_i["codigo_rh"] == "0000987654"
    assert datos_i["nombre_completo"] == "Investigador de Prueba"

    # 3. DialogoProducto
    dlg_prod = DialogoProducto(grupos=[("COL01", "Grupo Uno")])
    qtbot.addWidget(dlg_prod)
    dlg_prod.show()
    assert not dlg_prod.validar()
    assert not dlg_prod._err_codigo.isHidden()

    dlg_prod.txt_codigo.setText("PROD-100")
    dlg_prod.txt_titulo.setText("Artículo sobre Algoritmos de Grafos")
    dlg_prod.combo_tipo.setCurrentText("GNC")
    dlg_prod.spin_ano.setValue(2023)
    assert dlg_prod.validar()

    datos_p, cod_grupo = dlg_prod.obtener_datos()
    assert datos_p["codigo_identificador"] == "PROD-100"
    assert datos_p["tipo_mayor"] == "GNC"
    assert datos_p["ano"] == 2023

    # 4. DialogoEditarProducto
    datos_prev = {
        "codigo": "PROD-100",
        "titulo": "Título Original",
        "tipologia": "DTI",
        "anio": 2022,
        "validacion": "Avalado",
        "grupo_codigo": "COL01",
    }
    dlg_edit = DialogoEditarProducto(datos_previos=datos_prev, grupos=[("COL01", "Grupo Uno")])
    qtbot.addWidget(dlg_edit)
    dlg_edit.show()
    assert not dlg_edit.txt_codigo.isEnabled()
    assert dlg_edit.txt_titulo.text() == "Título Original"
    assert dlg_edit.combo_tipo.currentText() == "DTI"

    dlg_edit.txt_titulo.setText("Título Actualizado")
    dlg_edit.combo_tipo.setCurrentText("GNC")
    dlg_edit.spin_ano.setValue(2024)
    assert dlg_edit.validar()

    cod_orig, datos_upd = dlg_edit.obtener_datos()
    assert cod_orig == "PROD-100"
    assert datos_upd["titulo"] == "Título Actualizado"
    assert datos_upd["tipo_mayor"] == "GNC"
    assert datos_upd["ano"] == 2024


def test_popover_historial(qapp: QApplication, qtbot: Any) -> None:
    """Verifica PopoverHistorial con lista de operaciones y señal de deshacer."""
    popover = PopoverHistorial()
    qtbot.addWidget(popover)
    popover.show()

    # Estado inicial: vacío
    popover.actualizar_operaciones([])
    assert "0 ops" in popover._lbl_contador.text()
    assert not popover.btn_deshacer.isEnabled()
    assert not popover._lbl_vacio.isHidden()

    # Con operaciones
    ops = [
        "Crear producto PROD-004",
        "Actualizar investigador INV-01",
        "Crear grupo COL0001",
    ]
    popover.actualizar_operaciones(ops)
    assert "3 ops" in popover._lbl_contador.text()
    assert popover.btn_deshacer.isEnabled()
    assert popover._lbl_vacio.isHidden()
    assert popover._layout_lista.count() > 0

    # Emitir señal al hacer clic en deshacer
    with qtbot.waitSignal(popover.deshacer_solicitado, timeout=1000):
        popover.btn_deshacer.click()
