"""Pantalla 9: Acerca del proyecto PEA-i."""

from __future__ import annotations

import platform
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from pea.servicios.servicio_aplicacion import ServicioAplicacion


class PantallaAcerca(QWidget):
    """Pantalla informativa institucional y técnica sobre PEA-i."""

    def __init__(self, servicio: ServicioAplicacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._servicio = servicio
        self._configurar_ui()

    def _configurar_ui(self) -> None:
        disposicion_exterior = QVBoxLayout(self)
        disposicion_exterior.setContentsMargins(0, 0, 0, 0)

        area_desplazable = QScrollArea()
        area_desplazable.setWidgetResizable(True)
        area_desplazable.setFrameShape(QFrame.Shape.NoFrame)

        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(24, 24, 24, 24)
        disposicion.setSpacing(20)

        # Encabezado institucional
        tarjeta_institucional = QFrame()
        tarjeta_institucional.setStyleSheet(
            "QFrame { background-color: #003366; color: white; border-radius: 8px; padding: 24px; }"
        )
        disp_inst = QVBoxLayout(tarjeta_institucional)
        disp_inst.setSpacing(8)

        lbl_upc = QLabel("UNIVERSIDAD POPULAR DEL CESAR")
        lbl_upc.setStyleSheet("font-size: 14pt; font-weight: bold; color: #FFFFFF;")
        lbl_facultad = QLabel("Facultad de Ingenierías y Tecnológicas — Programa de Ingeniería de Sistemas")
        lbl_facultad.setStyleSheet("font-size: 10.5pt; color: #E0E0E0;")
        lbl_materia = QLabel("Asignatura: Estructuras de Datos · Taller 2")
        lbl_materia.setStyleSheet("font-size: 10pt; color: #BBDEFB;")

        disp_inst.addWidget(lbl_upc)
        disp_inst.addWidget(lbl_facultad)
        disp_inst.addWidget(lbl_materia)
        disposicion.addWidget(tarjeta_institucional)

        # Título del software
        tarjeta_software = QFrame()
        tarjeta_software.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #D1D5DB; border-radius: 8px; padding: 20px; }"
        )
        disp_soft = QVBoxLayout(tarjeta_software)
        disp_soft.setSpacing(10)

        lbl_titulo = QLabel("PEA-i: Programa Estadístico de Análisis de Investigación")
        lbl_titulo.setStyleSheet("font-size: 13pt; font-weight: bold; color: #003366;")
        lbl_subtitulo = QLabel(
            "Plataforma de procesamiento estadístico, interoperabilidad y visualización "
            "de grupos de investigación, investigadores y productos con base en el modelo MinCiencias."
        )
        lbl_subtitulo.setWordWrap(True)
        lbl_subtitulo.setStyleSheet("color: #4B5563; font-size: 10pt;")

        lbl_norma = QLabel(
            "Normativa de referencia: Documento M601PR04G01 (Convocatoria Nacional de Medición 2024 - MinCiencias)"
        )
        lbl_norma.setStyleSheet("font-style: italic; color: #1F2937; font-weight: 500;")

        disp_soft.addWidget(lbl_titulo)
        disp_soft.addWidget(lbl_subtitulo)
        disp_soft.addWidget(lbl_norma)
        disposicion.addWidget(tarjeta_software)

        # Ficha técnica
        tarjeta_tecnica = QFrame()
        tarjeta_tecnica.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #D1D5DB; border-radius: 8px; padding: 20px; }"
        )
        disp_tec = QVBoxLayout(tarjeta_tecnica)
        disp_tec.setSpacing(12)

        lbl_tec_titulo = QLabel("Ficha Técnica y Arquitectura")
        lbl_tec_titulo.setStyleSheet("font-size: 12pt; font-weight: bold; color: #003366;")
        disp_tec.addWidget(lbl_tec_titulo)

        items_ficha = [
            ("Arquitectura en capas", "GUI (PySide6) → Servicios → Estructuras Manuales → Repositorios → HTTPS/Supabase"),
            ("Estructuras de datos en memoria", "ListaDoble, Multilista, Pila (deshacer), Cola (ingesta), Hipercubo 5D"),
            ("Cálculo estadístico", "Exclusivamente en memoria desde Hipercubo 5D (sin consultas SQL)"),
            ("Base de datos compartida", "PostgreSQL en Supabase vía HTTPS (REST/RPC). Control por meta.revision"),
            ("Paridad C++", "Núcleo idéntico en C++17 (Qt 6 Widgets / CLI pea-cpp) con formatos de resumen byte-a-byte"),
            ("Entorno de ejecución", f"Python {platform.python_version()} · PySide6 {sys.version.split()[0]} · Plataforma {platform.system()} {platform.machine()}"),
        ]

        for clave, valor in items_ficha:
            fila = QHBoxLayout()
            lbl_c = QLabel(f"<b>{clave}:</b>")
            lbl_c.setFixedWidth(240)
            lbl_c.setStyleSheet("color: #1F2937;")
            lbl_v = QLabel(valor)
            lbl_v.setWordWrap(True)
            lbl_v.setStyleSheet("color: #374151;")
            fila.addWidget(lbl_c)
            fila.addWidget(lbl_v, 1)
            disp_tec.addLayout(fila)

        disposicion.addWidget(tarjeta_tecnica)

        # Estado del sistema y revisión
        tarjeta_revision = QFrame()
        tarjeta_revision.setStyleSheet(
            "QFrame { background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 16px; }"
        )
        disp_rev = QVBoxLayout(tarjeta_revision)
        self._lbl_estado_rev = QLabel()
        self._lbl_estado_rev.setStyleSheet("color: #334155; font-size: 9.5pt;")
        disp_rev.addWidget(self._lbl_estado_rev)
        disposicion.addWidget(tarjeta_revision)

        disposicion.addStretch(1)

        area_desplazable.setWidget(contenedor)
        disposicion_exterior.addWidget(area_desplazable)

        self.actualizar_vista()

    def actualizar_vista(self) -> None:
        """Actualiza la información dinámica de estado y revisión."""
        estado = self._servicio.estado()
        txt_rev = (
            f"<b>Revisión actual del esquema:</b> {estado.revision_local if estado.revision_local is not None else 'Sin conexión'}<br>"
            f"<b>Modo de conexión:</b> {estado.descripcion_modo}<br>"
            f"<b>Elementos en cola de importación:</b> {estado.tareas_pendientes} · "
            f"<b>Operaciones para deshacer:</b> {estado.operaciones_deshacer}"
        )
        self._lbl_estado_rev.setText(txt_rev)

    def refrescar(self) -> None:
        """Alias para mantener paridad con el resto de pantallas."""
        self.actualizar_vista()


