---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Construcción de los componentes reutilizables de la GUI PySide6 según sección 8 de GUI-Diseno-Python.md"
agente: "antigravity"
rama: "feat/gui-rediseno-faf"
commit: "pendiente"
---

# Bitácora · Componentes Reutilizables de Interfaz (Sección 8)

## Objetivo
Implementar la biblioteca de componentes reutilizables de la interfaz gráfica PySide6 de PEA-i descrita en la sección 8 de [[GUI-Diseno-Python]]:
1. `Tarjeta` (`tarjeta.py`): contenedor institucional con sombra suave, radio 16, barra de acento vertical de 3 px en color DTI (`#1F7A9E`), título y zona de acciones a la derecha.
2. `FichaKPI` / `TarjetaKPI` (`tarjeta_kpi.py`): indicador con rótulo superior (10 pt), valor destacado (22 pt bold en `PRIMARIO`), subtítulo explicativo, minigráfico opcional (sparkline 56×18 px) y preservación de la API pública `actualizar(valor, subtitulo)`.
3. `Pildora` (`pildora.py`): etiqueta redondeada para tipologías (GNC, DTI, ASC, FRH), validaciones, categorías de investigador y estados semánticos con contraste accesible.
4. `Avatar` (`avatar.py`): círculo con degradado determinista por hash de nombre, iniciales centradas, variante con anillo perimetral y variante con logo institucional (`logo_upc.png`).
5. `CampoBusqueda` (`campo_busqueda.py`): campo de texto con lupa, botón de limpieza rápida y retardo (debounce) de 250 ms antes de emitir señal `texto_cambiado`.
6. `SelectorSegmentado` (`selector_segmentado.py`): pastillas continuas excluyentes para alternar entre "Institución" y "Grupo".
7. `ChipVentana` y `PopoverFiltroAnios` (`filtro_anios.py`): control compacto que exhibe la ventana activa y despliega un menú flotante con las cuatro opciones del Modelo y filtros, manteniendo compatibilidad con `BarraFiltroAnios`.
8. `EstadoVacio` y `Esqueleto` (`estado_vacio.py`): vista ilustrada con hasta dos botones de acción y marcador de posición con pulso de carga animado.
9. `Toast` y `GestorAvisos` (`toast.py`): notificaciones flotantes temporales (4 s) apilables en la esquina inferior derecha.
10. `animacion.py`: módulo central que respeta la variable de entorno `PEA_SIN_ANIMACIONES`.
11. Generar la galería visual de componentes en `tools/galeria_gui.py` con captura en `datos/capturas/galeria.png` y auditoría comparativa con `ref-inicio-acabado.jpg`.

## Qué se hizo

1. **Tarjeta (`src/pea/gui/componentes/tarjeta.py`)**:
   - Hereda de `QFrame`, implementa `QGraphicsDropShadowEffect` (radio 24, desplazamiento [0, 4], opacidad 10 %), barra vertical de 3 px en `COLOR_DTI`, encabezado dinámico y separación interna de 20 px.

2. **FichaKPI y Minigráfico (`src/pea/gui/componentes/tarjeta_kpi.py`)**:
   - Implementa `Minigrafico` mediante `QPainter` trazando línea suavizada sin ejes con nodo destacado al final.
   - `FichaKPI` formatea automáticamente enteros con punto (`1.250`) y decimales con coma (`4.500,50`) usando `pea.gui.formato`.
   - Mantiene el alias `TarjetaKPI = FichaKPI` para preservar compatibilidad con pantallas existentes.

3. **Pildora (`src/pea/gui/componentes/pildora.py`)**:
   - Resuelve fondos y textos de alto contraste para tipologías Minciencias, validaciones y categorías.

4. **Avatar (`src/pea/gui/componentes/avatar.py`)**:
   - Dibuja círculos perfectos mediante `QPainterPath`, genera paleta armónica determinista según MD5 del nombre, dibuja iniciales en negrita y admite anillo perimetral de 3 px o pixmaps escalados suavemente.

5. **CampoBusqueda (`src/pea/gui/componentes/campo_busqueda.py`)**:
   - Incorpora acciones de lupa y limpiar con iconos SVG cargados mediante `pea.gui.recursos`, anillo de foco visible de 2 px en `ACENTO` y debounce mediante `QTimer`.

