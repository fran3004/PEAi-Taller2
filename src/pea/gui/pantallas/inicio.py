"""Pantalla 1: Inicio · Panorama Estadístico Institucional y por Grupo.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.1 y 11).
- Selector segmentado «Institución | Grupo ▾» con combo selector de grupo.
- Tarjeta de Ámbito con avatar de 112 px, información institucional/grupo,
  botón desplegable «Ver más detalles ⌄» y cuadrícula 2×3 de fichas KPI.
- Gráfico de barras apiladas de producción anual por tipología (GNC, DTI, ASC, FRH)
  con alternancia a tabla accesible.
- Gráfico de dona concéntrica doble (tipología y validación).
- Vista previa de la red de coautoría (MiniRed) con enlace a análisis completo.
- Segunda fila con rankings Top 5 (Investigadores y Grupos en modo Institución;
  Integrantes y Productos en modo Grupo).
- Menú «Exportar ▾» (CSV y PNG).
- Estado vacío accesible con botones «Conectar con Supabase» y «Cargar datos de demostración».
- Marcador de carga con Esqueleto animado.
- Disposición responsiva: 4 columnas a ≥ 1360 px y rejilla 2×2 por debajo.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.estado_vacio import Esqueleto, EstadoVacio
from pea.gui.componentes.filtro_anios import ChipVentana
from pea.gui.componentes.graficos.barras_apiladas import GraficoBarrasApiladas
from pea.gui.componentes.graficos.dona_doble import GraficoDonaDoble
from pea.gui.componentes.graficos.histograma import GraficoHistograma
from pea.gui.componentes.graficos.mini_red import MiniRed
from pea.gui.componentes.pildora import Pildora
from pea.gui.componentes.selector_segmentado import SelectorSegmentado
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.dialogos_exportacion import (
    FILTRO_CSV,
    FILTRO_PDF,
    FILTRO_PNG,
    describir_ubicacion,
    mensaje_error,
    nombre_archivo_seguro,
    resolver_archivo_destino,
    resolver_carpeta_destino,
)
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    COLOR_DTI,
    FICHA,
    LINEA,
    PRIMARIO,
    RADIO_BOTON,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TAMANO_SUBTITULO,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.exportador_visual import (
    exportar_png_institucional,
    exportar_reporte_pdf,
    guardar_csv_profesional,
    renderizar_widget_imagen,
)
from pea.gui.formato import (
    formatear_decimal,
    formatear_entero,
    formatear_porcentaje,
)
from pea.gui.recursos import cargar_icono, cargar_pixmap
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios


class FilaRanking(QFrame):
    """Fila para listas de Top 5 con puesto, barra horizontal y valor."""

    def __init__(
        self,
        puesto: int,
        titulo: str,
        subtitulo: str = "",
        valor: int = 0,
        max_valor: int = 1,
        etiqueta_valor: str = "prod.",
        pildora_estado: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"QFrame {{ background-color: transparent; border-bottom: 1px solid {LINEA}; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 8, 4)
        layout.setSpacing(10)

        # Insignia de puesto (24x24)
        lbl_puesto = QLabel(str(puesto), self)
        lbl_puesto.setFixedSize(24, 24)
        lbl_puesto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_puesto = PRIMARIO if puesto <= 3 else TEXTO_SECUNDARIO
        lbl_puesto.setStyleSheet(
            f"background-color: {FICHA}; color: {color_puesto}; font-weight: bold; "
            f"border-radius: {estilo.RADIO_PESTANA_ACTIVA}px; font-size: {estilo.TAMANO_AUXILIAR}pt;"
        )
        layout.addWidget(lbl_puesto)

        # Columna central: Título + barra horizontal de porcentaje
        col_centro = QVBoxLayout()
        col_centro.setContentsMargins(0, 2, 0, 2)
        col_centro.setSpacing(3)

        lbl_tit = QLabel(titulo, self)
        lbl_tit.setMinimumWidth(0)
        lbl_tit.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: 600; color: {TEXTO};")
        lbl_tit.setWordWrap(False)
        lbl_tit.setToolTip(titulo)
        col_centro.addWidget(lbl_tit)

        if subtitulo:
            lbl_sub = QLabel(subtitulo, self)
            lbl_sub.setMinimumWidth(0)
            lbl_sub.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            lbl_sub.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
            lbl_sub.setToolTip(subtitulo)
            col_centro.addWidget(lbl_sub)
        else:
            # Barra horizontal proporcional
            barra = QProgressBar(self)
            barra.setFixedHeight(6)
            barra.setTextVisible(False)
            barra.setRange(0, max(1, max_valor))
            barra.setValue(valor)
            barra.setStyleSheet(
                f"QProgressBar {{ background-color: {estilo.SUPERFICIE_GRAFICO_GUIA}; border-radius: {estilo.ESPACIADO_4}px; border: none; }}"
                f"QProgressBar::chunk {{ background-color: {COLOR_DTI}; border-radius: {estilo.ESPACIADO_4}px; }}"
            )
            col_centro.addWidget(barra)

        layout.addLayout(col_centro, 1)

        # Opcional píldora
        if pildora_estado:
            pildora = Pildora(pildora_estado, tipo="validacion", parent=self)
            layout.addWidget(pildora)

        # Valor numérico a la derecha
        lbl_val = QLabel(f"{formatear_entero(valor)} {etiqueta_valor}", self)
        lbl_val.setMinimumWidth(0)
        lbl_val.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        lbl_val.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {PRIMARIO};")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_val.setToolTip(f"{formatear_entero(valor)} {etiqueta_valor}")
        layout.addWidget(lbl_val)


class PantallaInicio(QWidget):
    """Pantalla 1: Panorama estadístico general institucional y por grupo."""

    solicitar_navegacion = Signal(object)  # Emite el índice o enum de la pantalla destino
    filtro_cambiado = Signal(object)      # Emite FiltroAnios cuando cambia el filtro
    ver_red_nodo_solicitado = Signal(str)  # Emite código de investigador al pulsar nodo en mini red
    datos_modificados = Signal()          # Emite cuando se conectan o cargan datos

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        filtro_global: FiltroAnios | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantalla_inicio")

        self._servicio = servicio
        self._ejecutor = ejecutor
        self._filtro_actual = filtro_global or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)
        self._modo_ambito: str = "institucion"  # "institucion" | "grupo"
        self._codigo_grupo_seleccionado: str | None = None
        self._es_cuatro_columnas: bool | None = None

        self._construir_ui()
        self.refrescar()

    # -----------------------------------------------------------------------
    # Construcción de Interfaz
    # -----------------------------------------------------------------------

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 14, 20, 14)
        layout_principal.setSpacing(12)

        # 1. Barra de contexto superior (56 px)
        self._barra_contexto = self._crear_barra_contexto()
        layout_principal.addWidget(self._barra_contexto)

        # 2. Apilador de estado (Esqueleto / Contenido / Estado Vacío)
        self._apilador_estado = QStackedWidget(self)

        # Estado 0: Esqueleto de carga
        self._esqueleto = Esqueleto(filas=7, altura_fila=36, espaciado=16, parent=self)
        self._apilador_estado.addWidget(self._esqueleto)

        # Estado 1: Contenido con desplazamiento
        self._scroll_contenido = QScrollArea(self)
        self._scroll_contenido.setWidgetResizable(True)
        self._scroll_contenido.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_contenido.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_contenido.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background-color: transparent; }"
        )

        self._widget_rejilla = QWidget(self._scroll_contenido)
        self._widget_rejilla.setMinimumWidth(0)
        self._widget_rejilla.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._widget_rejilla.setStyleSheet("background-color: transparent;")
        self._layout_rejilla = QGridLayout(self._widget_rejilla)
        self._layout_rejilla.setContentsMargins(0, 0, 0, 0)
        self._layout_rejilla.setHorizontalSpacing(16)
        self._layout_rejilla.setVerticalSpacing(16)

        # Construir las tarjetas del panel
        self._crear_tarjeta_ambito()
        self._crear_tarjeta_barras()
        self._crear_tarjeta_dona()
        self._crear_tarjeta_red()
        self._crear_tarjeta_histograma()
        self._crear_tarjetas_rankings()

        # Posicionar inicialmente en 4 columnas
        self._reorganizar_rejilla(1400)

        self._scroll_contenido.setWidget(self._widget_rejilla)
        self._apilador_estado.addWidget(self._scroll_contenido)

        # Estado 2: Estado vacío (selección directa de origen de datos)
        self._estado_vacio = EstadoVacio(
            titulo="Seleccione el origen de datos",
            mensaje="Cargue directamente los datos de la base de datos (conexión automática) o los datos de demostración.",
            texto_principal="Cargar base de datos (Supabase)",
            texto_secundario="Cargar datos de demostración",
            parent=self,
        )
        self._estado_vacio.accion_principal_pulsada.connect(self._al_clic_conectar)
        self._estado_vacio.accion_secundaria_pulsada.connect(self._al_clic_cargar_demostracion)
        self._apilador_estado.addWidget(self._estado_vacio)

        layout_principal.addWidget(self._apilador_estado, 1)

    # -----------------------------------------------------------------------
    # Barra de Contexto (Sección 6)
    # -----------------------------------------------------------------------

    def _crear_barra_contexto(self) -> QWidget:
        barra = QWidget(self)
        barra.setFixedHeight(56)
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Izquierda: Selector segmentado Institución | Grupo
        self._selector_ambito = SelectorSegmentado(
            opciones=[("institucion", "Institución"), ("grupo", "Grupo")],
            parent=barra,
        )
        self._selector_ambito.opcion_cambiada.connect(self._al_cambiar_ambito)
        layout.addWidget(self._selector_ambito)

        # Combo selector de grupo (oculto en modo institución)
        self._combo_grupos = QComboBox(barra)
        self._combo_grupos.setObjectName("comboGruposInicio")
        self._combo_grupos.setMinimumWidth(200)
        self._combo_grupos.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._combo_grupos.setVisible(False)
        self._combo_grupos.currentIndexChanged.connect(self._al_cambiar_grupo_combo)
        layout.addWidget(self._combo_grupos)

        layout.addStretch(1)

        # Derecha: Chip de ventana global y menú Exportar
        self._chip_ventana = ChipVentana(self._filtro_actual, parent=barra)
        self._chip_ventana.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout.addWidget(self._chip_ventana)

        self._btn_exportar = QPushButton("Exportar", barra)
        self._btn_exportar.setObjectName("btnExportarInicio")
        self._btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_exportar.setToolTip("Exportar reporte ejecutivo a PDF, datos a CSV o gráficos a PNG")
        self._btn_exportar.setAccessibleName("Exportar datos o gráficos")
        self._btn_exportar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; padding: 6px 14px; font-weight: 600; "
            f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO}; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; border-color: {COLOR_DTI}; }}"
        )
        self._menu_exportar = QMenu(self._btn_exportar)
        act_pdf = QAction("Reporte ejecutivo (PDF)…", self._menu_exportar)
        act_pdf.triggered.connect(lambda _marcado=False: self.exportar_pdf())
        self._menu_exportar.addAction(act_pdf)

        act_png = QAction("Lámina del panorama (PNG)…", self._menu_exportar)
        act_png.triggered.connect(lambda _marcado=False: self.exportar_png())
        self._menu_exportar.addAction(act_png)

        act_png_ind = QAction("Gráficos por separado (PNG)…", self._menu_exportar)
        act_png_ind.triggered.connect(lambda _marcado=False: self.exportar_png_individuales())
        self._menu_exportar.addAction(act_png_ind)

        act_csv = QAction("Datos del panorama (CSV)…", self._menu_exportar)
        act_csv.triggered.connect(lambda _marcado=False: self.exportar_csv())
        self._menu_exportar.addAction(act_csv)

        self._btn_exportar.setMenu(self._menu_exportar)
        layout.addWidget(self._btn_exportar)

        return barra

    # -----------------------------------------------------------------------
    # Tarjeta 1: Ámbito (Avatar, Datos, Detalles y 6 Fichas KPI)
    # -----------------------------------------------------------------------

    def _crear_tarjeta_ambito(self) -> None:
        self._tarjeta_ambito = Tarjeta(titulo=None, con_sombra=True, parent=self._widget_rejilla)
        layout = self._tarjeta_ambito.layout_contenido
        layout.setSpacing(10)

        # Bloque central superior: Avatar 112 px + Título + Subtítulo
        zona_avatar = QWidget(self._tarjeta_ambito)
        layout_av = QVBoxLayout(zona_avatar)
        layout_av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_av.setContentsMargins(0, 4, 0, 4)
        layout_av.setSpacing(6)

        self._avatar_ambito = Avatar(diametro=112, con_anillo=True, parent=zona_avatar)
        layout_av.addWidget(self._avatar_ambito, 0, Qt.AlignmentFlag.AlignCenter)

        self._lbl_titulo_ambito = QLabel("Universidad Popular del Cesar", zona_avatar)
        self._lbl_titulo_ambito.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_titulo_ambito.setStyleSheet(
            f"font-size: {TAMANO_SUBTITULO}pt; font-weight: bold; color: {TEXTO};"
        )
        layout_av.addWidget(self._lbl_titulo_ambito)

        self._lbl_lineas_ambito = QLabel("Grupos de investigación: —", zona_avatar)
        self._lbl_lineas_ambito.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_lineas_ambito.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};"
        )
        layout_av.addWidget(self._lbl_lineas_ambito)

        # Botón «Ver más detalles v»
        self._btn_detalles = QPushButton("Ver más detalles v", zona_avatar)
        self._btn_detalles.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_detalles.setToolTip("Ver más detalles institucionales o del grupo")
        self._btn_detalles.setAccessibleName("Ver más detalles")
        self._btn_detalles.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {COLOR_DTI}; "
            f"font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt; padding: 2px 8px; }}"
            f"QPushButton:hover {{ text-decoration: underline; }}"
        )
        self._btn_detalles.clicked.connect(self._alternar_detalles)
        layout_av.addWidget(self._btn_detalles, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(zona_avatar)

        # Panel desplegable de detalles
        self._panel_detalles = QFrame(self._tarjeta_ambito)
        self._panel_detalles.setStyleSheet(
            f"QFrame {{ background-color: {FICHA}; border-radius: {estilo.RADIO_BOTON}px; padding: 6px; }}"
        )
        self._layout_detalles = QVBoxLayout(self._panel_detalles)
        self._layout_detalles.setContentsMargins(10, 6, 10, 6)
        self._layout_detalles.setSpacing(3)
        self._panel_detalles.setVisible(False)
        layout.addWidget(self._panel_detalles)

        # Cuadrícula 2×3 de 6 Fichas KPI
        self._grid_kpi = QGridLayout()
        self._grid_kpi.setSpacing(8)

        self._kpi_1 = FichaKPI("Grupos activos", "0", "Total registrados", parent=self._tarjeta_ambito)
        self._kpi_2 = FichaKPI("Investigadores activos", "0", "Total registrados", parent=self._tarjeta_ambito)
        self._kpi_3 = FichaKPI("Productos (ventana)", "0", "En período", con_minigrafico=True, parent=self._tarjeta_ambito)
        self._kpi_4 = FichaKPI("Promedio por investigador", "0,00", "Productos / inv.", parent=self._tarjeta_ambito)
        self._kpi_5 = FichaKPI("Productos avalados", "0", "Con aval institucional", parent=self._tarjeta_ambito)
        self._kpi_6 = FichaKPI("Productos históricos", "0", "Total acumulado", parent=self._tarjeta_ambito)

        self._grid_kpi.addWidget(self._kpi_1, 0, 0)
        self._grid_kpi.addWidget(self._kpi_2, 0, 1)
        self._grid_kpi.addWidget(self._kpi_3, 1, 0)
        self._grid_kpi.addWidget(self._kpi_4, 1, 1)
        self._grid_kpi.addWidget(self._kpi_5, 2, 0)
        self._grid_kpi.addWidget(self._kpi_6, 2, 1)

        layout.addLayout(self._grid_kpi)

    def _alternar_detalles(self) -> None:
        visible = not self._panel_detalles.isVisible()
        self._panel_detalles.setVisible(visible)
        self._btn_detalles.setText("Ocultar detalles ^" if visible else "Ver más detalles v")
        self._btn_detalles.setToolTip("Ocultar detalles institucionales o del grupo" if visible else "Ver más detalles")
        self._btn_detalles.setAccessibleName("Ocultar detalles" if visible else "Ver más detalles")

    # -----------------------------------------------------------------------
    # Tarjeta 2: Producción por Año y Tipología (Barras Apiladas)
    # -----------------------------------------------------------------------

    def _crear_tarjeta_barras(self) -> None:
        self._tarjeta_barras = Tarjeta(
            titulo="Producción por año y tipología",
            con_sombra=True,
            parent=self._widget_rejilla,
        )
        self._grafico_barras = GraficoBarrasApiladas(
            titulo="",
            subtitulo="Evolución histórica según el Modelo Minciencias",
            parent=self._tarjeta_barras,
        )
        self._tarjeta_barras.agregar_widget(self._grafico_barras)

    # -----------------------------------------------------------------------
    # Tarjeta 3: Tipología de Productos (Dona Doble)
    # -----------------------------------------------------------------------

    def _crear_tarjeta_dona(self) -> None:
        self._tarjeta_dona = Tarjeta(
            titulo="Tipología de productos",
            con_sombra=True,
            parent=self._widget_rejilla,
        )
        self._grafico_dona = GraficoDonaDoble(
            titulo="",
            subtitulo="Distribución por tipología y validación",
            parent=self._tarjeta_dona,
        )
        self._grafico_dona.setMinimumHeight(260)
        self._tarjeta_dona.agregar_widget(self._grafico_dona)

    # -----------------------------------------------------------------------
    # Tarjeta 4: Red de Colaboración (Mini Red)
    # -----------------------------------------------------------------------

    def _crear_tarjeta_red(self) -> None:
        self._tarjeta_red = Tarjeta(
            titulo="Red de colaboración",
            con_sombra=True,
            parent=self._widget_rejilla,
        )

        btn_abrir = QPushButton("Ver red", self._tarjeta_red)
        btn_abrir.setIcon(cargar_icono("redes.svg", 16))
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir.setToolTip("Abrir análisis completo de la red de colaboración")
        btn_abrir.setAccessibleName("Abrir análisis de redes completo")
        btn_abrir.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {COLOR_DTI}; "
            f"font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt; padding: 0 4px; }}"
            f"QPushButton:hover {{ text-decoration: underline; }}"
        )
        btn_abrir.clicked.connect(self._al_abrir_red_completa)
        self._tarjeta_red.agregar_accion(btn_abrir)

        self._mini_red = MiniRed(
            titulo="",
            subtitulo="Principales coautorías entre investigadores",
            parent=self._tarjeta_red,
        )
        self._mini_red.setMinimumHeight(260)
        self._mini_red.abrir_analisis_completo.connect(self._al_abrir_red_completa)
        self._mini_red.nodo_pulsado.connect(self._al_pulsar_nodo_mini_red)
        self._tarjeta_red.agregar_widget(self._mini_red)

    def _crear_tarjeta_histograma(self) -> None:
        self._tarjeta_histograma = Tarjeta(
            titulo="Distribución de productos por investigador",
            con_sombra=True,
            parent=self._widget_rejilla,
        )
        self._grafico_histograma = GraficoHistograma(
            titulo="",
            subtitulo="Investigadores según cantidad de productos",
            unidad="investigador",
            parent=self._tarjeta_histograma,
        )
        self._grafico_histograma.setMinimumHeight(250)
        self._tarjeta_histograma.agregar_widget(self._grafico_histograma)

    def _al_abrir_red_completa(self) -> None:
        # Pestaña 4: Pantalla.REDES
        self.solicitar_navegacion.emit(4)

    def _al_pulsar_nodo_mini_red(self, codigo_investigador: str) -> None:
        self.ver_red_nodo_solicitado.emit(codigo_investigador)

    # -----------------------------------------------------------------------
    # Segunda Fila: Rankings (Top 5)
    # -----------------------------------------------------------------------

    def _crear_tarjetas_rankings(self) -> None:
        self._tarjeta_ranking_1 = Tarjeta(
            titulo="Investigadores más productivos",
            con_sombra=True,
            parent=self._widget_rejilla,
        )
        self._layout_ranking_1 = QVBoxLayout()
        self._layout_ranking_1.setContentsMargins(0, 0, 0, 0)
        self._layout_ranking_1.setSpacing(4)
        self._tarjeta_ranking_1.layout_contenido.addLayout(self._layout_ranking_1)

        self._tarjeta_ranking_2 = Tarjeta(
            titulo="Grupos más productivos",
            con_sombra=True,
            parent=self._widget_rejilla,
        )
        self._layout_ranking_2 = QVBoxLayout()
        self._layout_ranking_2.setContentsMargins(0, 0, 0, 0)
        self._layout_ranking_2.setSpacing(4)
        self._tarjeta_ranking_2.layout_contenido.addLayout(self._layout_ranking_2)

    # -----------------------------------------------------------------------
    # Responsividad de Rejilla (≥ 1360 px vs < 1360 px)
    # -----------------------------------------------------------------------

    def _reorganizar_rejilla(self, ancho: int) -> None:
        es_cuatro_columnas = ancho >= 1500
        if self._es_cuatro_columnas == es_cuatro_columnas:
            return
        self._es_cuatro_columnas = es_cuatro_columnas

        for w in (
            self._tarjeta_ambito,
            self._tarjeta_barras,
            self._tarjeta_dona,
            self._tarjeta_red,
            self._tarjeta_histograma,
            self._tarjeta_ranking_1,
            self._tarjeta_ranking_2,
        ):
            self._layout_rejilla.removeWidget(w)

        if es_cuatro_columnas:
            # Fila 0: 4 columnas (11 : 13 : 12 : 13)
            self._layout_rejilla.addWidget(self._tarjeta_ambito, 0, 0)
            self._layout_rejilla.addWidget(self._tarjeta_barras, 0, 1)
            self._layout_rejilla.addWidget(self._tarjeta_dona, 0, 2)
            self._layout_rejilla.addWidget(self._tarjeta_red, 0, 3)

            # Fila 1: 2 rankings anchos
            self._layout_rejilla.addWidget(self._tarjeta_ranking_1, 1, 0, 1, 2)
            self._layout_rejilla.addWidget(self._tarjeta_ranking_2, 1, 2, 1, 2)
            self._layout_rejilla.addWidget(self._tarjeta_histograma, 2, 0, 1, 4)

            self._layout_rejilla.setColumnStretch(0, 11)
            self._layout_rejilla.setColumnStretch(1, 13)
            self._layout_rejilla.setColumnStretch(2, 12)
            self._layout_rejilla.setColumnStretch(3, 13)
        else:
            # Rejilla 2×2 arriba y fila 2 rankings
            self._layout_rejilla.addWidget(self._tarjeta_ambito, 0, 0)
            self._layout_rejilla.addWidget(self._tarjeta_barras, 0, 1)
            self._layout_rejilla.addWidget(self._tarjeta_dona, 1, 0)
            self._layout_rejilla.addWidget(self._tarjeta_red, 1, 1)

            self._layout_rejilla.addWidget(self._tarjeta_ranking_1, 2, 0)
            self._layout_rejilla.addWidget(self._tarjeta_ranking_2, 2, 1)
            self._layout_rejilla.addWidget(self._tarjeta_histograma, 3, 0, 1, 2)

            self._layout_rejilla.setColumnStretch(0, 1)
            self._layout_rejilla.setColumnStretch(1, 1)
            self._layout_rejilla.setColumnStretch(2, 0)
            self._layout_rejilla.setColumnStretch(3, 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reorganizar_rejilla(self.width())
        self._combo_grupos.setMinimumWidth(200 if self.width() < 1240 else 280)

    # -----------------------------------------------------------------------
    # Refresco y Carga de Datos
    # -----------------------------------------------------------------------

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Actualiza el filtro global y recarga los datos."""
        self._filtro_actual = filtro
        self._chip_ventana.establecer_filtro(filtro)
        self.refrescar()

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self._filtro_actual = filtro
        self.filtro_cambiado.emit(filtro)
        self.refrescar()

    def _al_cambiar_ambito(self, clave: str) -> None:
        self._modo_ambito = clave
        es_grupo = clave == "grupo"
        self._combo_grupos.setVisible(es_grupo)
        if es_grupo:
            self._poblar_combo_grupos()
        self.refrescar()

    def _poblar_combo_grupos(self) -> None:
        self._combo_grupos.blockSignals(True)
        self._combo_grupos.clear()
        opciones = self._servicio.opciones_grupos()
        for cod, nom in opciones:
            self._combo_grupos.addItem(nom, cod)
        self._combo_grupos.blockSignals(False)

        if self._combo_grupos.count() > 0:
            self._codigo_grupo_seleccionado = self._combo_grupos.currentData()

    def _al_cambiar_grupo_combo(self, index: int) -> None:
        if index >= 0:
            self._codigo_grupo_seleccionado = self._combo_grupos.currentData()
            self.refrescar()

    def refrescar(self) -> None:
        """Carga y aplica los datos del servicio para el ámbito y filtro activos."""
        try:
            resumen_inst = self._servicio.resumen_general(self._filtro_actual)
            hay_datos = bool(resumen_inst.get("hay_datos", False))

            if not hay_datos:
                self._apilador_estado.setCurrentIndex(2)  # Estado vacío
                return

            self._apilador_estado.setCurrentIndex(1)  # Contenido

            if self._modo_ambito == "institucion":
                self._actualizar_modo_institucion(resumen_inst)
            else:
                self._actualizar_modo_grupo(resumen_inst)

        except Exception as err:
            GestorAvisos.mostrar_desde(self, f"Error cargando inicio: {err}", tipo="error", titulo="Inicio")

    # -----------------------------------------------------------------------
    # Modo Institución
    # -----------------------------------------------------------------------

    def _actualizar_modo_institucion(self, resumen: dict[str, Any]) -> None:
        # 1. Ámbito
        pix_upc = cargar_pixmap("logo_upc.png", 96, 96)
        self._avatar_ambito.establecer_nombre("Universidad Popular del Cesar")
        self._avatar_ambito.establecer_pixmap(pix_upc)
        self._lbl_titulo_ambito.setText("Universidad Popular del Cesar")
        grupos_tot = resumen.get("grupos_totales", 0)
        self._lbl_lineas_ambito.setText(f"Grupos de investigación: {grupos_tot}")

        # Detalles
        self._limpiar_layout(self._layout_detalles)
        g_act = resumen.get("grupos_activos", 0)
        inv_act = resumen.get("investigadores_activos", 0)
        inv_tot = resumen.get("investigadores_totales", 0)
        desc_f = self._servicio.descripcion_filtro(self._filtro_actual)
        for k, v in [
            ("Grupos activos:", f"{g_act} de {grupos_tot}"),
            ("Investigadores activos:", f"{inv_act} de {inv_tot}"),
            ("Ventana de análisis:", desc_f),
        ]:
            fila = QHBoxLayout()
            l1 = QLabel(k, self._panel_detalles)
            l1.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; font-weight: 600;")
            l2 = QLabel(v, self._panel_detalles)
            l2.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO};")
            fila.addWidget(l1)
            fila.addWidget(l2)
            fila.addStretch()
            self._layout_detalles.addLayout(fila)

        # 6 Fichas KPI
        prod_tot = resumen.get("total_productos", 0)
        hist_tot = resumen.get("productos_totales", 0)
        prom = resumen.get("promedio_por_investigador", 0.0)
        prod_por_anio = resumen.get("productos_por_anio", {})
        tendencia = [prod_por_anio[a] for a in sorted(prod_por_anio.keys())]

        val_map = resumen.get("productos_por_validacion", {})
        avalados = val_map.get("Avalado", 0)

        self._kpi_1.actualizar(g_act, f"{grupos_tot} registrados")
        self._kpi_1.lbl_titulo.setText("Grupos activos")

        self._kpi_2.actualizar(inv_act, f"{inv_tot} registrados")
        self._kpi_2.lbl_titulo.setText("Investigadores activos")

        self._kpi_3.actualizar(prod_tot, "En período", tendencia=tendencia)
        self._kpi_3.lbl_titulo.setText("Productos (ventana)")

        self._kpi_4.actualizar(prom, "Productos / inv.")
        self._kpi_4.lbl_titulo.setText("Promedio por investigador")

        self._kpi_5.actualizar(avalados, "Con aval institucional")
        self._kpi_5.lbl_titulo.setText("Productos avalados")

        self._kpi_6.actualizar(hist_tot, "Total histórico")
        self._kpi_6.lbl_titulo.setText("Productos históricos")

        # 2. Barras apiladas
        serie = self._servicio.serie_anual_por_categoria(self._filtro_actual)
        self._grafico_barras.establecer_datos(serie)
        self._grafico_histograma.establecer_datos(
            resumen.get("distribucion_productos_por_investigador", {})
        )

        # 3. Dona doble
        tip_map = resumen.get("productos_por_categoria", {})
        self._grafico_dona.establecer_datos(tip_map, val_map)

        # 4. Mini red
        red = self._servicio.red_coautoria(self._filtro_actual)
        self._mini_red.establecer_datos(red.get("nodos", []), red.get("aristas", []))

        # 5. Rankings
        self._tarjeta_ranking_1.establecer_titulo("Investigadores más productivos")
        self._limpiar_layout(self._layout_ranking_1)
        top_inv = resumen.get("top_investigadores")
        if top_inv and hasattr(top_inv, "filas") and top_inv.filas:
            max_v = max(f[2] for f in top_inv.filas)
            for i, f in enumerate(top_inv.filas[:5], start=1):
                fila_w = FilaRanking(i, f[1], "", f[2], max_v, parent=self._tarjeta_ranking_1)
                self._layout_ranking_1.addWidget(fila_w)
        else:
            lbl_vac = QLabel("Sin datos de investigadores en el período", self._tarjeta_ranking_1)
            lbl_vac.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; padding: 12px;")
            self._layout_ranking_1.addWidget(lbl_vac)

        self._tarjeta_ranking_2.establecer_titulo("Grupos más productivos")
        self._limpiar_layout(self._layout_ranking_2)
        top_grp = resumen.get("top_grupos")
        if top_grp and hasattr(top_grp, "filas") and top_grp.filas:
            max_v = max(f[2] for f in top_grp.filas)
            for i, f in enumerate(top_grp.filas[:5], start=1):
                fila_w = FilaRanking(i, f[1], "", f[2], max_v, parent=self._tarjeta_ranking_2)
                self._layout_ranking_2.addWidget(fila_w)
        else:
            lbl_vac = QLabel("Sin datos de grupos en el período", self._tarjeta_ranking_2)
            lbl_vac.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; padding: 12px;")
            self._layout_ranking_2.addWidget(lbl_vac)

    # -----------------------------------------------------------------------
    # Modo Grupo
    # -----------------------------------------------------------------------

    def _actualizar_modo_grupo(self, resumen_global: dict[str, Any]) -> None:
        if not self._codigo_grupo_seleccionado:
            return

        cod = self._codigo_grupo_seleccionado
        vg = self._servicio.vista_grupo(cod, self._filtro_actual)
        dg = self._servicio.datos_grupo(cod)

        nombre = vg.get("nombre", "Grupo")
        cat = vg.get("categoria", "Sin categoría")

        # 1. Ámbito
        self._avatar_ambito.establecer_pixmap(None)
        self._avatar_ambito.establecer_nombre(nombre)
        self._lbl_titulo_ambito.setText(f"Grupo de Investigación – {nombre}")
        self._lbl_lineas_ambito.setText(f"Código: {cod} · Categoría: {cat}")

        # Detalles
        self._limpiar_layout(self._layout_detalles)
        detalles_items = [
            ("Líder:", dg.get("lider")),
            ("Institución:", dg.get("institucion_principal")),
            ("Área OCDE:", dg.get("area_ocde") or dg.get("gran_area_ocde")),
            ("Ubicación:", dg.get("departamento_ciudad")),
            ("Creación:", str(dg.get("fecha_creacion")) if dg.get("fecha_creacion") else None),
        ]
        for k, v in detalles_items:
            if v:
                fila = QHBoxLayout()
                l1 = QLabel(k, self._panel_detalles)
                l1.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; font-weight: 600;")
                l2 = QLabel(str(v), self._panel_detalles)
                l2.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO};")
                fila.addWidget(l1)
                fila.addWidget(l2)
                fila.addStretch()
                self._layout_detalles.addLayout(fila)

        # 6 Fichas KPI
        integrantes_tabla = vg.get("integrantes")
        n_integrantes = len(integrantes_tabla.filas) if integrantes_tabla else 0
        estudiantes = vg.get("estudiantes", 0)
        prod_tot = vg.get("total_productos", 0)
        avalados = vg.get("productos_avalados", 0)
        prom = vg.get("promedio_por_investigador", 0.0)
        pct_inst = vg.get("porcentaje_sobre_institucion", 0.0)

        prod_por_anio = vg.get("productos_por_anio", {})
        tendencia = [prod_por_anio[a] for a in sorted(prod_por_anio.keys())]

        self._kpi_1.actualizar(n_integrantes, "Integrantes vinculados")
        self._kpi_1.lbl_titulo.setText("Integrantes")

        self._kpi_2.actualizar(estudiantes, "Rol estudiante")
        self._kpi_2.lbl_titulo.setText("Estudiantes")

        self._kpi_3.actualizar(prod_tot, "En período", tendencia=tendencia)
        self._kpi_3.lbl_titulo.setText("Productos (ventana)")

        self._kpi_4.actualizar(avalados, "Con aval institucional")
        self._kpi_4.lbl_titulo.setText("Productos avalados")

        self._kpi_5.actualizar(prom, "Productos / integrante")
        self._kpi_5.lbl_titulo.setText("Promedio por integrante")

        self._kpi_6.actualizar(f"{formatear_porcentaje(pct_inst)}", "Aporte institucional")
        self._kpi_6.lbl_titulo.setText("Aporte a la institución")

        # 2. Barras apiladas
        serie = self._servicio.serie_anual_por_categoria(self._filtro_actual, codigo_grupo=cod)
        self._grafico_barras.establecer_datos(serie)
        self._grafico_histograma.establecer_datos(
            vg.get("distribucion_productos_por_investigador", {})
        )

        # 3. Dona doble
        tip_map = vg.get("productos_por_categoria", {})
        val_map = vg.get("productos_por_validacion", {})
        self._grafico_dona.establecer_datos(tip_map, val_map)

        # 4. Mini red
        red = self._servicio.red_coautoria(self._filtro_actual, codigo_grupo=cod)
        self._mini_red.establecer_datos(red.get("nodos", []), red.get("aristas", []))

        # 5. Rankings modo grupo
        self._tarjeta_ranking_1.establecer_titulo("Integrantes con más productos")
        self._limpiar_layout(self._layout_ranking_1)
        if integrantes_tabla and integrantes_tabla.filas:
            max_v = max(f[3] for f in integrantes_tabla.filas)
            for i, f in enumerate(integrantes_tabla.filas[:5], start=1):
                # (codigo, nombre, rol, productos)
                sub = f[2] if f[2] else ""
                fila_w = FilaRanking(i, f[1], sub, f[3], max_v, parent=self._tarjeta_ranking_1)
                self._layout_ranking_1.addWidget(fila_w)
        else:
            lbl_vac = QLabel("Sin integrantes registrados", self._tarjeta_ranking_1)
            lbl_vac.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; padding: 12px;")
            self._layout_ranking_1.addWidget(lbl_vac)

        self._tarjeta_ranking_2.establecer_titulo("Últimos productos del grupo")
        self._limpiar_layout(self._layout_ranking_2)
        prods_tabla = vg.get("productos")
        if prods_tabla and prods_tabla.filas:
            for i, p in enumerate(prods_tabla.filas[:5], start=1):
                # columnas: ('Código', 'Título', 'Tipología', 'Subtipo', 'Año', 'Validación', ...)
                sub = f"{p[2]} · {p[4]} · {p[5]}"
                fila_w = FilaRanking(i, p[1], sub, int(p[4]), 2030, etiqueta_valor="año", parent=self._tarjeta_ranking_2)
                self._layout_ranking_2.addWidget(fila_w)
        else:
            lbl_vac = QLabel("Sin productos registrados", self._tarjeta_ranking_2)
            lbl_vac.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; padding: 12px;")
            self._layout_ranking_2.addWidget(lbl_vac)

    def _limpiar_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            elif item.layout() is not None:
                sub_l = item.layout()
                while sub_l.count():
                    sub_item = sub_l.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

    # -----------------------------------------------------------------------
    # Acciones de Estado Vacío
    # -----------------------------------------------------------------------

    def _al_clic_conectar(self) -> None:
        if self._estado_vacio.btn_principal is not None:
            self._estado_vacio.btn_principal.setEnabled(False)
        if self._estado_vacio.btn_secundario is not None:
            self._estado_vacio.btn_secundario.setEnabled(False)
        self._apilador_estado.setCurrentIndex(0)

        def trabajo() -> Any:
            return self._servicio.conectar()

        def exito(est: Any) -> None:
            if self._estado_vacio.btn_principal is not None:
                self._estado_vacio.btn_principal.setEnabled(True)
            if self._estado_vacio.btn_secundario is not None:
                self._estado_vacio.btn_secundario.setEnabled(True)
            self.refrescar()
            self.datos_modificados.emit()
            GestorAvisos.mostrar_desde(
                self,
                f"Datos cargados desde Supabase (revisión {est.revision_local}).",
                tipo="exito",
                titulo="Base de datos",
            )

        def fallo(err: Exception, detalle: str) -> None:
            if self._estado_vacio.btn_principal is not None:
                self._estado_vacio.btn_principal.setEnabled(True)
            if self._estado_vacio.btn_secundario is not None:
                self._estado_vacio.btn_secundario.setEnabled(True)
            self.refrescar()
            GestorAvisos.mostrar_desde(
                self,
                f"No se pudo conectar automáticamente: {err}",
                tipo="error",
                titulo="Error de conexión",
            )

        if self._ejecutor is not None:
            self._ejecutor.ejecutar(trabajo, al_terminar=exito, al_fallar=fallo)
        else:
            try:
                est = trabajo()
                exito(est)
            except Exception as err:
                fallo(err, str(err))

    def _al_clic_cargar_demostracion(self) -> None:
        try:
            self._servicio.cargar_demostracion()
            GestorAvisos.mostrar_desde(
                self, "Datos de demostración cargados exitosamente.", tipo="exito", titulo="Demostración"
            )
            self.refrescar()
            self.datos_modificados.emit()
        except Exception as err:
            GestorAvisos.mostrar_desde(self, str(err), tipo="error", titulo="Error de datos")

    # -----------------------------------------------------------------------
    # Exportaciones (PDF, PNG y CSV)
    # -----------------------------------------------------------------------

    def _serie_anual_exportable(self) -> list[tuple[Any, ...]]:
        """Serie anual por tipología del ámbito actual, lista para tablas de PDF y CSV."""
        if self._modo_ambito == "institucion":
            serie = self._servicio.serie_anual_por_categoria(self._filtro_actual)
        else:
            serie = self._servicio.serie_anual_por_categoria(
                self._filtro_actual, codigo_grupo=self._codigo_grupo_seleccionado
            )
        filas: list[tuple[Any, ...]] = []
        for anio in sorted(serie.keys()):
            d = serie[anio]
            filas.append((anio, d.get("GNC", 0), d.get("DTI", 0), d.get("ASC", 0), d.get("FRH", 0), sum(d.values())))
        return filas

    def _nombre_base_exportacion(self, tema: str) -> str:
        """Nombre sugerido coherente con el ámbito, el grupo y la ventana temporal activa."""
        ambito = "institucion" if self._modo_ambito == "institucion" else f"grupo_{self._codigo_grupo_seleccionado or ''}"
        return f"pea_{tema}_{ambito}_{self._filtro_actual.modo.value}"

    def exportar_pdf(self, ruta_destino: str | Path | None = None) -> None:
        """Exporta un reporte ejecutivo completo del panorama estadístico a PDF."""
        ruta = resolver_archivo_destino(
            self,
            ruta_destino,
            titulo="Guardar reporte ejecutivo (PDF)",
            nombre_base=self._nombre_base_exportacion("reporte"),
            filtro=FILTRO_PDF,
            extension=".pdf",
        )
        if ruta is None:
            return

        try:
            desc_f = self._servicio.descripcion_filtro(self._filtro_actual)
            kpis = [
                (self._kpi_1.lbl_titulo.text(), self._kpi_1.lbl_valor.text()),
                (self._kpi_2.lbl_titulo.text(), self._kpi_2.lbl_valor.text()),
                (self._kpi_3.lbl_titulo.text(), self._kpi_3.lbl_valor.text()),
                (self._kpi_4.lbl_titulo.text(), self._kpi_4.lbl_valor.text()),
                (self._kpi_5.lbl_titulo.text(), self._kpi_5.lbl_valor.text()),
                (self._kpi_6.lbl_titulo.text(), self._kpi_6.lbl_valor.text()),
            ]
            imagenes = [
                ("Producción anual por tipología (GNC · DTI · ASC · FRH)", renderizar_widget_imagen(self._grafico_barras)),
                ("Distribución por tipología y validación", renderizar_widget_imagen(self._grafico_dona)),
                ("Vista sintética de la red de coautoría", renderizar_widget_imagen(self._mini_red)),
                (
                    "Distribución de productos por investigador",
                    renderizar_widget_imagen(self._grafico_histograma),
                ),
            ]
            titulo_rep = (
                "Panorama Estadístico Institucional"
                if self._modo_ambito == "institucion"
                else f"Panorama de Grupo · {self._lbl_titulo_ambito.text()}"
            )
            ambito_txt = "Institución" if self._modo_ambito == "institucion" else "Grupo de investigación"
            exportar_reporte_pdf(
                ruta,
                titulo=titulo_rep,
                subtitulo=f"Universidad Popular del Cesar · {self._lbl_lineas_ambito.text()}",
                metadatos=[
                    ("Ámbito", ambito_txt),
                    ("Filtro temporal", desc_f),
                ],
                kpis=kpis,
                imagenes=imagenes,
                columnas_tabla=["Año", "GNC", "DTI", "ASC", "FRH", "Total anual"],
                filas_tabla=self._serie_anual_exportable(),
                nota_pie="Cálculos obtenidos en memoria desde el Hipercubo 4D y la Multilista de Productos.",
            )
            GestorAvisos.mostrar_desde(
                self,
                f"Reporte guardado: {describir_ubicacion(ruta)}.",
                tipo="exito",
                titulo="Exportación PDF",
            )
        except Exception as err:
            GestorAvisos.mostrar_desde(self, mensaje_error(err, ruta), tipo="error", titulo="No se pudo exportar el PDF")

    def exportar_csv(self, ruta_destino: str | Path | None = None) -> None:
        """Exporta un resumen tabular detallado a formato CSV con metadatos ejecutivos."""
        ruta = resolver_archivo_destino(
            self,
            ruta_destino,
            titulo="Guardar datos del panorama (CSV)",
            nombre_base=self._nombre_base_exportacion("resumen"),
            filtro=FILTRO_CSV,
            extension=".csv",
        )
        if ruta is None:
            return

        try:
            desc_f = self._servicio.descripcion_filtro(self._filtro_actual)
            if self._modo_ambito == "institucion":
                res = self._servicio.resumen_general(self._filtro_actual)
                metadatos = [
                    ("Ámbito", "Institución · Universidad Popular del Cesar"),
                    ("Filtro temporal", desc_f),
                    ("Grupos activos", str(res.get("grupos_activos", 0))),
                    ("Investigadores activos", str(res.get("investigadores_activos", 0))),
                    ("Total productos en período", str(res.get("total_productos", 0))),
                    ("Promedio por investigador", formatear_decimal(res.get("promedio_por_investigador", 0.0))),
                ]
            else:
                cod = self._codigo_grupo_seleccionado or ""
                vg = self._servicio.vista_grupo(cod, self._filtro_actual)
                metadatos = [
                    ("Ámbito", f"Grupo · {vg.get('nombre', '')}"),
                    ("Código GrupLAC", cod),
                    ("Categoría", str(vg.get("categoria", ""))),
                    ("Líder", str(vg.get("lider", ""))),
                    ("Filtro temporal", desc_f),
                    ("Total productos", str(vg.get("total_productos", 0))),
                    ("Productos avalados", str(vg.get("productos_avalados", 0))),
                ]

            guardar_csv_profesional(
                ruta,
                titulo=f"Resumen estadístico ({self._modo_ambito})",
                metadatos=metadatos,
                columnas=["Año", "GNC", "DTI", "ASC", "FRH", "Total"],
                filas=self._serie_anual_exportable(),
            )
            GestorAvisos.mostrar_desde(
                self,
                f"Datos guardados: {describir_ubicacion(ruta)}.",
                tipo="exito",
                titulo="Exportación CSV",
            )
        except Exception as err:
            GestorAvisos.mostrar_desde(self, mensaje_error(err, ruta), tipo="error", titulo="No se pudo exportar el CSV")

    def exportar_png(self, ruta_destino: str | Path | None = None) -> None:
        """Exporta las gráficas principales como una lámina PNG institucional."""
        ruta = resolver_archivo_destino(
            self,
            ruta_destino,
            titulo="Guardar lámina del panorama (PNG)",
            nombre_base=self._nombre_base_exportacion("panel"),
            filtro=FILTRO_PNG,
            extension=".png",
        )
        if ruta is None:
            return

        try:
            desc_f = self._servicio.descripcion_filtro(self._filtro_actual)
            exportar_png_institucional(
                ruta,
                titulo=f"Panorama Estadístico · {self._lbl_titulo_ambito.text()}",
                subtitulo=f"Filtro temporal: {desc_f}",
                imagenes=[
                    ("Producción anual por tipología", renderizar_widget_imagen(self._grafico_barras)),
                    ("Distribución por tipología y validación", renderizar_widget_imagen(self._grafico_dona)),
                    ("Red sintética de coautoría", renderizar_widget_imagen(self._mini_red)),
                    (
                        "Distribución de productos por investigador",
                        renderizar_widget_imagen(self._grafico_histograma),
                    ),
                ],
            )
            GestorAvisos.mostrar_desde(
                self,
                f"Lámina guardada: {describir_ubicacion(ruta)}.",
                tipo="exito",
                titulo="Exportación PNG",
            )
        except Exception as err:
            GestorAvisos.mostrar_desde(self, mensaje_error(err, ruta), tipo="error", titulo="No se pudo exportar el PNG")

    def exportar_png_individuales(self, directorio_destino: str | Path | None = None) -> None:
        """Exporta cada gráfico como un PNG independiente dentro de la carpeta que elija el usuario."""
        carpeta = resolver_carpeta_destino(
            self,
            directorio_destino,
            titulo="Elegir la carpeta donde guardar los gráficos (PNG)",
        )
        if carpeta is None:
            return

        prefijo = nombre_archivo_seguro(self._nombre_base_exportacion("grafico"), ".png").removesuffix(".png")
        try:
            desc_f = self._servicio.descripcion_filtro(self._filtro_actual)
            ambito = self._lbl_titulo_ambito.text()
            piezas = (
                (
                    "barras",
                    "Producción anual por tipología (GNC · DTI · ASC · FRH)",
                    "Evolución anual por gran categoría Minciencias",
                    self._grafico_barras,
                ),
                (
                    "dona",
                    "Distribución por tipología y validación",
                    "Anillo exterior: Tipología · Anillo interior: Validación",
                    self._grafico_dona,
                ),
                (
                    "red",
                    "Red sintética de coautoría científica",
                    "Subgrafo principal de colaboración",
                    self._mini_red,
                ),
                (
                    "histograma",
                    "Distribución de productos por investigador",
                    "Investigadores según cantidad de productos",
                    self._grafico_histograma,
                ),
            )
            for sufijo, titulo, leyenda, widget in piezas:
                exportar_png_institucional(
                    carpeta / f"{prefijo}_{sufijo}.png",
                    titulo=titulo,
                    subtitulo=f"{ambito} · Filtro: {desc_f}",
                    imagenes=[(leyenda, renderizar_widget_imagen(widget))],
                )
            GestorAvisos.mostrar_desde(
                self,
                f"Se guardaron {len(piezas)} gráficos PNG en la carpeta «{carpeta.name or carpeta}».",
                tipo="exito",
                titulo="Exportación PNG",
            )
        except Exception as err:
            GestorAvisos.mostrar_desde(
                self, mensaje_error(err, carpeta), tipo="error", titulo="No se pudieron exportar los gráficos"
            )
