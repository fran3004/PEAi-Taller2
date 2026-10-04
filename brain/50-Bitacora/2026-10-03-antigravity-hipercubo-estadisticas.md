---
tipo: bitacora
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Hipercubo]]"
  - "[[Estructuras]]"
  - "[[Multilista]]"
  - "[[ADR-0006-Hipercubo-estadisticas-en-memoria]]"
  - "[[SPEC]]"
origen: "Implementación oficial del Hipercubo 5D y Servicio de Estadísticas OLAP en Python y C++"
agente: "antigravity"
rama: "master"
commit: "pendiente"
---

# Bitácora · Hipercubo 5D y Estadísticas en Memoria (Python y C++)

> [!WARNING] Nota de vigencia (2026-10-03)
> Registro histórico. Los gráficos de Python se hacen con `QPainter`, **no** con `matplotlib` ([[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]); el diseño vigente está en [[GUI-Diseno-Python]].

## Objetivo
Implementar la estructura de datos hecha a mano **Hipercubo 5D** (Grupo × Investigador × Categoría × Año × Validación) y la capa analítica de **Servicio de Estadísticas** en Python y C++17, garantizando que el 100% de las métricas estadísticas se calculen exclusivamente en memoria sin recurrir a consultas de agregación SQL (`GROUP BY`, `SUM`, `COUNT`), documentando con rigor normativo la distinción entre filtros de interfaz, ventana general del Modelo 2024 y ventanas diferenciadas por tipología.

## Qué se hizo

1. **Estructura Hipercubo5D en Python (`src/pea/estructuras/hipercubo.py`)**:
   - Espacio pentadimensional con `Coordenada5D` y `CeldaHipercubo` encadenada en `ListaDoble` propia y mapa auxiliar para acceso $O(1)$ conforme a [[ADR-0006-Hipercubo-estadisticas-en-memoria]].
   - Operaciones canónicas implementadas:
     - `acumular()`: inserción e incremento de conteo y peso ponderado por celda.
     - `desacumular()`: decremento y poda de celdas ante desactivación o eliminación.
     - `rebanada()` (*Slice*): fijación de una dimensión fija (grupo, investigador, categoría, año, validación).
     - `subcubo_por_ventana()` (*Dice*): aislamiento de hipervolúmenes multidimensionales por rango de años y filtros opcionales.
     - `subcubo_modelo_2024()`: aplicación de ventanas temporales normativas diferenciadas por tipología.
     - `enrollar()` (*Roll-up*): proyección agregada colapsando dimensiones con conteo de productos únicos para neutralizar sobreconteos por coautoría.
     - `poblar_desde_multilista()`: reconstrucción de celdas exclusivamente a partir de productos activos.

2. **ServicioEstadisticas en Python (`src/pea/servicios/servicio_estadisticas.py`)**:
   - Cálculos analíticos: `productos_por_anio`, `productos_por_categoria`, `productos_por_validacion`, `productos_por_grupo`, `productos_por_investigador`.
   - Métricas derivadas: `promedio_por_investigador` (con redondeo a 2 decimales y control de división por cero).
   - Rankings deterministas: `top_5_investigadores` y `top_5_grupos` con criterio de desempate alfabético secundario por identificador.
   - Distribución porcentual exacta: `porcentajes_por_categoria` y `porcentajes_por_validacion`.
   - Las tres vistas analíticas: `obtener_vista_institucional()`, `obtener_vista_grupo()`, `obtener_vista_investigador()`.

3. **Estructura Hipercubo5D en C++17 (`cpp/include/pea/estructuras/hipercubo.hpp`)**:
   - Mismo contrato funcional con `Coordenada5D`, `qHashMulti`, `CeldaHipercubo`, `ListaDoble<CeldaHipercubo>` y `QHash<Coordenada5D, CeldaHipercubo*>`.
   - Métodos: `acumular`, `desacumular`, `rebanada`, `subcuboPorVentana`, `subcuboModelo2024`, `enrollar`, `enrollarAnio`, `poblarDesdeMultilista`.

4. **ServicioEstadisticas en C++17 (`cpp/include/pea/servicios/servicio_estadisticas.hpp`, `cpp/src/servicios/servicio_estadisticas.cpp`)**:
   - Métricas agregadas y tres vistas devolviendo `QJsonObject` interoperable y serializable.
   - Algoritmo de desempate determinista con `std::sort` y lambdas de comparación compuesta.

5. **Integración con el Dominio**:
   - `CatalogoInvestigacion` tanto en Python como en C++ instancia el hipercubo y sincroniza automáticamente las celdas tras inserciones, desactivaciones, activaciones, eliminaciones, operaciones de deshacer y recargas remotas.

6. **Documentación Normativa en el Cerebro**:
   - Actualización exhaustiva de [[Hipercubo]] detallando las diferencias entre:
     - Filtro dinámico de interfaz (ventana móvil "últimos N años").
     - Ventana formal del Modelo 2024 (corte cerrado 2019–2023).
     - Ventanas diferenciadas por tipología (5 años para artículos/software/ASC/FRH; 10 años para libros y patentes).

## Comandos y resultados
- `pytest tests/unit/test_hipercubo.py`: 10 passed (100% aprobado).
- `pytest`: 75 passed, 2 deselected (100% de la suite Python en verde).
- `cmake --build cpp/build`: compilación limpia con Ninja sin errores ni advertencias bajo `-Wall -Wextra -Wpedantic -Werror`.
- `cpp/build/pruebas_cpp.exe`: 28 test cases / 304 assertions aprobadas con éxito en doctest.
- `python tools/brain/verificar_brain.py`: 71 notas inspeccionadas, 0 errores, 0 advertencias.

## Decisiones
- Se adoptó el conteo de identificadores de producto únicos en las operaciones de *Roll-up* del hipercubo para evitar que la coautoría entre múltiples investigadores del mismo grupo duplique la métrica al totalizar por año o por grupo.
- Para desempates en el Top 5, se ordenó descendentemente por cantidad y ascendentemente por código/nombre alfabético, garantizando reproducibilidad absoluta e idéntica entre Python y C++.

## Pendientes y siguiente paso
- Integrar las tres vistas analíticas y las visualizaciones gráficas nativas (matplotlib en PySide6 y QPainter en Qt6 Widgets) en la interfaz de usuario GUI de escritorio.
