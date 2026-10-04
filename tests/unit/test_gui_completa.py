"""Pruebas unitarias completas de la interfaz gráfica PySide6 de PEA-i (Sección 5).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.graficos import GraficoBarras
from pea.gui.ventana_principal import Pantalla, VentanaPrincipal
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_exportacion import ServicioExportacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios, TablaDatos


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
    """Verifica que la ventana principal contenga las cuatro zonas de la Sección 5."""
    # 1. Barra superior
    assert ventana._barra_superior is not None
    assert ventana._barra_superior.height() == 88
    assert ventana._filete_upc is not None
    assert ventana._filete_upc.height() == 3

    # Botón Deshacer con popover
    assert ventana._btn_deshacer is not None
    assert ventana._popover_historial is not None

    # Avatar y sesión
    assert ventana._avatar_usuario is not None
    assert ventana.btn_cerrar_sesion is not None
    assert ventana.btn_acerca is not None

    # Franjas de revisión y sin conexión inicialmente acordes al estado
    assert not ventana._banner_revision.isVisible()
    assert not ventana._franja_sin_conexion.isVisible()

    # 2. Siete pestañas principales
    assert len(ventana._botones_pestanas) == 7
    nombres_esperados = [
        "Inicio",
        "Investigadores",
        "Grupos",
        "Productos",
        "Análisis de redes",
        "Importar",
        "Configuración",
    ]
    for btn, nombre_esperado in zip(ventana._botones_pestanas, nombres_esperados, strict=True):
        assert btn._texto == nombre_esperado

    # 3. Zona central apiladora con 8 pantallas
    assert ventana._apilador.count() == 8
    assert ventana._apilador.currentIndex() == int(Pantalla.INICIO)

    # 4. Pie institucional
    assert ventana._pie is not None
    assert ventana._pie.height() in (44, 72)
    assert ventana._pastilla_logo is not None
    assert "Revisión:" in ventana._chip_revision.text()
    assert "Deshacer:" in ventana._chip_deshacer.text()
    assert "Cola:" in ventana._chip_cola.text()


def test_navegacion_entre_todas_las_pantallas(ventana: VentanaPrincipal) -> None:
    """Verifica la navegación secuencial por las 8 pantallas oficiales (Pantalla enum)."""
    for pantalla_enum in Pantalla:
        ventana.seleccionar_pantalla(pantalla_enum)
        QApplication.processEvents()

        idx = int(pantalla_enum)
        assert ventana._apilador.currentIndex() == idx
        widget_actual = ventana._apilador.currentWidget()
        assert widget_actual is not None
        assert widget_actual.isVisible()

        # Verificar sincronización de pestañas
        if idx <= 6:
            btn_activo = ventana._pestanas.button(idx)
            assert btn_activo is not None
            assert btn_activo.isChecked()
        else:
            # "Acerca de" no deja ninguna pestaña central marcada
            for b in ventana._botones_pestanas:
                assert not b.isChecked()


def test_atajos_de_teclado(ventana: VentanaPrincipal) -> None:
    """Verifica que los atajos de teclado cambien de pantalla y respondan a acciones."""
    # Navegar a pantalla 3 (Productos)
    ventana.seleccionar_pantalla(Pantalla.PRODUCTOS)
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.PRODUCTOS)

    # Navegar a Acerca de y volver con atajo
    ventana.seleccionar_pantalla(Pantalla.ACERCA)
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.ACERCA)

    ventana._al_atajo_volver()
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.INICIO)


def test_filtro_anios_global_compartido(ventana: VentanaPrincipal) -> None:
    """Verifica el filtro de años global compartido en la ventana."""
    assert ventana._filtro_global.modo == ModoFiltroAnios.MODELO_2024

    nuevo_filtro = FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3)
    ventana._pantalla_inicio.establecer_filtro(nuevo_filtro)
    assert ventana._pantalla_inicio._filtro_actual.modo == ModoFiltroAnios.ULTIMOS


def test_deshacer_y_popover_historial(ventana: VentanaPrincipal) -> None:
    """Prueba la pila de deshacer reflejada en la barra y en el popover de historial."""
    # Desactivar un grupo para generar una operación en la pila de deshacer
    servicio = ventana._servicio
    grupos = servicio.tabla_grupos().claves
    assert len(grupos) > 0
    codigo_grupo = grupos[0]
    servicio.cambiar_estado("grupo", codigo_grupo, activo=False)
    ventana.actualizar_estado_global()
    QApplication.processEvents()

    assert servicio.estado().operaciones_deshacer >= 1
    assert ventana._btn_deshacer._contador >= 1
    assert ventana._btn_deshacer.btn_accion.isEnabled()

    # Abrir popover de historial
    ventana._abrir_popover_historial()
    QApplication.processEvents()
    assert ventana._popover_historial.isVisible()
    assert ventana._popover_historial._layout_lista.count() >= 1

    # Ejecutar deshacer
    ventana._al_clic_deshacer()
    QApplication.processEvents()

    assert servicio.estado().operaciones_deshacer == 0
    assert ventana._btn_deshacer._contador == 0
    assert not ventana._btn_deshacer.btn_accion.isEnabled()


def test_pantalla_importar_cola_ingesta(ventana: VentanaPrincipal, tmp_path: Path) -> None:
    """Prueba la pantalla Importar: encolar archivo CSV y consultar la cola."""
    ventana.seleccionar_pantalla(Pantalla.IMPORTAR)
    QApplication.processEvents()

    pantalla = ventana._pantalla_importar
    assert pantalla is not None

    archivo_csv = tmp_path / "datos_test.csv"
    archivo_csv.write_text(
        "codigo_gruplac,nombre,categoria,lider,institucion_principal,departamento_ciudad,gran_area_ocde,area_ocde,fecha_creacion,activo\n"
        "PRUEBA-G99,Grupo de Prueba 99,A1,Líder Prueba,UPC,Valledupar,Ingeniería,Sistemas,2020-01-01,true\n",
        encoding="utf-8",
    )

    tarea_id = ventana._servicio.encolar_csv(archivo_csv)
    assert len(str(tarea_id)) > 0

    pantalla.refrescar()
    QApplication.processEvents()

    modelo_cola = pantalla.tabla_cola.model()
    assert modelo_cola is not None
    assert modelo_cola.rowCount() > 0


def test_pantalla_acerca_institucional(ventana: VentanaPrincipal) -> None:
    """Verifica la pantalla Acerca de abierta desde la barra superior."""
    ventana.seleccionar_pantalla(Pantalla.ACERCA)
    QApplication.processEvents()

    pantalla = ventana._pantalla_acerca
    assert pantalla is not None
    assert "Revisión actual del esquema:" in pantalla._lbl_estado_rev.text()


def test_exportacion_tabla_csv_y_grafico_png(tmp_path: Path) -> None:
    """Verifica que la exportación de tablas a CSV y gráficos a PNG funcione correctamente."""
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
    assert contenido_bytes.startswith(b"\xef\xbb\xbf")
    contenido_texto = destino_csv.read_text(encoding="utf-8-sig")
    assert "Grupo Uno" in contenido_texto
    assert "25" in contenido_texto

    grafico = GraficoBarras(titulo="Prueba de Producción")
    grafico.establecer_datos({"2020": 15, "2021": 30, "2022": 45})
    grafico.resize(400, 300)

    destino_png = tmp_path / "grafico_barras.png"
    exito = grafico.exportar_png(destino_png)
    assert exito
    assert destino_png.exists()
    assert destino_png.stat().st_size > 0


def test_responsividad_ventana(ventana: VentanaPrincipal) -> None:
    """Verifica la adaptación de la barra superior y pie al cambiar dimensiones (Sección 11)."""
    # 1. Tamaño ancho normal (≥ 1240)
    ventana.resize(1360, 820)
    QApplication.processEvents()
    assert ventana._lbl_eslogan.isVisible()
    assert not ventana._botones_pestanas[0]._modo_compacto
    assert ventana._pie.height() == 72
    assert ventana._caja_texto_pie.isVisible()

    # 2. Ancho intermedio (< 1240)
    ventana.resize(1200, 820)
    QApplication.processEvents()
    assert not ventana._lbl_eslogan.isVisible()

    # 3. Ancho estrecho (< 1120)
    ventana.resize(1100, 700)
    QApplication.processEvents()
    assert not ventana._lbl_eslogan.isVisible()
    assert ventana._botones_pestanas[0]._modo_compacto

    # 4. Alto reducido (< 760): Pie compacto
    assert ventana._pie.height() == 44
    assert not ventana._caja_texto_pie.isVisible()
