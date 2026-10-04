---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Prompt 10: Componentes de graficos nativos seccion 9"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: componentes de graficos nativos seccion 9"
---

# Bitácora · Componentes de gráficos nativos (Sección 9)

## Objetivo
Implementar el paquete `src/pea/gui/componentes/graficos/` según la Sección 9 de [[GUI-Diseno-Python]]:
1. `GraficoBase`: exportación PNG a doble resolución (1600×1000 px para 800×500 lógico), estado vacío accesible con ícono tenue y textos centrados, tooltip oscuro institucional `#0A2045` y soporte de animaciones `OutCubic` respetando `PEA_SIN_ANIMACIONES`.
2. `GraficoBarrasApiladas`: apilado canónico de abajo hacia arriba (GNC, DTI, ASC, FRH), líneas punteadas `#E2E8F0`, esquinas redondeadas (4 px) en el segmento superior, totales numéricos en negrita, leyenda con atenuación interactiva, tooltip oscuro al hover y botón «Ver como tabla» para alternancia a vista tabular accesible.
3. `GraficoDonaDoble`: anillos concéntricos proporcionales (exterior tipología 22 %, interior validación 18 %, separación 4 %), orden canónico fijo desde las 12 en punto horario, hueco angular de 1°, centro dinámico (total y detalle al hover con desplazamiento de 4 px) y leyenda de dos columnas.
4. `GraficoSerieAnual`: barras simples en color petróleo `#1F7A9E` sin línea de tendencia para fichas laterales.
5. `Minigrafico`: línea de tendencia (sparkline) de 56×18 px sin ejes para `FichaKPI`.
6. `MiniRed`: vista previa de la red de colaboración con hasta 18 nodos de mayor grado, rótulos en los top 6, aristas en `#9DB5C9`, hover interactivo y señal `abrir_analisis_completo`.
7. Compatibilidad regresiva: preservación de `GraficoBarras`, `GraficoSeries` y `GraficoTorta` antiguos en `antiguos.py` reexportados desde el paquete.

## Qué se hizo
- Se reorganizó `src/pea/gui/componentes/graficos/` como paquete modular, migrando las clases legacy a `antiguos.py` para no romper pantallas previas antes del prompt 13.
- Se implementaron `base.py`, `barras_apiladas.py`, `dona_doble.py`, `serie_anual.py`, `minigrafico.py` y `mini_red.py`.
- Se integró `Minigrafico` directamente en `tarjeta_kpi.py` eliminando código duplicado.
- Se creó la suite de pruebas unitarias `tests/unit/test_graficos_seccion9.py` cubriendo datos vacíos, un solo dato, valores grandes, exportación PNG a doble resolución, atenuación en leyenda y alternancia de tabla accesible.
- Se creó `tools/galeria_graficos.py` generando capturas en `datos/capturas/` (`galeria_graficos_seccion9.png`, `grafico_barras_apiladas.png`, `grafico_dona_doble.png`, `grafico_serie_anual.png`, `grafico_mini_red.png`).
- Se comparó con `brain/_adjuntos/ref-inicio-acabado.jpg`, verificando fidelidad y superando el boceto al incorporar la alternancia accesible de tabla.

## Comandos y resultados
- `pytest tests/unit`: 118 pruebas pasadas en 12,00 s (0 fallas, 0 advertencias).
- `ruff check src tests tools/galeria_graficos.py tools/galeria_gui.py`: 0 errores.
- `python tools/brain/verificar_brain.py`: 80 notas inspeccionadas, 0 errores, 0 advertencias.
- `python tools/galeria_graficos.py`: capturas PNG generadas con éxito a doble resolución.

## Decisiones
- **Geometría precalculada**: Se calculan rectángulos interactivos y leyendas en `establecer_datos` para que la interacción y las pruebas unitarias offscreen no dependan de ciclos de refresco de ventana de Qt.
- **Doble resolución garantizada**: `exportar_png` renderiza a escala 2.0x sobre `QImage(ancho * 2, alto * 2)` con fondo blanco y antialiasing de texto completo.
- **Alternancia gráfica / tabular**: `GraficoBarrasApiladas` implementa un `QStackedWidget` con botón secundario «Ver como tabla», permitiendo acceder y copiar cifras exactas en cualquier momento.

## Pendientes y siguiente paso
- Continuar con el siguiente prompt del rediseño de interfaz gráfica de PEA-i (pantallas de Inicio, Investigadores, Grupos, Productos, Redes, etc.).
