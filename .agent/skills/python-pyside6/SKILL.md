---
name: python-pyside6
description: Usar al escribir o depurar el paquete Python pea (arquitectura por capas, PySide6, matplotlib embebido, hilos para la red, pruebas con pytest-qt en modo offscreen, tipos y ruff).
---
# Python 3.12 y PySide6 en PEA-i

## Arquitectura
- Paquete `pea` con layout `src/`: estructuras, dominio, datos, servicios, cubo, estadisticas, ingesta, cli y gui. Dependencias solo hacia abajo (la GUI usa servicios; los servicios usan estructuras y repositorios).
- Anotaciones de tipo en todo; `ruff` sin errores. Dominio con nombres en español sin tildes.
- Errores propios (sin conexión, sesión vencida, no autorizado, conflicto de revisión, dato inválido): clases con mensaje en español.
- Tokens y claves solo en memoria; nunca en logs ni en disco.

## Interfaz
- PySide6. Una ventana principal con barra lateral y páginas apiladas (Resumen general, Por grupo, Por investigador, Por producto, Gestión de datos, Importar, Verificación cruzada, Acerca del proyecto).
- Gráficos con matplotlib dentro de Qt: `matplotlib.use("QtAgg")` y `FigureCanvasQTAgg`. Ejes y leyendas en español; paleta de la UPC.
- Tablas con un modelo `QAbstractTableModel` y `QSortFilterProxyModel` para ordenar y buscar.
- Todo texto en español. Si no hay datos, "Sin datos".

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
- [ ] La ventana abre en 1280x720 y responde mientras carga datos.
- [ ] Sin textos en inglés en pantalla.
- [ ] El archivo de arranque `Taller2_AB_PO_XX.py` solo llama a `pea.gui`.
