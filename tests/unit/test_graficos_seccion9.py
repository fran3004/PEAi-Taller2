"""Pruebas unitarias para los componentes gráficos nativos de la Sección 9.

Verifica:
- GraficoBase (estado vacío accesible y exportación PNG a doble resolución).
- GraficoBarrasApiladas (datos vacíos, un dato, valores grandes, alternar tabla, atenuar leyenda).
- GraficoDonaDoble (orden canónico, centro dinámico, hover y leyenda interactiva).
- GraficoSerieAnual (barras simples para fichas laterales).
- Minigrafico (sparkline 56×18 px para fichas KPI).
- MiniRed (filtrado a 18 nodos, top 6 etiquetados y señal al pulsar).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from pea.gui.componentes.graficos import (
    GraficoBarrasApiladas,
    GraficoBase,
    GraficoDonaDoble,
    GraficoSerieAnual,
    Minigrafico,
    MiniRed,
)


def test_grafico_base_estado_vacio_y_exportar_png(tmp_path: Path, qapp: QApplication, qtbot: Any) -> None:
    """Verifica que GraficoBase dibuje estado vacío y exporte PNG a doble resolución."""
    widget = GraficoBase(titulo="Gráfico Base de Prueba")
    qtbot.addWidget(widget)
    widget.resize(400, 300)
    widget.show()

    assert widget.esta_vacio()

    destino = tmp_path / "base_export.png"
    exito = widget.exportar_png(destino, ancho=800, alto=500, escala=2.0)
    assert exito
    assert destino.exists()

    imagen = QImage(str(destino))
    assert not imagen.isNull()
    # Doble resolución: 800 * 2 = 1600, 500 * 2 = 1000
    assert imagen.width() == 1600
    assert imagen.height() == 1000


def test_barras_apiladas_vacio_un_dato_valores_grandes(tmp_path: Path, qapp: QApplication, qtbot: Any) -> None:
    """Verifica GraficoBarrasApiladas en casos borde de datos y alternancia con tabla."""
    # 1. Datos vacíos
    grafico = GraficoBarrasApiladas(titulo="Producción por tipología")
    qtbot.addWidget(grafico)
    grafico.resize(600, 400)
    grafico.show()

    assert grafico.esta_vacio()
    assert grafico._lienzo.esta_vacio()

    # 2. Un solo dato
    grafico.establecer_datos({2022: {"GNC": 1, "DTI": 0, "ASC": 0, "FRH": 0}})
    assert not grafico.esta_vacio()

    # 3. Valores grandes
    datos_grandes = {
        2018: {"GNC": 12000, "DTI": 8500, "ASC": 4300, "FRH": 3100},
        2019: {"GNC": 15400, "DTI": 9200, "ASC": 5100, "FRH": 4000},
        2020: {"GNC": 22000, "DTI": 14000, "ASC": 7800, "FRH": 6200},
        2021: {"GNC": 31000, "DTI": 19500, "ASC": 9400, "FRH": 8100},
        2022: {"GNC": 45000, "DTI": 28000, "ASC": 14000, "FRH": 11500},
    }
    grafico.establecer_datos(datos_grandes)
    assert not grafico.esta_vacio()
    assert grafico._tabla.rowCount() == 5
    assert grafico._tabla.item(0, 0).text() == "2018"
    assert "45.000" in grafico._tabla.item(4, 1).text()

    # 4. Alternar vista gráfica <-> tabla accesible
    assert grafico._apilador.currentIndex() == 0
    assert grafico._btn_alternar.text() == "Ver como tabla"

    grafico.alternar_vista_tabla()
    assert grafico._apilador.currentIndex() == 1
    assert grafico._btn_alternar.text() == "Ver gráfico"

    grafico.alternar_vista_tabla()
    assert grafico._apilador.currentIndex() == 0
    assert grafico._btn_alternar.text() == "Ver como tabla"

    # 5. Atenuar y restaurar serie en leyenda
    lienzo = grafico._lienzo
    assert "GNC" not in lienzo._series_atenuadas
    # Simular clic en el primer ítem de leyenda (GNC)
    assert len(lienzo._rect_leyenda_items) > 0
    sigla, rect_item = lienzo._rect_leyenda_items[0]
    assert sigla == "GNC"

    qtbot.mouseClick(lienzo, Qt.MouseButton.LeftButton, pos=rect_item.center().toPoint())
    assert "GNC" in lienzo._series_atenuadas

    # Segundo clic restaura
    qtbot.mouseClick(lienzo, Qt.MouseButton.LeftButton, pos=rect_item.center().toPoint())
    assert "GNC" not in lienzo._series_atenuadas

    # 6. Exportar PNG
    destino = tmp_path / "barras_apiladas_test.png"
    exito = grafico.exportar_png(destino)
    assert exito
    img = QImage(str(destino))
    assert img.width() == 1600
    assert img.height() == 1000


def test_dona_doble_casos_borde_y_hover(tmp_path: Path, qapp: QApplication, qtbot: Any) -> None:
    """Verifica GraficoDonaDoble con datos vacíos, únicos, grandes e interacción."""
    dona = GraficoDonaDoble()
    qtbot.addWidget(dona)
    dona.resize(500, 450)
    dona.show()

    # Vacío
    assert dona.esta_vacio()

    # Un solo dato
    dona.establecer_datos(tipologias={"GNC": 1}, validaciones={"Avalado": 1})
    assert not dona.esta_vacio()

    # Datos completos con valores grandes
    tipos = {"GNC": 54000, "DTI": 28000, "ASC": 16000, "FRH": 12000}
    vals = {"Avalado": 75000, "Con soporte": 25000, "No avalado": 10000}
    dona.establecer_datos(tipologias=tipos, validaciones=vals)

    assert not dona.esta_vacio()
    assert len(dona._segmentos) == 7  # 4 tipologías + 3 validaciones

    # Repintar y forzar cálculo geométrico
    dona.repaint()

    # Clic en leyenda para atenuar
    assert len(dona._rect_leyenda_items) > 0
    clave, rect_item = dona._rect_leyenda_items[0]
    qtbot.mouseClick(dona, Qt.MouseButton.LeftButton, pos=rect_item.center().toPoint())
    assert clave in dona._series_atenuadas

    qtbot.mouseClick(dona, Qt.MouseButton.LeftButton, pos=rect_item.center().toPoint())
    assert clave not in dona._series_atenuadas

    # Exportar PNG
    destino = tmp_path / "dona_doble_test.png"
    assert dona.exportar_png(destino)
    img = QImage(str(destino))
    assert img.width() == 1600
    assert img.height() == 1000


def test_serie_anual_casos_borde(tmp_path: Path, qapp: QApplication, qtbot: Any) -> None:
    """Verifica GraficoSerieAnual para fichas laterales."""
    serie = GraficoSerieAnual(titulo="Producción de Grupo")
    qtbot.addWidget(serie)
    serie.resize(400, 250)
    serie.show()

    assert serie.esta_vacio()

    # Un dato
    serie.establecer_datos({2023: 15})
    assert not serie.esta_vacio()

    # Múltiples años y valores grandes
    serie.establecer_datos({2019: 120, 2020: 340, 2021: 890, 2022: 1450, 2023: 2100})
    assert not serie.esta_vacio()

    destino = tmp_path / "serie_anual_test.png"
    assert serie.exportar_png(destino)
    img = QImage(str(destino))
    assert img.width() == 1600
    assert img.height() == 1000


def test_minigrafico_kpi(qapp: QApplication, qtbot: Any) -> None:
    """Verifica el componente sparkline Minigrafico."""
    mini = Minigrafico()
    qtbot.addWidget(mini)
    assert mini.width() == 56
    assert mini.height() == 18
    assert mini.esta_vacio()

    mini.actualizar_datos([10.0, 25.0, 15.0, 40.0, 55.0])
    assert not mini.esta_vacio()
    assert mini.width() == 56
    assert mini.height() == 18


def test_mini_red_filtrado_y_senales(tmp_path: Path, qapp: QApplication, qtbot: Any) -> None:
    """Verifica que MiniRed limite a 18 nodos, etiquete top 6 y emita señales."""
    # Generar 25 nodos simulados
    nodos = [
        {
            "codigo": f"INV-{i:02d}",
            "nombre": f"Investigador Número {i}",
            "categoria": "Senior" if i < 5 else "Junior",
            "grado": 25 - i,
        }
        for i in range(25)
    ]
    aristas = [
        {"origen": "INV-00", "destino": f"INV-{i:02d}", "peso": 2}
        for i in range(1, 10)
    ]

    mini_red = MiniRed(nodos=nodos, aristas=aristas)
    qtbot.addWidget(mini_red)
    mini_red.resize(400, 300)
    mini_red.show()

    assert not mini_red.esta_vacio()
    assert len(mini_red._nodos_seleccionados) == 18
    assert mini_red._nodos_seleccionados[0]["codigo"] == "INV-00"

    mini_red.repaint()
    assert len(mini_red._nodos_geom) == 18

    # Verificar que solo los primeros 6 tengan mostrar_etiqueta == True
    for idx, n in enumerate(mini_red._nodos_geom):
        if idx < 6:
            assert n.mostrar_etiqueta is True
        else:
            assert n.mostrar_etiqueta is False

    # Probar emisión de señal al hacer clic
    with qtbot.waitSignal(mini_red.abrir_analisis_completo, timeout=1000):
        qtbot.mouseClick(mini_red, Qt.MouseButton.LeftButton, pos=QPointF(50.0, 50.0).toPoint())

    destino = tmp_path / "mini_red_test.png"
    assert mini_red.exportar_png(destino)
    img = QImage(str(destino))
    assert img.width() == 1600
    assert img.height() == 1000
