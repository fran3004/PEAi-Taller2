"""Pantalla 5: Análisis de Redes de Colaboración (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.5) y ADR-0015.
- Tarjeta «Análisis de red de colaboración» flexible:
  * Filtro combo «Todos los grupos» y lista de grupos.
  * Selector «Mín. coautorías: N» (paso 1, por defecto 2).
  * Campo de búsqueda con atajo Ctrl+F para enfocar investigadores.
  * Botón «Reordenar» y controles de zoom (+, −, Ajustar).
  * Lienzo QGraphicsView nativo con cuadrícula tenue de puntos.
  * Nodos proporcionales a grado, aristas proporcionales a productos compartidos.
  * Hover con resaltado reactivo de vecinos y atenuación al 25%.
  * Aviso visible si la red supera el tope de 400 nodos.
- Panel «Métricas de centralidad» de 340 px:
  * Sin selección: texto orientativo, lista «Más conectados» (top 5 interactivo)
    y tarjeta «Resumen de la red» (investigadores, vínculos y densidad).
  * Con selección: avatar, nombre, categoría, fichas KPI (Grado e Intermediación),
    metadatos, botón «Ver ficha de investigador →» y «Deseleccionar».
- Disposición de fuerzas calculada en EjecutorAsincrono con semilla fija.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFontMetrics,
    QImage,
    QKeySequence,
    QPainter,
    QResizeEvent,
    QShortcut,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.campo_busqueda import CampoBusqueda
from pea.gui.componentes.filtro_anios import ChipVentana
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    ACENTO,
    AVISO,
    AVISO_FONDO,
    COLOR_DTI,
    FICHA,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import formatear_entero
from pea.gui.red.disposicion import calcular_disposicion_fuerzas
from pea.gui.red.nodo import abreviar_nombre_investigador
from pea.gui.red.vista_red import VistaRed
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


class FilaTopConectado(QFrame):
    """Elemento interactivo del top 5 de investigadores más conectados."""

    clicado = Signal(str)

    def __init__(
        self,
        puesto: int,
        codigo: str,
        nombre: str,
        categoria: str,
        grado: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.codigo = codigo
        self._nombre_completo = abreviar_nombre_investigador(nombre)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {estilo.RADIO_BOTON}px;"
            f"  padding: 4px 8px;"
            f"}}"
            f"QFrame:hover {{"
            f"  background-color: {estilo.FONDO_APP};"
            f"  border-color: {ACENTO};"
            f"}}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        lbl_num = QLabel(f"#{puesto}", self)
        lbl_num.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {TEXTO_SECUNDARIO};")
        lbl_num.setFixedWidth(24)
        layout.addWidget(lbl_num)

        av = Avatar(diametro=28, nombre=nombre, parent=self)
        layout.addWidget(av)

        col_txt = QVBoxLayout()
        col_txt.setContentsMargins(0, 0, 0, 0)
        col_txt.setSpacing(1)

        lbl_nom = QLabel(self._nombre_completo, self)
        lbl_nom.setMinimumWidth(0)
        lbl_nom.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: 600; color: {TEXTO};")
        self._lbl_nom = lbl_nom
        lbl_sub = QLabel(categoria, self)
        lbl_sub.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")

        col_txt.addWidget(lbl_nom)
        col_txt.addWidget(lbl_sub)
        layout.addLayout(col_txt, 1)

        lbl_grado = QLabel(f"{grado} coaut.", self)
        lbl_grado.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: bold; color: {COLOR_DTI};")
        layout.addWidget(lbl_grado)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        ancho = max(0, self._lbl_nom.width())
        texto = QFontMetrics(self._lbl_nom.font()).elidedText(
            self._nombre_completo,
            Qt.TextElideMode.ElideRight,
            ancho,
        )
        self._lbl_nom.setText(texto)

    def mousePressEvent(self, event: Any) -> None:
        self.clicado.emit(self.codigo)
        super().mousePressEvent(event)


class PantallaRedes(QWidget):
    """Pantalla oficial de Análisis de Redes de Colaboración (Sección 6.5)."""

    solicitar_navegacion = Signal(int)
    abrir_investigador_solicitado = Signal(str)
    filtro_cambiado = Signal(object)
    datos_modificados = Signal()

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        filtro_global: FiltroAnios | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaRedes")
        self._servicio = servicio
        self._ejecutor = ejecutor
        self._filtro_actual = filtro_global or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)

        self._codigo_grupo_actual: str | None = None
        self._min_coautorias_actual: int = 2
        self._datos_red_actual: dict[str, Any] = {}
        self._investigador_seleccionado_cod: str | None = None
        self._panel_metricas_visible = True

        self._construir_ui()
        self._configurar_atajos()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(24, 16, 24, 20)
        layout_raiz.setSpacing(14)

        # 1. Barra de contexto superior (56 px)
        barra_contexto = self._crear_barra_contexto()
        layout_raiz.addWidget(barra_contexto)

        # 2. Divisor central: Tarjeta de Red + Panel de Métricas (340 px)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setHandleWidth(12)
        self._splitter.setStyleSheet("QSplitter::handle { background: transparent; }")

        # Tarjeta izquierda: Red interactiva
        self._tarjeta_red = self._crear_tarjeta_red()
        self._splitter.addWidget(self._tarjeta_red)

        # Tarjeta derecha: Panel de Métricas de Centralidad (340 px)
        self._panel_metricas = self._crear_panel_metricas()
        self._splitter.addWidget(self._panel_metricas)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.splitterMoved.connect(self._al_mover_splitter)
        self._ajustar_distribucion(self.width())

        layout_raiz.addWidget(self._splitter, 1)

    def _crear_barra_contexto(self) -> QWidget:
        barra = QWidget(self)
        barra.setFixedHeight(56)
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        col_tit = QVBoxLayout()
        col_tit.setContentsMargins(0, 4, 0, 4)
        col_tit.setSpacing(2)

        lbl_tit = QLabel("Análisis de Redes de Colaboración", barra)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt; font-weight: bold; color: {TEXTO};")
        col_tit.addWidget(lbl_tit)

        lbl_sub = QLabel("Grafo de coautorías académicas y métricas de centralidad topológica", barra)
        lbl_sub.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        col_tit.addWidget(lbl_sub)
        layout.addLayout(col_tit)

        layout.addStretch()

        # Chip de ventana global interactivo
        self.chip_ventana = ChipVentana(self._filtro_actual, parent=barra)
        self.chip_ventana.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout.addWidget(self.chip_ventana)

        # Botón Exportar (PNG a 2x)
        self.btn_exportar = QPushButton("Exportar red (PNG)", barra)
        self.btn_exportar_png = self.btn_exportar
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {PRIMARIO}; border-radius: {RADIO_BOTON}px; padding: 7px 16px; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self.btn_exportar.clicked.connect(self.exportar_png)
        layout.addWidget(self.btn_exportar)

        self.btn_alternar_panel = QPushButton("Ocultar panel", barra)
        self.btn_alternar_panel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_alternar_panel.setToolTip("Oculta o muestra el panel de métricas")
        self.btn_alternar_panel.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 7px 12px; "
            f"font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self.btn_alternar_panel.clicked.connect(self._alternar_panel_metricas)
        layout.addWidget(self.btn_alternar_panel)

        return barra

    def _crear_tarjeta_red(self) -> Tarjeta:
        tarjeta = Tarjeta(titulo="Análisis de red de colaboración", con_sombra=True, parent=self)
        tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Contenedor de controles superiores
        contenedor_controles = QWidget(tarjeta)
        layout_c = QHBoxLayout(contenedor_controles)
        layout_c.setContentsMargins(0, 0, 0, 6)
        layout_c.setSpacing(8)

        # 1. Combo Grupo
        self.combo_grupo = QComboBox(contenedor_controles)
        self.combo_grupo.setMinimumWidth(120)
        self.combo_grupo.addItem("Todos los grupos", None)
        self.combo_grupo.currentIndexChanged.connect(self._al_cambiar_grupo)
        layout_c.addWidget(self.combo_grupo)

        # 2. Selector Mínimo de coautorías
        self.combo_min_coautorias = QComboBox(contenedor_controles)
        self.combo_min_coautorias.setMinimumWidth(100)
        for val in range(1, 6):
            txt = f"Mín. {val} coautoría" if val == 1 else f"Mín. {val} coautorías"
            self.combo_min_coautorias.addItem(txt, val)
        self.combo_min_coautorias.setCurrentIndex(1)  # Mín. 2 coautorías
        self.combo_min_coautorias.currentIndexChanged.connect(self._al_cambiar_min_coautorias)
        layout_c.addWidget(self.combo_min_coautorias)

        # 3. Campo de búsqueda interactivo
        self.campo_busqueda = CampoBusqueda(
            placeholder="Buscar investigador…",
            retardo_ms=250,
            parent=contenedor_controles,
        )
        self.campo_busqueda.setMinimumWidth(140)
        self.campo_busqueda.texto_cambiado.connect(self._al_buscar_investigador)
        layout_c.addWidget(self.campo_busqueda, 1)

        # 4. Botón Reordenar
        self.btn_reordenar = QPushButton("Reordenar", contenedor_controles)
        self.btn_reordenar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reordenar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 6px 12px; font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self.btn_reordenar.clicked.connect(self._reordenar_grafo)
        layout_c.addWidget(self.btn_reordenar)

        # 5. Controles de zoom (+, -, Ajustar)
        fila_zoom = QHBoxLayout()
        fila_zoom.setSpacing(4)

        self.btn_zoom_mas = QPushButton("+", contenedor_controles)
        self.btn_zoom_mas.setFixedSize(28, 28)
        self.btn_zoom_mas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_mas.setStyleSheet(
            f"QPushButton {{ background: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {estilo.FONDO_APP}; }}"
        )
        self.btn_zoom_mas.clicked.connect(lambda: self.vista_red.acercar())
        fila_zoom.addWidget(self.btn_zoom_mas)

        self.btn_zoom_menos = QPushButton("−", contenedor_controles)
        self.btn_zoom_menos.setFixedSize(28, 28)
        self.btn_zoom_menos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_menos.setStyleSheet(
            f"QPushButton {{ background: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {estilo.FONDO_APP}; }}"
        )
        self.btn_zoom_menos.clicked.connect(lambda: self.vista_red.alejar())
        fila_zoom.addWidget(self.btn_zoom_menos)

        self.btn_zoom_ajustar = QPushButton("Ajustar", contenedor_controles)
        self.btn_zoom_ajustar.setFixedHeight(28)
        self.btn_zoom_ajustar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_ajustar.setStyleSheet(
            f"QPushButton {{ background: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; border-radius: {estilo.RADIO_BOTON}px; font-size: {estilo.TAMANO_AUXILIAR}pt; padding: 0 6px; }}"
            f"QPushButton:hover {{ background: {estilo.FONDO_APP}; }}"
        )
        self.btn_zoom_ajustar.clicked.connect(lambda: self.vista_red.ajustar_vista())
        fila_zoom.addWidget(self.btn_zoom_ajustar)

        layout_c.addLayout(fila_zoom)
        tarjeta.agregar_widget(contenedor_controles)

        # Banner de aviso para tope de 400 nodos
        self.banner_tope = QFrame(tarjeta)
        self.banner_tope.setVisible(False)
        self.banner_tope.setStyleSheet(
            f"QFrame {{ background-color: {AVISO_FONDO}; border: 1px solid {AVISO}; "
            f"border-radius: {estilo.RADIO_BOTON}px; padding: 4px 8px; }}"
        )
        self.banner_limite = self.banner_tope
        lay_b = QHBoxLayout(self.banner_tope)
        lay_b.setContentsMargins(8, 4, 8, 4)
        lay_b.setSpacing(6)

        lbl_ico_b = QLabel("⚠️", self.banner_tope)
        lay_b.addWidget(lbl_ico_b)

        self.lbl_texto_tope = QLabel(
            "La red contiene más de 400 investigadores; se muestran los 400 con mayor número de coautorías.",
            self.banner_tope,
        )
        self.lbl_texto_tope.setStyleSheet(f"color: {AVISO}; font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt;")
        self.lbl_texto_banner = self.lbl_texto_tope
        lay_b.addWidget(self.lbl_texto_tope, 1)

        tarjeta.agregar_widget(self.banner_tope)

        # Lienzo QGraphicsView de la Red
        self.vista_red = VistaRed(parent=tarjeta)
        self.vista_red.nodo_seleccionado.connect(self._al_seleccionar_nodo)
        self.vista_red.nodo_deseleccionado.connect(self._al_deseleccionar_nodo)
        self.vista_red.abrir_investigador_solicitado.connect(self._al_doble_clic_investigador)
        self.vista_red.limite_nodos_alcanzado.connect(self._al_alcanzar_limite_nodos)

        tarjeta.agregar_widget(self.vista_red)
        return tarjeta

    def _crear_panel_metricas(self) -> Tarjeta:
        tarjeta = Tarjeta(titulo="Métricas de centralidad", con_sombra=True, parent=self)
        tarjeta.setMinimumWidth(280)
        tarjeta.setMaximumWidth(340)
        self.panel_metricas = tarjeta
        self.lbl_titulo_metricas = QLabel("Métricas de centralidad", self)

        # Área con desplazamiento para adaptarse a pantallas compactas
        self._scroll_panel = QScrollArea(tarjeta)
        self._scroll_panel.setWidgetResizable(True)
        self._scroll_panel.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_panel.setStyleSheet("background: transparent;")

        self._cuerpo_panel = QWidget(self._scroll_panel)
        self._layout_cuerpo_panel = QVBoxLayout(self._cuerpo_panel)
        self._layout_cuerpo_panel.setContentsMargins(0, 0, 4, 0)
        self._layout_cuerpo_panel.setSpacing(12)

        # -------------------------------------------------------------------
        # Estado 1: Sin selección (Texto orientativo + Top 5 Más Conectados)
        # -------------------------------------------------------------------
        self._caja_sin_seleccion = QWidget(self._cuerpo_panel)
        self.widget_estado_vacio = self._caja_sin_seleccion
        layout_sin = QVBoxLayout(self._caja_sin_seleccion)
        layout_sin.setContentsMargins(0, 0, 0, 0)
        layout_sin.setSpacing(12)

        lbl_orientacion = QLabel("Selecciona un nodo para ver su posición en la red.", self._caja_sin_seleccion)
        lbl_orientacion.setWordWrap(True)
        lbl_orientacion.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        layout_sin.addWidget(lbl_orientacion)

        lbl_tit_top = QLabel("Investigadores más conectados", self._caja_sin_seleccion)
        lbl_tit_top.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};")
        layout_sin.addWidget(lbl_tit_top)

        self._contenedor_top = QVBoxLayout()
        self._contenedor_top.setSpacing(6)
        self.contenedor_top5 = self._contenedor_top
        layout_sin.addLayout(self._contenedor_top)

        self._layout_cuerpo_panel.addWidget(self._caja_sin_seleccion)

        # -------------------------------------------------------------------
        # Estado 2: Con selección (Detalle completo del investigador)
        # -------------------------------------------------------------------
        self._caja_con_seleccion = QWidget(self._cuerpo_panel)
        self._caja_con_seleccion.setVisible(False)
        self.widget_estado_seleccionado = self._caja_con_seleccion
        layout_con = QVBoxLayout(self._caja_con_seleccion)
        layout_con.setContentsMargins(0, 0, 0, 0)
        layout_con.setSpacing(10)

        # Cabecera del seleccionado
        fila_cab_sel = QHBoxLayout()
        fila_cab_sel.setSpacing(10)

        self._avatar_sel = Avatar(diametro=48, nombre="", parent=self._caja_con_seleccion)
        fila_cab_sel.addWidget(self._avatar_sel)

        col_tit_sel = QVBoxLayout()
        col_tit_sel.setSpacing(1)

        self._lbl_nom_sel = QLabel("", self._caja_con_seleccion)
        self._lbl_nom_sel.setWordWrap(True)
        self._lbl_nom_sel.setStyleSheet(f"font-size: {estilo.TAMANO_SUBTITULO}pt; font-weight: bold; color: {TEXTO};")
        self.lbl_nombre_inv = self._lbl_nom_sel
        col_tit_sel.addWidget(self._lbl_nom_sel)

        self._lbl_sub_sel = QLabel("", self._caja_con_seleccion)
        self._lbl_sub_sel.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        self.lbl_cvlac_inv = self._lbl_sub_sel
        col_tit_sel.addWidget(self._lbl_sub_sel)

        fila_cab_sel.addLayout(col_tit_sel, 1)
        layout_con.addLayout(fila_cab_sel)

        # Fichas KPI principales: Grado de conexión e Intermediación
        fila_kpis = QHBoxLayout()
        fila_kpis.setSpacing(8)

        self.kpi_grado = FichaKPI("Grado de conexión", "0", "Vínculos directos", parent=self._caja_con_seleccion)
        self.kpi_intermediacion = FichaKPI("Intermediación", "0,000", "Centralidad Brandes", parent=self._caja_con_seleccion)

        fila_kpis.addWidget(self.kpi_grado)
        fila_kpis.addWidget(self.kpi_intermediacion)
        layout_con.addLayout(fila_kpis)

        # Cuadro de metadatos del investigador en la red
        self._cuadro_meta_sel = QFrame(self._caja_con_seleccion)
        self._cuadro_meta_sel.setStyleSheet(
            f"QFrame {{ background-color: {FICHA}; border-radius: {estilo.RADIO_BOTON}px; padding: 6px; }}"
        )
        self._layout_meta_sel = QVBoxLayout(self._cuadro_meta_sel)
        self._layout_meta_sel.setContentsMargins(8, 8, 8, 8)
        self._layout_meta_sel.setSpacing(4)
        layout_con.addWidget(self._cuadro_meta_sel)

        # Botones de acción del nodo seleccionado
        fila_btn_sel = QHBoxLayout()
        fila_btn_sel.setSpacing(8)

        self.btn_ver_investigador = QPushButton("Ver ficha →", self._caja_con_seleccion)
        self.btn_ver_ficha = self.btn_ver_investigador
        self.btn_ver_investigador.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_investigador.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: {estilo.SUPERFICIE}; font-weight: bold; "
            f"border: none; border-radius: {RADIO_BOTON}px; padding: 7px 14px; font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
        )
        self.btn_ver_investigador.clicked.connect(self._al_pulsar_ver_ficha_nodo)
        fila_btn_sel.addWidget(self.btn_ver_investigador, 1)

        self.btn_deseleccionar = QPushButton("Deseleccionar", self._caja_con_seleccion)
        self.btn_deseleccionar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_deseleccionar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 7px 12px; font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self.btn_deseleccionar.clicked.connect(self._al_pulsar_deseleccionar)
        fila_btn_sel.addWidget(self.btn_deseleccionar)

        layout_con.addLayout(fila_btn_sel)
        self._layout_cuerpo_panel.addWidget(self._caja_con_seleccion)

        # -------------------------------------------------------------------
        # Tarjeta inferior fija: Resumen de la Red
        # -------------------------------------------------------------------
        self._tarjeta_resumen_red = QFrame(self._cuerpo_panel)
        self._tarjeta_resumen_red.setStyleSheet(
            f"QFrame {{ background-color: {FICHA}; border: 1px solid {LINEA}; "
            f"border-radius: {estilo.RADIO_BOTON}px; padding: 8px; }}"
        )
        layout_res = QVBoxLayout(self._tarjeta_resumen_red)
        layout_res.setContentsMargins(8, 8, 8, 8)
        layout_res.setSpacing(6)

        lbl_tit_res = QLabel("Resumen de la red", self._tarjeta_resumen_red)
        lbl_tit_res.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};")
        layout_res.addWidget(lbl_tit_res)

        self.lbl_resumen_red = QLabel(
            "Investigadores: 0\nEnlaces de coautoría: 0\nDensidad: 0,0000",
            self._tarjeta_resumen_red,
        )
        self.lbl_resumen_red.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO};")
        layout_res.addWidget(self.lbl_resumen_red)

        self._layout_cuerpo_panel.addStretch(1)
        self._layout_cuerpo_panel.addWidget(self._tarjeta_resumen_red)

        self._scroll_panel.setWidget(self._cuerpo_panel)
        tarjeta.agregar_widget(self._scroll_panel)
        return tarjeta

    def _ajustar_distribucion(self, ancho: int) -> None:
        if not hasattr(self, "_splitter"):
            return
        compacto = ancho < 1240
        self.combo_grupo.setMinimumWidth(120 if compacto else 160)
        self.combo_min_coautorias.setMinimumWidth(100 if compacto else 130)
        self.campo_busqueda.setMinimumWidth(140 if compacto else 180)
        self.btn_reordenar.setText("Ordenar" if compacto else "Reordenar")
        self.btn_zoom_ajustar.setText("Ajustar" if not compacto else "↔")
        self.btn_zoom_ajustar.setToolTip("Ajusta el grafo al lienzo")
        self.btn_exportar.setText("PNG" if compacto else "Exportar red (PNG)")
        self.btn_exportar.setToolTip("Exporta la red como imagen PNG")
        self.btn_alternar_panel.setText("Panel" if compacto else ("Ocultar panel" if self._panel_metricas_visible else "Mostrar panel"))
        self.btn_alternar_panel.setToolTip(
            "Muestra el panel de métricas" if not self._panel_metricas_visible else "Oculta el panel de métricas"
        )
        if not self._panel_metricas_visible:
            self._splitter.setSizes([self._splitter.width(), 0])
            return
        ancho_panel = 280 if ancho < 1240 else 340
        self._splitter.setSizes([max(0, self._splitter.width() - ancho_panel), ancho_panel])

    def _al_mover_splitter(self, _: int, __: int) -> None:
        self.vista_red._programar_reencuadre()

    def _alternar_panel_metricas(self) -> None:
        self._panel_metricas_visible = not self._panel_metricas_visible
        self._panel_metricas.setVisible(self._panel_metricas_visible)
        self._ajustar_distribucion(self.width())
        self.vista_red._programar_reencuadre()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._ajustar_distribucion(self.width())

    def _configurar_atajos(self) -> None:
        atajo_buscar = QShortcut(QKeySequence.StandardKey.Find, self)
        atajo_buscar.activated.connect(self.enfocar_busqueda)

    def enfocar_busqueda(self) -> None:
        """Enfoca el campo de búsqueda (atajo global Ctrl+F)."""
        self.campo_busqueda.setFocus()
        self.campo_busqueda.selectAll()

    # -----------------------------------------------------------------------
    # Carga y Reactividad del Grafo
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Carga y calcula la red de coautorías según los filtros activos."""
        cat = self._servicio._catalogo

        # Actualizar opciones del combo Grupo
        grp_prev = self.combo_grupo.currentData()
        self.combo_grupo.blockSignals(True)
        self.combo_grupo.clear()
        self.combo_grupo.addItem("Todos los grupos", None)
        for g in sorted(cat.grupos, key=lambda x: x.nombre.lower()):
            self.combo_grupo.addItem(g.nombre, g.codigo_gruplac)

        # Restaurar selección si sigue existiendo
        idx_encontrado = 0
        if grp_prev:
            for i in range(self.combo_grupo.count()):
                if self.combo_grupo.itemData(i) == grp_prev:
                    idx_encontrado = i
                    break
        self.combo_grupo.setCurrentIndex(idx_encontrado)
        self.combo_grupo.blockSignals(False)

        self._codigo_grupo_actual = self.combo_grupo.currentData()
        self._min_coautorias_actual = int(self.combo_min_coautorias.currentData() or 2)

        # Calcular red en hilo secundario o síncrono controlado
        self._cargar_red_asincrona()

    def _cargar_red_asincrona(self) -> None:
        def tarea() -> dict[str, Any]:
            return self._servicio.red_coautoria(
                filtro=self._filtro_actual,
                codigo_grupo=self._codigo_grupo_actual,
                min_coautorias=self._min_coautorias_actual,
            )

        def exito(datos_red: dict[str, Any]) -> None:
            self._al_grafo_cargado(datos_red)

        def fallo(err: Exception, _: str) -> None:
            GestorAvisos.instancia().mostrar(f"Error al calcular la red: {err}", tipo="error")

        if self._ejecutor is not None:
            self._ejecutor.ejecutar(tarea, al_terminar=exito, al_fallar=fallo)
        else:
            try:
                res = tarea()
                exito(res)
            except Exception as err:
                fallo(err, "")

    def _al_grafo_cargado(self, datos_red: dict[str, Any]) -> None:
        """Procesa y aplica en la interfaz los datos de red calculados."""
        self._datos_red_actual = datos_red
        nodos = datos_red.get("nodos", ())
        aristas = datos_red.get("aristas", ())
        resumen = datos_red.get("resumen", {})

        # Cargar en el lienzo interactivo
        self.vista_red.cargar_red(nodos, aristas)

        # Actualizar panel de métricas con el resumen y top conectados
        self._actualizar_resumen_red(resumen)
        self._actualizar_top_conectados(nodos)

        # Restaurar selección si el nodo sigue presente
        if self._investigador_seleccionado_cod:
            self.seleccionar_investigador(self._investigador_seleccionado_cod)
        else:
            self._al_deseleccionar_nodo()

    def _reordenar_grafo(self) -> None:
        """Vuelve a ejecutar la disposición por fuerzas desde cero."""
        if not self._datos_red_actual:
            return
        nodos = self._datos_red_actual.get("nodos", ())
        aristas = self._datos_red_actual.get("aristas", ())

        ancho_vista = max(900.0, float(self.vista_red.viewport().width() or 1000.0))
        alto_vista = max(650.0, float(self.vista_red.viewport().height() or 700.0))

        posiciones = calcular_disposicion_fuerzas(
            nodos=nodos,
            aristas=aristas,
            ancho=ancho_vista,
            alto=alto_vista,
        )
        self.vista_red.cargar_red(nodos, aristas, posiciones=posiciones)

    def _al_cambiar_grupo(self, _: int) -> None:
        self._codigo_grupo_actual = self.combo_grupo.currentData()
        self._cargar_red_asincrona()

    def _al_cambiar_min_coautorias(self, _: int) -> None:
        self._min_coautorias_actual = int(self.combo_min_coautorias.currentData() or 2)
        self._cargar_red_asincrona()

    def _al_cambiar_filtro(self, nuevo_filtro: FiltroAnios) -> None:
        self._filtro_actual = nuevo_filtro
        self.filtro_cambiado.emit(nuevo_filtro)
        self._cargar_red_asincrona()

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Actualiza el filtro temporal desde el exterior."""
        self._filtro_actual = filtro
        self.chip_ventana.establecer_filtro(filtro)
        self._cargar_red_asincrona()

    def _al_buscar_investigador(self, texto: str) -> None:
        """Busca y enfoca al primer investigador cuyo nombre o código coincida."""
        texto_limpio = texto.strip().lower()
        if not texto_limpio:
            return

        for cod, item in self.vista_red._items_nodos.items():
            if texto_limpio in item.nombre.lower() or texto_limpio in cod.lower():
                self.vista_red.seleccionar_nodo(item)
                return

    def _al_alcanzar_limite_nodos(self, total_original: int, mostrados: int) -> None:
        if total_original > 400:
            self.lbl_texto_tope.setText(
                f"La red contiene {total_original} investigadores; "
                f"se muestran los 400 con mayor número de coautorías."
            )
            self.banner_tope.setVisible(True)
        else:
            self.banner_tope.setVisible(False)

    # -----------------------------------------------------------------------
    # Gestión del Panel de Métricas
    # -----------------------------------------------------------------------

    def _actualizar_resumen_red(self, resumen: dict[str, Any]) -> None:
        n_inv = int(resumen.get("investigadores", 0))
        n_vinc = int(resumen.get("vinculos", 0))
        dens = float(resumen.get("densidad", 0.0))

        self.lbl_resumen_red.setText(
            f"Investigadores: {formatear_entero(n_inv)}\n"
            f"Enlaces de coautoría: {formatear_entero(n_vinc)}\n"
            f"Densidad: {dens:.4f}"
        )

    def _actualizar_top_conectados(self, nodos: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> None:
        # Limpiar lista anterior
        while self._contenedor_top.count():
            item = self._contenedor_top.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        nodos_ordenados = sorted(nodos, key=lambda d: -int(d.get("grado", 0)))
        top_5 = nodos_ordenados[:5]

        if not top_5:
            lbl_vac = QLabel("Sin coautorías registradas en este período.", self._caja_sin_seleccion)
            lbl_vac.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
            self._contenedor_top.addWidget(lbl_vac)
            return

        for puesto, nd in enumerate(top_5, start=1):
            cod = str(nd.get("codigo", ""))
            nom = str(nd.get("nombre", cod))
            cat = str(nd.get("categoria", "Sin categoría"))
            grado = int(nd.get("grado", 0))

            fila_top = FilaTopConectado(
                puesto=puesto,
                codigo=cod,
                nombre=nom,
                categoria=cat,
                grado=grado,
                parent=self._caja_sin_seleccion,
            )
            fila_top.clicado.connect(self.seleccionar_investigador)
            self._contenedor_top.addWidget(fila_top)

    def _al_seleccionar_nodo(self, datos_nodo: dict[str, Any]) -> None:
        self._investigador_seleccionado_cod = str(datos_nodo.get("codigo", ""))
        self._caja_sin_seleccion.setVisible(False)
        self._caja_con_seleccion.setVisible(True)

        nombre = str(datos_nodo.get("nombre", self._investigador_seleccionado_cod))
        categoria = str(datos_nodo.get("categoria", "Sin categoría"))
        codigo = str(datos_nodo.get("codigo", ""))
        grado = int(datos_nodo.get("grado", 0))
        intermediacion = float(datos_nodo.get("intermediacion", 0.0))
        grupo_ppal = str(datos_nodo.get("grupo_principal", "Sin grupo"))
        es_externo = bool(datos_nodo.get("es_externo", False))

        self._avatar_sel.establecer_nombre(nombre)
        self._lbl_nom_sel.setText(nombre)
        self._lbl_sub_sel.setText(f"Código: {codigo}  ·  {categoria}")

        self.kpi_grado.actualizar(f"{grado} coautores")
        self.kpi_intermediacion.actualizar(f"{intermediacion:.4f}")

        # Limpiar y regenerar metadatos
        while self._layout_meta_sel.count():
            item = self._layout_meta_sel.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        items = [
            ("Grupo principal:", grupo_ppal),
            ("Categoría:", categoria),
            ("Rol en la red:", "Colaborador externo" if es_externo else "Integrante del grupo"),
        ]
        for k, v in items:
            f = QHBoxLayout()
            f.setContentsMargins(0, 0, 0, 0)
            l1 = QLabel(k, self._cuadro_meta_sel)
            l1.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; font-weight: 600;")
            l2 = QLabel(v, self._cuadro_meta_sel)
            l2.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO};")
            f.addWidget(l1)
            f.addWidget(l2)
            f.addStretch()
            self._layout_meta_sel.addLayout(f)

    def _al_deseleccionar_nodo(self) -> None:
        self._investigador_seleccionado_cod = None
        self._caja_con_seleccion.setVisible(False)
        self._caja_sin_seleccion.setVisible(True)

    def _al_pulsar_deseleccionar(self) -> None:
        self.vista_red.deseleccionar()

    def _al_pulsar_ver_ficha_nodo(self) -> None:
        if self._investigador_seleccionado_cod:
            self._al_doble_clic_investigador(self._investigador_seleccionado_cod)

    def _al_doble_clic_investigador(self, codigo_investigador: str) -> None:
        self.abrir_investigador_solicitado.emit(codigo_investigador)
        # Pestaña 1: Pantalla.INVESTIGADORES
        self.solicitar_navegacion.emit(1)

    def seleccionar_investigador(self, codigo_investigador: str) -> None:
        """Selecciona y centra al investigador en la red."""
        self._investigador_seleccionado_cod = codigo_investigador
        self.vista_red.seleccionar_nodo(codigo_investigador)

    def seleccionar_nodo(self, codigo_investigador: str) -> None:
        """Alias para seleccionar_investigador."""
        self.seleccionar_investigador(codigo_investigador)

    def seleccionar_grupo(self, codigo_grupo: str) -> None:
        """Ajusta el filtro al grupo indicado y recarga la red."""
        for i in range(self.combo_grupo.count()):
            if self.combo_grupo.itemData(i) == codigo_grupo:
                self.combo_grupo.setCurrentIndex(i)
                return

    # -----------------------------------------------------------------------
    # Exportación
    # -----------------------------------------------------------------------

    def exportar_png(self) -> None:
        """Exporta la vista actual de la red como imagen PNG a doble resolución (2x)."""
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Red de Colaboración",
            "red_colaboracion.png",
            "Imágenes PNG (*.png)",
        )
        if not ruta:
            return

        try:
            rect_escena = self.vista_red._escena.itemsBoundingRect().adjusted(-40, -40, 40, 40)
            if rect_escena.isEmpty():
                rect_escena = QRectF(0, 0, 800, 600)

            ancho_px = int(rect_escena.width() * 2.0)
            alto_px = int(rect_escena.height() * 2.0)

            imagen = QImage(ancho_px, alto_px, QImage.Format.Format_ARGB32_Premultiplied)
            imagen.fill(QColor("{estilo.SUPERFICIE}"))

            painter = QPainter(imagen)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            self.vista_red._escena.render(painter, QRectF(0, 0, ancho_px, alto_px), rect_escena)
            painter.end()

            imagen.save(ruta, "PNG")
            GestorAvisos.instancia().mostrar(f"Red exportada exitosamente a {Path(ruta).name}", tipo="exito")
        except Exception as err:
            GestorAvisos.instancia().mostrar(f"Error al exportar imagen de red: {err}", tipo="error")
