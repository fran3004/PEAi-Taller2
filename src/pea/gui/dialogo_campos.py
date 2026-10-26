"""Edición de campos complementarios con nombres legibles y validación del dominio."""

import json

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

ETIQUETAS = {
    "nombre": "Nombre",
    "categoria": "Categoría",
    "lider": "Líder",
    "pais": "País",
    "institucion_principal": "Institución principal",
    "departamento_ciudad": "Departamento / ciudad",
    "gran_area_ocde": "Gran área OCDE",
    "area_ocde": "Área OCDE",
    "fecha_creacion": "Fecha de creación (AAAA-MM-DD)",
    "nombre_completo": "Nombre completo",
    "nombre_en_citas": "Nombre en citas",
    "documento_identidad": "Documento de identidad",
    "par_evaluador": "Par evaluador",
    "formacion_academica": "Formación académica",
    "nacionalidad": "Nacionalidad",
    "sexo": "Sexo",
    "detalles": "Información complementaria (JSON)",
    "titulo": "Título",
    "tipo_mayor": "Tipología mayor",
    "subtipo": "Subtipo",
    "ano": "Año",
    "mes": "Mes (0 = sin dato)",
    "estado_validacion": "Estado de validación",
}


class DialogoCampos(QDialog):
    def __init__(self, datos: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar campos de la entidad")
        self.resize(620, 640)
        self.originales = datos
        self.campos = {}
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cuerpo = QWidget()
        form = QFormLayout(cuerpo)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for clave, valor in datos.items():
            if isinstance(valor, bool):
                campo = QCheckBox()
                campo.setChecked(valor)
            elif clave in {"ano", "mes"}:
                campo = QSpinBox()
                campo.setRange(1970 if clave == "ano" else 0, 2100 if clave == "ano" else 12)
                campo.setValue(valor or 0)
            elif isinstance(valor, dict):
                campo = QPlainTextEdit(json.dumps(valor, ensure_ascii=False, indent=2))
                campo.setMinimumHeight(160)
            else:
                campo = QLineEdit(str(valor or ""))
            etiqueta = ETIQUETAS.get(clave, clave.replace("_", " ").capitalize())
            campo.setAccessibleName(etiqueta)
            self.campos[clave] = campo
            form.addRow(etiqueta, campo)
        scroll.setWidget(cuerpo)
        layout.addWidget(scroll)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar cambios")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def cambios(self):
        resultado = {}
        for clave, campo in self.campos.items():
            if isinstance(campo, QCheckBox):
                valor = campo.isChecked()
            elif isinstance(campo, QSpinBox):
                valor = campo.value() or None
            elif isinstance(campo, QPlainTextEdit):
                valor = json.loads(campo.toPlainText())
                if not isinstance(valor, dict):
                    raise ValueError("La información complementaria debe ser un objeto JSON.")
            else:
                valor = campo.text().strip() or None
            if valor != self.originales[clave]:
                resultado[clave] = valor
        return resultado
