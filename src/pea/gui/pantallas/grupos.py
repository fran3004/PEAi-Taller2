"""Pantalla de Directorio de Grupos de Investigación (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.3).
- Barra de contexto: título, subtítulo, ChipVentana y menú Exportar ▾.
- Directorio de Grupos:
  * Cabecera con búsqueda (Ctrl+F, debounce 250 ms), combos Categoría y Estado (Activos/Todos),
    y botón primario «+ Nuevo grupo».
  * Tabla con filas de 48 px, hover #F3F7FB, selección #E3EEF7 con barra de acento de 3 px,
    encabezado FICHA en 10 pt negrita, ordenación insensible a mayúsculas y numérica en métricas.
  * Columnas: Nombre (avatar 28 px + nombre), Código GrupLAC (enlace copiable con toast),
    Categoría (píldora), Líder, Integrantes (número alineado a la derecha),
    Productos (número alineado a la derecha) y Estado (píldora).
  * Inactivos renderizados con 60 % de opacidad y píldora «Inactivo».
  * Pie de tabla con conteo dinámico «Mostrando N de M grupos».
- Ficha lateral (FichaGrupo):
  * Reutiliza la tarjeta de Ámbito de Inicio en modo Grupo (360 px).
  * Avatar de 96 px con iniciales y degradado determinista.
  * Título del grupo y subtítulo «Código · Categoría».
  * Botón desplegable «Ver más detalles ⌄» con panel conmutable (Líder, Institución, Área OCDE,
    Ubicación y Fecha de creación).
  * Cuadrícula 2×3 de 6 FichaKPI: Integrantes, Estudiantes, Productos (ventana con minigráfico),
    Productos avalados, Promedio por integrante y Aporte a la institución (%).
  * Minigráfico de barras apiladas de producción por tipología anual.
  * Botones de acción: Editar, Activar/Desactivar, Eliminar… (muestra describir_cascada),
    Ver ficha completa (diálogo con Integrantes y coautores, y Productos enlazados) y Ver productos.
- Notificaciones breves mediante Toast (GestorAvisos).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QKeySequence,
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
from pea.gui.componentes.graficos.barras_apiladas import GraficoBarrasApiladas
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.tabla import (
    ROL_ACTIVO,
    TablaEstilizada,
)
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.dialogos import DialogoGrupo
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    COLOR_DTI,
    ERROR,
    FICHA,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.gui.formato import (
    formatear_porcentaje,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios

# ---------------------------------------------------------------------------
# Modelo de Datos del Directorio de Grupos
# ---------------------------------------------------------------------------


class ModeloDirectorioGrupos(QAbstractTableModel):
    """Modelo tabular especializado para el directorio de grupos de investigación."""

    COLUMNAS = (
        "Nombre",
        "Código GrupLAC",
        "Categoría",
        "Líder",
        "Integrantes",
        "Productos",
        "Estado",
    )

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
                return reg["nombre"]
            if col == 1:
                return reg["codigo_gruplac"]
            if col == 2:
                if not reg["activo"]:
                    return "Inactivo"
                return reg["categoria"] or "Sin clasificar"
            if col == 3:
                return reg["lider"] or "—"
            if col == 4:
                return reg["integrantes"]
            if col == 5:
                return reg["productos"]
            if col == 6:
                return "Activo" if reg["activo"] else "Inactivo"

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (4, 5):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == ROL_ACTIVO:
            return reg["activo"]

        if role == Qt.ItemDataRole.UserRole:
            return reg["codigo_gruplac"]

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNAS):
                return self.COLUMNAS[section]
        return None

    def registro_en_fila(self, fila: int) -> dict[str, Any] | None:
        if 0 <= fila < len(self._registros):
            return self._registros[fila]
        return None

    def obtener_clave_fila(self, fila: int) -> str | None:
        reg = self.registro_en_fila(fila)
        return reg["codigo_gruplac"] if reg else None


# ---------------------------------------------------------------------------
# Proxy de Filtrado y Ordenamiento
# ---------------------------------------------------------------------------


class ProxyDirectorioGrupos(QSortFilterProxyModel):
    """Proxy para búsqueda textual, filtro por categoría, estado y orden numérico."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._texto_busqueda: str = ""
        self._categoria_filtro: str = "Todas las categorías"
        self._solo_activos: bool = True
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def establecer_texto_busqueda(self, texto: str) -> None:
        self._texto_busqueda = texto.strip().lower()
        self.invalidate()

    def establecer_categoria(self, categoria: str) -> None:
        self._categoria_filtro = categoria
        self.invalidate()

    def establecer_solo_activos(self, solo_activos: bool) -> None:
        self._solo_activos = solo_activos
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex) -> bool:
        modelo = self.sourceModel()
        if not isinstance(modelo, ModeloDirectorioGrupos):
            return True

        reg = modelo.registro_en_fila(source_row)
        if reg is None:
            return False

        # 1. Filtro por estado activo
        if self._solo_activos and not reg["activo"]:
            return False

        # 2. Filtro por categoría
        if self._categoria_filtro != "Todas las categorías":
            cat_reg = (reg["categoria"] or "").strip()
            if self._categoria_filtro == "Sin clasificar":
                if cat_reg not in ("", "Sin clasificar"):
                    return False
            elif cat_reg != self._categoria_filtro:
                return False

        # 3. Filtro textual
        if self._texto_busqueda:
            texto_todo = f"{reg['nombre']} {reg['codigo_gruplac']} {reg['lider']}".lower()
            if self._texto_busqueda not in texto_todo:
                return False

        return True

    def lessThan(
        self,
        source_left: QModelIndex | QPersistentModelIndex,
        source_right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        col = source_left.column()
        # Columnas 4 (Integrantes) y 5 (Productos): orden numérico
        if col in (4, 5):
            val_izq = source_left.data(Qt.ItemDataRole.DisplayRole) or 0
            val_der = source_right.data(Qt.ItemDataRole.DisplayRole) or 0
            try:
                return int(val_izq) < int(val_der)
            except (ValueError, TypeError):
                return str(val_izq) < str(val_der)

        val_izq = str(source_left.data(Qt.ItemDataRole.DisplayRole) or "").lower()
        val_der = str(source_right.data(Qt.ItemDataRole.DisplayRole) or "").lower()
        return val_izq < val_der


# ---------------------------------------------------------------------------
# Diálogo Modal: Confirmar Eliminación en Cascada
# ---------------------------------------------------------------------------


class DialogoConfirmarEliminar(QDialog):
    """Diálogo modal que presenta la descripción de cascada antes de eliminar un grupo."""

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
        lbl_undo.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: 9pt;")
        layout_aviso.addWidget(lbl_undo)

        layout.addWidget(cuadro_aviso)

        # Botones de acción
        fila_btn = QHBoxLayout()
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
# Diálogo Modal: Ficha Completa del Grupo (Integrantes y Productos)
# ---------------------------------------------------------------------------


class DialogoFichaCompletaGrupo(QDialog):
    """Diálogo modal amplio con las tablas de integrantes y coautores, y productos enlazados."""

    def __init__(
        self,
        vista: dict[str, Any],
        servicio: ServicioAplicacion,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Ficha Completa · {vista['nombre']} ({vista['codigo']})")
        self.setModal(True)
        self.resize(880, 600)
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
            f"Código GrupLAC: {vista['codigo']}  ·  Categoría: {vista['categoria']}  ·  "
            f"Líder: {vista['lider']}  ·  Filtro: {vista['filtro']}",
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

        # Tab 1: Integrantes y coautores
        self.tabla_integrantes = TablaEstilizada(self.pestanas)
        self.modelo_integrantes = ModeloTabla(vista["integrantes"], parent=self.tabla_integrantes)
        self.tabla_integrantes.establecer_modelo(self.modelo_integrantes)
        self.pestanas.addTab(self.tabla_integrantes, "Integrantes y Coautores Vinculados")

        # Tab 2: Productos enlazados
        self.tabla_productos = TablaEstilizada(self.pestanas)
        self.modelo_productos = ModeloTabla(vista["productos"], parent=self.tabla_productos)
        self.tabla_productos.establecer_modelo(self.modelo_productos)
        self.pestanas.addTab(self.tabla_productos, "Productos Enlazados al Grupo")

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
        r_int = p_dir / f"grupo_{cod}_integrantes.csv"
        r_prd = p_dir / f"grupo_{cod}_productos.csv"
        servicio.exportar_tabla_csv(vista["integrantes"], r_int)
        servicio.exportar_tabla_csv(vista["productos"], r_prd)
        GestorAvisos.instancia().mostrar("Tablas de grupo exportadas a CSV con éxito.", tipo="exito")


# ---------------------------------------------------------------------------
# Ficha Lateral del Grupo (FichaGrupo)
# ---------------------------------------------------------------------------


class FichaGrupo(FichaLateral):
    """Ficha lateral de 360 px para grupo, reutilizando la tarjeta de Ámbito de Inicio en modo Grupo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, diametro_avatar=96)
        self.setObjectName("fichaGrupo")

        # Botón «Ver más detalles ⌄» y panel colapsable
        self.btn_detalles = QPushButton("Ver más detalles ⌄", self._contenedor_cabecera)
        self.btn_detalles.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detalles.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {COLOR_DTI}; "
            f"font-weight: 600; font-size: 9.5pt; padding: 2px 8px; }}"
            f"QPushButton:hover {{ text-decoration: underline; }}"
        )
        self.btn_detalles.clicked.connect(self._alternar_detalles)
        self._contenedor_cabecera.layout().addWidget(self.btn_detalles, alignment=Qt.AlignmentFlag.AlignCenter)

        # Panel desplegable de detalles
        self._panel_detalles = QFrame(self._contenedor_cabecera)
        self._panel_detalles.setStyleSheet(
            f"QFrame {{ background-color: {FICHA}; border-radius: 8px; padding: 6px; }}"
        )
        self._layout_detalles = QVBoxLayout(self._panel_detalles)
        self._layout_detalles.setContentsMargins(10, 6, 10, 6)
        self._layout_detalles.setSpacing(4)
        self._panel_detalles.setVisible(False)
        self._contenedor_cabecera.layout().addWidget(self._panel_detalles)

        # 6 Fichas KPI en cuadrícula 2×3 (Ámbito Inicio en modo Grupo)
        self.kpi_integrantes = FichaKPI("Integrantes", "0", "Integrantes vinculados", parent=self)
        self.kpi_estudiantes = FichaKPI("Estudiantes", "0", "Rol estudiante", parent=self)
        self.kpi_productos = FichaKPI("Productos (ventana)", "0", "En período", con_minigrafico=True, parent=self)
        self.kpi_avalados = FichaKPI("Productos avalados", "0", "Con aval institucional", parent=self)
        self.kpi_promedio = FichaKPI("Promedio por integrante", "0,00", "Prod. / integrante", parent=self)
        self.kpi_aporte = FichaKPI("Aporte a la institución", "0,0 %", "Aporte institucional", parent=self)

        self.agregar_kpi(self.kpi_integrantes, 0, 0)
        self.agregar_kpi(self.kpi_estudiantes, 0, 1)
        self.agregar_kpi(self.kpi_productos, 1, 0)
        self.agregar_kpi(self.kpi_avalados, 1, 1)
        self.agregar_kpi(self.kpi_promedio, 2, 0)
        self.agregar_kpi(self.kpi_aporte, 2, 1)

        # Minigráfico de barras apiladas (producción por año y tipología del grupo)
        self.grafico_barras = GraficoBarrasApiladas(
            titulo="Producción por tipología",
            subtitulo="Evolución anual de productos del grupo",
            parent=self,
        )
        self.grafico_barras.setFixedHeight(180)
        self.agregar_contenido(self.grafico_barras)

    def _alternar_detalles(self) -> None:
        visible = not self._panel_detalles.isVisible()
        self._panel_detalles.setVisible(visible)
        self.btn_detalles.setText("Ocultar detalles ⌃" if visible else "Ver más detalles ⌄")

    def actualizar(
        self,
        vista: dict[str, Any],
        datos_grupo: dict[str, Any],
        serie_anual: dict[int, dict[str, int]],
    ) -> None:
        self.mostrar_contenido()

        nombre = vista.get("nombre", "Grupo")
        cod = vista.get("codigo", "")
        cat = vista.get("categoria", "Sin clasificar")

        # Cabecera
        self.establecer_cabecera(
            nombre=nombre,
            subtitulo=f"Código: {cod} · Categoría: {cat}",
            iniciales=nombre,
        )

        # Panel de detalles
        while self._layout_detalles.count():
            item = self._layout_detalles.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        items_detalles = [
            ("Líder:", datos_grupo.get("lider") or "—"),
            ("Institución:", datos_grupo.get("institucion_principal") or "Universidad Popular del Cesar"),
            ("Área OCDE:", datos_grupo.get("area_ocde") or datos_grupo.get("gran_area_ocde") or "—"),
            ("Ubicación:", datos_grupo.get("departamento_ciudad") or "—"),
            ("Creación:", str(datos_grupo.get("fecha_creacion") or "—")),
        ]
        for k, v in items_detalles:
            fila = QHBoxLayout()
            fila.setContentsMargins(0, 0, 0, 0)
            l1 = QLabel(k, self._panel_detalles)
            l1.setStyleSheet(f"font-size: 8.5pt; color: {TEXTO_SECUNDARIO}; font-weight: 600;")
            l2 = QLabel(str(v), self._panel_detalles)
            l2.setStyleSheet(f"font-size: 8.5pt; color: {TEXTO};")
            fila.addWidget(l1)
            fila.addWidget(l2)
            fila.addStretch()
            self._layout_detalles.addLayout(fila)

        # 6 Fichas KPI
        integrantes_tabla = vista.get("integrantes")
        n_integrantes = len(integrantes_tabla.filas) if integrantes_tabla else 0
        estudiantes = vista.get("estudiantes", 0)
        prod_tot = vista.get("total_productos", 0)
        avalados = vista.get("productos_avalados", 0)
        prom = vista.get("promedio_por_investigador", 0.0)
        pct_inst = vista.get("porcentaje_sobre_institucion", 0.0)

        prod_por_anio = vista.get("productos_por_anio", {})
        tendencia = [prod_por_anio[a] for a in sorted(prod_por_anio.keys())]

        self.kpi_integrantes.actualizar(n_integrantes, "Integrantes vinculados")
        self.kpi_estudiantes.actualizar(estudiantes, "Rol estudiante")
        self.kpi_productos.actualizar(prod_tot, "En período", tendencia=tendencia)
        self.kpi_avalados.actualizar(avalados, "Con aval institucional")
        self.kpi_promedio.actualizar(prom, "Prod. / integrante")
        self.kpi_aporte.actualizar(f"{formatear_porcentaje(pct_inst)}", "Aporte institucional")

        # Barras apiladas
        self.grafico_barras.establecer_datos(serie_anual)

        # Estado del botón Activar / Desactivar
        self.configurar_estado_activo(bool(vista.get("activo", True)))


# ---------------------------------------------------------------------------
# Pantalla Principal de Directorio de Grupos
# ---------------------------------------------------------------------------


class PantallaGrupos(QWidget):
    """Pantalla 3: Directorio institucional de grupos de investigación con ficha lateral."""

    solicitar_navegacion = Signal(object)  # Emite el índice o enum de la pantalla destino
    ver_productos_solicitado = Signal(str)  # Emite el nombre del grupo para filtrar productos
    filtro_cambiado = Signal(object)       # Emite FiltroAnios cuando cambia el filtro
    datos_modificados = Signal()           # Emite cuando se altera la base de datos

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        filtro_global: FiltroAnios | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaGrupos")
        self._servicio = servicio
        self._ejecutor = ejecutor or EjecutorHilos.instancia()
        self._filtro_actual = filtro_global or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)
        self._grupo_seleccionado_cod: str | None = None
        self._grupo_seleccionado_nom: str = ""

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

        # Proporciones del divisor: Directorio flexible y Ficha 360 px
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setSizes([900, 360])

        layout_raiz.addWidget(self._splitter, 1)

    def _crear_barra_contexto(self) -> QWidget:
        barra = QWidget(self)
        barra.setFixedHeight(56)
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Título y subtítulo institucional
        col_tit = QVBoxLayout()
        col_tit.setContentsMargins(0, 4, 0, 4)
        col_tit.setSpacing(2)

        lbl_tit = QLabel("Grupos de Investigación", barra)
        lbl_tit.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {TEXTO};")
        col_tit.addWidget(lbl_tit)

        lbl_sub = QLabel("Directorio de grupos clasificados según Scienti / GrupLAC", barra)
        lbl_sub.setStyleSheet(f"font-size: 9.5pt; color: {TEXTO_SECUNDARIO};")
        col_tit.addWidget(lbl_sub)
        layout.addLayout(col_tit)

        layout.addStretch()

        # Chip de ventana global interactivo
        self.chip_ventana = ChipVentana(self._filtro_actual, parent=barra)
        self.chip_ventana.filtro_cambiado.connect(self._al_cambiar_filtro)
        self._chip_ventana = self.chip_ventana
        layout.addWidget(self.chip_ventana)

        # Menú desplegable «Exportar ▾»
        self.btn_exportar = QPushButton("Exportar ▾", barra)
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setStyleSheet(
            f"QPushButton {{ background-color: #FFFFFF; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {PRIMARIO}; border-radius: {RADIO_BOTON}px; padding: 7px 16px; font-size: 10pt; }}"
            f"QPushButton:hover {{ background-color: #F1F5F9; }}"
        )
        self._btn_exportar = self.btn_exportar
        menu_exp = QMenu(self.btn_exportar)
        act_csv = menu_exp.addAction("Exportar directorio visible a CSV")
        act_csv.triggered.connect(self._exportar_directorio_csv)
        self.btn_exportar.setMenu(menu_exp)
        layout.addWidget(self.btn_exportar)

        return barra

    def _crear_tarjeta_directorio(self) -> Tarjeta:
        tarjeta = Tarjeta(titulo="Directorio de grupos", con_sombra=True, parent=self)
        tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Contenedor de filtros y acciones superiores
        contenedor_filtros = QWidget(tarjeta)
        layout_f = QHBoxLayout(contenedor_filtros)
        layout_f.setContentsMargins(0, 0, 0, 8)
        layout_f.setSpacing(10)

        # Campo de búsqueda interactivo (Ctrl+F, 250 ms debounce)
        self.campo_busqueda = CampoBusqueda(
            placeholder="Buscar por nombre, código o líder…",
            retardo_ms=250,
            parent=contenedor_filtros,
        )
        self.campo_busqueda.texto_cambiado.connect(self._al_cambiar_texto_busqueda)
        layout_f.addWidget(self.campo_busqueda, 1)

        # Combo Categoría
        self.combo_categoria = QComboBox(contenedor_filtros)
        self.combo_categoria.setMinimumWidth(150)
        self.combo_categoria.addItem("Todas las categorías")
        for cat in ("A1", "A", "B", "C", "Reconocido", "Sin clasificar"):
            self.combo_categoria.addItem(cat)
        self.combo_categoria.currentTextChanged.connect(self._al_cambiar_combo_categoria)
        layout_f.addWidget(self.combo_categoria)

        # Combo Estado (Activos / Todos)
        self.combo_estado = QComboBox(contenedor_filtros)
        self.combo_estado.setMinimumWidth(110)
        self.combo_estado.addItem("Activos")
        self.combo_estado.addItem("Todos")
        self.combo_estado.currentTextChanged.connect(self._al_cambiar_combo_estado)
        layout_f.addWidget(self.combo_estado)

        # Botón primario «+ Nuevo grupo»
        self.btn_nuevo = QPushButton("+ Nuevo grupo", contenedor_filtros)
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
        self._modelo = ModeloDirectorioGrupos(parent=self.tabla)
        self._proxy = ProxyDirectorioGrupos(parent=self.tabla)
        self._proxy.setSourceModel(self._modelo)
        self.tabla.establecer_proxy(self._proxy)

        # Configurar delegados según especificación 6.3:
        # Col 0: Nombre (avatar + texto)
        # Col 1: Código GrupLAC (enlace copiable)
        # Col 2: Categoría (píldora)
        # Col 3: Líder (texto)
        # Col 4: Integrantes (número alineado a derecha)
        # Col 5: Productos (número alineado a derecha)
        # Col 6: Estado (píldora)
        self.tabla.establecer_delegado_columna(0, self.tabla.delegado_avatar)
        self.tabla.establecer_delegado_columna(1, self.tabla.delegado_enlace)
        self.tabla.establecer_delegado_columna(2, self.tabla.delegado_pildora)
        self.tabla.establecer_delegado_columna(3, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(4, self.tabla.delegado_numero)
        self.tabla.establecer_delegado_columna(5, self.tabla.delegado_numero)
        self.tabla.establecer_delegado_columna(6, self.tabla.delegado_pildora)

        # Conectar copia de código GrupLAC al gestor de avisos (toast)
        self.tabla.delegado_enlace.copiado.connect(
            lambda cod: GestorAvisos.instancia().mostrar(f"Código GrupLAC {cod} copiado al portapapeles.", tipo="info")
        )

        # Señales de selección y apertura de ficha completa
        self.tabla.clave_seleccionada.connect(self._al_seleccionar_clave)
        self.tabla.fila_doble_clic.connect(lambda _: self._al_pulsar_ver_ficha_completa())

        # Anchos preferidos de columnas
        self.tabla.ajustar_columnas({
            0: 240,
            1: 130,
            2: 110,
            3: 160,
            4: 100,
            5: 100,
            6: 90,
        })

        tarjeta.agregar_widget(self.tabla)
        return tarjeta

    def _crear_ficha_lateral(self) -> FichaGrupo:
        ficha = FichaGrupo(parent=self)

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

    def enfocar_busqueda(self) -> None:
        """Enfoca y selecciona el campo de búsqueda (atajo global Ctrl+F)."""
        self._al_atajo_buscar()

    # -----------------------------------------------------------------------
    # Filtrado y Reactividad
    # -----------------------------------------------------------------------

    def _al_cambiar_texto_busqueda(self, texto: str) -> None:
        self._proxy.establecer_texto_busqueda(texto)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_primera_fila()

    def _al_cambiar_combo_categoria(self, categoria: str) -> None:
        self._proxy.establecer_categoria(categoria)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_primera_fila()

    def _al_cambiar_combo_estado(self, texto_estado: str) -> None:
        solo_activos = texto_estado == "Activos"
        self._proxy.establecer_solo_activos(solo_activos)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_primera_fila()

    def _al_cambiar_filtro(self, nuevo_filtro: FiltroAnios) -> None:
        self._filtro_actual = nuevo_filtro
        self.filtro_cambiado.emit(nuevo_filtro)
        self.refrescar()

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Actualiza el filtro temporal desde el exterior."""
        self._filtro_actual = filtro
        self.chip_ventana.establecer_filtro(filtro)
        self.refrescar()

    def _auto_seleccionar_primera_fila(self) -> None:
        if self._proxy.rowCount() > 0:
            idx = self._proxy.index(0, 0)
            self.tabla.vista.setCurrentIndex(idx)
            clave = self._proxy.data(idx, Qt.ItemDataRole.UserRole)
            if clave:
                self._al_seleccionar_clave(str(clave))
        else:
            self._ficha_lateral.mostrar_vacio("No hay grupos que coincidan con los filtros aplicados")

    # -----------------------------------------------------------------------
    # Carga de Datos y Refresco
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Carga los grupos del servicio y actualiza la tabla y la ficha lateral."""
        try:
            # Obtener datos tabulares filtrados por la ventana de años
            tabla_datos = self._servicio.tabla_grupos(filtro=self._filtro_actual)
            registros: list[dict[str, Any]] = []

            for fila in tabla_datos.filas:
                # Fila: (codigo, nombre, categoria, lider, integrantes, productos, estado)
                cod = str(fila[0])
                nom = str(fila[1])
                cat = str(fila[2])
                lid = str(fila[3])
                integrantes = int(fila[4]) if fila[4] is not None else 0
                productos = int(fila[5]) if fila[5] is not None else 0
                activo = str(fila[6]).lower() == "activo"

                registros.append({
                    "codigo_gruplac": cod,
                    "nombre": nom,
                    "categoria": cat,
                    "lider": lid,
                    "integrantes": integrantes,
                    "productos": productos,
                    "activo": activo,
                })

            self._modelo.establecer_registros(registros)
            self.tabla.actualizar_pie()

            # Sincronizar selección previa o seleccionar primera fila
            filas_proxy = self._proxy.rowCount()
            fila_encontrada = -1
            if self._grupo_seleccionado_cod:
                for r in range(filas_proxy):
                    idx = self._proxy.index(r, 0)
                    if self._proxy.data(idx, Qt.ItemDataRole.UserRole) == self._grupo_seleccionado_cod:
                        fila_encontrada = r
                        break

            if fila_encontrada >= 0:
                idx = self._proxy.index(fila_encontrada, 0)
                self.tabla.vista.setCurrentIndex(idx)
                self._al_seleccionar_clave(self._grupo_seleccionado_cod)
            elif filas_proxy > 0:
                self._auto_seleccionar_primera_fila()
            else:
                self._ficha_lateral.mostrar_vacio("No hay grupos registrados en el catálogo")

        except Exception as err:
            GestorAvisos.instancia().mostrar(f"Error cargando directorio de grupos: {err}", tipo="error")

    def _al_seleccionar_clave(self, codigo_gruplac: str) -> None:
        """Carga y visualiza los datos en la ficha lateral para el grupo seleccionado."""
        self._grupo_seleccionado_cod = codigo_gruplac
        try:
            vista = self._servicio.vista_grupo(codigo_gruplac, self._filtro_actual)
            datos_grupo = self._servicio.datos_grupo(codigo_gruplac)
            serie_anual = self._servicio.serie_anual_por_categoria(self._filtro_actual, codigo_grupo=codigo_gruplac)
            self._grupo_seleccionado_nom = vista.get("nombre", "")
            self._ficha_lateral.actualizar(vista, datos_grupo, serie_anual)
        except Exception as err:
            self._ficha_lateral.mostrar_vacio(f"Error al cargar detalle del grupo: {err}")

    # -----------------------------------------------------------------------
    # Operaciones CRUD y Acciones de la Ficha
    # -----------------------------------------------------------------------

    def _al_pulsar_nuevo(self) -> None:
        dlg = DialogoGrupo(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            datos = dlg.obtener_datos()
            try:
                msg = self._servicio.crear_grupo(datos)
                self.datos_modificados.emit()
                self._grupo_seleccionado_cod = datos["codigo_gruplac"]
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al crear grupo: {e}", tipo="error")

    def _al_pulsar_editar(self) -> None:
        if not self._grupo_seleccionado_cod:
            return
        cod = self._grupo_seleccionado_cod
        try:
            datos_prev = self._servicio.datos_grupo(cod)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"No se pudieron cargar datos del grupo: {e}", tipo="error")
            return

        dlg = DialogoGrupo(datos_previos=datos_prev, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            nuevos_datos = dlg.obtener_datos()
            try:
                msg = self._servicio.actualizar_grupo(cod, nuevos_datos)
                self.datos_modificados.emit()
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al actualizar grupo: {e}", tipo="error")

    def _al_pulsar_cambiar_estado(self) -> None:
        if not self._grupo_seleccionado_cod:
            return
        cod = self._grupo_seleccionado_cod
        try:
            datos = self._servicio.datos_grupo(cod)
            nuevo_estado = not bool(datos.get("activo", True))
            msg = self._servicio.cambiar_estado("grupo", cod, nuevo_estado)
            self.datos_modificados.emit()
            self.refrescar()
            GestorAvisos.instancia().mostrar(msg, tipo="exito")
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al modificar estado: {e}", tipo="error")

    def _al_pulsar_eliminar(self) -> None:
        if not self._grupo_seleccionado_cod:
            return
        cod = self._grupo_seleccionado_cod
        try:
            cascada = self._servicio.describir_cascada("grupo", cod)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al inspeccionar dependencias: {e}", tipo="error")
            return

        dlg = DialogoConfirmarEliminar(
            titulo=f"Eliminar Grupo · {self._grupo_seleccionado_nom} ({cod})",
            descripcion_cascada=cascada,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self._servicio.eliminar("grupo", cod)
                self.datos_modificados.emit()
                self._grupo_seleccionado_cod = None
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al eliminar grupo: {e}", tipo="error")

    def _al_pulsar_ver_ficha_completa(self) -> None:
        if not self._grupo_seleccionado_cod:
            return
        try:
            vista = self._servicio.vista_grupo(self._grupo_seleccionado_cod, self._filtro_actual)
            dlg = DialogoFichaCompletaGrupo(vista, self._servicio, parent=self)
            dlg.exec()
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al abrir ficha completa: {e}", tipo="error")

    def _al_pulsar_ver_productos(self) -> None:
        if self._grupo_seleccionado_nom:
            self.ver_productos_solicitado.emit(self._grupo_seleccionado_nom)
        # Pestaña 3: Pantalla.PRODUCTOS
        self.solicitar_navegacion.emit(3)

    # -----------------------------------------------------------------------
    # Exportación
    # -----------------------------------------------------------------------

    def _exportar_directorio_csv(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Directorio de Grupos",
            "directorio_grupos.csv",
            "Archivos CSV (*.csv)",
        )
        if not ruta:
            return

        try:
            filas_visibles: list[list[str]] = []
            cols = [self._modelo.headerData(c, Qt.Orientation.Horizontal) for c in range(self._modelo.columnCount())]
            filas_visibles.append(cols)

            for r in range(self._proxy.rowCount()):
                fila_datos: list[str] = []
                for c in range(self._proxy.columnCount()):
                    idx = self._proxy.index(r, c)
                    val = self._proxy.data(idx, Qt.ItemDataRole.DisplayRole)
                    fila_datos.append(str(val) if val is not None else "")
                filas_visibles.append(fila_datos)

            with open(ruta, "w", newline="", encoding="utf-8") as f:
                escritor = csv.writer(f, delimiter=";")
                escritor.writerows(filas_visibles)

            GestorAvisos.instancia().mostrar(f"Directorio de grupos exportado a {Path(ruta).name}", tipo="exito")
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al exportar CSV: {e}", tipo="error")
