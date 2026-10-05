"""Diálogos modales institucionales de creación y edición de entidades.

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 8).
- Radio definido por los tokens de estilo; botones primario y secundario.
- Errores de validación visibles bajo cada campo en color ERROR.
- Incluye:
  * DialogoGrupo (creación y edición)
  * DialogoInvestigador (creación y edición)
  * DialogoProducto (creación)
  * DialogoEditarProducto (edición mediante actualizar_producto)
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pea.gui import estilo
from pea.gui.estilo import (
    COLOR_DTI,
    ERROR,
    LINEA,
    PRIMARIO,
    PRIMARIO_HOVER,
    RADIO_BOTON,
    TEXTO,
    TEXTO_SECUNDARIO,
)


class DialogoBase(QDialog):
    """Clase base para formularios modales de PEA-i con estilo institucional y validación."""

    def __init__(self, titulo: str, subtitulo: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet(
            f"QDialog {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"}}"
            f"QLineEdit, QComboBox, QSpinBox {{"
            f"  background-color: {estilo.SUPERFICIE};"
            f"  color: {TEXTO};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"  padding: 8px 12px;"
            f"  font-size: {estilo.TAMANO_CUERPO}pt;"
            f"}}"
            f"QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{"
            f"  border: 1px solid {COLOR_DTI};"
            f"}}"
            f"QLineEdit:disabled, QComboBox:disabled {{"
            f"  background-color: {estilo.FONDO_APP};"
            f"  color: {TEXTO_SECUNDARIO};"
            f"}}"
        )

        self._layout_raiz = QVBoxLayout(self)
        self._layout_raiz.setContentsMargins(24, 20, 24, 20)
        self._layout_raiz.setSpacing(14)

        # Encabezado del diálogo
        self._cabecera = QWidget(self)
        layout_cab = QVBoxLayout(self._cabecera)
        layout_cab.setContentsMargins(0, 0, 0, 0)
        layout_cab.setSpacing(4)

        fila_tit = QHBoxLayout()
        fila_tit.setSpacing(8)

        barra_acento = QFrame(self._cabecera)
        barra_acento.setFixedWidth(3)
        barra_acento.setFixedHeight(22)
        barra_acento.setStyleSheet(f"background-color: {COLOR_DTI}; border-radius: 1px;")
        fila_tit.addWidget(barra_acento)

        self._lbl_titulo = QLabel(titulo, self._cabecera)
        self._lbl_titulo.setStyleSheet(f"font-size: {estilo.TAMANO_TITULO_TARJETA}pt; font-weight: bold; color: {TEXTO};")
        fila_tit.addWidget(self._lbl_titulo)
        fila_tit.addStretch()
        layout_cab.addLayout(fila_tit)

        if subtitulo:
            self._lbl_sub = QLabel(subtitulo, self._cabecera)
            self._lbl_sub.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
            layout_cab.addWidget(self._lbl_sub)

        self._layout_raiz.addWidget(self._cabecera)

        # Contenedor del formulario
        self._cuerpo_form = QWidget(self)
        self._layout_form = QVBoxLayout(self._cuerpo_form)
        self._layout_form.setContentsMargins(0, 4, 0, 4)
        self._layout_form.setSpacing(10)
        self._layout_raiz.addWidget(self._cuerpo_form)

        # Botones de pie
        fila_botones = QHBoxLayout()
        fila_botones.setContentsMargins(0, 10, 0, 0)
        fila_botones.setSpacing(10)
        fila_botones.addStretch()

        self.btn_cancelar = QPushButton("Cancelar", self)
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setStyleSheet(
            f"QPushButton {{ background-color: {estilo.SUPERFICIE}; color: {TEXTO_SECUNDARIO}; font-weight: 600; "
            f"border: 1px solid {LINEA}; border-radius: {RADIO_BOTON}px; padding: 8px 16px; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {estilo.FONDO_APP}; color: {TEXTO}; }}"
        )
        self.btn_cancelar.clicked.connect(self.reject)
        fila_botones.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("Guardar", self)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet(
            f"QPushButton {{ background-color: {PRIMARIO}; color: {estilo.SUPERFICIE}; font-weight: 600; "
            f"border: none; border-radius: {RADIO_BOTON}px; padding: 8px 20px; font-size: {estilo.TAMANO_CUERPO}pt; }}"
            f"QPushButton:hover {{ background-color: {PRIMARIO_HOVER}; }}"
        )
        self.btn_guardar.clicked.connect(self._al_pulsar_guardar)
        fila_botones.addWidget(self.btn_guardar)

        self._layout_raiz.addLayout(fila_botones)

    def _agregar_campo(
        self,
        etiqueta_texto: str,
        widget_entrada: QWidget,
        mensaje_error: str = "",
    ) -> QLabel:
        """Agrega un campo al formulario con etiqueta arriba y mensaje de error debajo."""
        bloque = QWidget(self._cuerpo_form)
        layout_b = QVBoxLayout(bloque)
        layout_b.setContentsMargins(0, 0, 0, 0)
        layout_b.setSpacing(3)

        lbl_eti = QLabel(etiqueta_texto, bloque)
        lbl_eti.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; font-weight: 600; color: {TEXTO};")
        layout_b.addWidget(lbl_eti)

        layout_b.addWidget(widget_entrada)

        lbl_err = QLabel(mensaje_error, bloque)
        lbl_err.setStyleSheet(f"font-size: {estilo.TAMANO_AUXILIAR}pt; color: {ERROR}; padding-left: 2px;")
        lbl_err.setVisible(False)
        layout_b.addWidget(lbl_err)

        self._layout_form.addWidget(bloque)
        return lbl_err

    def _al_pulsar_guardar(self) -> None:
        """Valida el formulario antes de aceptar."""
        if self.validar():
            self.accept()

    def validar(self) -> bool:
        """Método de validación implementado por cada diálogo concreto."""
        return True


# ---------------------------------------------------------------------------
# Diálogo de Grupo de Investigación
# ---------------------------------------------------------------------------


class DialogoGrupo(DialogoBase):
    """Formulario modal para crear o editar un grupo de investigación."""

    def __init__(
        self,
        datos_previos: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self.es_edicion = datos_previos is not None
        titulo = "Editar grupo de investigación" if self.es_edicion else "Nuevo grupo de investigación"
        subtitulo = "Información institucional registrada en Scienti / GrupLAC"
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. COL0001234")
        if self.es_edicion:
            self.txt_codigo.setText(str(datos_previos.get("codigo_gruplac", "")))
            self.txt_codigo.setEnabled(False)
        self._err_codigo = self._agregar_campo("Código GrupLAC *:", self.txt_codigo, "El código GrupLAC es obligatorio.")

        self.txt_nombre = QLineEdit(self)
        self.txt_nombre.setPlaceholderText("Nombre oficial del grupo")
        if self.es_edicion:
            self.txt_nombre.setText(str(datos_previos.get("nombre", "")))
        self._err_nombre = self._agregar_campo("Nombre del grupo *:", self.txt_nombre, "El nombre del grupo es obligatorio.")

        self.combo_cat = QComboBox(self)
        self.combo_cat.addItems(["A1", "A", "B", "C", "Reconocido", "Sin clasificar"])
        if self.es_edicion and datos_previos.get("categoria"):
            self.combo_cat.setCurrentText(str(datos_previos["categoria"]))
        self._agregar_campo("Categoría Minciencias:", self.combo_cat)

        self.txt_lider = QLineEdit(self)
        self.txt_lider.setPlaceholderText("Nombre del investigador líder")
        if self.es_edicion and datos_previos.get("lider"):
            self.txt_lider.setText(str(datos_previos["lider"]))
        self._agregar_campo("Líder del grupo:", self.txt_lider)

        self.txt_inst = QLineEdit(self)
        inst_defecto = "Universidad Popular del Cesar"
        if self.es_edicion:
            inst_defecto = str(datos_previos.get("institucion_principal", inst_defecto))
        self.txt_inst.setText(inst_defecto)
        self._agregar_campo("Institución principal:", self.txt_inst)

    def validar(self) -> bool:
        valido = True
        if not self.txt_codigo.text().strip():
            self._err_codigo.setVisible(True)
            valido = False
        else:
            self._err_codigo.setVisible(False)

        if not self.txt_nombre.text().strip():
            self._err_nombre.setVisible(True)
            valido = False
        else:
            self._err_nombre.setVisible(False)

        return valido

    def obtener_datos(self) -> dict[str, Any]:
        return {
            "codigo_gruplac": self.txt_codigo.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "categoria": self.combo_cat.currentText(),
            "lider": self.txt_lider.text().strip() or None,
            "institucion_principal": self.txt_inst.text().strip() or "Universidad Popular del Cesar",
        }


# ---------------------------------------------------------------------------
# Diálogo de Investigador
# ---------------------------------------------------------------------------


class DialogoInvestigador(DialogoBase):
    """Formulario modal para crear o editar un investigador."""

    def __init__(
        self,
        datos_previos: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self.es_edicion = datos_previos is not None
        titulo = "Editar investigador" if self.es_edicion else "Nuevo investigador"
        subtitulo = "Datos del investigador vinculados a su hoja de vida CvLAC"
        super().__init__(titulo=titulo, subtitulo=subtitulo, parent=parent)

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. 0000494917")
        if self.es_edicion:
            self.txt_codigo.setText(str(datos_previos.get("codigo_rh", "")))
            self.txt_codigo.setEnabled(False)
        self._err_codigo = self._agregar_campo("Código CvLAC (RH) *:", self.txt_codigo, "El código CvLAC es obligatorio.")

        self.txt_nombre = QLineEdit(self)
        self.txt_nombre.setPlaceholderText("Nombres y apellidos completos")
        if self.es_edicion:
            self.txt_nombre.setText(str(datos_previos.get("nombre_completo", "")))
        self._err_nombre = self._agregar_campo("Nombre completo *:", self.txt_nombre, "El nombre completo es obligatorio.")

        self.combo_cat = QComboBox(self)
        self.combo_cat.addItems(["Emérito", "Senior", "Asociado", "Junior", "Sin categoría"])
        if self.es_edicion and datos_previos.get("categoria"):
            cat_norm = str(datos_previos["categoria"]).replace("Emerito", "Emérito").replace("Sin categoria", "Sin categoría")
            self.combo_cat.setCurrentText(cat_norm)
        self._agregar_campo("Categoría Minciencias:", self.combo_cat)

        self.combo_form = QComboBox(self)
        self.combo_form.addItems(["Doctorado", "Maestría", "Especialización", "Pregrado", "Sin especificar"])
        if self.es_edicion and datos_previos.get("formacion_academica"):
            form_norm = str(datos_previos["formacion_academica"]).replace("Maestria", "Maestría").replace("Especializacion", "Especialización")
            self.combo_form.setCurrentText(form_norm)
        self._agregar_campo("Formación académica:", self.combo_form)

    def validar(self) -> bool:
        valido = True
        if not self.txt_codigo.text().strip():
            self._err_codigo.setVisible(True)
            valido = False
        else:
            self._err_codigo.setVisible(False)

        if not self.txt_nombre.text().strip():
            self._err_nombre.setVisible(True)
            valido = False
        else:
            self._err_nombre.setVisible(False)

        return valido

    def obtener_datos(self) -> dict[str, Any]:
        return {
            "codigo_rh": self.txt_codigo.text().strip(),
            "nombre_completo": self.txt_nombre.text().strip(),
            "categoria": self.combo_cat.currentText(),
            "formacion_academica": self.combo_form.currentText(),
        }


# ---------------------------------------------------------------------------
# Diálogo de Creación de Producto
# ---------------------------------------------------------------------------


class DialogoProducto(DialogoBase):
    """Formulario modal para registrar un nuevo producto científico enlazado en multilista."""

    def __init__(
        self,
        grupos: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            titulo="Nuevo producto científico",
            subtitulo="Registro clasificado según las 4 tipologías del Modelo 2024",
            parent=parent,
        )

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setPlaceholderText("Ej. PROD-00123")
        self._err_codigo = self._agregar_campo("Código identificador *:", self.txt_codigo, "El código del producto es obligatorio.")

        self.txt_titulo = QLineEdit(self)
        self.txt_titulo.setPlaceholderText("Título completo del producto o artículo")
        self._err_titulo = self._agregar_campo("Título del producto *:", self.txt_titulo, "El título del producto es obligatorio.")

        self.combo_tipo = QComboBox(self)
        self.combo_tipo.addItems(["GNC", "DTI", "ASC", "FRH"])
        self._agregar_campo("Tipología mayor *:", self.combo_tipo)

        self.txt_subtipo = QLineEdit(self)
        self.txt_subtipo.setPlaceholderText("Artículo, Libro, Software, Tesis...")
        self._agregar_campo("Subtipo de producto:", self.txt_subtipo)

        self.spin_ano = QSpinBox(self)
        self.spin_ano.setRange(1950, 2030)
        self.spin_ano.setValue(2024)
        self._agregar_campo("Año de publicación *:", self.spin_ano)

        self.combo_val = QComboBox(self)
        self.combo_val.addItems(["Avalado", "Con soporte", "No avalado"])
        self._agregar_campo("Estado de validación:", self.combo_val)

        self.combo_grupo = QComboBox(self)
        self.combo_grupo.addItem("Sin grupo asignado", None)
        if grupos:
            for cod, nom in grupos:
                self.combo_grupo.addItem(f"{nom} ({cod})", cod)
        self._agregar_campo("Grupo de investigación asociado:", self.combo_grupo)

    def validar(self) -> bool:
        valido = True
        if not self.txt_codigo.text().strip():
            self._err_codigo.setVisible(True)
            valido = False
        else:
            self._err_codigo.setVisible(False)

        if not self.txt_titulo.text().strip():
            self._err_titulo.setVisible(True)
            valido = False
        else:
            self._err_titulo.setVisible(False)

        return valido

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


# ---------------------------------------------------------------------------
# Diálogo de Edición de Producto (usa actualizar_producto)
# ---------------------------------------------------------------------------


class DialogoEditarProducto(DialogoBase):
    """Formulario modal para modificar los datos de un producto existente."""

    def __init__(
        self,
        datos_previos: dict[str, Any],
        grupos: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            titulo="Editar producto científico",
            subtitulo="Actualización de metadatos, tipología, año o grupo asociado",
            parent=parent,
        )
        self._codigo_original = str(datos_previos.get("codigo_identificador", datos_previos.get("codigo", "")))

        self.txt_codigo = QLineEdit(self)
        self.txt_codigo.setText(self._codigo_original)
        self.txt_codigo.setEnabled(False)
        self._agregar_campo("Código identificador:", self.txt_codigo)

        self.txt_titulo = QLineEdit(self)
        self.txt_titulo.setText(str(datos_previos.get("titulo", "")))
        self._err_titulo = self._agregar_campo("Título del producto *:", self.txt_titulo, "El título no puede estar vacío.")

        self.combo_tipo = QComboBox(self)
        self.combo_tipo.addItems(["GNC", "DTI", "ASC", "FRH"])
        tipo_prev = str(datos_previos.get("tipo_mayor", datos_previos.get("tipologia", "GNC")))
        self.combo_tipo.setCurrentText(tipo_prev)
        self._agregar_campo("Tipología mayor *:", self.combo_tipo)

        self.txt_subtipo = QLineEdit(self)
        self.txt_subtipo.setText(str(datos_previos.get("subtipo", "") or ""))
        self._agregar_campo("Subtipo de producto:", self.txt_subtipo)

        self.spin_ano = QSpinBox(self)
        self.spin_ano.setRange(1950, 2030)
        self.spin_ano.setValue(int(datos_previos.get("ano", datos_previos.get("anio", 2024))))
        self._agregar_campo("Año de publicación *:", self.spin_ano)

        self.combo_val = QComboBox(self)
        self.combo_val.addItems(["Avalado", "Con soporte", "No avalado"])
        val_prev = str(datos_previos.get("estado_validacion", datos_previos.get("validacion", "Avalado")))
        self.combo_val.setCurrentText(val_prev)
        self._agregar_campo("Estado de validación:", self.combo_val)

        self.combo_grupo = QComboBox(self)
        self.combo_grupo.addItem("Sin grupo asignado", None)
        grupo_prev = datos_previos.get("codigo_grupo", datos_previos.get("grupo_codigo", None))
        if grupos:
            for cod, nom in grupos:
                self.combo_grupo.addItem(f"{nom} ({cod})", cod)
                if cod == grupo_prev:
                    self.combo_grupo.setCurrentIndex(self.combo_grupo.count() - 1)
        self._agregar_campo("Grupo de investigación asociado:", self.combo_grupo)

    def validar(self) -> bool:
        if not self.txt_titulo.text().strip():
            self._err_titulo.setVisible(True)
            return False
        self._err_titulo.setVisible(False)
        return True

    def obtener_datos(self) -> tuple[str, dict[str, Any]]:
        """Devuelve el código identificador y el diccionario de campos para actualizar_producto."""
        datos = {
            "titulo": self.txt_titulo.text().strip(),
            "tipo_mayor": self.combo_tipo.currentText(),
            "subtipo": self.txt_subtipo.text().strip() or None,
            "ano": self.spin_ano.value(),
            "estado_validacion": self.combo_val.currentText(),
            "codigo_grupo": self.combo_grupo.currentData(),
        }
        return self._codigo_original, datos
