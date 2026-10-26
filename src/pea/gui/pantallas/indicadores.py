"""Indicador de producción científica y archivos de trabajo del Parcial 2."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pea.datos.archivo_local import guardar_archivo
from pea.excepciones import ErrorPEA
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.indicadores import calcular_indicador, modelo
from pea.servicios.servicio_dominio import CatalogoInvestigacion


class PantallaIndicadores(QWidget):
    datos_modificados = Signal()

    def __init__(self, servicio, ejecutor, parent=None):
        super().__init__(parent)
        self.setObjectName("pantallaIndicadores")
        self.servicio, self.ejecutor = servicio, ejecutor
        self._referencia = None
        self._resultado = None
        self._ocupado = False
        self._catalogo_descargado = None
        exterior = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cuerpo = QWidget()
        layout = QVBoxLayout(cuerpo)
        layout.setContentsMargins(24, 20, 24, 24)
        titulo = QLabel("Producción científica · Parcial 2")
        titulo.setObjectName("tituloPantalla")
        layout.addWidget(titulo)
        ayuda = QLabel(
            "Calcule el indicador de un grupo o investigador con categorías y pesos del Modelo 2024. "
            "El desglose muestra productos incluidos, exclusiones y referencia de normalización."
        )
        ayuda.setWordWrap(True)
        layout.addWidget(ayuda)
        controles = QGridLayout()
        self.ambito = QComboBox()
        self.ambito.addItem("Grupo", "grupo")
        self.ambito.addItem("Investigador", "investigador")
        self.entidad = QComboBox()
        self.entidad.setMinimumWidth(0)
        self.entidad.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.entidad.setMinimumContentsLength(18)
        self.corte = QSpinBox()
        self.corte.setRange(1970, 2100)
        self.corte.setValue(2023)
        self.desde = QSpinBox()
        self.desde.setRange(1969, 2100)
        self.desde.setSpecialValueText("Ventanas del Modelo")
        self.desde.setValue(1969)
        for fila, (texto, widget) in enumerate(
            [
                ("Ámbito", self.ambito),
                ("Grupo o investigador", self.entidad),
                ("Año de corte", self.corte),
                ("Límite inicial opcional", self.desde),
            ]
        ):
            etiqueta = QLabel(texto)
            etiqueta.setBuddy(widget)
            widget.setAccessibleName(texto)
            controles.addWidget(etiqueta, fila, 0)
            controles.addWidget(widget, fila, 1)
        self.url = QLineEdit()
        self.url.setPlaceholderText("URL HTTPS de GrupLAC o CvLAC")
        self.url.setAccessibleName("URL SCIENTI para calcular el indicador")
        controles.addWidget(self.url, 4, 0, 1, 2)
        self.calcular = QPushButton("Calcular catálogo")
        self.descargar = QPushButton("Calcular desde URL")
        controles.addWidget(self.calcular, 5, 0)
        controles.addWidget(self.descargar, 5, 1)
        layout.addLayout(controles)
        self.estado = QLabel("Seleccione una entidad o introduzca su URL SCIENTI.")
        self.estado.setWordWrap(True)
        self.estado.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.estado)
        self.resultado = QLabel("Indicador: —")
        self.resultado.setObjectName("tituloPantalla")
        self.resultado.setWordWrap(True)
        layout.addWidget(self.resultado)
        self.tabla = self._tabla(["Componente", "Bruto", "Máximo", "Índice", "Coeficiente", "Aporte"])
        layout.addWidget(self.tabla)
        self.exclusiones = QLabel()
        self.exclusiones.setWordWrap(True)
        layout.addWidget(self.exclusiones)
        botones = QGridLayout()
        for fila, (texto, accion) in enumerate(
            [
                ("Cargar referencia de máximos", self._cargar_referencia),
                ("Usar referencia del catálogo", self._quitar_referencia),
                ("Exportar desglose JSON", self._exportar_resultado),
                ("Guardar catálogo local", self._guardar_local),
                ("Abrir catálogo local", self._abrir_local),
                ("Iniciar sin datos", self._vaciar),
                ("Editar datos de la entidad", self._editar_entidad),
            ]
        ):
            b = QPushButton(texto)
            b.clicked.connect(accion)
            botones.addWidget(b, fila // 2, fila % 2)
        layout.addLayout(botones)
        leyenda = QLabel(
            "Puntaje individual = peso base × peso relativo. La calidad debe estar respaldada por "
            "los requisitos del Modelo; una etiqueta genérica como «Artículo» no determina un cuartil."
        )
        leyenda.setWordWrap(True)
        layout.addWidget(leyenda)
        self.productos = self._tabla(["Código", "Título", "Categoría", "Peso relativo", "Puntaje", "Validación"])
        self.productos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.productos)
        self.categorias = QComboBox()
        self.categorias.addItem("Seleccione categoría de calidad", "")
        for r in modelo()["categorias"]:
            self.categorias.addItem(f"{r['codigo']} · {r['clase']} · peso {r['peso_relativo']}", r["codigo"])
        self.categorias.setAccessibleName("Categoría Minciencias del producto seleccionado")
        layout.addWidget(self.categorias)
        guardar = QPushButton("Asignar categoría al producto seleccionado")
        guardar.clicked.connect(self._clasificar)
        layout.addWidget(guardar)
        editar_producto = QPushButton("Editar otros datos del producto seleccionado")
        editar_producto.clicked.connect(self._editar_producto)
        layout.addWidget(editar_producto)
        layout.addStretch()
        scroll.setWidget(cuerpo)
        exterior.addWidget(scroll)
        self.ambito.currentIndexChanged.connect(self.refrescar)
        self.entidad.currentIndexChanged.connect(self._cargar_productos)
        self.calcular.clicked.connect(self._calcular)
        self.descargar.clicked.connect(self._desde_url)
        self.corte.valueChanged.connect(self._invalidar_calculo)
        self.desde.valueChanged.connect(self._invalidar_calculo)
        self.refrescar()

    def _invalidar_calculo(self, *_):
        self._resultado = None
        self.resultado.setText("Indicador: —")
        self.tabla.setRowCount(0)
        self.exclusiones.clear()

    def _editar_entidad(self):
        from pea.gui.dialogo_campos import DialogoCampos

        ambito, codigo = self.ambito.currentData(), self.entidad.currentData()
        try:
            datos = self.servicio.campos_entidad(ambito, codigo or "")
            dialogo = DialogoCampos(datos, self)
            if dialogo.exec() == dialogo.DialogCode.Accepted:
                cambios = dialogo.cambios()
                if cambios:
                    self._ejecutar(
                        lambda: self.servicio.editar_campos_entidad(ambito, codigo, cambios), self._edicion_terminada
                    )
        except (ValueError, OSError, ErrorPEA) as error:
            self._error(error)

    def _editar_producto(self):
        from pea.gui.dialogo_campos import DialogoCampos

        fila = self.productos.currentRow()
        if fila < 0 or self._catalogo_descargado is not None:
            return self._error(ValueError("Seleccione un producto del catálogo de trabajo para editarlo."))
        codigo = self.productos.item(fila, 0).text()
        try:
            dialogo = DialogoCampos(self.servicio.campos_entidad("producto", codigo), self)
            if dialogo.exec() == dialogo.DialogCode.Accepted:
                cambios = dialogo.cambios()
                if cambios:
                    self._ejecutar(
                        lambda: self.servicio.editar_campos_entidad("producto", codigo, cambios),
                        self._edicion_terminada,
                    )
        except (ValueError, OSError, ErrorPEA) as error:
            self._error(error)

    def _edicion_terminada(self, mensaje):
        self.estado.setText(mensaje)
        self.refrescar()
        self.datos_modificados.emit()

    @staticmethod
    def _tabla(columnas):
        tabla = QTableWidget(0, len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla.setMinimumHeight(250)
        tabla.verticalHeader().setVisible(False)
        return tabla

    def _error(self, error, _detalle=""):
        self._ocupado = False
        self.setEnabled(True)
        self.calcular.setEnabled(True)
        self.descargar.setEnabled(True)
        self.estado.setText(str(error))

    def _ejecutar(self, funcion, exito):
        if self._ocupado:
            return
        self._ocupado = True
        self.setEnabled(False)
        self.calcular.setEnabled(False)
        self.descargar.setEnabled(False)
        self.estado.setText("Procesando…")

        def terminado(res):
            self._ocupado = False
            self.setEnabled(True)
            self.calcular.setEnabled(True)
            self.descargar.setEnabled(True)
            exito(res)

        self.ejecutor.ejecutar(funcion, al_terminar=terminado, al_fallar=self._error)

    def refrescar(self, *_):
        anterior = self.entidad.currentData()
        self.entidad.blockSignals(True)
        self.entidad.clear()
        opciones = (
            self.servicio.opciones_grupos()
            if self.ambito.currentData() == "grupo"
            else self.servicio.opciones_investigadores()
        )
        for codigo, nombre in opciones:
            self.entidad.addItem(f"{nombre} ({codigo})", codigo)
        if anterior:
            self.entidad.setCurrentIndex(max(0, self.entidad.findData(anterior)))
        self.entidad.blockSignals(False)
        self._cargar_productos()

    def _cargar_productos(self, *_):
        self._catalogo_descargado = None
        self._resultado = None
        self.resultado.setText("Indicador: —")
        self.tabla.setRowCount(0)
        self.exclusiones.clear()
        filas = self.servicio.productos_puntuables(self.ambito.currentData(), self.entidad.currentData() or "")
        self.productos.setRowCount(len(filas))
        for fila, p in enumerate(filas):
            for col, valor in enumerate(
                [
                    p["codigo_identificador"],
                    p["titulo"],
                    p["categoria"] or "Sin clasificar",
                    p["peso_relativo"],
                    p["puntaje"],
                    p["estado_validacion"],
                ]
            ):
                item = QTableWidgetItem("—" if valor is None else str(valor))
                item.setToolTip(str(valor or "Sin dato verificable"))
                self.productos.setItem(fila, col, item)

    def _parametros(self):
        return self.corte.value(), self.desde.value() if self.desde.value() >= 1970 else None

    def _calcular(self):
        ambito, codigo = self.ambito.currentData(), self.entidad.currentData()
        corte, desde = self._parametros()
        referencia = self._referencia
        if not codigo:
            return self._error(ValueError("No hay una entidad seleccionada."))
        self._ejecutar(lambda: self.servicio.datos_indicador(ambito, codigo, corte, desde, referencia), self._mostrar)

    def _desde_url(self):
        url = self.url.text().strip()
        corte, desde = self._parametros()
        referencia = self._referencia

        def calcular():
            from pea.datos.archivo_local import serializar_catalogo

            consulta = parse_qs(urlparse(url).query)
            ambito = "grupo" if "nro" in consulta else "investigador"
            codigo = consulta.get("nro" if ambito == "grupo" else "cod_rh", [""])[0]
            catalogo = CatalogoInvestigacion()
            ingesta = ServicioIngesta(catalogo)
            ingesta.encolar_url(url, persistir=False)
            informes = ingesta.procesar_todas()
            errores = [i.mensaje for i in informes if not i.exito]
            if errores:
                raise ValueError("; ".join(errores))
            datos = serializar_catalogo(catalogo)
            return datos, calcular_indicador(datos, ambito, codigo, corte, desde, referencia)

        def terminado(res):
            datos, resultado = res
            self._catalogo_descargado = datos
            self.productos.setRowCount(0)
            self._mostrar(resultado)
            self.estado.setText(
                "Datos descargados desde SCIENTI. Guardar catálogo local conserva esta descarga.\n" + self.estado.text()
            )

        self._ejecutar(calcular, terminado)

    def _mostrar(self, resultado):
        self._resultado = resultado
        etiqueta = "Indicador" if resultado["completo"] else "Indicador parcial"
        self.resultado.setText(f"{resultado['nombre']} · {etiqueta}: {resultado['indicador']:.6f}")
        self.estado.setText(resultado["referencia"] + "\n" + "\n".join(resultado["avisos"]))
        self.tabla.setRowCount(len(resultado["componentes"]))
        for f, c in enumerate(resultado["componentes"]):
            for col, clave in enumerate(["componente", "bruto", "maximo", "indice", "coeficiente", "aporte"]):
                v = c[clave]
                self.tabla.setItem(f, col, QTableWidgetItem(v if isinstance(v, str) else f"{v:.6f}"))
        self.exclusiones.setText(
            f"{len(resultado['incluidos'])} productos incluidos; {len(resultado['excluidos'])} excluidos.\n"
            + "\n".join(f"{p['codigo']}: {p['motivo']}" for p in resultado["excluidos"][:30])
        )

    def _cargar_referencia(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Referencia de máximos", "", "JSON (*.json)")
        if ruta:
            try:
                self._referencia = json.loads(Path(ruta).read_text(encoding="utf-8-sig"))
                self._invalidar_calculo()
                self.estado.setText(f"Referencia cargada: {ruta}. Calcule para validar sus máximos y periodo.")
            except (OSError, ValueError) as error:
                self._error(error)

    def _quitar_referencia(self):
        self._referencia = None
        self._invalidar_calculo()
        self.estado.setText("Se usarán máximos del catálogo cargado.")

    def _exportar_resultado(self):
        if self._resultado is None:
            return self._error(ValueError("Calcule un indicador antes de exportar."))
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar desglose", "indicador.json", "JSON (*.json)")
        if ruta:
            try:
                guardar_archivo(ruta, self._resultado)
                self.estado.setText(f"Desglose guardado en {ruta}")
            except (OSError, ValueError) as error:
                self._error(error)

    def _guardar_local(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar catálogo", "catalogo-pea.json", "JSON (*.json)")
        if ruta:
            datos_descargados = self._catalogo_descargado

            def guardar():
                if datos_descargados is not None:
                    guardar_archivo(ruta, datos_descargados)
                    return f"Catálogo descargado guardado en {ruta}"
                return self.servicio.guardar_local(ruta)

            self._ejecutar(guardar, lambda msg: self.estado.setText(msg))

    def _abrir_local(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir catálogo", "", "JSON (*.json)")
        if ruta:
            self._ejecutar(lambda: self.servicio.iniciar_local(ruta), self._cambio_catalogo)

    def _cambio_catalogo(self, estado):
        self.refrescar()
        self._resultado = None
        self.resultado.setText("Indicador: —")
        self.tabla.setRowCount(0)
        self.estado.setText(estado.mensaje)
        self.datos_modificados.emit()

    def _vaciar(self):
        if (
            QMessageBox.question(
                self,
                "Iniciar sin datos",
                "Se sustituirá el catálogo en memoria. Guarde antes los cambios locales que quiera conservar.",
            )
            == QMessageBox.StandardButton.Yes
        ):
            self._cambio_catalogo(self.servicio.iniciar_local())

    def _clasificar(self):
        fila = self.productos.currentRow()
        categoria = self.categorias.currentData()
        if fila < 0 or not categoria or self._catalogo_descargado is not None:
            return self._error(ValueError("Seleccione un producto y su categoría de calidad."))
        codigo = self.productos.item(fila, 0).text()

        def terminado(msg):
            self.estado.setText(msg)
            self._cargar_productos()
            self.datos_modificados.emit()

        self._ejecutar(lambda: self.servicio.clasificar_producto(codigo, categoria), terminado)
