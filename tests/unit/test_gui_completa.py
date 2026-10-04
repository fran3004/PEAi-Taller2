"""Pruebas unitarias completas de la interfaz gráfica PySide6 de PEA-i."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.graficos import GraficoBarras
from pea.gui.ventana_principal import VentanaPrincipal
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_exportacion import ServicioExportacion
from pea.servicios.vistas import ModoFiltroAnios, TablaDatos


@pytest.fixture
def ventana(qapp: QApplication, qtbot: Any) -> VentanaPrincipal:
    """Fixture que crea y registra la ventana principal en qtbot."""
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    win = VentanaPrincipal(servicio=servicio)
    qtbot.addWidget(win)
    win.show()
    return win


def test_ventana_principal_estructura_cuatro_zonas(ventana: VentanaPrincipal) -> None:
    """Verifica que la ventana principal contenga las cuatro zonas arquitectónicas."""
    # 1. Barra superior
    assert ventana._barra_superior is not None
    assert ventana._btn_deshacer is not None
    assert ventana._punto_conexion is not None

    # Banner de advertencia inicialmente oculto
    assert not ventana._banner_revision.isVisible()

    # 2. Navegación lateral con 9 pantallas
    assert ventana._navegacion.count() == 9
    assert ventana._navegacion.item(0).text() == "Conectar con PEA-i"
    assert ventana._navegacion.item(1).text() == "Resumen general"
    assert ventana._navegacion.item(8).text() == "Acerca del proyecto"

    # 3. Zona central apilador
    assert ventana._apilador.count() == 9

    # 4. Barra de estado
    assert ventana._barra_estado is not None
    assert "Revisión:" in ventana._lbl_estado_revision.text()


def test_navegacion_entre_todas_las_pantallas(ventana: VentanaPrincipal) -> None:
    """Verifica la navegación secuencial por las 9 pantallas sin fallas."""
    for idx in range(9):
        ventana.seleccionar_pantalla(idx)
        QApplication.processEvents()
        assert ventana._apilador.currentIndex() == idx
        pantalla_actual = ventana._apilador.currentWidget()
        assert pantalla_actual is not None
        assert pantalla_actual.isVisible()


def test_pantalla_resumen_interaccion_filtros(ventana: VentanaPrincipal) -> None:
    """Prueba la pantalla de Resumen general y la reactividad del filtro temporal."""
    ventana.seleccionar_pantalla(1)  # Resumen general
    QApplication.processEvents()

    pantalla = ventana._pantalla_resumen
    assert pantalla.lbl_sin_datos.isHidden()
    assert pantalla.area_desplazamiento.isVisible()

    # Modificar filtro a últimos 5 años
    pantalla.barra_filtro.combo_modo.setCurrentIndex(1)  # ModoFiltroAnios.ULTIMOS
    QApplication.processEvents()
    assert pantalla._filtro_actual.modo == ModoFiltroAnios.ULTIMOS

    # Modificar a Modelo 2024
    pantalla.barra_filtro.combo_modo.setCurrentIndex(3)  # ModoFiltroAnios.MODELO_2024
    QApplication.processEvents()
    assert pantalla._filtro_actual.modo == ModoFiltroAnios.MODELO_2024


def test_pantalla_grupo_seleccion_y_contenido(ventana: VentanaPrincipal) -> None:
    """Prueba la pantalla Por grupo: selector y detalle de integrantes."""
    ventana.seleccionar_pantalla(2)  # Por grupo
    QApplication.processEvents()

    pantalla = ventana._pantalla_grupo
    assert pantalla.combo_grupo.count() > 0

    # Seleccionar el primer grupo disponible
    pantalla.combo_grupo.setCurrentIndex(0)
    QApplication.processEvents()

    assert not pantalla.area_desplazamiento.isHidden()
    assert "Líder:" in pantalla.lbl_lider_grupo.text()
    assert pantalla.tabla_integrantes.model() is not None


def test_pantalla_investigador_seleccion_y_productos(ventana: VentanaPrincipal) -> None:
    """Prueba la pantalla Por investigador: selector y tabla de productos."""
    ventana.seleccionar_pantalla(3)  # Por investigador
    QApplication.processEvents()

    pantalla = ventana._pantalla_investigador
    assert pantalla.combo_inv.count() > 0

    pantalla.combo_inv.setCurrentIndex(0)
    QApplication.processEvents()

    assert not pantalla.area_desplazamiento.isHidden()
    assert "Categoría:" in pantalla.lbl_categoria.text()
    assert pantalla.tabla_productos.model() is not None


def test_pantalla_producto_seleccion_tabla(ventana: VentanaPrincipal) -> None:
    """Prueba la pantalla Por producto y el panel de detalle lateral al seleccionar."""
    ventana.seleccionar_pantalla(4)  # Por producto
    QApplication.processEvents()

    pantalla = ventana._pantalla_producto
    modelo = pantalla.tabla.model()
    assert modelo is not None
    assert modelo.rowCount() > 0

    # Seleccionar la primera fila
    indice = modelo.index(0, 0)
    pantalla.tabla.setCurrentIndex(indice)
    QApplication.processEvents()

    # El panel de detalle debe mostrar el código
    codigo_seleccionado = modelo.data(indice, Qt.ItemDataRole.DisplayRole)
    assert codigo_seleccionado in pantalla.lbl_det_codigo.text()


def test_pantalla_gestion_cambio_estado_y_deshacer(ventana: VentanaPrincipal) -> None:
    """Prueba la pantalla Gestión de datos: desactivar entidad y deshacer con Ctrl+Z."""
    ventana.seleccionar_pantalla(5)  # Gestión de datos
    QApplication.processEvents()

    pantalla = ventana._pantalla_gestion
    modelo = pantalla.tabla_grupos.model()
    assert modelo is not None
    assert modelo.rowCount() > 0

    # Seleccionar primer grupo
    pantalla.tabla_grupos.setCurrentIndex(modelo.index(0, 0))
    QApplication.processEvents()

    # Desactivar grupo
    pantalla._al_toggle_estado("grupo", pantalla.tabla_grupos, pantalla.modelo_grupos)
    QApplication.processEvents()

    # La pila de deshacer debe contener una operación
    estado = ventana._servicio.estado()
    assert estado.operaciones_deshacer == 1
    assert ventana._btn_deshacer.isEnabled()

    # Ejecutar deshacer
    ventana._al_clic_deshacer()
    QApplication.processEvents()

    # Verificamos que se haya restaurado
    estado_restaurado = ventana._servicio.estado()
    assert estado_restaurado.operaciones_deshacer == 0
    assert not ventana._btn_deshacer.isEnabled()


def test_pantalla_importar_cola_ingesta(ventana: VentanaPrincipal, tmp_path: Path) -> None:
    """Prueba la pantalla Importar: encolar archivo CSV y consultar la cola."""
    ventana.seleccionar_pantalla(6)  # Importar
    QApplication.processEvents()

    pantalla = ventana._pantalla_importar

    # Crear archivo CSV temporal con cabeceras válidas
    archivo_csv = tmp_path / "datos_test.csv"
    archivo_csv.write_text(
        "codigo_gruplac,nombre,categoria,lider,institucion_principal,departamento_ciudad,gran_area_ocde,area_ocde,fecha_creacion,activo\n"
        "PRUEBA-G99,Grupo de Prueba 99,A1,Líder Prueba,UPC,Valledupar,Ingeniería,Sistemas,2020-01-01,true\n",
        encoding="utf-8",
    )

    # Encolar CSV
    tarea_id = ventana._servicio.encolar_csv(archivo_csv)
    assert len(str(tarea_id)) > 0

    pantalla.refrescar()
    QApplication.processEvents()

    modelo_cola = pantalla.tabla_cola.model()
    assert modelo_cola is not None
    assert modelo_cola.rowCount() > 0



def test_exportacion_tabla_csv_y_grafico_png(tmp_path: Path) -> None:
    """Verifica que la exportación de tablas a CSV y gráficos a PNG funcione correctamente."""
    # 1. Exportación CSV
    tabla = TablaDatos(
        columnas=("Código", "Nombre", "Total"),
        filas=(
            ("G01", "Grupo Uno", 10),
            ("G02", "Grupo Dos", 25),
        ),
        claves=("G01", "G02"),
    )
    destino_csv = tmp_path / "tabla_exportada.csv"
    ServicioExportacion.exportar_tabla_csv(tabla, destino_csv)

    assert destino_csv.exists()
    contenido_bytes = destino_csv.read_bytes()
    # Debe tener BOM UTF-8 (\xef\xbb\xbf)
    assert contenido_bytes.startswith(b"\xef\xbb\xbf")
    contenido_texto = destino_csv.read_text(encoding="utf-8-sig")
    assert "Grupo Uno" in contenido_texto
    assert "25" in contenido_texto

    # 2. Exportación de gráfico nativo a PNG
    grafico = GraficoBarras(titulo="Prueba de Producción")
    grafico.establecer_datos({"2020": 15, "2021": 30, "2022": 45})
    grafico.resize(400, 300)

    destino_png = tmp_path / "grafico_barras.png"
    exito = grafico.exportar_png(destino_png)
    assert exito
    assert destino_png.exists()
    assert destino_png.stat().st_size > 0


def test_pantalla_acerca_institucional(ventana: VentanaPrincipal) -> None:
    """Verifica la pantalla Acerca del proyecto y la ficha técnica."""
    ventana.seleccionar_pantalla(8)  # Acerca del proyecto
    QApplication.processEvents()

    pantalla = ventana._pantalla_acerca
    assert "Revisión actual del esquema:" in pantalla._lbl_estado_rev.text()
