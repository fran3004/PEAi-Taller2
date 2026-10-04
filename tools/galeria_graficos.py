"""Generador de capturas de demostración para los componentes gráficos de la Sección 9.

Renderiza cada gráfico con datos realistas y guarda las capturas en datos/capturas/
para verificar paridad visual con ref-inicio-acabado.jpg.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from pea.gui.componentes.graficos import (
    GraficoBarrasApiladas,
    GraficoDonaDoble,
    GraficoSerieAnual,
    MiniRed,
)
from pea.gui.componentes.tarjeta import Tarjeta
from pea.gui.componentes.tarjeta_kpi import FichaKPI
from pea.gui.estilo import generar_hoja_estilos


def generar_capturas() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(generar_hoja_estilos())

    directorio_salida = Path("datos/capturas")
    directorio_salida.mkdir(parents=True, exist_ok=True)

    # 1. Datos realistas
    datos_barras = {
        2018: {"GNC": 10, "DTI": 5, "ASC": 3, "FRH": 2},
        2019: {"GNC": 14, "DTI": 7, "ASC": 4, "FRH": 3},
        2020: {"GNC": 19, "DTI": 9, "ASC": 6, "FRH": 5},
        2021: {"GNC": 28, "DTI": 12, "ASC": 8, "FRH": 7},
        2022: {"GNC": 36, "DTI": 18, "ASC": 11, "FRH": 9},
    }

    tipologias_dona = {
        "GNC": 62,
        "DTI": 35,
        "ASC": 28,
        "FRH": 25,
    }

    validaciones_dona = {
        "Avalado": 95,
        "Con soporte": 40,
        "No avalado": 15,
    }

    datos_serie = {
        2018: 12,
        2019: 18,
        2020: 25,
        2021: 34,
        2022: 48,
    }

    nodos_red = [
        {"codigo": "INV-01", "nombre": "Marly Celina Beleño Díaz", "categoria": "Senior", "grado": 14},
        {"codigo": "INV-02", "nombre": "Wilman Orozco Cotes", "categoria": "Senior", "grado": 12},
        {"codigo": "INV-03", "nombre": "Adith Pérez Orozco", "categoria": "Asociado", "grado": 9},
        {"codigo": "INV-04", "nombre": "Emiro De la Hoz Franco", "categoria": "Asociado", "grado": 8},
        {"codigo": "INV-05", "nombre": "Carlos Mendoza Cuello", "categoria": "Junior", "grado": 7},
        {"codigo": "INV-06", "nombre": "Nelly Rosa Rosero Delgado", "categoria": "Junior", "grado": 6},
        {"codigo": "INV-07", "nombre": "Jesús David Vega", "categoria": "Junior", "grado": 5},
        {"codigo": "INV-08", "nombre": "Álvaro Javier Araujo", "categoria": "Sin categoría", "grado": 4},
        {"codigo": "INV-09", "nombre": "Katherin Morales Daza", "categoria": "Sin categoría", "grado": 4},
        {"codigo": "INV-10", "nombre": "Luis Fernando Romero", "categoria": "Sin categoría", "grado": 3},
        {"codigo": "INV-11", "nombre": "Diana Patricia Gómez", "categoria": "Sin categoría", "grado": 3},
        {"codigo": "INV-12", "nombre": "Jorge Enrique Mejía", "categoria": "Sin categoría", "grado": 2},
        {"codigo": "INV-13", "nombre": "Andrés Felipe Castro", "categoria": "Sin categoría", "grado": 2},
        {"codigo": "INV-14", "nombre": "Claudia Milena Rincón", "categoria": "Sin categoría", "grado": 2},
        {"codigo": "INV-15", "nombre": "Oscar Iván Sánchez", "categoria": "Sin categoría", "grado": 1},
        {"codigo": "INV-16", "nombre": "Martha Isabel Quintero", "categoria": "Sin categoría", "grado": 1},
        {"codigo": "INV-17", "nombre": "Hernán Darío Guerra", "categoria": "Sin categoría", "grado": 1},
        {"codigo": "INV-18", "nombre": "Paola Andrea Salcedo", "categoria": "Sin categoría", "grado": 1},
    ]

    aristas_red = [
        {"origen": "INV-01", "destino": "INV-02", "peso": 8},
        {"origen": "INV-01", "destino": "INV-03", "peso": 5},
        {"origen": "INV-01", "destino": "INV-04", "peso": 4},
        {"origen": "INV-02", "destino": "INV-05", "peso": 4},
        {"origen": "INV-02", "destino": "INV-06", "peso": 3},
        {"origen": "INV-03", "destino": "INV-04", "peso": 6},
        {"origen": "INV-04", "destino": "INV-07", "peso": 3},
        {"origen": "INV-05", "destino": "INV-08", "peso": 2},
        {"origen": "INV-06", "destino": "INV-09", "peso": 2},
        {"origen": "INV-07", "destino": "INV-10", "peso": 2},
        {"origen": "INV-01", "destino": "INV-11", "peso": 2},
        {"origen": "INV-02", "destino": "INV-12", "peso": 1},
        {"origen": "INV-03", "destino": "INV-13", "peso": 1},
    ]

    # 2. Instanciar gráficos individuales
    graf_barras = GraficoBarrasApiladas(
        titulo="Producción anual por tipología",
        subtitulo="Evolución histórica según el Modelo Minciencias",
        datos=datos_barras,
    )
    graf_barras.exportar_png(directorio_salida / "grafico_barras_apiladas.png", ancho=650, alto=420)

    graf_dona = GraficoDonaDoble(
        titulo="Distribución y validación de productos",
        subtitulo="Tipologías (exterior) y estados (interior)",
        tipologias=tipologias_dona,
        validaciones=validaciones_dona,
    )
    graf_dona.exportar_png(directorio_salida / "grafico_dona_doble.png", ancho=550, alto=480)

    graf_serie = GraficoSerieAnual(
        titulo="Producción anual del grupo",
        subtitulo="Histórico de productos validados",
        datos=datos_serie,
    )
    graf_serie.exportar_png(directorio_salida / "grafico_serie_anual.png", ancho=450, alto=280)

    graf_red = MiniRed(
        titulo="Red de colaboración",
        subtitulo="Principales coautorías entre investigadores",
        nodos=nodos_red,
        aristas=aristas_red,
    )
    graf_red.exportar_png(directorio_salida / "grafico_mini_red.png", ancho=450, alto=320)

    # 3. Crear panel completo de Inicio (Galería)
    contenedor = QWidget()
    contenedor.setObjectName("galeria_graficos_seccion9")
    contenedor.setStyleSheet("background-color: #F1F5F9;")
    contenedor.resize(1366, 850)

    layout_ppal = QVBoxLayout(contenedor)
    layout_ppal.setContentsMargins(24, 24, 24, 24)
    layout_ppal.setSpacing(16)

    # Cuadrícula superior: 4 Fichas KPI con minigráficos
    fila_kpi = QHBoxLayout()
    fila_kpi.setSpacing(16)

    kpi1 = FichaKPI(titulo="Productos totales", valor_inicial="150", subtitulo="+24 % vs. año anterior", con_minigrafico=True)
    kpi1.actualizar("150", "+24 % vs. año anterior", [12, 18, 25, 34, 48])

    kpi2 = FichaKPI(titulo="Artículos GNC", valor_inicial="62", subtitulo="41,3 % de la producción", con_minigrafico=True)
    kpi2.actualizar("62", "41,3 % de la producción", [10, 14, 19, 28, 36])

    kpi3 = FichaKPI(titulo="Investigadores", valor_inicial="18", subtitulo="6 categorizados", con_minigrafico=True)
    kpi3.actualizar("18", "6 categorizados", [14, 15, 16, 17, 18])

    kpi4 = FichaKPI(titulo="Coautorías", valor_inicial="41", subtitulo="Densidad de red 0,268", con_minigrafico=True)
    kpi4.actualizar("41", "Densidad de red 0,268", [8, 14, 22, 31, 41])

    fila_kpi.addWidget(kpi1)
    fila_kpi.addWidget(kpi2)
    fila_kpi.addWidget(kpi3)
    fila_kpi.addWidget(kpi4)
    layout_ppal.addLayout(fila_kpi)

    # Cuadrícula inferior: Tarjetas con los gráficos de la Sección 9
    rejilla_graficos = QGridLayout()
    rejilla_graficos.setSpacing(16)

    # Tarjeta 1: Barras apiladas
    tarjeta_barras = Tarjeta(titulo="Producción por tipología")
    tarjeta_barras.agregar_widget(graf_barras)
    rejilla_graficos.addWidget(tarjeta_barras, 0, 0)

    # Tarjeta 2: Dona doble
    tarjeta_dona = Tarjeta(titulo="Tipologías y validación")
    tarjeta_dona.agregar_widget(graf_dona)
    rejilla_graficos.addWidget(tarjeta_dona, 0, 1)

    # Tarjeta 3: Mini Red
    tarjeta_red = Tarjeta(titulo="Red de colaboración")
    tarjeta_red.agregar_widget(graf_red)
    rejilla_graficos.addWidget(tarjeta_red, 0, 2)

    layout_ppal.addLayout(rejilla_graficos)

    # Renderizar y capturar el widget completo
    contenedor.show()
    QApplication.processEvents()

    pixmap = contenedor.grab()
    ruta_galeria = directorio_salida / "galeria_graficos_seccion9.png"
    pixmap.save(str(ruta_galeria), "PNG")
    print(f"Galería generada con éxito en: {ruta_galeria}")


if __name__ == "__main__":
    generar_capturas()
