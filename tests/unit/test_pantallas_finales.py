"""Pruebas unitarias de las pantallas finales de la interfaz PySide6 (Secciones 6.6, 6.7 y 6.8).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md.
- PantallaImportar: tres fuentes (CSV, PDF, URL), Drag and Drop con ZonaSoltarArchivo,
  tabla de cola con píldoras de estado y procesamiento.
- PantallaConfiguracion: selector segmentado, sección de conexión HTTPS/Demo y
  sección de verificación cruzada con visores comparativos.
- PantallaAcerca: tarjeta institucional UPC, ficha técnica, estado dinámico y botón volver.
"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QSizePolicy

from pea.gui import estilo
from pea.gui.pantallas.acerca import PantallaAcerca
from pea.gui.pantallas.configuracion import PantallaConfiguracion
from pea.gui.pantallas.importar import PantallaImportar, ZonaSoltarArchivo
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoConexion, ModoFiltroAnios


@pytest.fixture
def servicio_demo() -> ServicioAplicacion:
    """Servicio inicializado con datos de demostración en memoria."""
    serv = ServicioAplicacion()
    serv.cargar_demostracion()
    return serv


# ===========================================================================
# 1. Pruebas de PantallaImportar y ZonaSoltarArchivo (Sección 6.6)
# ===========================================================================


def test_zona_soltar_archivo(qapp: QApplication, qtbot: Any) -> None:
    """Verifica el comportamiento de la zona interactiva de archivos."""
    zona = ZonaSoltarArchivo(
        extensiones=(".csv",),
        filtro="Archivos CSV (*.csv)",
        placeholder="Arrastre su archivo CSV",
    )
    qtbot.addWidget(zona)
    zona.show()

    assert zona.ruta() == ""
    assert zona.btn_limpiar.isHidden()

    senales: list[str] = []
    zona.archivo_seleccionado.connect(senales.append)

    # Establecer ruta válida
    zona.establecer_ruta("C:/datos/investigadores.csv")
    assert zona.ruta() == "C:/datos/investigadores.csv"
    assert not zona.btn_limpiar.isHidden()
    assert "investigadores.csv" in zona._lbl_principal.text()
    assert len(senales) == 1
    assert senales[0] == "C:/datos/investigadores.csv"

    # Limpiar archivo
    zona.limpiar()
    assert zona.ruta() == ""
    assert not zona.btn_limpiar.isVisible()
    assert len(senales) == 2
    assert senales[1] == ""


def test_pantalla_importar_estructura_y_encolamiento(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any, tmp_path: Any
) -> None:
    """Verifica las 3 tarjetas de fuente, encolamiento y vista de cola."""
    pantalla = PantallaImportar(servicio=servicio_demo, ejecutor=None)
    qtbot.addWidget(pantalla)
    pantalla.show()

    # Verificar presencia de las tres tarjetas
    assert pantalla.tarjeta_csv is not None
    assert pantalla.tarjeta_pdf is not None
    assert pantalla.tarjeta_url is not None
    assert pantalla.tarjeta_cola is not None

    # Encolar archivo CSV temporal
    csv_file = tmp_path / "prueba_grupos.csv"
    csv_file.write_text("codigo_gruplac,nombre\nCOL001,Grupo Alfa\n", encoding="utf-8")

    pantalla.zona_csv.establecer_ruta(str(csv_file))
    pantalla.combo_tipo_csv.setCurrentIndex(1)  # Grupos
    pantalla._al_encolar_csv()

    # Verificar que la tarea ingresó a la cola
    assert servicio_demo.tareas_pendientes() >= 1
    assert "Tareas pendientes: " in pantalla.lbl_estado_cola.text()

    # Encolar URL
    pantalla.txt_url.setText("https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000001")
    pantalla._al_encolar_url()
    assert servicio_demo.tareas_pendientes() >= 2

    # Procesar una tarea sincrónicamente
    pendientes_antes = servicio_demo.tareas_pendientes()
    pantalla._al_procesar_siguiente()
    assert servicio_demo.tareas_pendientes() == pendientes_antes - 1

    # Procesar todas las tareas restantes
    pantalla._al_procesar_todas()
    assert servicio_demo.tareas_pendientes() == 0

    # Verificar que la API pública responde
    pantalla.establecer_filtro(FiltroAnios(modo=ModoFiltroAnios.TODOS))
    pantalla.refrescar()


def test_zona_soltar_archivo_formatos_aceptados_adaptable(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica que «Formatos aceptados: ...» tenga ancho adaptable y wordWrap sin cortar texto."""
    pantalla = PantallaImportar(servicio=servicio_demo, ejecutor=None)
    qtbot.addWidget(pantalla)

    # 1. Verificar propiedades de las zonas de arrastrar y soltar
    for nombre_zona, zona in [("CSV", pantalla.zona_csv), ("PDF", pantalla.zona_pdf)]:
        assert zona.acceptDrops(), f"La zona {nombre_zona} debe aceptar Drag & Drop"
        assert zona.height() == 88, f"La zona {nombre_zona} debe conservar altura de 88 px"
        assert zona._lbl_subtexto.wordWrap(), f"El subtexto de {nombre_zona} debe tener wordWrap activo"
        assert zona._lbl_subtexto.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
        assert zona._lbl_subtexto.minimumWidth() == 0, f"El ancho de {nombre_zona} debe ser adaptable (minWidth=0)"
        assert zona._lbl_principal.wordWrap()
        assert not zona.btn_examinar.isHidden()
        assert zona.btn_examinar.text() == "Examinar..."

    # 2. Verificar en las tres resoluciones oficiales: 1100x700, 1366x768, 1920x1080
    for ancho, alto in [(1100, 700), (1366, 768), (1920, 1080)]:
        pantalla.resize(ancho, alto)
        pantalla.show()
        qapp.processEvents()

        # Verificar presencia de las tres tarjetas de fuente
        assert pantalla.tarjeta_csv.isVisible()
        assert pantalla.tarjeta_pdf.isVisible()
        assert pantalla.tarjeta_url.isVisible()
        assert pantalla.txt_url.isVisible()
        assert pantalla.btn_encolar_url.isVisible()

        for nombre_zona, zona in [("CSV", pantalla.zona_csv), ("PDF", pantalla.zona_pdf)]:
            sub = zona._lbl_subtexto
            btn = zona.btn_examinar

            # La tarjeta conserva altura de 88 px
            assert zona.height() == 88

            # El subtexto tiene geometría útil y cabe íntegramente dentro de los 88 px de la tarjeta
            assert sub.width() > 80, f"Ancho insuficiente para {nombre_zona} en {ancho}x{alto}: {sub.width()}"
            if ancho <= 1100:
                assert sub.height() >= 24, (
                    f"Altura insuficiente para {nombre_zona} en {ancho}x{alto}: {sub.height()} "
                    "(debe expandirse a múltiples líneas)"
                )
            else:
                assert sub.height() >= 12, (
                    f"Altura insuficiente para {nombre_zona} en {ancho}x{alto}: {sub.height()}"
                )
            assert sub.geometry().bottom() < zona.height(), (
                f"El subtexto de {nombre_zona} desborda la tarjeta en {ancho}x{alto}: "
                f"bottom={sub.geometry().bottom()} vs max={zona.height()}"
            )

            # Botón Examinar visible y dentro de la zona
            assert btn.isVisible()
            assert btn.geometry().right() <= zona.width()


