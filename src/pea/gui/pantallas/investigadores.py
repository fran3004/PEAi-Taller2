"""Pantalla de Directorio de Investigadores (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.2).
Referencia visual: brain/_adjuntos/ref-investigadores.png.
- Barra de contexto: título, ChipVentana y menú Exportar ▾.
- Directorio de Investigadores:
  * Cabecera con búsqueda (Ctrl+F, debounce 250 ms), combos Grupo, Categoría y Estado (Activos/Todos),
    y botón primario «+ Nuevo investigador».
  * Tabla con filas de 48 px, hover #F3F7FB, selección #E3EEF7 con barra de acento de 3 px,
    encabezado FICHA en 10 pt negrita, ordenación insensible a mayúsculas y numérica en productos.
  * Columnas: Nombre (avatar 28 px + nombre), Grupo(s), Categoría (píldora), Formación,
    Productos (alineado a derecha) y Código CvLAC (enlace copiable con toast).
  * Inactivos renderizados con 60 % de opacidad y píldora «Inactivo».
  * Pie de tabla con conteo dinámico «Mostrando N de M».
- Ficha lateral de 360 px:
  * Avatar de 96 px con iniciales y degradado determinista.
  * Nombre (16 pt negrita) y subtítulo «GRUPO · Categoría».
  * Cuadrícula 2×2 de FichaKPI: Productos (ventana), Grupos (membresías), Coautores y Años con producción.
  * Minigráfico de Producción anual (GraficoSerieAnual).
  * Barras de tipología (GNC, DTI, ASC, FRH) con porcentajes y barras proporcionales.
  * Botones de acción: Editar, Activar/Desactivar, Eliminar… (muestra describir_cascada),
    Ver ficha completa (diálogo con pestañas de Aportes, Membresías y Productos) y Ver productos.
- Notificaciones breves mediante Toast (GestorAvisos).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QRectF,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QKeySequence,
    QPainter,
    QPaintEvent,
    QShortcut,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.campo_busqueda import CampoBusqueda
from pea.gui.componentes.ficha_lateral import FichaLateral
from pea.gui.componentes.filtro_anios import ChipVentana
from pea.gui.componentes.graficos.serie_anual import GraficoSerieAnual
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.tabla import (
    ROL_ACTIVO,
    TablaEstilizada,
)
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.dialogos import DialogoInvestigador
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    COLOR_ASC,
    COLOR_DTI,
    COLOR_FRH,
    COLOR_GNC,
    ERROR,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    RADIO_PILDORA,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
)
from pea.gui.formato import (
    formatear_entero,
    formatear_porcentaje,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios

# ---------------------------------------------------------------------------
# Modelo de Datos del Directorio de Investigadores
# ---------------------------------------------------------------------------


class ModeloDirectorioInvestigadores(QAbstractTableModel):
    """Modelo tabular especializado para el directorio de investigadores."""

    COLUMNAS = ("Nombre", "Grupo(s)", "Categoría", "Formación", "Productos", "Código CvLAC")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._registros: list[dict[str, Any]] = []

    def establecer_registros(self, registros: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._registros = list(registros)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self._registros)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex | None = None) -> int:
        if parent is not None and parent.isValid():
            return 0
        return len(self.COLUMNAS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        fila = index.row()
        col = index.column()
        if fila < 0 or fila >= len(self._registros):
            return None

        reg = self._registros[fila]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return reg["nombre_completo"]
            if col == 1:
                return reg["grupos"] or "Sin grupo"
            if col == 2:
                # Si está inactivo, la píldora muestra «Inactivo»
                if not reg["activo"]:
                    return "Inactivo"
                return reg["categoria"] or "Sin categoría"
            if col == 3:
                return reg["formacion"] or "—"
            if col == 4:
                return reg["productos"]
            if col == 5:
                return reg["codigo_rh"]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 4:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == ROL_ACTIVO:
            return reg["activo"]

        if role == Qt.ItemDataRole.UserRole:
            return reg["codigo_rh"]

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.COLUMNAS):
                return self.COLUMNAS[section]
        return None

    def obtener_clave_fila(self, fila: int) -> str | None:
        if 0 <= fila < len(self._registros):
            return str(self._registros[fila]["codigo_rh"])
        return None

    def registro(self, fila: int) -> dict[str, Any] | None:
        if 0 <= fila < len(self._registros):
            return self._registros[fila]
        return None


class ProxyDirectorioInvestigadores(QSortFilterProxyModel):
    """Proxy de filtrado reactivo y ordenación para el directorio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._texto_busqueda: str = ""
        self._filtro_grupo: str = ""
        self._filtro_categoria: str = ""
        self._solo_activos: bool = True  # Por defecto Estado = Activos

    def _invalidar_filtro(self) -> None:
        self.invalidate()

    def establecer_busqueda(self, texto: str) -> None:
        self._texto_busqueda = texto.strip().lower()
        self._invalidar_filtro()

    def establecer_grupo(self, grupo: str) -> None:
        self._filtro_grupo = grupo.strip()
        self._invalidar_filtro()

    def establecer_categoria(self, categoria: str) -> None:
        self._filtro_categoria = categoria.strip()
        self._invalidar_filtro()

    def establecer_solo_activos(self, solo_activos: bool) -> None:
        self._solo_activos = solo_activos
        self._invalidar_filtro()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex) -> bool:
        src = self.sourceModel()
        if not isinstance(src, ModeloDirectorioInvestigadores):
            return super().filterAcceptsRow(source_row, source_parent)

        reg = src.registro(source_row)
        if reg is None:
            return False

        # 1. Filtro por Estado
        if self._solo_activos and not reg["activo"]:
            return False

        # 2. Filtro por Categoría
        if self._filtro_categoria and self._filtro_categoria not in ("Todas las categorías", "Categoría"):
            cat_reg = (reg["categoria"] or "").strip().lower()
            if self._filtro_categoria.lower() not in cat_reg:
                return False

        # 3. Filtro por Grupo
        if self._filtro_grupo and self._filtro_grupo not in ("Todos los grupos", "Grupo"):
            grupos_reg = (reg["grupos"] or "").lower()
            if self._filtro_grupo.lower() not in grupos_reg:
                return False

        # 4. Búsqueda de texto (Nombre, CvLAC o Grupos)
        if self._texto_busqueda:
            texto_completo = f"{reg['nombre_completo']} {reg['codigo_rh']} {reg['grupos']}".lower()
            if self._texto_busqueda not in texto_completo:
                return False

        return True

    def lessThan(
        self,
        source_left: QModelIndex | QPersistentModelIndex,
        source_right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        col = source_left.column()
        # Columna 4: Productos (orden numérico)
        if col == 4:
            v_izq = source_left.data(Qt.ItemDataRole.DisplayRole)
            v_der = source_right.data(Qt.ItemDataRole.DisplayRole)
            try:
                n_izq = int(v_izq) if v_izq is not None else 0
                n_der = int(v_der) if v_der is not None else 0
                return n_izq < n_der
            except (ValueError, TypeError):
                pass

        # Otras columnas: orden alfabético insensible a mayúsculas
        v_l = str(source_left.data(Qt.ItemDataRole.DisplayRole) or "").lower()
        v_r = str(source_right.data(Qt.ItemDataRole.DisplayRole) or "").lower()
        return v_l < v_r


# ---------------------------------------------------------------------------
# Componente: Barra de Progreso de Tipología
# ---------------------------------------------------------------------------


class _BarraProgresoMini(QWidget):
    """Barra horizontal suave con porcentaje proporcional."""

    def __init__(self, color_hex: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._color_hex = color_hex
        self._fraccion: float = 0.0

    def establecer_fraccion(self, fraccion: float) -> None:
        self._fraccion = max(0.0, min(1.0, fraccion))
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ancho = float(self.width())
        alto = float(self.height())
        rect_total = QRectF(0, 0, ancho, alto)

        # Fondo tenue
        painter.setBrush(QBrush(QColor("#E2E8F0")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect_total, 4.0, 4.0)

        # Barra activa
        if self._fraccion > 0:
            ancho_activo = max(6.0, ancho * self._fraccion)
            rect_activo = QRectF(0, 0, ancho_activo, alto)
            painter.setBrush(QBrush(QColor(self._color_hex)))
            painter.drawRoundedRect(rect_activo, 4.0, 4.0)


class BarrasTipologia(QWidget):
    """Panel de tipologías (GNC, DTI, ASC, FRH) con barras horizontales y conteos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        lbl_tit = QLabel("Tipología de productos", self)
        lbl_tit.setStyleSheet(f"font-size: 10.5pt; font-weight: bold; color: {TEXTO};")
        layout.addWidget(lbl_tit)

        self._filas: dict[str, tuple[_BarraProgresoMini, QLabel]] = {}
        tipologias = [
            ("GNC", COLOR_GNC),
            ("DTI", COLOR_DTI),
            ("ASC", COLOR_ASC),
            ("FRH", COLOR_FRH),
        ]

        for sigla, color_hex in tipologias:
            fila = QHBoxLayout()
            fila.setContentsMargins(0, 0, 0, 0)
            fila.setSpacing(8)

            badge = QLabel(sigla, self)
            badge.setFixedSize(36, 20)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background-color: {color_hex}; color: {TEXTO_SOBRE_OSCURO}; "
                f"font-weight: bold; font-size: 8.5pt; border-radius: {RADIO_PILDORA}px;"
            )
            fila.addWidget(badge)

            barra = _BarraProgresoMini(color_hex, self)
            fila.addWidget(barra, 1)

            lbl_valor = QLabel("0 (0 %)", self)
            lbl_valor.setMinimumWidth(80)
            lbl_valor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_valor.setStyleSheet(f"font-size: 9.5pt; color: {TEXTO_SECUNDARIO};")
            fila.addWidget(lbl_valor)

            layout.addLayout(fila)
            self._filas[sigla] = (barra, lbl_valor)

    def actualizar(self, conteos: dict[str, int]) -> None:
        total = sum(conteos.values())
        max_val = max(conteos.values()) if conteos and max(conteos.values()) > 0 else 1

        for sigla, (barra, lbl) in self._filas.items():
            cant = conteos.get(sigla, 0)
            pct = (cant / total * 100.0) if total > 0 else 0.0
            fraccion = cant / max_val if max_val > 0 else 0.0

            barra.establecer_fraccion(fraccion)
            lbl.setText(f"{formatear_entero(cant)} ({formatear_porcentaje(pct)})")


# ---------------------------------------------------------------------------
# Diálogo Modal: Confirmar Eliminación en Cascada
# ---------------------------------------------------------------------------


class DialogoConfirmarEliminar(QDialog):
    """Diálogo modal que presenta la descripción de cascada antes de eliminar."""

    def __init__(self, titulo: str, descripcion_cascada: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedWidth(460)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Encabezado con ícono
        fila_tit = QHBoxLayout()
        fila_tit.setSpacing(10)
        lbl_ico = QLabel("⚠️", self)
        lbl_ico.setStyleSheet("font-size: 18pt;")
        fila_tit.addWidget(lbl_ico)

        lbl_tit = QLabel("¿Confirmar eliminación permanente?", self)
        lbl_tit.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {TEXTO};")
        fila_tit.addWidget(lbl_tit, 1)
        layout.addLayout(fila_tit)

        # Tarjeta de advertencia de cascada
        cuadro_aviso = QFrame(self)
        cuadro_aviso.setStyleSheet(
            f"QFrame {{ background-color: {AVISO_FONDO}; border: 1px solid {AVISO}; "
            f"border-radius: {RADIO_BOTON}px; padding: 12px; }}"
        )
        layout_aviso = QVBoxLayout(cuadro_aviso)
        layout_aviso.setContentsMargins(8, 8, 8, 8)
        layout_aviso.setSpacing(6)

        lbl_cascada = QLabel(descripcion_cascada, cuadro_aviso)
        lbl_cascada.setWordWrap(True)
        lbl_cascada.setStyleSheet(f"color: {AVISO}; font-size: 10.5pt; font-weight: 500;")
        layout_aviso.addWidget(lbl_cascada)

        lbl_undo = QLabel("Nota: La operación se guardará en la pila de deshacer (Ctrl+Z).", cuadro_aviso)
        lbl_undo.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: 9.5pt;")
        layout_aviso.addWidget(lbl_undo)

        layout.addWidget(cuadro_aviso)

        # Botones de acción
        fila_btn = QHBoxLayout()
        fila_btn.setContentsMargins(0, 8, 0, 0)
        fila_btn.setSpacing(10)
        fila_btn.addStretch()

        btn_cancelar = QPushButton("Cancelar", self)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(
            f"QPushButton {{ background-color: #FFFFFF; color: {TEXTO}; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; padding: 8px 16px; font-weight: 600; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: #F1F5F9; }}"
        )
        btn_cancelar.clicked.connect(self.reject)
        fila_btn.addWidget(btn_cancelar)

        btn_eliminar = QPushButton("Eliminar permanentemente", self)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.setStyleSheet(
            f"QPushButton {{ background-color: {ERROR}; color: #FFFFFF; border: none; "
            f"border-radius: {RADIO_BOTON}px; padding: 8px 18px; font-weight: bold; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: #7A1D1D; }}"
        )
        btn_eliminar.clicked.connect(self.accept)
        fila_btn.addWidget(btn_eliminar)

        layout.addLayout(fila_btn)


# ---------------------------------------------------------------------------
# Diálogo Modal: Ficha Completa del Investigador (Tabs de Aportes, Membresías, Productos)
# ---------------------------------------------------------------------------


class DialogoFichaCompletaInvestigador(QDialog):
    """Diálogo modal amplio con las tablas completas de aportes, membresías y productos."""

    def __init__(
        self,
        vista: dict[str, Any],
        servicio: ServicioAplicacion,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Ficha Completa · {vista['nombre']} ({vista['codigo']})")
        self.setModal(True)
        self.resize(860, 580)
        self.setStyleSheet("QDialog { background-color: #FFFFFF; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Cabecera institucional
        fila_cab = QHBoxLayout()
        fila_cab.setSpacing(12)

        barra_acento = QFrame(self)
        barra_acento.setFixedWidth(3)
        barra_acento.setFixedHeight(36)
        barra_acento.setStyleSheet(f"background-color: {COLOR_DTI}; border-radius: 1px;")
        fila_cab.addWidget(barra_acento)

        col_tit = QVBoxLayout()
        col_tit.setSpacing(2)

        lbl_nom = QLabel(vista["nombre"], self)
        lbl_nom.setStyleSheet(f"font-size: 15pt; font-weight: bold; color: {TEXTO};")
        col_tit.addWidget(lbl_nom)

        lbl_meta = QLabel(
            f"Código CvLAC: {vista['codigo']}  ·  Categoría: {vista['categoria']}  ·  "
            f"Formación: {vista['formacion']}  ·  Filtro: {vista['filtro']}",
            self,
        )
        lbl_meta.setStyleSheet(f"font-size: 10.5pt; color: {TEXTO_SECUNDARIO};")
        col_tit.addWidget(lbl_meta)
        fila_cab.addLayout(col_tit)
        fila_cab.addStretch()

        layout.addLayout(fila_cab)

        # Pestañas con tablas completas
        self.pestanas = QTabWidget(self)
        self.pestanas.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; background: #FFFFFF; }}"
            f"QTabBar::tab {{ background: #F1F5F9; color: {TEXTO}; padding: 8px 16px; font-weight: 600; "
            f"border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; font-size: 10.5pt; }}"
            f"QTabBar::tab:selected {{ background: #FFFFFF; color: {PRIMARIO}; border: 1px solid {LINEA}; border-bottom: none; }}"
        )

        # Tab 1: Aporte a Grupos
        self.tabla_aportes = TablaEstilizada(self.pestanas)
        self.modelo_aportes = ModeloTabla(vista["aportes"], parent=self.tabla_aportes)
        self.tabla_aportes.establecer_modelo(self.modelo_aportes)
        self.pestanas.addTab(self.tabla_aportes, "Aporte a Grupos de Investigación")

        # Tab 2: Membresías
        self.tabla_membresias = TablaEstilizada(self.pestanas)
        self.modelo_membresias = ModeloTabla(vista["membresias"], parent=self.tabla_membresias)
        self.tabla_membresias.establecer_modelo(self.modelo_membresias)
        self.pestanas.addTab(self.tabla_membresias, "Membresías Registradas")

        # Tab 3: Productos
        self.tabla_productos = TablaEstilizada(self.pestanas)
        self.modelo_productos = ModeloTabla(vista["productos"], parent=self.tabla_productos)
        self.tabla_productos.establecer_modelo(self.modelo_productos)
        self.pestanas.addTab(self.tabla_productos, "Productos Autorados en Multilista")

        layout.addWidget(self.pestanas, 1)

        # Pie con botón exportar y cerrar
        fila_pie = QHBoxLayout()
        fila_pie.setSpacing(10)

        btn_exportar = QPushButton("Exportar tablas (CSV)", self)
        btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar.setStyleSheet(
            f"QPushButton {{ background-color: #FFFFFF; color: {PRIMARIO}; border: 1px solid {PRIMARIO}; "
            f"border-radius: {RADIO_BOTON}px; padding: 7px 16px; font-weight: 600; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: #F1F5F9; }}"
        )
        btn_exportar.clicked.connect(lambda: self._exportar_csv(servicio, vista))
        fila_pie.addWidget(btn_exportar)

        fila_pie.addStretch()

        btn_cerrar = QPushButton("Cerrar", self)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: #FFFFFF; border: none; "
            f"border-radius: {RADIO_BOTON}px; padding: 7px 22px; font-weight: bold; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
        )
        btn_cerrar.clicked.connect(self.accept)
        fila_pie.addWidget(btn_cerrar)

        layout.addLayout(fila_pie)

    def _exportar_csv(self, servicio: ServicioAplicacion, vista: dict[str, Any]) -> None:
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportar tablas")
        if not directorio:
            return
        p_dir = Path(directorio)
        cod = vista["codigo"]
        r_ap = p_dir / f"investigador_{cod}_aportes.csv"
        r_prd = p_dir / f"investigador_{cod}_productos.csv"
        servicio.exportar_tabla_csv(vista["aportes"], r_ap)
        servicio.exportar_tabla_csv(vista["productos"], r_prd)
        GestorAvisos.instancia().mostrar("Tablas exportadas a CSV con éxito.", tipo="exito")


# ---------------------------------------------------------------------------
# Pantalla Principal de Investigadores
# ---------------------------------------------------------------------------


class PantallaInvestigadores(QWidget):
    """Pantalla oficial de Directorio de Investigadores (Sección 6.2)."""

    solicitar_navegacion = Signal(int)
    ver_productos_solicitado = Signal(str)
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
        self.setObjectName("pantallaInvestigadores")
        self._servicio = servicio
        self._ejecutor = ejecutor or EjecutorHilos.instancia()
        self._filtro_actual = filtro_global or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)
        self._investigador_seleccionado_cod: str | None = None
        self._investigador_seleccionado_nom: str = ""

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

        # 2. Contenedor central: Tarjeta Directorio + Ficha Lateral (360 px)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setHandleWidth(12)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background: transparent; }"
        )

        # Tarjeta izquierda: Directorio
        self._tarjeta_directorio = self._crear_tarjeta_directorio()
        self._splitter.addWidget(self._tarjeta_directorio)

        # Ficha lateral derecha: 360 px
        self._ficha_lateral = self._crear_ficha_lateral()
        self._splitter.addWidget(self._ficha_lateral)

        # Proporciones iniciales: flexible para tabla, 360 fijo para lateral
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)

        layout_raiz.addWidget(self._splitter, 1)

    def _crear_barra_contexto(self) -> QWidget:
        barra = QWidget(self)
        barra.setFixedHeight(56)
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        lbl_tit = QLabel("Investigadores", barra)
        lbl_tit.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {TEXTO};")
        layout.addWidget(lbl_tit)

        lbl_sub = QLabel("Directorio institucional clasificado según CvLAC y producción Minciencias", barra)
        lbl_sub.setStyleSheet(f"font-size: 10pt; color: {TEXTO_SECUNDARIO};")
        layout.addWidget(lbl_sub)

        layout.addStretch(1)

        # Chip de ventana global
        self._chip_ventana = ChipVentana(self._filtro_actual, parent=barra)
        self._chip_ventana.filtro_cambiado.connect(self._al_cambiar_filtro)
        layout.addWidget(self._chip_ventana)

        # Menú Exportar
        self._btn_exportar = QPushButton("Exportar ▾", barra)
        self._btn_exportar.setObjectName("btnExportarInvestigadores")
        self._btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_exportar.setStyleSheet(
            f"QPushButton {{ background-color: #FFFFFF; color: {TEXTO}; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; padding: 6px 14px; font-weight: 600; font-size: 10pt; }}"
            f"QPushButton:hover {{ background-color: #F1F5F9; }}"
        )
        menu_exp = QMenu(self._btn_exportar)
        menu_exp.setStyleSheet(
            f"QMenu {{ background: #FFFFFF; border: 1px solid {LINEA}; border-radius: 8px; padding: 4px; }}"
            f"QMenu::item {{ padding: 6px 16px; font-size: 10.5pt; color: {TEXTO}; }}"
            f"QMenu::item:selected {{ background-color: #F1F5F9; color: {PRIMARIO}; }}"
        )
        act_csv = menu_exp.addAction("Directorio actual (CSV)")
        act_csv.triggered.connect(self._al_exportar_directorio_csv)
        self._btn_exportar.setMenu(menu_exp)
        layout.addWidget(self._btn_exportar)

        return barra

    def _crear_tarjeta_directorio(self) -> Tarjeta:
        tarjeta = Tarjeta(
            titulo="Directorio de Investigadores",
            con_sombra=True,
            parent=self,
        )

        # Barra de filtros y búsqueda en la cabecera de la tarjeta
        contenedor_filtros = QWidget(tarjeta)
        layout_f = QHBoxLayout(contenedor_filtros)
        layout_f.setContentsMargins(0, 0, 0, 0)
        layout_f.setSpacing(10)

        # Campo de búsqueda
        self.campo_busqueda = CampoBusqueda(placeholder="Buscar investigador…", parent=contenedor_filtros)
        self.campo_busqueda.setMinimumWidth(220)
        self.campo_busqueda.texto_cambiado.connect(self._al_buscar_texto)
        layout_f.addWidget(self.campo_busqueda, 1)

        # Combo Grupo
        self.combo_grupo = QComboBox(contenedor_filtros)
        self.combo_grupo.setMinimumWidth(150)
        self.combo_grupo.addItem("Todos los grupos")
        self.combo_grupo.currentTextChanged.connect(self._al_cambiar_combo_grupo)
        layout_f.addWidget(self.combo_grupo)

        # Combo Categoría
        self.combo_categoria = QComboBox(contenedor_filtros)
        self.combo_categoria.setMinimumWidth(140)
        self.combo_categoria.addItems([
            "Todas las categorías",
            "Emérito",
            "Senior",
            "Asociado",
            "Junior",
            "Sin categoría",
        ])
        self.combo_categoria.currentTextChanged.connect(self._al_cambiar_combo_categoria)
        layout_f.addWidget(self.combo_categoria)

        # Combo Estado
        self.combo_estado = QComboBox(contenedor_filtros)
        self.combo_estado.setMinimumWidth(110)
        self.combo_estado.addItems(["Activos", "Todos"])
        self.combo_estado.currentTextChanged.connect(self._al_cambiar_combo_estado)
        layout_f.addWidget(self.combo_estado)

        # Botón primario «+ Nuevo investigador»
        self.btn_nuevo = QPushButton("+ Nuevo investigador", contenedor_filtros)
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: #FFFFFF; font-weight: bold; "
            f"border: none; border-radius: {RADIO_BOTON}px; padding: 8px 16px; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
        )
        self.btn_nuevo.clicked.connect(self._al_pulsar_nuevo)
        layout_f.addWidget(self.btn_nuevo)

        tarjeta.agregar_widget(contenedor_filtros)

        # Tabla institucional
        self.tabla = TablaEstilizada(parent=tarjeta)
        self._modelo = ModeloDirectorioInvestigadores(parent=self.tabla)
        self._proxy = ProxyDirectorioInvestigadores(parent=self.tabla)
        self._proxy.setSourceModel(self._modelo)
        self.tabla.establecer_proxy(self._proxy)

        # Configurar delegados
        self.tabla.establecer_delegado_columna(0, self.tabla.delegado_avatar)
        self.tabla.establecer_delegado_columna(1, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(2, self.tabla.delegado_pildora)
        self.tabla.establecer_delegado_columna(3, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(4, self.tabla.delegado_numero)
        self.tabla.establecer_delegado_columna(5, self.tabla.delegado_enlace)

        # Conectar copia de código CvLAC al gestor de avisos (toast)
        self.tabla.delegado_enlace.copiado.connect(
            lambda cod: GestorAvisos.instancia().mostrar(f"Código CvLAC {cod} copiado al portapapeles.", tipo="info")
        )

        # Señales de selección y apertura de ficha completa
        self.tabla.clave_seleccionada.connect(self._al_seleccionar_clave)
        self.tabla.fila_doble_clic.connect(lambda _: self._al_pulsar_ver_ficha_completa())

        # Anchos preferidos de columnas
        self.tabla.ajustar_columnas({
            0: 240,
            1: 170,
            2: 120,
            3: 140,
            4: 100,
            5: 140,
        })

        tarjeta.agregar_widget(self.tabla)
        return tarjeta

    def _crear_ficha_lateral(self) -> FichaLateral:
        ficha = FichaLateral(diametro_avatar=96, parent=self)

        # Cuadrícula 2×2 de Fichas KPI
        self.kpi_productos = FichaKPI("Productos", "0", "En ventana", parent=ficha)
        self.kpi_grupos = FichaKPI("Grupos", "0", "Membresías", parent=ficha)
        self.kpi_coautores = FichaKPI("Coautores", "0", "Red de coautoría", parent=ficha)
        self.kpi_anios = FichaKPI("Años con producción", "0", "Histórico", parent=ficha)

        ficha.agregar_kpi(self.kpi_productos, 0, 0)
        ficha.agregar_kpi(self.kpi_grupos, 0, 1)
        ficha.agregar_kpi(self.kpi_coautores, 1, 0)
        ficha.agregar_kpi(self.kpi_anios, 1, 1)

        # Gráfico de evolución temporal anual
        self.grafico_serie = GraficoSerieAnual(
            titulo="Producción anual",
            subtitulo="Histórico de productos autorados",
            parent=ficha,
        )
        self.grafico_serie.setFixedHeight(140)
        ficha.agregar_contenido(self.grafico_serie)

        # Barras de tipología de productos
        self.barras_tipologia = BarrasTipologia(parent=ficha)
        ficha.agregar_contenido(self.barras_tipologia)

        # Conectar señales de acciones
        ficha.editar_solicitado.connect(self._al_pulsar_editar)
        ficha.cambiar_estado_solicitado.connect(self._al_pulsar_cambiar_estado)
        ficha.eliminar_solicitado.connect(self._al_pulsar_eliminar)
        ficha.ver_completa_solicitado.connect(self._al_pulsar_ver_ficha_completa)
        ficha.ver_productos_solicitado.connect(self._al_pulsar_ver_productos)

        return ficha

    def _configurar_atajos(self) -> None:
        # Ctrl+F: enfocar campo de búsqueda
        atajo_buscar = QShortcut(QKeySequence.StandardKey.Find, self)
        atajo_buscar.activated.connect(self._al_atajo_buscar)

        # Enter en la tabla: abrir ficha completa
        atajo_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self.tabla.vista)
        atajo_enter.activated.connect(self._al_pulsar_ver_ficha_completa)

    def _al_atajo_buscar(self) -> None:
        self.campo_busqueda.setFocus()
        self.campo_busqueda.selectAll()

    # -----------------------------------------------------------------------
    # Carga y Actualización Reactiva de Datos
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Recarga la lista completa de investigadores respetando el filtro temporal."""
        cat = self._servicio._catalogo

        # Actualizar opciones del combo Grupo
        grp_prev = self.combo_grupo.currentText()
        self.combo_grupo.blockSignals(True)
        self.combo_grupo.clear()
        self.combo_grupo.addItem("Todos los grupos")
        for g in sorted(cat.grupos, key=lambda x: x.nombre.lower()):
            self.combo_grupo.addItem(g.nombre, g.codigo_gruplac)
        idx_grp = self.combo_grupo.findText(grp_prev)
        self.combo_grupo.setCurrentIndex(max(0, idx_grp))
        self.combo_grupo.blockSignals(False)

        # Obtener registros desde catálogo y servicio
        registros: list[dict[str, Any]] = []
        for i in sorted(cat.investigadores, key=lambda x: x.nombre_completo.lower()):
            mems = [m for m in cat.integrantes if m.codigo_rh == i.codigo_rh]
            nom_grupos = ", ".join(self._servicio._nombre_grupo(m.codigo_gruplac) for m in mems)
            n_prod = sum(
                1 for p in cat.multilista_productos.obtener_productos_investigador(i.codigo_rh)
                if p.activo and self._servicio._producto_en_filtro(p, self._filtro_actual)
            )
            registros.append({
                "codigo_rh": i.codigo_rh,
                "nombre_completo": i.nombre_completo,
                "categoria": i.categoria or "Sin categoría",
                "formacion": i.formacion_academica or "—",
                "grupos": nom_grupos,
                "productos": n_prod,
                "activo": i.activo,
            })

        self._modelo.establecer_registros(registros)
        self.tabla.actualizar_pie()

        # Restaurar selección o seleccionar primer elemento
        if self._investigador_seleccionado_cod:
            self._seleccionar_por_codigo(self._investigador_seleccionado_cod)
        elif self._proxy.rowCount() > 0:
            self.tabla.seleccionar_fila(0)
        else:
            self._ficha_lateral.mostrar_vacio("No hay investigadores registrados o coincidentes")

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Ajusta el filtro global y actualiza directorio y ficha lateral."""
        self._filtro_actual = filtro
        self._chip_ventana.establecer_filtro(filtro)
        self.refrescar()

    def _al_cambiar_filtro(self, filtro: FiltroAnios) -> None:
        self.establecer_filtro(filtro)
        self.filtro_cambiado.emit(filtro)

    def _seleccionar_por_codigo(self, codigo_rh: str) -> None:
        src = self._modelo
        for row in range(src.rowCount()):
            if src.obtener_clave_fila(row) == codigo_rh:
                self.tabla.seleccionar_fila(row)
                return
        if self._proxy.rowCount() > 0:
            self.tabla.seleccionar_fila(0)
        else:
            self._ficha_lateral.mostrar_vacio()

    def seleccionar_investigador(self, clave_o_nombre: str) -> None:
        """Selecciona un investigador por código CvLAC o nombre completo."""
        src = self._modelo
        for row in range(src.rowCount()):
            if src.obtener_clave_fila(row) == clave_o_nombre:
                self.tabla.seleccionar_fila(row)
                return
        nom_busq = clave_o_nombre.strip().lower()
        for row in range(src.rowCount()):
            reg = src.registro(row)
            if reg and nom_busq in reg["nombre_completo"].lower():
                self.tabla.seleccionar_fila(row)
                return
        # Si no está en la vista actual, aplicar búsqueda de texto
        self.campo_busqueda.establecer_texto(clave_o_nombre)

    def filtrar_por_grupo(self, cod_o_nombre_grupo: str) -> None:
        """Filtra los investigadores pertenecientes al grupo indicado."""
        idx = self.combo_grupo.findText(cod_o_nombre_grupo)
        if idx >= 0:
            self.combo_grupo.setCurrentIndex(idx)
        else:
            self.campo_busqueda.establecer_texto(cod_o_nombre_grupo)

    # -----------------------------------------------------------------------
    # Filtros Reactivos del Directorio
    # -----------------------------------------------------------------------

    def _al_buscar_texto(self, texto: str) -> None:
        self._proxy.establecer_busqueda(texto)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_tras_filtro()

    def _al_cambiar_combo_grupo(self, grupo: str) -> None:
        self._proxy.establecer_grupo(grupo)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_tras_filtro()

    def _al_cambiar_combo_categoria(self, categoria: str) -> None:
        self._proxy.establecer_categoria(categoria)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_tras_filtro()

    def _al_cambiar_combo_estado(self, estado: str) -> None:
        solo_activos = (estado == "Activos")
        self._proxy.establecer_solo_activos(solo_activos)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_tras_filtro()

    def _auto_seleccionar_tras_filtro(self) -> None:
        if self._proxy.rowCount() > 0:
            # Si el actual sigue visible, mantenerse; si no, seleccionar el primero
            if self.tabla.fila_seleccionada_actual() is None:
                self.tabla.seleccionar_fila(0)
        else:
            self._ficha_lateral.mostrar_vacio("Sin resultados para los filtros aplicados")

    # -----------------------------------------------------------------------
    # Actualización de la Ficha Lateral
    # -----------------------------------------------------------------------

    def _al_seleccionar_clave(self, codigo_rh: str) -> None:
        self._investigador_seleccionado_cod = codigo_rh
        try:
            vista = self._servicio.vista_investigador(codigo_rh, self._filtro_actual)
            ficha = self._servicio.datos_ficha_investigador(codigo_rh, self._filtro_actual)
        except Exception:
            self._ficha_lateral.mostrar_vacio("Error al cargar datos del investigador")
            return

        self._investigador_seleccionado_nom = str(ficha["nombre"])

        # Cabecera
        subtitulo = f"{ficha['grupo_principal']}  ·  {ficha['categoria']}"
        pildoras: list[tuple[str, str | None]] = []
        if not ficha["activo"]:
            pildoras.append(("Inactivo", "error"))
        else:
            pildoras.append((str(ficha["categoria"]), None))

        self._ficha_lateral.establecer_cabecera(
            nombre=str(ficha["nombre"]),
            subtitulo=subtitulo,
            pildoras=pildoras,
        )

        # Fichas KPI
        self.kpi_productos.actualizar(formatear_entero(int(ficha["total_productos"])))
        self.kpi_grupos.actualizar(formatear_entero(len(vista["membresias"].filas)))
        self.kpi_coautores.actualizar(formatear_entero(int(ficha["coautores"])))
        self.kpi_anios.actualizar(formatear_entero(int(ficha["anios_con_produccion"])))

        # Gráficos
        self.grafico_serie.establecer_datos(ficha["productos_por_anio"])
        self.barras_tipologia.actualizar(ficha["productos_por_categoria"])

        # Estado del botón Activar / Desactivar
        self._ficha_lateral.configurar_estado_activo(bool(ficha["activo"]))

    # -----------------------------------------------------------------------
    # Operaciones CRUD y Acciones de la Ficha
    # -----------------------------------------------------------------------

    def _al_pulsar_nuevo(self) -> None:
        dlg = DialogoInvestigador(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            datos = dlg.obtener_datos()
            try:
                msg = self._servicio.crear_investigador(datos)
                self.datos_modificados.emit()
                self._investigador_seleccionado_cod = datos["codigo_rh"]
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al crear investigador: {e}", tipo="error")

    def _al_pulsar_editar(self) -> None:
        if not self._investigador_seleccionado_cod:
            return
        cod = self._investigador_seleccionado_cod
        try:
            datos_prev = self._servicio.datos_investigador(cod)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"No se pudieron cargar datos: {e}", tipo="error")
            return

        dlg = DialogoInvestigador(datos_previos=datos_prev, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            nuevos_datos = dlg.obtener_datos()
            try:
                msg = self._servicio.actualizar_investigador(cod, nuevos_datos)
                self.datos_modificados.emit()
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al actualizar: {e}", tipo="error")

    def _al_pulsar_cambiar_estado(self) -> None:
        if not self._investigador_seleccionado_cod:
            return
        cod = self._investigador_seleccionado_cod
        try:
            datos = self._servicio.datos_investigador(cod)
            nuevo_estado = not bool(datos.get("activo", True))
            msg = self._servicio.cambiar_estado("investigador", cod, nuevo_estado)
            self.datos_modificados.emit()
            self.refrescar()
            tipo_toast = "exito" if nuevo_estado else "aviso"
            GestorAvisos.instancia().mostrar(f"{msg} (Presiona Ctrl+Z para deshacer)", tipo=tipo_toast)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al cambiar estado: {e}", tipo="error")

    def _al_pulsar_eliminar(self) -> None:
        if not self._investigador_seleccionado_cod:
            return
        cod = self._investigador_seleccionado_cod
        try:
            cascada = self._servicio.describir_cascada("investigador", cod)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al consultar cascada: {e}", tipo="error")
            return

        dlg = DialogoConfirmarEliminar(
            titulo="Confirmar eliminación de investigador",
            descripcion_cascada=cascada,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self._servicio.eliminar("investigador", cod)
                self._investigador_seleccionado_cod = None
                self.datos_modificados.emit()
                self.refrescar()
                GestorAvisos.instancia().mostrar(f"{msg} (Presiona Ctrl+Z para deshacer)", tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al eliminar: {e}", tipo="error")

    def _al_pulsar_ver_ficha_completa(self) -> None:
        if not self._investigador_seleccionado_cod:
            return
        cod = self._investigador_seleccionado_cod
        try:
            vista = self._servicio.vista_investigador(cod, self._filtro_actual)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al abrir ficha completa: {e}", tipo="error")
            return

        dlg = DialogoFichaCompletaInvestigador(vista, self._servicio, parent=self)
        dlg.exec()

    def _al_pulsar_ver_productos(self) -> None:
        """Navega a la pantalla de Productos filtrando por el investigador seleccionado."""
        if not self._investigador_seleccionado_nom:
            return
        self.ver_productos_solicitado.emit(self._investigador_seleccionado_nom)
        # Pantalla.PRODUCTOS = 3
        self.solicitar_navegacion.emit(3)

    def _al_exportar_directorio_csv(self) -> None:
        """Exporta la vista filtrada del directorio a un archivo CSV."""
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para exportar directorio")
        if not directorio:
            return
        ruta = Path(directorio) / "directorio_investigadores.csv"

        # Construir TablaDatos con las filas visibles
        filas: list[tuple[Any, ...]] = []
        for r_idx in range(self._proxy.rowCount()):
            nom = self._proxy.index(r_idx, 0).data()
            grp = self._proxy.index(r_idx, 1).data()
            cat = self._proxy.index(r_idx, 2).data()
            frm = self._proxy.index(r_idx, 3).data()
            prd = self._proxy.index(r_idx, 4).data()
            cv = self._proxy.index(r_idx, 5).data()
            filas.append((nom, grp, cat, frm, prd, cv))

        from pea.servicios.vistas import TablaDatos

        tabla_exp = TablaDatos(
            columnas=("Nombre", "Grupo(s)", "Categoría", "Formación", "Productos", "Código CvLAC"),
            filas=tuple(filas),
            claves=tuple(str(f[5]) for f in filas),
        )
        self._servicio.exportar_tabla_csv(tabla_exp, ruta)
        GestorAvisos.instancia().mostrar(f"Directorio exportado a {ruta.name} con éxito.", tipo="exito")
