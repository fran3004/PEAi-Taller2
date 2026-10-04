---
name: python-pyside6
description: Usar al escribir o depurar el paquete Python pea (arquitectura por capas, PySide6 con Qt Widgets, QSS y QPainter, hilos para la red, pruebas con pytest-qt en modo offscreen, tipos y ruff). La interfaz sigue brain/20-Diseno/GUI-Diseno-Python.md.
---
# Python 3.12 y PySide6 en PEA-i

## Arquitectura
- Paquete `pea` con layout `src/`: estructuras, dominio, datos, servicios, cubo, estadisticas, ingesta, cli y gui. Dependencias solo hacia abajo (la GUI usa servicios; los servicios usan estructuras y repositorios).
- Anotaciones de tipo en todo; `ruff` sin errores. Dominio con nombres en español sin tildes.
- Errores propios (sin conexión, sesión vencida, no autorizado, conflicto de revisión, dato inválido): clases con mensaje en español.
- Tokens y claves solo en memoria; nunca en logs ni en disco.

## Interfaz
- **Antes de tocar `src/pea/gui/`**: lee `brain/20-Diseno/GUI-Diseno-Python.md` completo y mira las imágenes de `brain/_adjuntos/ref-*`. Esa nota manda sobre cualquier otro texto.
- Una ventana principal con barra superior de siete pestañas (Inicio, Investigadores, Grupos, Productos, Análisis de redes, Importar, Configuración) sobre un `QStackedWidget`, filete institucional y pie con estado de conexión. No hay barra lateral.
- Solo Qt Widgets + hoja de estilo central (`estilo.py` con tokens) + `QPainter` + `QtSvg`. Gráficos propios (`GraficoBarrasApiladas`, `GraficoDonaDoble`, `GraficoSerieAnual`, `Minigrafico`, `MiniRed`) y red con `QGraphicsView`. **Prohibido** QML, QtWebEngine, matplotlib y QtCharts (ADR-0017).
- Tablas con `QAbstractTableModel` + `QSortFilterProxyModel` y delegados (píldoras, avatar + nombre, enlace, número).
- Sombras con `QGraphicsDropShadowEffect` solo en tarjetas contenedoras. Animaciones con `QVariantAnimation`, desactivables con `PEA_SIN_ANIMACIONES=1`.
- Números con `QLocale(Spanish, Colombia)` a través de `gui/formato.py`.
- Todo texto en español. Si no hay datos, "Sin datos en esta ventana".
- No se muestra nada que PEA-i no tenga (H-Index, ORCID, semilleros, centros, logos de terceros): ver ADR-0016.

## Hilos y red
- La red y la importación NUNCA bloquean la interfaz: usar `QThreadPool` con `QRunnable` o un `QThread` con señales.
- La GUI solo actualiza widgets desde el hilo principal (señales).
- Consultar la revisión de la base con un temporizador (`QTimer`) cada pocos segundos y mostrar "La base de datos cambió".

## Pruebas
- `pytest` con `pytest-qt`. Para ventanas: variable `QT_QPA_PLATFORM=offscreen`.
- Las llamadas HTTP se prueban con la biblioteca `responses` (sin internet). Las pruebas con internet llevan la marca `red`.
- Modo `--autoprueba`: crea la ventana, guarda una captura y termina con código 0.

## Lista de comprobación
- [ ] `ruff check` y `pytest` en verde.
- [ ] La ventana abre en 1360x820 (mínimo 1100x700) y responde mientras carga datos.
- [ ] Capturas de la autoprueba en 1100x700, 1366x768 y 1920x1080 comparadas con las referencias.
- [ ] Sin textos en inglés en pantalla.
- [ ] El archivo de arranque `Taller2_AB_PO_XX.py` solo llama a `pea.gui`.
