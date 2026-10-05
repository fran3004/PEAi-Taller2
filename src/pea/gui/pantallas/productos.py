"""Pantalla 4: Catálogo de Productos Científicos (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.4).
- Barra de contexto: título «Catálogo de productos», subtítulo institucional,
  ChipVentana global y menú «Exportar ▾» (CSV del catálogo visible o filtrado).
- Tarjeta de Catálogo de Productos:
  * Cabecera con búsqueda («Buscar por título, código o autor…», Ctrl+F, debounce 250 ms),
    combos Tipología (GNC, DTI, ASC, FRH), Validación (Avalado, Con soporte, No avalado)
    y Estado (Activos/Todos), y botón primario «+ Nuevo producto».
  * Tabla con filas de 48 px, hover superficie de gr?fico, selección superficie seleccionada con barra de acento de 3 px,
    encabezado FICHA en 10 pt negrita, ordenación insensible a mayúsculas y numérica en años.
  * Columnas: Código (enlace copiable con toast), Título (hasta 2 líneas con elipsis),
    Tipología (píldora con color de dato), Subtipo, Año (número centrado),
    Validación (píldora), Grupo, Autores (primer autor + «+N») y Estado (píldora).
  * Inactivos renderizados con 60 % de opacidad y píldora «Inactivo».
  * Pie de tabla con conteo dinámico «Mostrando N de M productos».
- Ficha lateral (360 px):
  * Título, código, píldoras de tipología y validación, año, grupo y subtipo.
  * Lista de coautores interactiva (avatar 28 px + nombre; clic abre su ficha en Investigadores).
  * Insignia de la ventana del Modelo 2024 con tooltip explicativo
    («✔ Dentro de la ventana del Modelo 2024» / «✖ Fuera de la ventana…»).
  * Botones de acción: Editar (DialogoEditarProducto), Activar/Desactivar y Eliminar…
- Sincronización con el filtro de años global.
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
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.componentes.avatar import Avatar
from pea.gui.componentes.campo_busqueda import CampoBusqueda
from pea.gui.componentes.ficha_lateral import FichaLateral
from pea.gui.componentes.filtro_anios import ChipVentana
from pea.gui.componentes.pildora import Pildora
from pea.gui.componentes.tabla import (
    ROL_ACTIVO,
    ColumnSpecification,
    TablaEstilizada,
)
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.toast import GestorAvisos
from pea.gui.dialogos import DialogoEditarProducto, DialogoProducto
from pea.gui.ejecutor import EjecutorHilos
from pea.gui.estilo import (
    AVISO,
    AVISO_FONDO,
    COLOR_DTI,
    ERROR,
    EXITO,
    EXITO_FONDO,
    FICHA,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
)
from pea.servicios.servicio_aplicacion import ServicioAplicacion
from pea.servicios.vistas import FiltroAnios, ModoFiltroAnios

# ---------------------------------------------------------------------------
# Modelo de Datos del Catálogo de Productos
# ---------------------------------------------------------------------------


class ModeloCatalogoProductos(QAbstractTableModel):
    """Modelo tabular especializado para el catálogo de productos científicos."""

    COLUMNAS = (
        "Código",
        "Título",
        "Tipología",
        "Subtipo",
        "Año",
        "Validación",
        "Grupo",
        "Autores",
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
                return reg["codigo"]
            if col == 1:
                return reg["titulo"]
            if col == 2:
                return reg["tipo_mayor"]
            if col == 3:
                return reg["subtipo"] or "—"
            if col == 4:
                return reg["ano"]
            if col == 5:
                return reg["validacion"]
            if col == 6:
                return reg["grupo"] or "Sin grupo"
            if col == 7:
                # Formato primer autor + «+N»
                autores = reg["autores_lista"]
                if not autores:
                    return reg.get("autores_texto", "Sin autores")
                if len(autores) == 1:
                    return autores[0]
                return f"{autores[0]} (+{len(autores) - 1})"
            if col == 8:
                return "Activo" if reg["activo"] else "Inactivo"

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 4:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == ROL_ACTIVO:
            return reg["activo"]

        if role == Qt.ItemDataRole.UserRole:
            return reg["codigo"]

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
        return reg["codigo"] if reg else None


# ---------------------------------------------------------------------------
# Proxy de Filtrado y Ordenamiento
# ---------------------------------------------------------------------------


class ProxyCatalogoProductos(QSortFilterProxyModel):
    """Proxy para búsqueda textual, filtro por tipología, validación, estado y orden."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._texto_busqueda: str = ""
        self._tipologia_filtro: str = "Todas las tipologías"
        self._validacion_filtro: str = "Todas"
        self._solo_activos: bool = True
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def establecer_texto_busqueda(self, texto: str) -> None:
        self._texto_busqueda = texto.strip().lower()
        self.invalidate()

    def establecer_tipologia(self, tipologia: str) -> None:
        self._tipologia_filtro = tipologia
        self.invalidate()

    def establecer_validacion(self, validacion: str) -> None:
        self._validacion_filtro = validacion
        self.invalidate()

    def establecer_solo_activos(self, solo_activos: bool) -> None:
        self._solo_activos = solo_activos
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex) -> bool:
        modelo = self.sourceModel()
        if not isinstance(modelo, ModeloCatalogoProductos):
            return True

        reg = modelo.registro_en_fila(source_row)
        if reg is None:
            return False

        # 1. Filtro por estado activo
        if self._solo_activos and not reg["activo"]:
            return False

        # 2. Filtro por tipología
        if self._tipologia_filtro != "Todas las tipologías":
            sigla = self._tipologia_filtro.split(" ")[0].strip()
            if reg["tipo_mayor"] != sigla:
                return False

        # 3. Filtro por validación
        if self._validacion_filtro != "Todas":
            if reg["validacion"] != self._validacion_filtro:
                return False

        # 4. Filtro textual (título, código o autores)
        if self._texto_busqueda:
            texto_todo = f"{reg['codigo']} {reg['titulo']} {reg.get('autores_texto', '')}".lower()
            if self._texto_busqueda not in texto_todo:
                return False

        return True

    def lessThan(
        self,
        source_left: QModelIndex | QPersistentModelIndex,
        source_right: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        col = source_left.column()
        # Columna 4 (Año): orden numérico
        if col == 4:
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
    """Diálogo modal que presenta la descripción de cascada antes de eliminar un producto."""

    def __init__(self, titulo: str, descripcion_cascada: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background-color: {estilo.SUPERFICIE}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Encabezado con ícono
        fila_tit = QHBoxLayout()
        fila_tit.setSpacing(10)
        lbl_ico = QLabel("⚠️", self)
        lbl_ico.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt;")
        fila_tit.addWidget(lbl_ico)

        lbl_tit = QLabel("¿Confirmar eliminación permanente?", self)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {TEXTO};")
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
        lbl_cascada.setStyleSheet(f"color: {AVISO}; font-size: {estilo.TAMANO_CUERPO}pt; font-weight: 500;")
        layout_aviso.addWidget(lbl_cascada)

        lbl_undo = QLabel("Nota: La operación se guardará en la pila de deshacer (Ctrl+Z).", cuadro_aviso)
        lbl_undo.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {estilo.TAMANO_AUXILIAR}pt;")
        layout_aviso.addWidget(lbl_undo)

        layout.addWidget(cuadro_aviso)

        # Botones de acción
        fila_btn = QHBoxLayout()
        fila_btn.setSpacing(10)
        fila_btn.addStretch()

        btn_cancelar = QPushButton("Cancelar", self)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO}; border: 1px solid {LINEA}; "
            f"border-radius: {RADIO_BOTON}px; padding: 8px 16px; font-weight: 600; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        btn_cancelar.clicked.connect(self.reject)
        fila_btn.addWidget(btn_cancelar)

        btn_eliminar = QPushButton("Eliminar permanentemente", self)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.setStyleSheet(
            f"QPushButton {{ background-color: {ERROR}; color: {estilo.SUPERFICIE}; border: none; "
            f"border-radius: {RADIO_BOTON}px; padding: 8px 18px; font-weight: bold; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.ERROR_HOVER}; }}"
        )
        btn_eliminar.clicked.connect(self.accept)
        fila_btn.addWidget(btn_eliminar)

        self.btn_cancelar = btn_cancelar
        self.btn_confirmar = btn_eliminar

        layout.addLayout(fila_btn)


# ---------------------------------------------------------------------------
# Ficha Lateral del Producto (FichaProducto, 360 px)
# ---------------------------------------------------------------------------


class FichaProducto(FichaLateral):
    """Ficha lateral de 360 px para visualización detallada de un producto científico."""

    autor_clicado = Signal(str)  # Emite el código o nombre del investigador clicado

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, diametro_avatar=64)
        self.setObjectName("fichaProducto")

        # Ocultar avatar de persona ya que es un producto
        self._avatar.setVisible(False)

        # Configurar nombre a alineación izquierda y tamaño adaptable
        self._lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._lbl_nombre.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {TEXTO};")

        self._lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Ocultar botones de ficha amplia y catálogo de productos (no aplican en productos)
        self.btn_ver_completa.setVisible(False)
        self.btn_ver_productos.setVisible(False)

        # -------------------------------------------------------------------
        # Contenido Específico de Producto
        # -------------------------------------------------------------------

        # 1. Metadatos generales (Año, Grupo, Subtipo)
        self._cuadro_meta = QFrame(self._cuerpo)
        self._cuadro_meta.setStyleSheet(
            f"QFrame {{ background-color: {FICHA}; border-radius: {estilo.RADIO_BOTON}px; padding: 6px; }}"
        )
        self._layout_meta = QVBoxLayout(self._cuadro_meta)
        self._layout_meta.setContentsMargins(10, 8, 10, 8)
        self._layout_meta.setSpacing(5)
        self.agregar_contenido(self._cuadro_meta)

        # 2. Insignia de la ventana del Modelo 2024
        self.insignia_ventana = QFrame(self._cuerpo)
        layout_ins = QHBoxLayout(self.insignia_ventana)
        layout_ins.setContentsMargins(10, 8, 10, 8)
        layout_ins.setSpacing(8)

        self.lbl_insignia_ventana = QLabel("✔ Dentro de la ventana del Modelo 2024", self.insignia_ventana)
        self.lbl_insignia_ventana.setWordWrap(True)
        self.lbl_insignia_ventana.setStyleSheet(f"font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt;")
        layout_ins.addWidget(self.lbl_insignia_ventana)

        self.agregar_contenido(self.insignia_ventana)

        # 3. Sección de Coautores y Colaboradores
        self._contenedor_autores = QWidget(self._cuerpo)
        self._layout_autores = QVBoxLayout(self._contenedor_autores)
        self._layout_autores.setContentsMargins(0, 4, 0, 0)
        self._layout_autores.setSpacing(6)

        lbl_tit_autores = QLabel("Autores y colaboradores vinculados", self._contenedor_autores)
        lbl_tit_autores.setStyleSheet(f"font-size: {estilo.TAMANO_CUERPO}pt; font-weight: bold; color: {TEXTO};")
        self._layout_autores.addWidget(lbl_tit_autores)

        self._caja_lista_autores = QVBoxLayout()
        self._caja_lista_autores.setSpacing(6)
        self._layout_autores.addLayout(self._caja_lista_autores)

        self._lbl_titulo = self._lbl_nombre
        self._lbl_codigo = self._lbl_subtitulo
        self._insignia_ventana = self.insignia_ventana
        self._contenedor_coautores = self._contenedor_autores
        self._filas_autores: list[QFrame] = []
        self._filas_coautores = self._filas_autores
        self._lbl_anio = QLabel("", self)
        self._pildora_tipologia = Pildora("GNC", parent=self)
        self._pildora_validacion = Pildora("Avalado", parent=self)

        self.agregar_contenido(self._contenedor_autores)

    def actualizar(self, detalle: dict[str, Any]) -> None:
        self.mostrar_contenido()

        titulo = detalle.get("titulo", "Producto sin título")
        codigo = detalle.get("codigo", "")
        tipo = detalle.get("tipo_mayor", "GNC")
        val = detalle.get("validacion", "Avalado")
        activo = bool(detalle.get("activo", True))
        ano = detalle.get("ano", 2024)
        subtipo = detalle.get("subtipo", "—")
        grupo = detalle.get("grupo", "Sin grupo")
        en_ventana = bool(detalle.get("en_ventana_modelo_2024", False))

        pildoras: list[tuple[str, str | None]] = [
            (tipo, None),
            (val, None),
        ]
        if not activo:
            pildoras.append(("Inactivo", "aviso"))

        self.establecer_cabecera(
            nombre=titulo,
            subtitulo=f"Código: {codigo}",
            pildoras=pildoras,
        )
        self._avatar.setVisible(False)
        self._lbl_titulo = self._lbl_nombre
        self._lbl_codigo = self._lbl_subtitulo
        self._lbl_anio.setText(str(ano))

        # Metadatos del cuadro
        while self._layout_meta.count():
            item = self._layout_meta.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        items_meta = [
            ("Año de publicación:", str(ano)),
            ("Subtipo:", str(subtipo)),
            ("Grupo de investigación:", str(grupo)),
        ]
        for k, v in items_meta:
            fila = QHBoxLayout()
            fila.setContentsMargins(0, 0, 0, 0)
            l1 = QLabel(k, self._cuadro_meta)
            l1.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; font-weight: 600;")
            l2 = QLabel(v, self._cuadro_meta)
            l2.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO};")
            fila.addWidget(l1)
            fila.addWidget(l2)
            fila.addStretch()
            self._layout_meta.addLayout(fila)

        # Insignia de la ventana del Modelo 2024
        if en_ventana:
            self.insignia_ventana.setStyleSheet(
                f"QFrame {{ background-color: {EXITO_FONDO}; border: 1px solid {estilo.EXITO_BORDE_SUAVE}; "
                f"border-radius: {estilo.RADIO_BOTON}px; }}"
            )
            self.lbl_insignia_ventana.setText("✔ Dentro de la ventana del Modelo 2024")
            self.lbl_insignia_ventana.setStyleSheet(f"color: {EXITO}; font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt;")
            self.insignia_ventana.setToolTip(
                "Cumple con la ventana de observación del Modelo Minciencias 2024\n"
                "(5 años para artículos, software, ASC y FRH; 10 años para libros y patentes)."
            )
        else:
            self.insignia_ventana.setStyleSheet(
                f"QFrame {{ background-color: {estilo.ERROR_FONDO}; border: 1px solid {estilo.ERROR_DESHABILITADO}; border-radius: {estilo.RADIO_BOTON}px; }}"
            )
            self.lbl_insignia_ventana.setText("✖ Fuera de la ventana del Modelo 2024")
            self.lbl_insignia_ventana.setStyleSheet(f"color: {ERROR}; font-weight: 600; font-size: {estilo.TAMANO_AUXILIAR}pt;")
            self.insignia_ventana.setToolTip(
                "No se encuentra dentro de la ventana de observación del Modelo Minciencias 2024\n"
                "(5 años para artículos, software, ASC y FRH; 10 años para libros y patentes)."
            )

        # Lista de autores interactiva
        while self._caja_lista_autores.count():
            item = self._caja_lista_autores.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self._filas_autores.clear()
        autores_lista = detalle.get("autores_lista", ())
        if not autores_lista and detalle.get("autores"):
            # Si solo vino la tupla de strings
            autores_lista = [{"nombre": a, "codigo_rh": ""} for a in detalle["autores"]]

        if autores_lista:
            for aut in autores_lista:
                nombre_aut = aut.get("nombre", "") if isinstance(aut, dict) else str(aut)
                cod_rh = aut.get("codigo_rh", "") if isinstance(aut, dict) else ""

                fila_aut = QFrame(self._contenedor_autores)
                fila_aut.setCursor(Qt.CursorShape.PointingHandCursor)
                fila_aut.setStyleSheet(
                    "QFrame { background: transparent; border-radius: {estilo.RADIO_BOTON}px; padding: 2px 4px; }"
                    "QFrame:hover { background-color: {estilo.FONDO_APP}; }"
                )
                lay_aut = QHBoxLayout(fila_aut)
                lay_aut.setContentsMargins(4, 2, 4, 2)
                lay_aut.setSpacing(8)

                av_aut = Avatar(diametro=28, nombre=nombre_aut, parent=fila_aut)
                lay_aut.addWidget(av_aut)

                lbl_aut = QLabel(nombre_aut, fila_aut)
                lbl_aut.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: 600; color: {COLOR_DTI};")
                lbl_aut.setWordWrap(True)
                lay_aut.addWidget(lbl_aut, 1)

                # Conectar clic a apertura de su ficha en Investigadores
                destino = cod_rh or nombre_aut
                fila_aut._identificador = destino
                fila_aut.mousePressEvent = lambda _, d=destino: self.autor_clicado.emit(d)

                self._filas_autores.append(fila_aut)
                self._caja_lista_autores.addWidget(fila_aut)
        else:
            lbl_sin = QLabel("Sin autores registrados para este producto", self._contenedor_autores)
            lbl_sin.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO}; padding: 4px;")
            self._caja_lista_autores.addWidget(lbl_sin)

        # Estado del botón Activar / Desactivar
        self.configurar_estado_activo(activo)


