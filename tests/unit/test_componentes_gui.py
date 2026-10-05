"""Pruebas unitarias para componentes reutilizables de la GUI (Sección 8 de GUI-Diseno-Python.md)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from pea.gui.componentes import (
    Avatar,
    CampoBusqueda,
    ChipVentana,
    Esqueleto,
    EstadoVacio,
    FichaKPI,
    GestorAvisos,
    Minigrafico,
    Pildora,
    PopoverFiltroAnios,
    SelectorSegmentado,
    Tarjeta,
    TarjetaKPI,
    Toast,
    animaciones_habilitadas,
    duracion_efectiva,
)
from pea.gui.componentes.animacion import VARIABLE_SIN_ANIMACIONES
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios

# ===========================================================================
# 1. Pruebas de animacion.py
# ===========================================================================


def test_animacion_respeta_variable_entorno(monkeypatch: Any) -> None:
    """Verifica que PEA_SIN_ANIMACIONES active o desactive la duración de animaciones."""
    monkeypatch.setenv(VARIABLE_SIN_ANIMACIONES, "1")
    assert not animaciones_habilitadas()
    assert duracion_efectiva(350) == 0

    monkeypatch.setenv(VARIABLE_SIN_ANIMACIONES, "0")
    assert animaciones_habilitadas()
    assert duracion_efectiva(350) == 350


# ===========================================================================
# 2. Pruebas de Tarjeta
# ===========================================================================


def test_tarjeta_estructura_y_accesibilidad(qapp: Any) -> None:
    """Verifica creación de Tarjeta con barra de acento, encabezado y contenedor."""
    tarjeta = Tarjeta(titulo="Producción por año")
    assert tarjeta.objectName() == "tarjeta"
    assert "Producción por año" in tarjeta.accessibleName()

    widget_hijo = QLabel("Contenido de prueba")
    tarjeta.agregar_widget(widget_hijo)

    btn_accion = QPushButton("Filtro")
    tarjeta.agregar_accion(btn_accion)

    tarjeta.establecer_titulo("Nuevo Título")
    assert "Nuevo Título" in tarjeta.accessibleName()

    # Ocultar título
    tarjeta.establecer_titulo(None)


# ===========================================================================
# 3. Pruebas de FichaKPI y Minigrafico
# ===========================================================================


def test_ficha_kpi_actualizacion_y_retrocompatibilidad(qapp: Any) -> None:
    """Verifica funcionamiento de FichaKPI y compatibilidad con API de TarjetaKPI."""
    kpi = FichaKPI(titulo="Productos", valor_inicial=1250, subtitulo="En ventana", con_minigrafico=True)
    assert isinstance(kpi, TarjetaKPI)
    assert kpi.objectName() == "fichaKPI"
    assert "1.250" in kpi.lbl_valor.text()

    # Minigráfico presente
    assert kpi.minigrafico is not None
    assert isinstance(kpi.minigrafico, Minigrafico)

    # Actualizar valores
    kpi.actualizar(valor=4500.5, subtitulo="Histórico", tendencia=[10, 25, 40, 60])
    assert "4.500,50" in kpi.lbl_valor.text()
    assert kpi.lbl_subtitulo.text() == "Histórico"
    assert len(kpi.minigrafico._datos) == 4
    contenedor.deleteLater() if (contenedor := getattr(kpi, "_test_parent", None)) else None


def test_ficha_kpi_ancho_util_y_visibilidad_lbl_valor(qapp: Any) -> None:
    """Regresión: comprueba que lbl_valor conserva ancho útil y texto tras actualizar()."""
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    kpi = FichaKPI(titulo="Investigadores", valor_inicial=42, subtitulo="Activos", con_minigrafico=True)
    layout.addWidget(kpi)
    contenedor.resize(220, 100)
    contenedor.show()
    qapp.processEvents()

    # Comprueba visibilidad y ancho útil inicial
    assert kpi.lbl_valor.isVisible()
    assert kpi.lbl_valor.text() == "42"
    assert kpi.lbl_valor.width() > 0
    assert kpi.lbl_valor.width() >= 15

    # Posición relativa con minigráfico a la derecha
    assert kpi.minigrafico is not None
    assert kpi.minigrafico.geometry().left() > kpi.lbl_valor.geometry().right()

    # Actualizar con valor formateado y comprobar persistencia de ancho útil y texto
    kpi.actualizar(valor=1250, subtitulo="Registrados", tendencia=[10, 20, 30])
    qapp.processEvents()

    assert kpi.lbl_valor.text() == "1.250"
    assert kpi.lbl_valor.width() > 0
    assert kpi.lbl_subtitulo.text() == "Registrados"
    assert kpi.minigrafico.geometry().left() > kpi.lbl_valor.geometry().right()
    contenedor.deleteLater()


# ===========================================================================
# 4. Pruebas de Pildora
# ===========================================================================


def test_pildora_variantes_y_colores(qapp: Any) -> None:
    """Verifica resolución de colores por tipología, validación, categoría y estado semántico."""
    p_gnc = Pildora("GNC")
    assert p_gnc.texto == "GNC"
    assert p_gnc.color_fondo == "#17375E"

    p_val = Pildora("Avalado")
    assert p_val.texto == "Avalado"
    assert p_val.color_fondo == "#6BBF8E"

    p_cat = Pildora("Senior")
    assert p_cat.texto == "Senior"
    assert p_cat.color_fondo == "#196E8F"

    p_exito = Pildora("Activo", variante="exito")
    assert p_exito.texto == "Activo"
    assert p_exito.color_fondo == "#E6F4EC"

    p_gnc.establecer_texto("DTI")
    assert p_gnc.texto == "DTI"
    assert p_gnc.color_fondo == "#1F7A9E"


# ===========================================================================
# 5. Pruebas de Avatar
# ===========================================================================


def test_avatar_iniciales_anillo_y_pixmap(qapp: Any) -> None:
    """Verifica renderizado de Avatar con iniciales, variante con anillo y pixmap."""
    avatar = Avatar(diametro=44, nombre="Carlos Gómez", con_anillo=True)
    assert avatar.diametro == 44
    assert avatar.nombre == "Carlos Gómez"
    assert "Carlos Gómez" in avatar.accessibleName()

    # Cambiar nombre
    avatar.establecer_nombre("Sistemas Inteligentes")
    assert avatar.nombre == "Sistemas Inteligentes"

    # Establecer imagen
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.white)
    avatar.establecer_pixmap(pm)
    assert avatar._pixmap is not None

    avatar.establecer_anillo(False)
    assert not avatar._con_anillo


# ===========================================================================
# 6. Pruebas de CampoBusqueda (Debounce de 250 ms)
# ===========================================================================


def test_campo_busqueda_debounce_y_limpiar(qapp: Any, qtbot: Any) -> None:
    """Verifica que CampoBusqueda emita texto_cambiado tras el retardo configurado."""
    campo = CampoBusqueda(placeholder="Buscar...", retardo_ms=50)
    qtbot.addWidget(campo)

    textos_emitidos: list[str] = []
    campo.texto_cambiado.connect(textos_emitidos.append)

    # Escribir texto
    campo.setText("Minciencias")
    assert len(textos_emitidos) == 0  # Aún no debe emitir de inmediato

    # Esperar el debounce
    qtbot.wait(100)
    assert "Minciencias" in textos_emitidos

    # Limpiar
    campo.limpiar()
    assert campo.text() == ""
    assert "" in textos_emitidos


# ===========================================================================
# 7. Pruebas de SelectorSegmentado
# ===========================================================================


def test_selector_segmentado_cambio_opcion(qapp: Any) -> None:
    """Verifica alternancia excluyente de opciones en SelectorSegmentado."""
    selector = SelectorSegmentado(opciones=[("institucion", "Institución"), ("grupo", "Grupo")])
    assert selector.clave_seleccionada() == "institucion"

    cambios: list[str] = []
    selector.opcion_cambiada.connect(cambios.append)

    selector.seleccionar("grupo")
    assert selector.clave_seleccionada() == "grupo"
    assert selector.texto_seleccionado() == "Grupo"


# ===========================================================================
# 8. Pruebas de ChipVentana y PopoverFiltroAnios
# ===========================================================================


def test_chip_ventana_y_popover(qapp: Any) -> None:
    """Verifica integración de ChipVentana con PopoverFiltroAnios y emisión de FiltroAnios."""
    chip = ChipVentana(filtro_inicial=FiltroAnios(modo=ModoFiltroAnios.MODELO_2024))
    assert "Modelo 2024" in chip.text()

    popover = PopoverFiltroAnios()
    filtros_emitidos: list[FiltroAnios] = []
    popover.filtro_cambiado.connect(filtros_emitidos.append)

    popover.rb_todos.setChecked(True)
    assert len(filtros_emitidos) > 0
    assert filtros_emitidos[-1].modo == ModoFiltroAnios.TODOS

    chip.establecer_filtro(FiltroAnios(modo=ModoFiltroAnios.ULTIMOS, ultimos_n=3))
    assert "Últimos 3 años" in chip.text()


# ===========================================================================
# 9. Pruebas de EstadoVacio y Esqueleto
# ===========================================================================


def test_estado_vacio_y_botones(qapp: Any) -> None:
    """Verifica configuración de textos y señales de EstadoVacio."""
    vacio = EstadoVacio(
        titulo="Sin investigadores",
        mensaje="No hay registros",
        texto_principal="Crear uno",
        texto_secundario="Cargar demo",
    )
    pulsado_principal = False
    pulsado_secundario = False

    def on_principal() -> None:
        nonlocal pulsado_principal
        pulsado_principal = True

    def on_secundario() -> None:
        nonlocal pulsado_secundario
        pulsado_secundario = True

    vacio.accion_principal_pulsada.connect(on_principal)
    vacio.accion_secundaria_pulsada.connect(on_secundario)

    vacio.btn_principal.click()
    vacio.btn_secundario.click()

    assert pulsado_principal
    assert pulsado_secundario


def test_esqueleto_renderizado(qapp: Any) -> None:
    """Verifica inicialización y dimensiones del Esqueleto placeholder."""
    esqueleto = Esqueleto(filas=3, altura_fila=20, espaciado=8)
    assert esqueleto.accessibleName() == "Cargando contenido..."
    assert esqueleto._filas == 3


# ===========================================================================
# 10. Pruebas de Toast y GestorAvisos
# ===========================================================================


def test_toast_y_gestor_avisos(qapp: Any, qtbot: Any) -> None:
    """Verifica creación, apilado y cierre de toasts mediante GestorAvisos."""
    ventana_padre = QWidget()
    ventana_padre.resize(800, 600)
    qtbot.addWidget(ventana_padre)
    ventana_padre.show()

    gestor = GestorAvisos(ventana_padre)

    toast_exito = gestor.mostrar_exito("Operación completada", titulo="Guardado", duracion_ms=2000)
    assert isinstance(toast_exito, Toast)
    assert len(gestor._toasts) == 1
    assert toast_exito.isVisible()

    toast_aviso = gestor.mostrar_aviso("Revisión pendiente")
    assert toast_aviso.isVisible()
    assert len(gestor._toasts) == 2

    # Cerrar manualmente
    toast_exito.cerrar()
    assert len(gestor._toasts) == 1

    gestor.limpiar_todos()
    assert len(gestor._toasts) == 0
