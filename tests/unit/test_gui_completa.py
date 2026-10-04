"""Pruebas unitarias completas de la interfaz gráfica PySide6 de PEA-i (Sección 5).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md.
Cubre la suite completa de verificación para:
1. Siete pestañas y textos institucionales.
2. Navegación entre las 8 pantallas oficiales y navegación cruzada.
3. Filtros globales de años y filtros reactivos de directorios.
4. Fichas laterales y paneles de detalle interactivos.
5. Creación, edición y pila de deshacer con popover.
6. Pantalla Importar con cola FIFO y píldoras de estado.
7. Exportación de tablas a CSV (UTF-8 con BOM) y gráficos vectoriales a PNG.
8. Análisis de redes de coautoría con QGraphicsView y panel de métricas.
9. Estados de aviso de revisión remota y modo sin conexión.
10. Adaptabilidad y responsividad dimensional en las resoluciones oficiales.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.filtro_anios import texto_resumen_filtro
from pea.gui.componentes.graficos.barras_apiladas import GraficoBarrasApiladas
from pea.gui.ventana_principal import Pantalla, VentanaPrincipal
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.servicio_exportacion import ServicioExportacion
from pea.servicios.vistas import (
    FiltroAnios,
    ModoFiltroAnios,
    TablaDatos,
)


@pytest.fixture
def ventana(qapp: QApplication, qtbot: Any) -> VentanaPrincipal:
    """Fixture que crea y registra la ventana principal en qtbot con datos demo."""
    servicio = ServicioAplicacion()
    servicio.cargar_demostracion()
    win = VentanaPrincipal(servicio=servicio)
    qtbot.addWidget(win)
    win.show()
    return win


def test_ventana_principal_estructura_siete_pestanas(ventana: VentanaPrincipal) -> None:
    """Verifica que la ventana principal contenga las cuatro zonas y 7 pestañas oficiales."""
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

    # Franjas de revisión y sin conexión inicialmente ocultas
    assert not ventana._banner_revision.isVisible()
    assert not ventana._franja_sin_conexion.isVisible()

    # 2. Siete pestañas principales con sus textos oficiales exactos
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

    # 3. Zona central apiladora con las 8 pantallas oficiales
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

        # Verificar sincronización de pestañas de barra superior
        if idx <= 6:
            btn_activo = ventana._pestanas.button(idx)
            assert btn_activo is not None
            assert btn_activo.isChecked()
        else:
            # "Acerca de" (índice 7) no deja ninguna pestaña superior seleccionada
            for b in ventana._botones_pestanas:
                assert not b.isChecked()


def test_navegacion_cruzada_entre_pantallas(ventana: VentanaPrincipal) -> None:
    """Verifica los atajos y flujos de navegación contextual entre pantallas."""
    # 1. De Inicio a Redes al solicitar ver nodo
    ventana.seleccionar_pantalla(Pantalla.INICIO)
    QApplication.processEvents()
    ventana._al_solicitar_ver_nodo_red("INV-01")
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.REDES)

    # 2. De Investigadores a Productos
    ventana.seleccionar_pantalla(Pantalla.INVESTIGADORES)
    QApplication.processEvents()
    ventana._al_solicitar_ver_productos("INV-01")
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.PRODUCTOS)

    # 3. De Grupos a Productos
    ventana.seleccionar_pantalla(Pantalla.GRUPOS)
    QApplication.processEvents()
    ventana._al_solicitar_ver_productos("COL001")
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.PRODUCTOS)

    # 4. De Productos a Investigadores
    ventana._al_solicitar_abrir_investigador("INV-01")
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.INVESTIGADORES)

    # 5. De Acerca de hacia Inicio mediante señal de volver
    ventana.seleccionar_pantalla(Pantalla.ACERCA)
    QApplication.processEvents()
    ventana._pantalla_acerca.volver_solicitado.emit()
    QApplication.processEvents()
    assert ventana._apilador.currentIndex() == int(Pantalla.INICIO)


def test_filtros_globales_y_reactividad(ventana: VentanaPrincipal) -> None:
    """Verifica el filtro de años global compartido y su resumen."""
    assert ventana._filtro_global.modo == ModoFiltroAnios.MODELO_2024
    resumen_inicial = texto_resumen_filtro(ventana._filtro_global)
    assert "Modelo 2024" in resumen_inicial

    nuevo_filtro = FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3)
    ventana._al_cambiar_filtro_global(nuevo_filtro)
    assert ventana._filtro_global.modo == ModoFiltroAnios.ULTIMOS
    assert ventana._filtro_global.ultimos_n == 3

    # Las pantallas modulares deben reflejar el filtro actualizado
    assert ventana._pantalla_inicio._filtro_actual.modo == ModoFiltroAnios.ULTIMOS
    assert ventana._pantalla_investigadores_modulo._filtro_actual.modo == ModoFiltroAnios.ULTIMOS
    assert ventana._pantalla_grupos_modulo._filtro_actual.modo == ModoFiltroAnios.ULTIMOS
    assert ventana._pantalla_productos_modulo._filtro_actual.modo == ModoFiltroAnios.ULTIMOS


def test_fichas_laterales_directorios(ventana: VentanaPrincipal) -> None:
    """Verifica que las fichas laterales de Investigadores, Grupos y Productos respondan a selecciones."""
    # Investigadores
    ventana.seleccionar_pantalla(Pantalla.INVESTIGADORES)
    QApplication.processEvents()
    pantalla_inv = ventana._pantalla_investigadores_modulo
    assert hasattr(pantalla_inv, "_ficha_lateral")
    assert pantalla_inv._ficha_lateral.isVisible()

    # Grupos
    ventana.seleccionar_pantalla(Pantalla.GRUPOS)
    QApplication.processEvents()
    pantalla_grp = ventana._pantalla_grupos_modulo
    assert hasattr(pantalla_grp, "_ficha_lateral")
    assert pantalla_grp._ficha_lateral.isVisible()

    # Productos
    ventana.seleccionar_pantalla(Pantalla.PRODUCTOS)
    QApplication.processEvents()
    pantalla_prd = ventana._pantalla_productos_modulo
    assert hasattr(pantalla_prd, "_ficha_lateral")
    assert pantalla_prd._ficha_lateral.isVisible()


def test_creacion_edicion_y_pila_deshacer(ventana: VentanaPrincipal) -> None:
    """Prueba la pila de deshacer reflejada en la barra y en el popover de historial."""
    servicio = ventana._servicio
    grupos = servicio.tabla_grupos().claves
    assert len(grupos) > 0
    codigo_grupo = grupos[0]

    # Desactivar grupo para registrar una acción en la pila de deshacer
    servicio.cambiar_estado("grupo", codigo_grupo, activo=False)
    ventana.actualizar_estado_global()
    QApplication.processEvents()

    assert servicio.estado().operaciones_deshacer >= 1
    assert ventana._btn_deshacer._contador >= 1
    assert ventana._btn_deshacer.btn_accion.isEnabled()
    assert "Deshacer: 1" in ventana._chip_deshacer.text()

    # Abrir popover de historial
    ventana._abrir_popover_historial()
    QApplication.processEvents()
    assert ventana._popover_historial.isVisible()

    # Ejecutar deshacer
    ventana._al_clic_deshacer()
    QApplication.processEvents()

    assert servicio.estado().operaciones_deshacer == 0
    assert ventana._btn_deshacer._contador == 0
    assert not ventana._btn_deshacer.btn_accion.isEnabled()
    assert "Deshacer: 0" in ventana._chip_deshacer.text()


def test_pantalla_importar_cola_ingesta(ventana: VentanaPrincipal, tmp_path: Path) -> None:
    """Prueba la pantalla Importar: encolar archivo CSV y consultar la cola FIFO."""
    ventana.seleccionar_pantalla(Pantalla.IMPORTAR)
    QApplication.processEvents()

    pantalla = ventana._pantalla_importar
    assert pantalla is not None

    archivo_csv = tmp_path / "datos_prueba.csv"
    archivo_csv.write_text(
        "codigo_gruplac,nombre,categoria,lider,institucion_principal,departamento_ciudad,gran_area_ocde,area_ocde,fecha_creacion,activo\n"
        "PRUEBA-G99,Grupo de Prueba 99,A1,Líder Prueba,UPC,Valledupar,Ingeniería,Sistemas,2020-01-01,true\n",
        encoding="utf-8",
    )

    tarea_id = ventana._servicio.encolar_csv(archivo_csv)
    assert len(str(tarea_id)) > 0

    pantalla.refrescar()
    ventana.actualizar_estado_global()
    QApplication.processEvents()

    modelo_cola = pantalla.tabla_cola.model()
    assert modelo_cola is not None
    assert modelo_cola.rowCount() > 0


def test_exportacion_tabla_csv_y_grafico_png(tmp_path: Path) -> None:
    """Verifica la exportación de tablas a CSV (con BOM UTF-8) y gráficos a PNG."""
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
    # Debe iniciar con el BOM oficial UTF-8 (\xef\xbb\xbf)
    assert contenido_bytes.startswith(b"\xef\xbb\xbf")
    contenido_texto = destino_csv.read_text(encoding="utf-8-sig")
    assert "Grupo Uno" in contenido_texto
    assert "25" in contenido_texto

    # Exportación de gráfico nativo moderno con QPainter
    grafico = GraficoBarrasApiladas(titulo="Producción por Tipología")
    grafico.establecer_datos(
        {
            2020: {"GNC": 10, "DTI": 5, "ASC": 2, "FRH": 1},
            2021: {"GNC": 15, "DTI": 8, "ASC": 4, "FRH": 3},
            2022: {"GNC": 20, "DTI": 12, "ASC": 6, "FRH": 5},
        }
    )
    grafico.resize(600, 400)

    destino_png = tmp_path / "grafico_barras_apiladas.png"
    exito = grafico.exportar_png(destino_png, ancho=600, alto=400)
    assert exito
    assert destino_png.exists()
    assert destino_png.stat().st_size > 0


def test_pantalla_redes_componentes_y_metricas(ventana: VentanaPrincipal) -> None:
    """Verifica que PantallaRedes cargue la visualización interactiva y el panel de métricas."""
    ventana.seleccionar_pantalla(Pantalla.REDES)
    QApplication.processEvents()

    pantalla_red = ventana._pantalla_redes_modulo
    assert pantalla_red is not None
    assert hasattr(pantalla_red, "vista_red")
    assert pantalla_red.vista_red is not None
    assert hasattr(pantalla_red, "panel_metricas")
    assert pantalla_red.panel_metricas is not None


def test_estados_vacio_aviso_y_sin_conexion(ventana: VentanaPrincipal) -> None:
    """Verifica las franjas reactivas de sin conexión y revisión remota."""
    # 1. Franja sin conexión
    assert not ventana._franja_sin_conexion.isVisible()
    ventana._servicio._sin_conexion = True
    ventana.actualizar_estado_global()
    QApplication.processEvents()
    assert ventana._franja_sin_conexion.isVisible()

    ventana._servicio._sin_conexion = False
    ventana.actualizar_estado_global()
    QApplication.processEvents()
    assert not ventana._franja_sin_conexion.isVisible()

    # 2. Banner de revisión remota
    assert not ventana._banner_revision.isVisible()
    ventana.mostrar_aviso_revision(5, 8)
    QApplication.processEvents()
    assert ventana._banner_revision.isVisible()
    assert "La base de datos cambió en el servidor" in ventana._lbl_texto_banner.text()


def test_responsividad_adaptativa_ventana(ventana: VentanaPrincipal) -> None:
    """Verifica la adaptación de la barra superior y pie al cambiar dimensiones (Sección 11)."""
    # 1. Tamaño amplio (1360x820)
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

    # 3. Ancho estrecho (< 1120): pestañas en modo compacto
    ventana.resize(1100, 700)
    QApplication.processEvents()
    assert not ventana._lbl_eslogan.isVisible()
    assert ventana._botones_pestanas[0]._modo_compacto

    # 4. Alto reducido (< 760): pie compacto (44 px)
    assert ventana._pie.height() == 44
    assert not ventana._caja_texto_pie.isVisible()
