"""Pantalla 6: Gestión de datos (CRUD, activar/desactivar, cascadas y deshacer)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.servicios.servicio_aplicacion import ServicioAplicacion


class DialogoGrupo(QDialog):
    """Formulario modal para crear o editar un grupo de investigación."""

    def __init__(self, datos_previos: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo Grupo" if datos_previos is None else "Editar Grupo")
        self.setMinimumWidth(420)
        self.es_edicion = datos_previos is not None

        layout = QVBoxLayout(self)
        layout_form = QFormLayout()

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. COL0001234")
        if self.es_edicion:
            self.txt_codigo.setText(datos_previos.get("codigo_gruplac", ""))
            self.txt_codigo.setEnabled(False)
        layout_form.addRow("Código GrupLAC *:", self.txt_codigo)

        self.txt_nombre = QLineEdit(self)
        if datos_previos:
            self.txt_nombre.setText(datos_previos.get("nombre", ""))
        layout_form.addRow("Nombre del grupo *:", self.txt_nombre)

        self.combo_cat = QComboBox(self)
        self.combo_cat.addItems(["A1", "A", "B", "C", "Reconocido", "Sin clasificar"])
        if datos_previos and datos_previos.get("categoria"):
            self.combo_cat.setCurrentText(datos_previos["categoria"])
        layout_form.addRow("Categoría Minciencias:", self.combo_cat)

        self.txt_lider = QLineEdit(self)
        if datos_previos:
            self.txt_lider.setText(datos_previos.get("lider", "") or "")
        layout_form.addRow("Líder del grupo:", self.txt_lider)

        self.txt_inst = QLineEdit(self)
        self.txt_inst.setText(
            datos_previos.get("institucion_principal", "Universidad Popular del Cesar")
            if datos_previos
            else "Universidad Popular del Cesar"
        )
        layout_form.addRow("Institución principal:", self.txt_inst)

        layout.addLayout(layout_form)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def obtener_datos(self) -> dict[str, Any]:
        return {
            "codigo_gruplac": self.txt_codigo.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "categoria": self.combo_cat.currentText(),
            "lider": self.txt_lider.text().strip() or None,
            "institucion_principal": self.txt_inst.text().strip() or "Universidad Popular del Cesar",
        }


class DialogoInvestigador(QDialog):
    """Formulario modal para crear o editar un investigador."""

    def __init__(self, datos_previos: dict[str, Any] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo Investigador" if datos_previos is None else "Editar Investigador")
        self.setMinimumWidth(420)
        self.es_edicion = datos_previos is not None

        layout = QVBoxLayout(self)
        layout_form = QFormLayout()

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. 0000494917")
        if self.es_edicion:
            self.txt_codigo.setText(datos_previos.get("codigo_rh", ""))
            self.txt_codigo.setEnabled(False)
        layout_form.addRow("Código CvLAC (RH) *:", self.txt_codigo)

        self.txt_nombre = QLineEdit(self)
        if datos_previos:
            self.txt_nombre.setText(datos_previos.get("nombre_completo", ""))
        layout_form.addRow("Nombre completo *:", self.txt_nombre)

        self.combo_cat = QComboBox(self)
        self.combo_cat.addItems(["Emerito", "Senior", "Asociado", "Junior", "Sin categoria"])
        if datos_previos and datos_previos.get("categoria"):
            self.combo_cat.setCurrentText(datos_previos["categoria"])
        layout_form.addRow("Categoría Minciencias:", self.combo_cat)

        self.combo_form = QComboBox(self)
        self.combo_form.addItems(["Doctorado", "Maestria", "Especializacion", "Pregrado"])
        if datos_previos and datos_previos.get("formacion_academica"):
            self.combo_form.setCurrentText(datos_previos["formacion_academica"])
        layout_form.addRow("Formación académica:", self.combo_form)

        layout.addLayout(layout_form)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def obtener_datos(self) -> dict[str, Any]:
        return {
            "codigo_rh": self.txt_codigo.text().strip(),
            "nombre_completo": self.txt_nombre.text().strip(),
            "categoria": self.combo_cat.currentText(),
            "formacion_academica": self.combo_form.currentText(),
        }


class DialogoProducto(QDialog):
    """Formulario modal para registrar un nuevo producto enlazado en multilista."""

    def __init__(self, grupos: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo Producto Científico")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout_form = QFormLayout()

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. PROD-00123")
        layout_form.addRow("Código identificador *:", self.txt_codigo)

        self.txt_titulo = QLineEdit(self)
        layout_form.addRow("Título del producto *:", self.txt_titulo)

        self.combo_tipo = QComboBox(self)
        self.combo_tipo.addItems(["GNC", "DTI", "ASC", "FRH"])
        layout_form.addRow("Tipología mayor *:", self.combo_tipo)

        self.txt_subtipo = QLineEdit(self)
        self.txt_subtipo.setPlaceholderText("Artículo, Libro, Software...")
        layout_form.addRow("Subtipo:", self.txt_subtipo)

        self.spin_ano = QSpinBox(self)
        self.spin_ano.setRange(1950, 2030)
        self.spin_ano.setValue(2024)
        layout_form.addRow("Año de publicación *:", self.spin_ano)

        self.combo_val = QComboBox(self)
        self.combo_val.addItems(["Avalado", "Con soporte", "No avalado"])
        layout_form.addRow("Estado de validación:", self.combo_val)

        self.combo_grupo = QComboBox(self)
        self.combo_grupo.addItem("Sin grupo asignado", None)
        for cod, nom in grupos:
            self.combo_grupo.addItem(f"{nom} ({cod})", cod)
        layout_form.addRow("Grupo asociado:", self.combo_grupo)

        layout.addLayout(layout_form)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def obtener_datos(self) -> tuple[dict[str, Any], str | None]:
        datos = {
            "codigo_identificador": self.txt_codigo.text().strip(),
            "titulo": self.txt_titulo.text().strip(),
            "tipo_mayor": self.combo_tipo.currentText(),
            "subtipo": self.txt_subtipo.text().strip() or None,
            "ano": self.spin_ano.value(),
            "estado_validacion": self.combo_val.currentText(),
        }
        grupo_cod = self.combo_grupo.currentData()
        return datos, grupo_cod


class PantallaGestion(QWidget):
    """Gestión de entidades: altas, bajas, modificaciones, cascadas y reversión (Undo)."""

    datos_modificados = Signal()

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.servicio = servicio


        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 16, 20, 16)
        layout_principal.setSpacing(14)

        # Encabezado con botón Deshacer
        layout_cabecera = QHBoxLayout()
        lbl_titulo = QLabel("Gestión de Datos y Colecciones", self)
        lbl_titulo.setObjectName("tituloPantalla")
        layout_cabecera.addWidget(lbl_titulo)
        layout_cabecera.addStretch()

        self.btn_deshacer = QPushButton("↺ Deshacer última operación", self)
        self.btn_deshacer.setStyleSheet("font-weight: bold; background-color: #E3ECF8; color: #0D47A1;")
        self.btn_deshacer.clicked.connect(self._al_deshacer)
        layout_cabecera.addWidget(self.btn_deshacer)

        layout_principal.addLayout(layout_cabecera)

        # Aviso de bloqueo de escritura si aplica
        self.lbl_bloqueo = QLabel("", self)
        self.lbl_bloqueo.setObjectName("bloqueo")
        self.lbl_bloqueo.setVisible(False)
        layout_principal.addWidget(self.lbl_bloqueo)

        # Pestañas de entidades
        self.pestanas = QTabWidget(self)

        # ----------------- Pestaña Grupos -----------------
        widget_grupos = QWidget()
        layout_grp = QVBoxLayout(widget_grupos)
        layout_grp.setContentsMargins(10, 10, 10, 10)

        layout_bar_grp = QHBoxLayout()
        btn_nuevo_grp = QPushButton("+ Nuevo Grupo", widget_grupos)
        btn_nuevo_grp.setObjectName("primario")
        btn_nuevo_grp.clicked.connect(self._al_nuevo_grupo)
        layout_bar_grp.addWidget(btn_nuevo_grp)

        btn_editar_grp = QPushButton("Editar Grupo", widget_grupos)
        btn_editar_grp.clicked.connect(self._al_editar_grupo)
        layout_bar_grp.addWidget(btn_editar_grp)

        btn_toggle_grp = QPushButton("Activar / Desactivar", widget_grupos)
        btn_toggle_grp.clicked.connect(lambda: self._al_toggle_estado("grupo", self.tabla_grupos, self.modelo_grupos))
        layout_bar_grp.addWidget(btn_toggle_grp)

        btn_eliminar_grp = QPushButton("Eliminar (Cascada)", widget_grupos)
        btn_eliminar_grp.setObjectName("peligro")
        btn_eliminar_grp.clicked.connect(lambda: self._al_eliminar_entidad("grupo", self.tabla_grupos, self.modelo_grupos))
        layout_bar_grp.addWidget(btn_eliminar_grp)

        layout_bar_grp.addStretch()
        layout_grp.addLayout(layout_bar_grp)

        self.tabla_grupos = QTableView(widget_grupos)
        self.modelo_grupos = ModeloTabla(parent=self.tabla_grupos)
        self.tabla_grupos.setModel(self.modelo_grupos)
        self.tabla_grupos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_grupos.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout_grp.addWidget(self.tabla_grupos)

        self.pestanas.addTab(widget_grupos, "Grupos de Investigación")

        # ----------------- Pestaña Investigadores -----------------
        widget_inv = QWidget()
        layout_inv = QVBoxLayout(widget_inv)
        layout_inv.setContentsMargins(10, 10, 10, 10)

        layout_bar_inv = QHBoxLayout()
        btn_nuevo_inv = QPushButton("+ Nuevo Investigador", widget_inv)
        btn_nuevo_inv.setObjectName("primario")
        btn_nuevo_inv.clicked.connect(self._al_nuevo_investigador)
        layout_bar_inv.addWidget(btn_nuevo_inv)

        btn_editar_inv = QPushButton("Editar Investigador", widget_inv)
        btn_editar_inv.clicked.connect(self._al_editar_investigador)
        layout_bar_inv.addWidget(btn_editar_inv)

        btn_toggle_inv = QPushButton("Activar / Desactivar", widget_inv)
        btn_toggle_inv.clicked.connect(lambda: self._al_toggle_estado("investigador", self.tabla_inv, self.modelo_inv))
        layout_bar_inv.addWidget(btn_toggle_inv)

        btn_eliminar_inv = QPushButton("Eliminar (Cascada)", widget_inv)
        btn_eliminar_inv.setObjectName("peligro")
        btn_eliminar_inv.clicked.connect(lambda: self._al_eliminar_entidad("investigador", self.tabla_inv, self.modelo_inv))
        layout_bar_inv.addWidget(btn_eliminar_inv)

        layout_bar_inv.addStretch()
        layout_inv.addLayout(layout_bar_inv)

        self.tabla_inv = QTableView(widget_inv)
        self.modelo_inv = ModeloTabla(parent=self.tabla_inv)
        self.tabla_inv.setModel(self.modelo_inv)
        self.tabla_inv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_inv.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout_inv.addWidget(self.tabla_inv)

        self.pestanas.addTab(widget_inv, "Investigadores")

        # ----------------- Pestaña Productos -----------------
        widget_prd = QWidget()
        layout_prd = QVBoxLayout(widget_prd)
        layout_prd.setContentsMargins(10, 10, 10, 10)

        layout_bar_prd = QHBoxLayout()
        btn_nuevo_prd = QPushButton("+ Nuevo Producto", widget_prd)
        btn_nuevo_prd.setObjectName("primario")
        btn_nuevo_prd.clicked.connect(self._al_nuevo_producto)
        layout_bar_prd.addWidget(btn_nuevo_prd)

        btn_toggle_prd = QPushButton("Activar / Desactivar", widget_prd)
        btn_toggle_prd.clicked.connect(lambda: self._al_toggle_estado("producto", self.tabla_prd, self.modelo_prd))
        layout_bar_prd.addWidget(btn_toggle_prd)

        btn_eliminar_prd = QPushButton("Eliminar", widget_prd)
        btn_eliminar_prd.setObjectName("peligro")
        btn_eliminar_prd.clicked.connect(lambda: self._al_eliminar_entidad("producto", self.tabla_prd, self.modelo_prd))
        layout_bar_prd.addWidget(btn_eliminar_prd)

        layout_bar_prd.addStretch()
        layout_prd.addLayout(layout_bar_prd)

        self.tabla_prd = QTableView(widget_prd)
        self.modelo_prd = ModeloTabla(parent=self.tabla_prd)
        self.tabla_prd.setModel(self.modelo_prd)
        self.tabla_prd.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_prd.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout_prd.addWidget(self.tabla_prd)

        self.pestanas.addTab(widget_prd, "Productos Científicos")

        layout_principal.addWidget(self.pestanas)

    def refrescar(self) -> None:
        est = self.servicio.estado()
        bloqueo = est.motivo_bloqueo
        if bloqueo:
            self.lbl_bloqueo.setText(f"⚠ Escritura restringida: {bloqueo}")
            self.lbl_bloqueo.setVisible(True)
        else:
            self.lbl_bloqueo.setVisible(False)

        self.btn_deshacer.setEnabled(est.operaciones_deshacer > 0 and est.escritura_permitida)
        self.btn_deshacer.setText(f"↺ Deshacer ({est.operaciones_deshacer})")

        self.modelo_grupos.establecer_tabla(self.servicio.tabla_grupos())
        self.modelo_inv.establecer_tabla(self.servicio.tabla_investigadores())
        self.modelo_prd.establecer_tabla(self.servicio.tabla_productos(incluir_inactivos=True))

    def _obtener_codigo_seleccionado(self, tabla: QTableView, modelo: ModeloTabla) -> str | None:
        indexes = tabla.selectionModel().selectedRows()
        if not indexes:
            return None
        fila = indexes[0].row()
        return modelo.obtener_clave_fila(fila)

    def _al_nuevo_grupo(self) -> None:
        dlg = DialogoGrupo(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self.servicio.crear_grupo(dlg.obtener_datos())
                QMessageBox.information(self, "Grupo Creado", msg)
                self.refrescar()
            except Exception as err:
                QMessageBox.warning(self, "Error al crear grupo", str(err))

    def _al_editar_grupo(self) -> None:
        cod = self._obtener_codigo_seleccionado(self.tabla_grupos, self.modelo_grupos)
        if not cod:
            QMessageBox.information(self, "Selección requerida", "Seleccione un grupo para editar.")
            return
        datos = self.servicio.datos_grupo(cod)
        dlg = DialogoGrupo(datos_previos=datos, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self.servicio.actualizar_grupo(cod, dlg.obtener_datos())
                QMessageBox.information(self, "Grupo Actualizado", msg)
                self.refrescar()
            except Exception as err:
                QMessageBox.warning(self, "Error al actualizar", str(err))

    def _al_nuevo_investigador(self) -> None:
        dlg = DialogoInvestigador(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self.servicio.crear_investigador(dlg.obtener_datos())
                QMessageBox.information(self, "Investigador Creado", msg)
                self.refrescar()
            except Exception as err:
                QMessageBox.warning(self, "Error al crear investigador", str(err))

    def _al_editar_investigador(self) -> None:
        cod = self._obtener_codigo_seleccionado(self.tabla_inv, self.modelo_inv)
        if not cod:
            QMessageBox.information(self, "Selección requerida", "Seleccione un investigador para editar.")
            return
        datos = self.servicio.datos_investigador(cod)
        dlg = DialogoInvestigador(datos_previos=datos, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                msg = self.servicio.actualizar_investigador(cod, dlg.obtener_datos())
                QMessageBox.information(self, "Investigador Actualizado", msg)
                self.refrescar()
            except Exception as err:
                QMessageBox.warning(self, "Error al actualizar", str(err))

    def _al_nuevo_producto(self) -> None:
        grupos = list(self.servicio.opciones_grupos())
        dlg = DialogoProducto(grupos=grupos, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            datos, cod_grp = dlg.obtener_datos()
            try:
                msg = self.servicio.crear_producto(datos, codigo_grupo=cod_grp)
                QMessageBox.information(self, "Producto Creado", msg)
                self.refrescar()
            except Exception as err:
                QMessageBox.warning(self, "Error al crear producto", str(err))

    def _al_toggle_estado(self, entidad: str, tabla: QTableView, modelo: ModeloTabla) -> None:
        cod = self._obtener_codigo_seleccionado(tabla, modelo)
        if not cod:
            QMessageBox.information(self, "Selección requerida", f"Seleccione un {entidad} en la tabla.")
            return
        indexes = tabla.selectionModel().selectedRows()
        fila = indexes[0].row()
        estado_actual = modelo.tabla_actual.filas[fila][-1]
        nuevo_activo = estado_actual != "Activo"
        try:
            self.servicio.cambiar_estado(entidad, cod, nuevo_activo)
            self.refrescar()
            self.datos_modificados.emit()

        except Exception as err:
            QMessageBox.warning(self, "Error al cambiar estado", str(err))

    def _al_eliminar_entidad(self, entidad: str, tabla: QTableView, modelo: ModeloTabla) -> None:
        cod = self._obtener_codigo_seleccionado(tabla, modelo)
        if not cod:
            QMessageBox.information(self, "Selección requerida", f"Seleccione un {entidad} para eliminar.")
            return
        cascada = self.servicio.describir_cascada(entidad, cod)
        resp = QMessageBox.question(
            self,
            f"Confirmar eliminación de {entidad}",
            f"{cascada}\n\n¿Desea proceder con la eliminación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                msg = self.servicio.eliminar(entidad, cod)
                QMessageBox.information(self, "Eliminado", msg)
                self.refrescar()
                self.datos_modificados.emit()
            except Exception as err:
                QMessageBox.warning(self, "Error al eliminar", str(err))

    def _al_deshacer(self) -> None:
        try:
            msg = self.servicio.deshacer()
            QMessageBox.information(self, "Operación Deshecha", msg)
            self.refrescar()
            self.datos_modificados.emit()
        except Exception as err:
            QMessageBox.warning(self, "Error al deshacer", str(err))