6. **SelectorSegmentado (`src/pea/gui/componentes/selector_segmentado.py`)**:
   - Contenedor con `QButtonGroup` exclusivo, fondo `FICHA`, borde `LINEA` y segmento activo en blanco elevado con texto en negrita.

7. **ChipVentana y PopoverFiltroAnios (`src/pea/gui/componentes/filtro_anios.py`)**:
   - Botón chip estilizado con resumen («Ventana: Modelo 2024 ▾») y popover modal sin marco con sombra suave y radio buttons para los 4 modos del Modelo Minciencias.

8. **EstadoVacio y Esqueleto (`src/pea/gui/componentes/estado_vacio.py`)**:
   - `EstadoVacio`: contenedor con borde punteado tenue, icono, título, mensaje y dos botones de acción.
   - `Esqueleto`: simulación de bloques de texto mediante rectángulos redondeados con pulso de opacidad (0.40 a 0.85) a 40 ms cuando las animaciones están activas.

9. **Toast y GestorAvisos (`src/pea/gui/componentes/toast.py`)**:
   - `Toast`: tarjeta flotante de 320 px con icono semántico, auto-cierre a 4 s (pausa en hover) y botón de cierre manual.
   - `GestorAvisos`: gestor asociado a la ventana padre que apila avisos verticalmente a 24 px del margen derecho y 76 px del margen inferior.

10. **Galería y captura (`tools/galeria_gui.py` y `datos/capturas/galeria.png`)**:
    - Exhibe los componentes en una cuadrícula armónica 2×2 con toasts flotantes y permite captura offscreen directa.

## Comparación visual con ref-inicio-acabado.jpg
Al comparar `datos/capturas/galeria.png` frente a `ref-inicio-acabado.jpg` se evalúan los siguientes aspectos:
1. **Lo que se ve mejor en PEA-i**:
   - Tipografía nítida con pesos consistentes y legibilidad perfecta (Segoe UI 11 pt).
   - Acabado de tarjetas con sombra suave (`#0A2045` al 10 %) y radio de 16 px sin bordes toscos.
   - El minigráfico integrado en la ficha KPI es limpio, moderno y sin sobrecarga gráfica.
   - Las píldoras y avatares tienen una paleta armónica con contraste WCAG 2.1 verificado.
   - Los avisos flotantes (toasts) tienen una jerarquía clara con colores semánticos definidos.
2. **Lo que se ve peor o requiere pulido al ensamblar pantallas**:
   - En la galería aislada, las tarjetas inferiores presentan espacio vertical sobrante porque no contienen tablas ni gráficos grandes como en el boceto acabado.
   - El boceto incluye el encabezado institucional con degradado azul profundo y las pestañas de navegación con iconos de color que unifican toda la composición visual; en la galería de componentes este encabezado aún no está presente en la ventana general.
   - El selector segmentado requiere margen adecuado para que el texto en negrita mantenga holgura lateral uniforme frente al campo de búsqueda.

## Comandos y resultados
- `ruff check src tests tools/galeria_gui.py`: **OK** (0 errores).
- `pytest tests/unit/test_componentes_gui.py`: **OK** (11 de 11 pruebas aprobadas en 1.84 s).
- `pytest tests/unit`: **OK** (112 de 112 pruebas aprobadas en 10.95 s, 1 deseleccionada que requiere red).
- `python tools/brain/verificar_brain.py`: **OK** (79 notas inspeccionadas, 0 errores, 0 advertencias).
- `python tools/galeria_gui.py`: genera captura en `datos/capturas/galeria.png`.

## Decisiones
- Se mantuvo `TarjetaKPI = FichaKPI` y `BarraFiltroAnios` en sus respectivos módulos para garantizar paridad y retrocompatibilidad absoluta con las pantallas de datos preexistentes.
- Se implementó `animacion.py` con consulta a `PEA_SIN_ANIMACIONES`, asegurando que tanto `pytest` como entornos headless operen de forma instantánea y determinista.

## Pendientes y siguiente paso
- Construir los componentes estructurales de la ventana principal: la barra superior institucional (88 px con degradado, 7 pestañas con subrayado de 3 px, botón Deshacer con popover de historial, avatar de usuario, Cerrar sesión, Acerca de y filete institucional tricolor de 3 px) y el pie institucional (72 px con logo UPC, texto oficial y estado vivo de conexión/revisión).
