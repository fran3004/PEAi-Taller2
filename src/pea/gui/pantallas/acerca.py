"""Pantalla informativa institucional y técnica sobre PEA-i (PySide6).

Fuente de verdad: brain/20-Diseno/GUI-Diseno-Python.md (Sección 6.8).
- Se abre desde el enlace «ⓘ Acerca de» en la barra superior (no es pestaña central).
- Botón «← Volver» para regresar a la vista anterior o de Inicio.
- Tarjeta institucional con identidad visual UPC.
- Tarjeta descriptiva del software y referencia al modelo MinCiencias 2024.
- Ficha técnica de arquitectura en capas, estructuras en memoria y base de datos.
- Estado dinámico vivo del sistema (modo, revisión, cola, deshacer).
"""

from __future__ import annotations

import platform
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.estilo import (
    ACENTO,
    ENCABEZADO_INICIO,
    FICHA,
    LINEA,
    PRIMARIO,
    RADIO_BOTON,
    TAMANO_AUXILIAR,
    TAMANO_CUERPO,
    TEXTO,
    TEXTO_SECUNDARIO,
    TEXTO_SOBRE_OSCURO,
    TEXTO_SOBRE_OSCURO_SUAVE,
)
from pea.gui.recursos.cargador import cargar_pixmap
from pea.servicios.vistas import FiltroAnios
from pea.version import APP_VERSION, ESLOGAN_LINEA_1, ESLOGAN_LINEA_2, NOMBRE_COMPLETO

if TYPE_CHECKING:
    from pea.servicios.servicio_aplicacion import ServicioAplicacion