# ---------------------------------------------------------------------------
# Pantalla Principal de Catálogo de Productos
# ---------------------------------------------------------------------------


class PantallaProductos(QWidget):
    """Pantalla 4: Catálogo institucional de productos con filtros y ficha lateral."""

    solicitar_navegacion = Signal(object)        # Emite el índice o enum de la pantalla destino
    filtro_cambiado = Signal(object)             # Emite FiltroAnios cuando cambia el filtro
    datos_modificados = Signal()                 # Emite cuando se altera la base de datos
    abrir_investigador_solicitado = Signal(str)  # Emite el código o nombre del autor para abrirlo

    def __init__(
        self,
        servicio: ServicioAplicacion,
        ejecutor: EjecutorHilos | None = None,
        filtro_global: FiltroAnios | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaProductos")
        self._servicio = servicio
        self._ejecutor = ejecutor or EjecutorHilos.instancia()
        self._filtro_actual = filtro_global or FiltroAnios(modo=ModoFiltroAnios.MODELO_2024)
        self._producto_seleccionado_cod: str | None = None

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

        # 2. Contenedor central: Tarjeta Catálogo + Ficha Lateral (360 px)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._splitter.setHandleWidth(12)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background: transparent; }"
        )

        # Tarjeta izquierda: Catálogo
        self._tarjeta_catalogo = self._crear_tarjeta_catalogo()
        self._splitter.addWidget(self._tarjeta_catalogo)

        # Ficha lateral derecha: 360 px
        self._ficha_lateral = self._crear_ficha_lateral()
        self._splitter.addWidget(self._ficha_lateral)

        # Proporciones del divisor: Catálogo flexible y Ficha 360 px
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setSizes([900, 320])

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

        lbl_tit = QLabel("Catálogo de Productos", barra)
        lbl_tit.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_PANTALLA}pt; font-weight: bold; color: {TEXTO};")
        col_tit.addWidget(lbl_tit)

        lbl_sub = QLabel("Producción científica clasificada en las 4 tipologías del Modelo Minciencias", barra)
        lbl_sub.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
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
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {PRIMARIO}; font-weight: 600; "
            f"border: 1px solid {PRIMARIO}; border-radius: {RADIO_BOTON}px; padding: 7px 16px; font-size: {estilo.TAMANO_AUXILIAR}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; }}"
        )
        self._btn_exportar = self.btn_exportar
        menu_exp = QMenu(self.btn_exportar)
        act_csv = menu_exp.addAction("Exportar catálogo visible a CSV")
        act_csv.triggered.connect(self._exportar_catalogo_csv)
        self.btn_exportar.setMenu(menu_exp)
        layout.addWidget(self.btn_exportar)

        return barra

    def _crear_tarjeta_catalogo(self) -> Tarjeta:
        tarjeta = Tarjeta(titulo="Catálogo de productos", con_sombra=True, parent=self)
        tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Contenedor de filtros y acciones superiores
        contenedor_filtros = QWidget(tarjeta)
        layout_f = QHBoxLayout(contenedor_filtros)
        layout_f.setContentsMargins(0, 0, 0, 8)
        layout_f.setSpacing(10)

        # Campo de búsqueda interactivo (Ctrl+F, 250 ms debounce)
        self.campo_busqueda = CampoBusqueda(
            placeholder="Buscar por título, código o autor…",
            retardo_ms=250,
            parent=contenedor_filtros,
        )
        self.campo_busqueda.texto_cambiado.connect(self._al_cambiar_texto_busqueda)
        layout_f.addWidget(self.campo_busqueda, 1)

        # Combo Tipología
        self.combo_tipologia = QComboBox(contenedor_filtros)
        self.combo_tipologia.setMinimumWidth(160)
        self.combo_tipologia.addItem("Todas las tipologías")
        self.combo_tipologia.addItem("GNC – Generación de nuevo conocimiento")
        self.combo_tipologia.addItem("DTI – Desarrollo tecnológico e innovación")
        self.combo_tipologia.addItem("ASC – Apropiación social del conocimiento")
        self.combo_tipologia.addItem("FRH – Formación de recurso humano")
        self.combo_tipologia.currentTextChanged.connect(self._al_cambiar_combo_tipologia)
        layout_f.addWidget(self.combo_tipologia)

        # Combo Validación
        self.combo_validacion = QComboBox(contenedor_filtros)
        self.combo_validacion.setMinimumWidth(110)
        self.combo_validacion.addItem("Todas")
        self.combo_validacion.addItem("Avalado")
        self.combo_validacion.addItem("Con soporte")
        self.combo_validacion.addItem("No avalado")
        self.combo_validacion.currentTextChanged.connect(self._al_cambiar_combo_validacion)
        layout_f.addWidget(self.combo_validacion)

        # Combo Estado (Activos / Todos)
        self.combo_estado = QComboBox(contenedor_filtros)
        self.combo_estado.setMinimumWidth(100)
        self.combo_estado.addItem("Activos")
        self.combo_estado.addItem("Todos")
        self.combo_estado.currentTextChanged.connect(self._al_cambiar_combo_estado)
        layout_f.addWidget(self.combo_estado)

        # Botón primario «+ Nuevo producto»
        self.btn_nuevo = QPushButton("+ Nuevo producto", contenedor_filtros)
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: {estilo.SUPERFICIE}; font-weight: bold; "
            f"border: none; border-radius: {RADIO_BOTON}px; padding: 8px 16px; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
        )
        self.btn_nuevo.clicked.connect(self._al_pulsar_nuevo)
        layout_f.addWidget(self.btn_nuevo)

        tarjeta.agregar_widget(contenedor_filtros)

        # Tabla institucional
        self.tabla = TablaEstilizada(parent=tarjeta)
        self._modelo = ModeloCatalogoProductos(parent=self.tabla)
        self._proxy = ProxyCatalogoProductos(parent=self.tabla)
        self._proxy.setSourceModel(self._modelo)
        self.tabla.establecer_proxy(self._proxy)

        # Configurar delegados según especificación 6.4:
        # Col 0: Código (enlace copiable con toast)
        # Col 1: Título (texto con elipsis)
        # Col 2: Tipología (píldora cromática)
        # Col 3: Subtipo (texto)
        # Col 4: Año (número centrado)
        # Col 5: Validación (píldora)
        # Col 6: Grupo (texto)
        # Col 7: Autores (texto)
        # Col 8: Estado (píldora)
        self.tabla.establecer_delegado_columna(0, self.tabla.delegado_enlace)
        self.tabla.establecer_delegado_columna(1, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(2, self.tabla.delegado_pildora)
        self.tabla.establecer_delegado_columna(3, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(4, self.tabla.delegado_numero)
        self.tabla.establecer_delegado_columna(5, self.tabla.delegado_pildora)
        self.tabla.establecer_delegado_columna(6, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(7, self.tabla.delegado_texto)
        self.tabla.establecer_delegado_columna(8, self.tabla.delegado_pildora)

        # Conectar copia de código al gestor de avisos (toast)
        self.tabla.delegado_enlace.copiado.connect(
            lambda cod: GestorAvisos.instancia().mostrar(f"Código de producto {cod} copiado al portapapeles.", tipo="info")
        )

        # Señales de selección
        self.tabla.clave_seleccionada.connect(self._al_seleccionar_clave)

        # Anchos preferidos de columnas
        self.tabla.configurar_columnas([
            ColumnSpecification("fijo", 80, 3),
            ColumnSpecification("estirar", 220, 1),
            ColumnSpecification("contenido", 85, 3),
            ColumnSpecification("contenido", 100, 2),
            ColumnSpecification("fijo", 65, 2),
            ColumnSpecification("contenido", 95, 3),
            ColumnSpecification("contenido", 120, 2),
            ColumnSpecification("contenido", 120, 3),
            ColumnSpecification("contenido", 85, 3),
        ])

        tarjeta.agregar_widget(self.tabla)
        return tarjeta

    def _crear_ficha_lateral(self) -> FichaProducto:
        ficha = FichaProducto(parent=self)

        # Conectar señales de acciones
        ficha.editar_solicitado.connect(self._al_pulsar_editar)
        ficha.cambiar_estado_solicitado.connect(self._al_pulsar_cambiar_estado)
        ficha.eliminar_solicitado.connect(self._al_pulsar_eliminar)
        ficha.autor_clicado.connect(self._al_clic_autor)

        return ficha

    def _configurar_atajos(self) -> None:
        # Ctrl+F: enfocar campo de búsqueda
        atajo_buscar = QShortcut(QKeySequence.StandardKey.Find, self)
        atajo_buscar.activated.connect(self._al_atajo_buscar)

    def _al_atajo_buscar(self) -> None:
        self.campo_busqueda.setFocus()
        self.campo_busqueda.selectAll()

    def enfocar_busqueda(self) -> None:
        """Enfoca y selecciona el campo de búsqueda (atajo global Ctrl+F)."""
        self._al_atajo_buscar()

    def filtrar_por_texto(self, texto: str) -> None:
        """Establece el texto en el campo de búsqueda y actualiza el filtro."""
        self.campo_busqueda.establecer_texto(texto)
        self._al_cambiar_texto_busqueda(texto)

    # -----------------------------------------------------------------------
    # Filtrado y Reactividad
    # -----------------------------------------------------------------------

    def _al_cambiar_texto_busqueda(self, texto: str) -> None:
        self._proxy.establecer_texto_busqueda(texto)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_primera_fila()

    def _al_cambiar_combo_tipologia(self, tipologia: str) -> None:
        self._proxy.establecer_tipologia(tipologia)
        self.tabla.actualizar_pie()
        self._auto_seleccionar_primera_fila()

    def _al_cambiar_combo_validacion(self, validacion: str) -> None:
        self._proxy.establecer_validacion(validacion)
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
            self._ficha_lateral.mostrar_vacio("No hay productos que coincidan con los filtros aplicados")

    # -----------------------------------------------------------------------
    # Carga de Datos y Refresco
    # -----------------------------------------------------------------------

    def refrescar(self) -> None:
        """Carga los productos del catálogo filtrados por la ventana de años."""
        try:
            tabla_datos = self._servicio.tabla_productos(filtro=self._filtro_actual, incluir_inactivos=True)
            registros: list[dict[str, Any]] = []

            for fila in tabla_datos.filas:
                # Fila: (codigo, titulo, tipologia, subtipo, ano, validacion, grupo, autores, estado)
                cod = str(fila[0])
                tit = str(fila[1])
                tipo = str(fila[2])
                subt = str(fila[3])
                ano = int(fila[4]) if fila[4] is not None else 0
                val = str(fila[5])
                grp = str(fila[6])
                aut_txt = str(fila[7])
                activo = str(fila[8]).lower() == "activo"

                # Separar autores si vienen por coma
                aut_lista = [a.strip() for a in aut_txt.split(",") if a.strip()]

                registros.append({
                    "codigo": cod,
                    "titulo": tit,
                    "tipo_mayor": tipo,
                    "subtipo": subt,
                    "ano": ano,
                    "validacion": val,
                    "grupo": grp,
                    "autores_lista": aut_lista,
                    "autores_texto": aut_txt,
                    "activo": activo,
                })

            self._modelo.establecer_registros(registros)
            self.tabla.actualizar_pie()

            # Sincronizar selección previa o seleccionar primera fila
            filas_proxy = self._proxy.rowCount()
            fila_encontrada = -1
            if self._producto_seleccionado_cod:
                for r in range(filas_proxy):
                    idx = self._proxy.index(r, 0)
                    if self._proxy.data(idx, Qt.ItemDataRole.UserRole) == self._producto_seleccionado_cod:
                        fila_encontrada = r
                        break

            if fila_encontrada >= 0:
                idx = self._proxy.index(fila_encontrada, 0)
                self.tabla.vista.setCurrentIndex(idx)
                self._al_seleccionar_clave(self._producto_seleccionado_cod)
            elif filas_proxy > 0:
                self._auto_seleccionar_primera_fila()
            else:
                self._ficha_lateral.mostrar_vacio("No hay productos registrados en esta ventana temporal")

        except Exception as err:
            GestorAvisos.instancia().mostrar(f"Error cargando catálogo de productos: {err}", tipo="error")

    def _al_seleccionar_clave(self, codigo_producto: str) -> None:
        """Carga y visualiza los datos en la ficha lateral para el producto seleccionado."""
        self._producto_seleccionado_cod = codigo_producto
        try:
            detalle = self._servicio.detalle_producto(codigo_producto)
            self._ficha_lateral.actualizar(detalle)
        except Exception as err:
            self._ficha_lateral.mostrar_vacio(f"Error al cargar detalle del producto: {err}")

    def _al_clic_autor(self, identificador_autor: str) -> None:
        """Navega a la pantalla de Investigadores para ver al autor seleccionado."""
        self.abrir_investigador_solicitado.emit(identificador_autor)
        # Pestaña 1: Pantalla.INVESTIGADORES
        self.solicitar_navegacion.emit(1)

    # -----------------------------------------------------------------------
    # Operaciones CRUD y Acciones de la Ficha
    # -----------------------------------------------------------------------

    def _al_pulsar_nuevo(self) -> None:
        opciones_grupos = self._servicio.opciones_grupos()
        dlg = DialogoProducto(grupos=opciones_grupos, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            datos, codigo_grupo = dlg.obtener_datos()
            try:
                msg = self._servicio.crear_producto(datos, codigo_grupo=codigo_grupo)
                self.datos_modificados.emit()
                self._producto_seleccionado_cod = datos["codigo_identificador"]
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al registrar producto: {e}", tipo="error")

    def _al_pulsar_editar(self) -> None:
        if not self._producto_seleccionado_cod:
            return
        cod = self._producto_seleccionado_cod
        try:
            detalle = self._servicio.detalle_producto(cod)
            opciones_grupos = self._servicio.opciones_grupos()
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"No se pudieron cargar datos del producto: {e}", tipo="error")
            return

        dlg = DialogoEditarProducto(datos_previos=detalle, grupos=opciones_grupos, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            cod_orig, nuevos_datos = dlg.obtener_datos()
            try:
                msg = self._servicio.actualizar_producto(cod_orig, nuevos_datos)
                self.datos_modificados.emit()
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al actualizar producto: {e}", tipo="error")

    def _al_pulsar_cambiar_estado(self) -> None:
        if not self._producto_seleccionado_cod:
            return
        cod = self._producto_seleccionado_cod
        try:
            detalle = self._servicio.detalle_producto(cod)
            nuevo_estado = not bool(detalle.get("activo", True))
            msg = self._servicio.cambiar_estado("producto", cod, nuevo_estado)
            self.datos_modificados.emit()
            self.refrescar()
            GestorAvisos.instancia().mostrar(msg, tipo="exito")
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al cambiar estado del producto: {e}", tipo="error")

    def _al_pulsar_eliminar(self) -> None:
        if not self._producto_seleccionado_cod:
            return
        cod = self._producto_seleccionado_cod
        try:
            cascada = self._servicio.describir_cascada("producto", cod)
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al inspeccionar dependencias: {e}", tipo="error")
            return

        dlg = DialogoConfirmarEliminar(
            titulo=f"Eliminar Producto · {cod}",
            descripcion_cascada=cascada,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self._servicio.eliminar("producto", cod)
                self.datos_modificados.emit()
                self._producto_seleccionado_cod = None
                self.refrescar()
                GestorAvisos.instancia().mostrar(msg, tipo="exito")
            except Exception as e:
                GestorAvisos.instancia().mostrar(f"Error al eliminar producto: {e}", tipo="error")

    # -----------------------------------------------------------------------
    # Exportación
    # -----------------------------------------------------------------------

    def _exportar_catalogo_csv(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Catálogo de Productos",
            "catalogo_productos.csv",
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

            GestorAvisos.instancia().mostrar(f"Catálogo de productos exportado a {Path(ruta).name}", tipo="exito")
        except Exception as e:
            GestorAvisos.instancia().mostrar(f"Error al exportar CSV: {e}", tipo="error")
