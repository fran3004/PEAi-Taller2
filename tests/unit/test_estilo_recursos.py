"""Pruebas unitarias para estilo.py, formato.py y el cargador de recursos de PEA-i."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtGui import QFont, QFontDatabase, QFontMetricsF, QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from pea.gui.estilo import (
    ACENTO,
    AVISO,
    AVISO_FONDO,
    COLOR_ASC,
    COLOR_CAT_ASOCIADO,
    COLOR_CAT_EMERITO,
    COLOR_CAT_JUNIOR,
    COLOR_CAT_SENIOR,
    COLOR_CAT_SIN_CATEGORIA_FONDO,
    COLOR_CAT_SIN_CATEGORIA_TEXTO,
    COLOR_DTI,
    COLOR_FRH,
    COLOR_GNC,
    COLOR_VALIDACION_AVALADO,
    COLOR_VALIDACION_CON_SOPORTE,
    COLOR_VALIDACION_NO_AVALADO,
    ENCABEZADO_FIN,
    ENCABEZADO_INICIO,
    ENCABEZADO_MEDIO,
    ENLACE,
    ERROR,
    ERROR_FONDO,
    EXITO,
    EXITO_FONDO,
    FICHA,
    FONDO_APP,
    HOJA_ESTILOS_GLOBAL,
    LINEA,
    LINEA_FUERTE,
    PARES_CONTRASTE_TABLA_4_1,
    PIE,
    PRIMARIO,
    PRIMARIO_HOVER,
    PRIMARIO_PULSADO,
    SUPERFICIE,
    TAMANO_CUERPO,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
    TEXTO_SOBRE_OSCURO_SUAVE,
    UPC_VERDE,
    UPC_VERDE_CLARO,
    UPC_VERDE_OSCURO,
    calcular_radio_contraste,
    css_boton,
    css_etiqueta,
    css_menu,
    css_pestana_interna,
    css_pildora,
    generar_hoja_estilos,
)
from pea.gui.formato import (
    NOMBRES_TIPOLOGIAS,
    NOMBRES_VALIDACIONES,
    descripcion_tipologia,
    formatear_decimal,
    formatear_entero,
    formatear_porcentaje,
    iniciales_nombre,
    nombre_categoria_investigador,
    nombre_tipologia,
    nombre_validacion,
)
from pea.gui.recursos import (
    CARPETA_FUENTES,
    CARPETA_ICONOS,
    CARPETA_RECURSOS,
    FUENTES_INTER,
    SIMBOLOS_ESPECIALES,
    cargar_fuentes,
    cargar_icono,
    cargar_pixmap,
    cargar_svg_renderer,
    limpiar_cache_recursos,
    listar_iconos_disponibles,
    resolver_ruta_recurso,
)

# ===========================================================================
# 1. Pruebas de tokens de estilo y contraste WCAG 2.1
# ===========================================================================


def test_contraste_wcag_tabla_4_1() -> None:
    """Verifica que todos los pares de texto/fondo de la tabla 4.1 cumplan el contraste mínimo de 4.5:1."""
    for c_texto, c_fondo, descripcion in PARES_CONTRASTE_TABLA_4_1:
        ratio = calcular_radio_contraste(c_texto, c_fondo)
        assert ratio >= 4.5, (
            f"El par '{descripcion}' ({c_texto} sobre {c_fondo}) tiene un ratio de {ratio:.2f}:1, "
            f"inferior al mínimo exigido de 4.5:1."
        )


def test_eliminacion_paleta_obsoleta() -> None:
    """Verifica que la paleta vieja (#003366, #0D47A1) ya no forme parte de estilo.py."""
    import pea.gui.estilo as mod_estilo

    # No deben existir atributos con la paleta vieja
    assert not hasattr(mod_estilo, "AZUL_UPC")
    assert not hasattr(mod_estilo, "AZUL_ACENTO")

    # Tampoco deben figurar los códigos hex obsoletos en el archivo
    ruta_archivo = Path(mod_estilo.__file__)
    contenido = ruta_archivo.read_text(encoding="utf-8")
    assert "#003366" not in contenido
    assert "#0D47A1" not in contenido


def test_todos_los_tokens_oficiales_definidos() -> None:
    """Comprueba que todos los tokens principales de la sección 4 estén exportados y sean no vacíos."""
    tokens_color = [
        ENCABEZADO_INICIO,
        ENCABEZADO_MEDIO,
        ENCABEZADO_FIN,
        ACENTO,
        PRIMARIO,
        PRIMARIO_HOVER,
        PRIMARIO_PULSADO,
        FONDO_APP,
        SUPERFICIE,
        FICHA,
        PIE,
        LINEA,
        LINEA_FUERTE,
        TEXTO,
        TEXTO_SECUNDARIO,
        TEXTO_SOBRE_OSCURO,
        TEXTO_SOBRE_OSCURO_SUAVE,
        ENLACE,
        UPC_VERDE_OSCURO,
        UPC_VERDE,
        UPC_VERDE_CLARO,
        EXITO,
        EXITO_FONDO,
        AVISO,
        AVISO_FONDO,
        ERROR,
        ERROR_FONDO,
        COLOR_GNC,
        COLOR_DTI,
        COLOR_ASC,
        COLOR_FRH,
        COLOR_VALIDACION_AVALADO,
        COLOR_VALIDACION_CON_SOPORTE,
        COLOR_VALIDACION_NO_AVALADO,
        COLOR_CAT_EMERITO,
        COLOR_CAT_SENIOR,
        COLOR_CAT_ASOCIADO,
        COLOR_CAT_JUNIOR,
        COLOR_CAT_SIN_CATEGORIA_FONDO,
        COLOR_CAT_SIN_CATEGORIA_TEXTO,
    ]
    for c in tokens_color:
        assert isinstance(c, str) and c.startswith("#") and len(c) == 7

    assert TAMANO_CUERPO >= 11, "El tamaño del cuerpo de texto debe ser al menos 11 pt (criterio de accesibilidad)"


def test_generar_hoja_estilos() -> None:
    """Verifica que la función generadora de estilos devuelva un QSS completo con selectores esenciales."""
    qss = generar_hoja_estilos()
    assert isinstance(qss, str)
    assert len(qss) > 500
    assert "QMainWindow" in qss
    assert "QTableView" in qss
    assert "QPushButton#primario" in qss
    assert "QFrame#barraSuperior" in qss
    assert HOJA_ESTILOS_GLOBAL == qss
    assert "QToolTip" in qss
    assert "QMenu" in qss
    assert "QComboBox" in qss


def test_generadores_css_aceptados_por_qt() -> None:
    """Comprueba que los generadores producen hojas que Qt puede aplicar."""
    aplicacion = QApplication.instance() or QApplication([])
    hojas = (
        css_etiqueta(11),
        css_boton("primario"),
        css_boton("secundario"),
        css_boton("peligro"),
        css_boton("icono"),
        css_pildora(EXITO_FONDO, EXITO),
        css_menu(),
        css_pestana_interna(),
    )
    avisos: list[str] = []

    def capturar_aviso(_tipo: Any, _contexto: Any, mensaje: str) -> None:
        if "Could not parse stylesheet" in mensaje:
            avisos.append(mensaje)

    from PySide6.QtCore import qInstallMessageHandler

    anterior = qInstallMessageHandler(capturar_aviso)
    try:
        for hoja in hojas:
            aplicacion.setStyleSheet(hoja)
    finally:
        qInstallMessageHandler(anterior)
    assert not avisos, "\n".join(avisos)


def test_no_hay_tokens_de_estilo_sin_interpolar_en_qss() -> None:
    """Detecta tokens estilo.X que llegaron literalmente a estilos o colores Qt."""
    raiz = Path(__file__).parents[2] / "src" / "pea" / "gui"
    hallazgos: list[str] = []

    class Visitante(ast.NodeVisitor):
        def visit_Call(self, nodo: ast.Call) -> None:
            nombre = ""
            if isinstance(nodo.func, ast.Attribute):
                nombre = nodo.func.attr
            if nombre in {"setStyleSheet", "QColor"}:
                for argumento in nodo.args:
                    for subnodo in ast.walk(argumento):
                        if isinstance(subnodo, ast.Constant) and isinstance(subnodo.value, str):
                            if re.search(r"\{estilo\.[A-Z][A-Z0-9_]*\}", subnodo.value):
                                hallazgos.append(
                                    f"{ruta.relative_to(raiz)}:{subnodo.lineno}: {subnodo.value}"
                                )
            self.generic_visit(nodo)

    for ruta in sorted(raiz.rglob("*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        Visitante().visit(arbol)
    assert not hallazgos, "Tokens de estilo sin interpolar:\n" + "\n".join(hallazgos)


def test_variantes_css_desconocidas_fallan_explicitamente() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        css_boton("inexistente")


def test_guardian_estilos_sin_literales_en_gui() -> None:
    """Verifica que la GUI no mantenga literales de color o tamaño."""
    raiz = Path(__file__).parents[2] / "src" / "pea" / "gui"
    patrones = (
        re.compile(r"#[0-9A-Fa-f]{6}"),
        re.compile(r"rgba?\([^)]*\)"),
        re.compile(r"font-size:\s*\d+"),
        re.compile(r"setPointSize\(\s*\d+"),
    )
    infracciones: list[str] = []
    for archivo in raiz.rglob("*.py"):
        if archivo.name == "estilo.py":
            continue
        contenido = archivo.read_text(encoding="utf-8")
        for patron in patrones:
            if patron.search(contenido):
                infracciones.append(f"{archivo}: {patron.pattern}")
    assert not infracciones, "\n".join(infracciones)


# ===========================================================================
# 2. Pruebas de formateo numérico y de texto (formato.py)
# ===========================================================================


def test_formatear_entero() -> None:
    """Verifica separador de miles con punto según locale colombiano."""
    assert formatear_entero(1234567) == "1.234.567"
    assert formatear_entero(0) == "0"
    assert formatear_entero(999) == "999"
    assert formatear_entero(1000) == "1.000"
    assert formatear_entero(-54321) == "-54.321"
    assert formatear_entero(None) == "0"
    assert formatear_entero(None, sustituto_nulo="--") == "--"


def test_formatear_decimal() -> None:
    """Verifica separador decimal con coma y de miles con punto."""
    assert formatear_decimal(1234.56) == "1.234,56"
    assert formatear_decimal(0.0) == "0,00"
    assert formatear_decimal(3.14159, decimales=3) == "3,142"
    assert formatear_decimal(None) == "0,00"


def test_formatear_porcentaje() -> None:
    """Verifica formato de porcentajes con coma y símbolo opcional."""
    assert formatear_porcentaje(25.5) == "25,5 %"
    assert formatear_porcentaje(100.0, decimales=0) == "100 %"
    assert formatear_porcentaje(42.876, decimales=2) == "42,88 %"
    assert formatear_porcentaje(50.0, incluir_simbolo=False) == "50,0"
    assert formatear_porcentaje(None) == "0,0 %"


def test_iniciales_nombre() -> None:
    """Verifica extracción de iniciales para avatares."""
    assert iniciales_nombre("Juan Pérez") == "JP"
    assert iniciales_nombre("Juan Carlos Pérez") == "JC"
    assert iniciales_nombre("Sistemas Inteligentes") == "SI"
    assert iniciales_nombre("Ana") == "AN"
    assert iniciales_nombre("PEA-i") == "PI"
    assert iniciales_nombre("") == "--"
    assert iniciales_nombre(None) == "--"
    assert iniciales_nombre("   ") == "--"


def test_nombres_tipologias_y_validaciones() -> None:
    """Verifica resolución correcta de nombres completos de tipologías según el Modelo 2024."""
    assert nombre_tipologia("GNC") == "Generación de nuevo conocimiento"
    assert nombre_tipologia("DTI") == "Desarrollo tecnológico e innovación"
    assert nombre_tipologia("ASC") == "Apropiación social del conocimiento"
    assert nombre_tipologia("FRH") == "Formación de recurso humano"
    assert nombre_tipologia("OTRA") == "OTRA"
    assert nombre_tipologia(None) == "Desconocida"

    assert len(NOMBRES_TIPOLOGIAS) == 4
    for codigo in ("GNC", "DTI", "ASC", "FRH"):
        assert len(descripcion_tipologia(codigo)) > 10

    assert nombre_validacion("Avalado") == "Avalado en convocatoria"
    assert nombre_validacion("Con soporte") == "Con soporte verificado"
    assert nombre_validacion("No avalado") == "No avalado"
    assert len(NOMBRES_VALIDACIONES) == 3

    assert nombre_categoria_investigador("Senior") == "Investigador Senior"
    assert nombre_categoria_investigador("") == "Sin categoría asignada"


# ===========================================================================
# 3. Pruebas de recursos gráficos (iconos, logos y cargador)
# ===========================================================================


def test_existencia_archivos_recursos() -> None:
    """Comprueba que todos los recursos gráficos exigidos existan físicamente en disco."""
    assert CARPETA_RECURSOS.is_dir()
    assert (CARPETA_RECURSOS / "logo_pea.svg").is_file()
    assert (CARPETA_RECURSOS / "logo_upc.png").is_file()

    pestanas_seccion_4_4 = [
        "inicio",
        "investigadores",
        "grupos",
        "productos",
        "redes",
        "importar",
        "configuracion",
    ]
    iconos_utilitarios = ["deshacer", "cerrar_sesion", "buscar", "acerca", "limpiar"]

    for nombre in pestanas_seccion_4_4 + iconos_utilitarios:
        ruta_svg = CARPETA_ICONOS / f"{nombre}.svg"
        assert ruta_svg.is_file(), f"No existe el icono requerido: {ruta_svg}"

    for nombre in FUENTES_INTER:
        assert (CARPETA_FUENTES / nombre).is_file(), f"No existe la fuente requerida: {nombre}"
    assert (CARPETA_FUENTES / "OFL.txt").is_file()


def test_cargar_fuentes_registra_inter(qapp: Any) -> None:
    """Las variantes estáticas deben exponer la familia Inter en Qt."""
    familia = cargar_fuentes()

    assert familia == "Inter"
    assert "Inter" in QFontDatabase.families()


def test_inter_contiene_acentos_y_simbolos_visibles(qapp: Any) -> None:
    """Inter debe cubrir el texto español y los símbolos que usa la GUI."""
    cargar_fuentes()
    metricas = QFontMetricsF(QFont("Inter", 11))
    caracteres = "áéíóúüñÁÉÍÓÚÑ¿¡°" + SIMBOLOS_ESPECIALES

    faltantes = [caracter for caracter in caracteres if not metricas.inFontUcs4(ord(caracter))]

    assert not faltantes, f"Inter no contiene estos caracteres: {faltantes!r}"


def test_cargador_svg_renderer(qapp: Any) -> None:
    """Verifica que el cargador pueda instanciar y cachear QSvgRenderer para archivos SVG válidos."""
    limpiar_cache_recursos()
    renderer_pea = cargar_svg_renderer("logo_pea.svg")
    assert isinstance(renderer_pea, QSvgRenderer)
    assert renderer_pea.isValid()

    # Segunda llamada debe retornar el mismo objeto en caché
    renderer_pea_cached = cargar_svg_renderer("logo_pea")
    assert renderer_pea is renderer_pea_cached


def test_cargador_pixmap_svg_y_png(qapp: Any) -> None:
    """Verifica la carga de pixmaps a partir de SVG y PNG con tamaños configurables."""
    limpiar_cache_recursos()

    # Cargar SVG a pixmap
    pm_icono = cargar_pixmap("inicio", 32, 32)
    assert isinstance(pm_icono, QPixmap)
    assert not pm_icono.isNull()
    assert pm_icono.width() == 32
    assert pm_icono.height() == 32

    # Cargar PNG institucional
    pm_upc = cargar_pixmap("logo_upc.png", 52, 52)
    assert isinstance(pm_upc, QPixmap)
    assert not pm_upc.isNull()
    assert pm_upc.width() <= 52 and pm_upc.height() <= 52


def test_cargador_icono(qapp: Any) -> None:
    """Verifica la creación y caché de QIcon para las pestañas."""
    limpiar_cache_recursos()
    ico = cargar_icono("investigadores", 28)
    assert isinstance(ico, QIcon)
    assert not ico.isNull()


def test_cargador_recurso_inexistente() -> None:
    """Verifica que resolver_ruta_recurso lance FileNotFoundError al pedir un archivo inexistente."""
    with pytest.raises(FileNotFoundError):
        resolver_ruta_recurso("recurso_fantasma_inexistente_12345.svg")


def test_listar_iconos_disponibles() -> None:
    """Verifica el listado de todos los iconos SVG del paquete."""
    iconos = listar_iconos_disponibles()
    assert "inicio" in iconos
    assert "investigadores" in iconos
    assert "grupos" in iconos
    assert "productos" in iconos
    assert "redes" in iconos
    assert "importar" in iconos
    assert "configuracion" in iconos
    assert len(iconos) >= 12