class PantallaAcerca(QWidget):
    """Pantalla oficial institucional y técnica sobre el proyecto PEA-i (Sección 6.8)."""

    volver_solicitado = Signal()
    solicitar_navegacion = Signal(object)

    def __init__(
        self,
        servicio: ServicioAplicacion,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pantallaAcerca")
        self._servicio = servicio
        self._filtro_actual: FiltroAnios | None = None

        self._construir_ui()
        self.refrescar()

    def _construir_ui(self) -> None:
        disposicion_exterior = QVBoxLayout(self)
        disposicion_exterior.setContentsMargins(0, 0, 0, 0)

        area_desplazable = QScrollArea(self)
        area_desplazable.setWidgetResizable(True)
        area_desplazable.setFrameShape(QFrame.Shape.NoFrame)

        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        # -------------------------------------------------------------------
        # 1. Barra de Navegación Superior: Botón Volver y Título
        # -------------------------------------------------------------------
        fila_volver = QHBoxLayout()
        fila_volver.setContentsMargins(0, 0, 0, 0)
        fila_volver.setSpacing(12)

        self.btn_volver = QPushButton("← Volver al inicio", contenedor)
        self.btn_volver.setObjectName("btnVolverAcerca")
        self.btn_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_volver.setStyleSheet(
            f"QPushButton#btnVolverAcerca {{"
            f"  background-color: {FICHA};"
            f"  color: {PRIMARIO};"
            f"  border: 1px solid {LINEA};"
            f"  border-radius: {RADIO_BOTON}px;"
            f"  padding: 6px 14px;"
            f"  font-weight: bold;"
            f"  font-size: {TAMANO_CUERPO}pt;"
            f"}}"
            f"QPushButton#btnVolverAcerca:hover {{"
            f"  background-color: #E2E8F0;"
            f"}}"
        )
        self.btn_volver.clicked.connect(self.volver_solicitado.emit)
        fila_volver.addWidget(self.btn_volver)

        fila_volver.addStretch(1)

        layout.addLayout(fila_volver)

        # -------------------------------------------------------------------
        # 2. Tarjeta Institucional UPC
        # -------------------------------------------------------------------
        tarjeta_institucional = QFrame(contenedor)
        tarjeta_institucional.setObjectName("tarjetaInstitucional")
        tarjeta_institucional.setStyleSheet(
            f"QFrame#tarjetaInstitucional {{"
            f"  background-color: {ENCABEZADO_INICIO};"
            f"  border-radius: 16px;"
            f"  padding: 24px;"
            f"}}"
        )
        disp_inst = QHBoxLayout(tarjeta_institucional)
        disp_inst.setContentsMargins(18, 16, 18, 16)
        disp_inst.setSpacing(20)

        # Pastilla blanca con logo de la UPC
        pastilla_logo = QFrame(tarjeta_institucional)
        pastilla_logo.setFixedSize(72, 72)
        pastilla_logo.setStyleSheet("background-color: #FFFFFF; border-radius: 12px;")
        disp_logo = QVBoxLayout(pastilla_logo)
        disp_logo.setContentsMargins(4, 4, 4, 4)
        disp_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pix_upc = cargar_pixmap("logo_upc.png", 64, 64)
        lbl_img_upc = QLabel(pastilla_logo)
        lbl_img_upc.setPixmap(pix_upc)
        lbl_img_upc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disp_logo.addWidget(lbl_img_upc)
        disp_inst.addWidget(pastilla_logo)

        # Textos institucionales
        disp_textos_upc = QVBoxLayout()
        disp_textos_upc.setContentsMargins(0, 0, 0, 0)
        disp_textos_upc.setSpacing(4)

        lbl_upc = QLabel("UNIVERSIDAD POPULAR DEL CESAR", tarjeta_institucional)
        lbl_upc.setStyleSheet(
            f"font-size: 14pt; font-weight: 800; color: {TEXTO_SOBRE_OSCURO}; letter-spacing: 0.5px;"
        )
        disp_textos_upc.addWidget(lbl_upc)

        lbl_facultad = QLabel(
            "Facultad de Ingenierías y Tecnológicas — Programa de Ingeniería de Sistemas",
            tarjeta_institucional,
        )
        lbl_facultad.setStyleSheet(
            f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SOBRE_OSCURO_SUAVE};"
        )
        disp_textos_upc.addWidget(lbl_facultad)

        lbl_materia = QLabel(
            "Asignatura: Estructuras de Datos · Taller 2 (PEA-i)",
            tarjeta_institucional,
        )
        lbl_materia.setStyleSheet(
            f"font-size: {TAMANO_AUXILIAR}pt; font-weight: bold; color: {ACENTO};"
        )
        disp_textos_upc.addWidget(lbl_materia)

        disp_inst.addLayout(disp_textos_upc, 1)
        layout.addWidget(tarjeta_institucional)

        # -------------------------------------------------------------------
        # 3. Tarjeta del Software
        # -------------------------------------------------------------------
        self.tarjeta_software = Tarjeta(titulo="Software PEA-i", parent=contenedor)
        lbl_titulo_soft = QLabel(f"{NOMBRE_COMPLETO} (v{APP_VERSION})", self.tarjeta_software)
        lbl_titulo_soft.setStyleSheet(f"font-size: 13pt; font-weight: bold; color: {PRIMARIO};")
        self.tarjeta_software.agregar_widget(lbl_titulo_soft)

        lbl_eslogan = QLabel(f"{ESLOGAN_LINEA_1} — {ESLOGAN_LINEA_2}", self.tarjeta_software)
        lbl_eslogan.setStyleSheet(f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO_SECUNDARIO};")
        lbl_eslogan.setWordWrap(True)
        self.tarjeta_software.agregar_widget(lbl_eslogan)

        lbl_norma = QLabel(
            "Normativa de referencia: Documento M601PR04G01 "
            "(Convocatoria Nacional para el Reconocimiento y Medición de Grupos de Investigación "
            "e Investigadores 2024 — MinCiencias)",
            self.tarjeta_software,
        )
        lbl_norma.setWordWrap(True)
        lbl_norma.setStyleSheet(
            f"font-style: italic; color: {TEXTO}; font-size: {TAMANO_AUXILIAR}pt; padding-top: 4px;"
        )
        self.tarjeta_software.agregar_widget(lbl_norma)

        layout.addWidget(self.tarjeta_software)

        # -------------------------------------------------------------------
        # 4. Ficha Técnica y Arquitectura
        # -------------------------------------------------------------------
        self.tarjeta_tecnica = Tarjeta(titulo="Ficha Técnica y Arquitectura", parent=contenedor)

        items_ficha = [
            (
                "Arquitectura en capas",
                "GUI (PySide6) → Servicios → Estructuras Manuales → Repositorios → HTTPS/Supabase",
            ),
            (
                "Estructuras de datos en memoria",
                "ListaDoble, Multilista, Pila (deshacer), Cola (ingesta), Hipercubo 5D (hechas a mano)",
            ),
            (
                "Cálculo estadístico",
                "Exclusivamente en memoria desde Hipercubo 5D (sin consultas SQL a la base de datos)",
            ),
            (
                "Base de datos compartida",
                "PostgreSQL en Supabase vía HTTPS (REST/RPC). Control de concurrencia mediante meta.revision",
            ),
            (
                "Paridad con C++",
                "Núcleo idéntico en C++17 (Qt 6 Widgets / CLI pea-cpp) con formatos de resumen byte-a-byte",
            ),
            (
                "Entorno de ejecución",
                f"Python {platform.python_version()} · PySide6 {sys.version.split()[0]} · "
                f"Plataforma {platform.system()} {platform.machine()}",
            ),
        ]

        for clave, valor in items_ficha:
            fila = QHBoxLayout()
            fila.setSpacing(10)
            lbl_c = QLabel(f"• <b>{clave}:</b>")
            lbl_c.setFixedWidth(240)
            lbl_c.setStyleSheet(f"color: {TEXTO}; font-size: {TAMANO_CUERPO}pt;")
            lbl_v = QLabel(valor)
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet(f"color: {TEXTO_SECUNDARIO}; font-size: {TAMANO_CUERPO}pt;")
            fila.addWidget(lbl_c)
            fila.addWidget(lbl_v, 1)
            self.tarjeta_tecnica.layout_contenido.addLayout(fila)

        layout.addWidget(self.tarjeta_tecnica)

        # -------------------------------------------------------------------
        # 5. Equipo de Desarrollo
        # -------------------------------------------------------------------
        self.tarjeta_equipo = Tarjeta(titulo="Equipo de Desarrollo", parent=contenedor)
        lbl_equipo = QLabel(
            "Proyecto desarrollado por estudiantes de Ingeniería de Sistemas de la Universidad "
            "Popular del Cesar para el Taller 2 de Estructuras de Datos.",
            self.tarjeta_equipo,
        )
        lbl_equipo.setWordWrap(True)
        lbl_equipo.setStyleSheet(f"font-size: {TAMANO_CUERPO}pt; color: {TEXTO};")
        self.tarjeta_equipo.agregar_widget(lbl_equipo)

        lbl_ciudad = QLabel("Valledupar, Cesar, Colombia · 2026", self.tarjeta_equipo)
        lbl_ciudad.setStyleSheet(f"font-size: {TAMANO_AUXILIAR}pt; color: {TEXTO_SECUNDARIO};")
        self.tarjeta_equipo.agregar_widget(lbl_ciudad)

        layout.addWidget(self.tarjeta_equipo)

        # -------------------------------------------------------------------
        # 6. Estado Dinámico del Sistema
        # -------------------------------------------------------------------
        self.tarjeta_revision = Tarjeta(titulo="Estado Dinámico del Sistema", parent=contenedor)
        self._lbl_estado_rev = QLabel(self.tarjeta_revision)
        self._lbl_estado_rev.setWordWrap(True)
        self._lbl_estado_rev.setStyleSheet(
            f"color: {TEXTO}; font-size: {TAMANO_CUERPO}pt; line-height: 1.4;"
        )
        self.tarjeta_revision.agregar_widget(self._lbl_estado_rev)

        layout.addWidget(self.tarjeta_revision)

        layout.addStretch(1)

        area_desplazable.setWidget(contenedor)
        disposicion_exterior.addWidget(area_desplazable)

    # -----------------------------------------------------------------------
    # API Pública Requerida
    # -----------------------------------------------------------------------

    def actualizar_vista(self) -> None:
        """Actualiza la información dinámica de estado y revisión."""
        estado = self._servicio.estado()
        rev_loc = estado.revision_local if estado.revision_local is not None else "Sin conexión"
        rev_rem = estado.revision_remota if estado.revision_remota is not None else "—"

        txt_rev = (
            f"<b>Revisión actual del esquema:</b> {rev_loc} &nbsp;|&nbsp; "
            f"<b>Revisión remota:</b> {rev_rem}<br>"
            f"<b>Modo de conexión:</b> {estado.descripcion_modo}<br>"
            f"<b>Tareas en cola de importación:</b> {estado.tareas_pendientes} &nbsp;|&nbsp; "
            f"<b>Operaciones para deshacer:</b> {estado.operaciones_deshacer}"
        )
        self._lbl_estado_rev.setText(txt_rev)

    def refrescar(self) -> None:
        """Alias para mantener paridad con el resto de pantallas."""
        self.actualizar_vista()

    def establecer_filtro(self, filtro: FiltroAnios) -> None:
        """Conserva la API uniforme entre todas las pantallas."""
        self._filtro_actual = filtro
