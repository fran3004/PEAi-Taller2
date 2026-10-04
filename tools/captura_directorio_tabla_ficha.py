"""Script temporal para generar capturas offscreen de TablaEstilizada, FichaLateral y Diálogos."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QWidget,
)

from pea.gui.componentes.ficha_lateral import FichaLateral
from pea.gui.componentes.modelo_tabla import ModeloTabla
from pea.gui.componentes.popover_historial import PopoverHistorial
from pea.gui.componentes.tabla import TablaEstilizada
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.dialogos import DialogoProducto
from pea.gui.estilo import FONDO_APP, HOJA_ESTILO
from pea.servicios.vistas import TablaDatos


def main() -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyleSheet(HOJA_ESTILO)

    # 1. Ventana Directorio: TablaEstilizada + FichaLateral
    ventana = QMainWindow()
    ventana.setWindowTitle("PEA-i - Directorio de Investigadores")
    ventana.resize(1180, 680)

    central = QWidget()
    central.setStyleSheet(f"background-color: {FONDO_APP};")
    layout = QHBoxLayout(central)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)

    # Tabla Estilizada
    tabla = TablaEstilizada()
    datos = TablaDatos(
        columnas=("Investigador", "Código CvLAC", "Categoría", "Productos"),
        filas=(
            ("Wilman Orozco Cotes", "0000123456", "Senior", 42),
            ("Adith Pérez Orozco", "0000789012", "Asociado", 28),
            ("Emiro De la Hoz", "0000345678", "Junior", 15),
            ("Carlos Ramos", "0000555123", "Asociado", 19),
            ("Ana María Morales", "0000998877", "Senior", 37),
            ("David Martínez", "0000443322", "Sin categoría", 4),
        ),
        claves=("INV-01", "INV-02", "INV-03", "INV-04", "INV-05", "INV-06"),
    )
    modelo = ModeloTabla(datos)
    tabla.establecer_modelo(modelo)
    tabla.establecer_delegado_columna(0, tabla.delegado_avatar)
    tabla.establecer_delegado_columna(1, tabla.delegado_enlace)
    tabla.establecer_delegado_columna(2, tabla.delegado_pildora)
    tabla.establecer_delegado_columna(3, tabla.delegado_numero)
    tabla.ajustar_columnas({0: 240, 1: 140, 2: 150, 3: 100})

    layout.addWidget(tabla, stretch=1)

    # Ficha Lateral
    ficha = FichaLateral()
    ficha.establecer_cabecera(
        nombre="Wilman Orozco Cotes",
        subtitulo="Ingeniería y Tecnologías · Código 0000123456",
        pildoras=[("Senior", "exito"), ("Activo", "exito")],
    )
    ficha.agregar_kpi(FichaKPI("42", "Total productos"), 0, 0)
    ficha.agregar_kpi(FichaKPI("18", "Artículos A1/A2"), 0, 1)
    ficha.agregar_kpi(FichaKPI("12", "Coautores"), 1, 0)
    ficha.agregar_kpi(FichaKPI("9", "Proyectos"), 1, 1)
    layout.addWidget(ficha)

    ventana.setCentralWidget(central)
    ventana.show()
    tabla.seleccionar_fila(0)
    app.processEvents()

    # Guardar captura
    salida_dir = Path("datos/capturas")
    salida_dir.mkdir(parents=True, exist_ok=True)
    pix = ventana.grab()
    pix.save(str(salida_dir / "directorio_investigadores.png"), "PNG")
    print(f"Captura guardada en {salida_dir / 'directorio_investigadores.png'}")

    # 2. Ventana de Diálogo y Popover de Historial
    ventana_dialogos = QMainWindow()
    ventana_dialogos.resize(950, 600)
    cen2 = QWidget()
    cen2.setStyleSheet(f"background-color: {FONDO_APP};")
    lay2 = QHBoxLayout(cen2)
    lay2.setContentsMargins(20, 20, 20, 20)
    lay2.setSpacing(24)

    # Diálogo de Producto embebido visualmente
    dlg = DialogoProducto(grupos=[("COL0001", "GIECOM"), ("COL0002", "INFORMATICA")])
    dlg.txt_codigo.setText("ART-2024-001")
    dlg.txt_titulo.setText("Análisis Topológico de Redes Académicas en Instituciones Universitarias")
    dlg.spin_ano.setValue(2024)
    lay2.addWidget(dlg)

    # Popover de Historial
    popover = PopoverHistorial()
    popover.actualizar_operaciones([
        "Crear producto ART-2024-001 en grupo GIECOM",
        "Actualizar investigador 0000123456",
        "Desactivar producto SOFTWARE-09",
        "Crear grupo COL0002 INFORMATICA",
    ])
    lay2.addWidget(popover, alignment=Qt.AlignmentFlag.AlignTop)

    ventana_dialogos.setCentralWidget(cen2)
    ventana_dialogos.show()
    app.processEvents()

    pix2 = ventana_dialogos.grab()
    pix2.save(str(salida_dir / "dialogos_popover.png"), "PNG")
    print(f"Captura guardada en {salida_dir / 'dialogos_popover.png'}")


if __name__ == "__main__":
    main()