# ===========================================================================
# 2. Pruebas de PantallaConfiguracion (Sección 6.7)
# ===========================================================================


def test_pantalla_configuracion_selector_y_conexion(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica el selector segmentado y las acciones de conexión."""
    pantalla = PantallaConfiguracion(servicio=servicio_demo, ejecutor=None)
    qtbot.addWidget(pantalla)
    pantalla.show()

    # Selector segmentado
    assert pantalla.selector_seccion is not None
    assert pantalla._apilador_secciones.currentIndex() == 0

    # Cambiar a Verificación Cruzada
    pantalla.selector_seccion.seleccionar("cruzada")
    assert pantalla._apilador_secciones.currentIndex() == 1

    # Regresar a Conexión
    pantalla.selector_seccion.seleccionar("conexion")
    assert pantalla._apilador_secciones.currentIndex() == 0

    # Estado inicial: Demostración
    est = servicio_demo.estado()
    assert est.modo == ModoConexion.DEMOSTRACION
    assert "Demostración" in pantalla.pildora_modo.text()

    # Probar desconexión
    senales_estado: list[Any] = []
    pantalla.estado_actualizado.connect(senales_estado.append)

    pantalla._al_desconectar()
    assert servicio_demo.estado().modo == ModoConexion.DESCONECTADO
    assert "Desconectado" in pantalla.pildora_modo.text()
    assert len(senales_estado) >= 1

    # Probar recarga de demostración
    pantalla._al_cargar_demostracion()
    assert servicio_demo.estado().modo == ModoConexion.DEMOSTRACION
    assert "Demostración" in pantalla.pildora_modo.text()


def test_pantalla_configuracion_altura_minima_campos(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica que los cuatro QLineEdit de Supabase tengan altura mínima reglamentaria (>= 36 px) y no corten texto."""
    from pea.gui import estilo

    qapp.setStyleSheet(estilo.HOJA_ESTILO)
    pantalla = PantallaConfiguracion(servicio=servicio_demo, ejecutor=None)
    qtbot.addWidget(pantalla)
    pantalla.show()
    qapp.processEvents()

    campos = (pantalla.txt_url, pantalla.txt_clave, pantalla.txt_correo, pantalla.txt_pass)
    for campo in campos:
        assert campo.minimumHeight() >= 36
        assert campo.minimumHeight() == estilo.ALTURA_CAMPO_MINIMA
        assert campo.height() >= 36
        # Tipografía de 11 pt
        assert campo.font().pointSize() >= estilo.TAMANO_CUERPO


def test_pantalla_configuracion_verificacion_cruzada(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica la ejecución de la prueba cruzada y el visor comparativo."""
    pantalla = PantallaConfiguracion(servicio=servicio_demo, ejecutor=None)
    qtbot.addWidget(pantalla)
    pantalla.show()

    pantalla.selector_seccion.seleccionar("cruzada")
    assert pantalla._apilador_secciones.currentIndex() == 1

    # Ejecutar verificación cruzada
    pantalla._al_ejecutar_cruzada()
    assert pantalla._resultado_cruzada is not None

    # Verificar tabla de pasos y selección de fila
    assert pantalla.modelo_pasos.rowCount() > 0
    pantalla._al_seleccionar_paso_cruzada(0)

    # Verificar que los visores recibieron contenido
    assert len(pantalla.txt_out_py.toPlainText()) > 0
    assert len(pantalla.txt_out_cpp.toPlainText()) > 0


# ===========================================================================
# 3. Pruebas de PantallaAcerca (Sección 6.8)
# ===========================================================================


def test_pantalla_acerca_contenido_y_volver(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica la tarjeta institucional, ficha técnica y botón volver."""
    pantalla = PantallaAcerca(servicio=servicio_demo)
    qtbot.addWidget(pantalla)
    pantalla.show()

    # Verificar tarjetas requeridas
    assert pantalla.tarjeta_software is not None
    assert pantalla.tarjeta_tecnica is not None
    assert pantalla.tarjeta_equipo is not None
    assert pantalla.tarjeta_revision is not None

    # Verificar señal de volver al inicio
    recibido_volver: list[bool] = []
    pantalla.volver_solicitado.connect(lambda: recibido_volver.append(True))

    pantalla.btn_volver.click()
    assert len(recibido_volver) == 1

    # Verificar actualización de estado en la ficha técnica
    pantalla.refrescar()
    assert "Modo de conexión:" in pantalla._lbl_estado_rev.text()
    assert "demostraci" in pantalla._lbl_estado_rev.text().lower()


def test_pantalla_acerca_tarjeta_institucional_y_ficha_tecnica_responsive(
    servicio_demo: ServicioAplicacion, qapp: QApplication, qtbot: Any
) -> None:
    """Verifica tarjeta institucional sin bordes residuales, contraste alto y ficha técnica responsive."""
    pantalla = PantallaAcerca(servicio=servicio_demo)
    qtbot.addWidget(pantalla)

    # 1. Tarjeta institucional y ausencia de bordes en QLabel
    tarj_inst = pantalla.findChild(QFrame, "tarjetaInstitucional")
    assert tarj_inst is not None
    assert "border: none" in tarj_inst.styleSheet()

    etiquetas_inst = tarj_inst.findChildren(QLabel)
    assert len(etiquetas_inst) >= 4
    for lbl in etiquetas_inst:
        css = lbl.styleSheet()
        assert "background-color: transparent" in css
        assert "border: none" in css

    # 2. Contraste de texto institucional sobre ENCABEZADO_INICIO
    ratio = estilo.calcular_radio_contraste(estilo.TEXTO_SOBRE_OSCURO, estilo.ENCABEZADO_INICIO)
    assert ratio >= 4.5

    # 3. Ficha técnica: distribución en QGridLayout responsive y wordWrap
    grid_ficha = pantalla.tarjeta_tecnica.findChild(QGridLayout)
    assert grid_ficha is not None
    assert grid_ficha.columnMinimumWidth(0) >= 220
    assert grid_ficha.columnStretch(0) >= 1
    assert grid_ficha.columnStretch(1) >= 2

    etiquetas_tecnica = pantalla.tarjeta_tecnica.findChildren(QLabel)
    claves_ficha = [lbl for lbl in etiquetas_tecnica if "•" in lbl.text()]
    assert len(claves_ficha) == 6
    for lbl in claves_ficha:
        assert lbl.wordWrap()
        # No debe estar restringido rígidamente con setFixedWidth(240)
        assert lbl.maximumWidth() > 240

    # Verificar que en 1100x700, 1366x768 y 1920x1080 la etiqueta larga se adapta responsive
    lbl_estructuras = next(lbl for lbl in claves_ficha if "Estructuras de datos en memoria" in lbl.text())
    anchos_observados: list[int] = []
    for ancho, alto in [(1100, 700), (1366, 768), (1920, 1080)]:
        pantalla.resize(ancho, alto)
        pantalla.show()
        qapp.processEvents()
        assert lbl_estructuras.width() >= 220
        assert lbl_estructuras.height() > 0
        assert "Estructuras de datos en memoria" in lbl_estructuras.text()
        anchos_observados.append(lbl_estructuras.width())

    # La distribución responsive debe expandir el ancho de la columna en pantallas más anchas
    assert anchos_observados[2] >= anchos_observados[1] >= anchos_observados[0]

