---
tipo: bitacora
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[Hipercubo]]"
  - "[[Multilista]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
origen: "Implementación de servicios analíticos y de gestión requeridos por el rediseño GUI Python (secciones 6 y 7 de GUI-Diseno-Python.md)"
agente: "antigravity"
rama: "feat/gui-rediseno-faf"
commit: "pendiente"
---

# Bitácora · Servicios Analíticos y Gestión para Rediseño GUI Python

## Objetivo
Implementar en la capa de servicios (`ServicioAplicacion`, `CatalogoInvestigacion`, `ServicioEstadisticas` y `Multilista`) todos los contratos analíticos y de gestión requeridos por el rediseño oficial de la interfaz gráfica de Python ([[GUI-Diseno-Python]]):
1. `serie_anual_por_categoria(filtro, codigo_grupo=None)`: matriz año × tipología (GNC, DTI, ASC, FRH) calculada exclusivamente desde el [[Hipercubo]] con operaciones `rebanada` y `enrollar`, garantizando que la suma por tipologías coincide con `productos_por_anio`.
2. `red_coautoria(filtro, codigo_grupo=None, min_coautorias=2)`: grafo no dirigido con pesos desde la [[Multilista]], ordenación y métricas deterministas, algoritmo de Brandes implementado a mano para intermediación, cálculo de grado y densidad, e inclusión de investigadores externos al filtrar por grupo ([[ADR-0015-Analisis-de-red-nativo]]).
3. `actualizar_producto(codigo, datos)`: edición de cualquier campo del producto (título, tipología, subtipo, año, validación, reasignación de grupo) con soporte completo de compensación transaccional ante fallos de persistencia y reversión en la pila de deshacer.
4. Métricas consolidadas para fichas: estudiantes del grupo, productos avalados, años con producción por investigador, coautores y aporte porcentual del grupo a la institución (`datos_ficha_grupo` y `datos_ficha_investigador`).

## Qué se hizo

1. **Estructura Multilista (`src/pea/estructuras/multilista.py`)**:
   - Se implementó `cambiar_grupo_de_producto(codigo_identificador, nuevo_grupo)` para desenlazar y reasociar un producto entre secuencias de grupos manteniendo intactas las listas dobles intra-grupo.
   - Se implementó `_reconstruir_enlaces_grupo(codigo_gruplac)` para garantizar coherencia en punteros `anterior_en_grupo` y `siguiente_en_grupo`.

2. **Repositorio de Productos (`src/pea/datos/repositorios.py`)**:
   - Se añadió `actualizar(codigo_identificador, datos)` para peticiones PATCH a la tabla `productos`.
   - Se añadió `desasociar_grupos(producto_id)` para limpiar vínculos en `producto_grupos` al reasignar grupo.

3. **Catálogo de Dominio (`src/pea/servicios/servicio_dominio.py`)**:
   - Se implementó `actualizar_producto(codigo_identificador, datos, persistir=True)`: guarda valores anteriores, aplica cambios en memoria sobre la entidad y la multilista, sincroniza el hipercubo y persiste. En caso de fallo remoto, ejecuta compensación estricta y relanza la excepción.
   - Se integró la reversión de `editar` producto en el método `deshacer()`.

4. **Estadísticas OLAP (`src/pea/servicios/servicio_estadisticas.py`)**:
   - Se implementó `serie_anual_por_categoria(cubo)` utilizando `rebanada` por año y `productos_por_categoria` sobre el hipercubo 5D.

5. **Fachada de Aplicación (`src/pea/servicios/servicio_aplicacion.py`)**:
   - `_CAMPOS_EDITABLES_PRODUCTO`: lista blanca de campos editables.
   - `actualizar_producto(codigo, datos)`: validación de tipologías, validaciones, rango de años y existencia de grupo destino antes de mutar.
   - `serie_anual_por_categoria(filtro, codigo_grupo=None)`: resolución de ventana y rebanada por grupo si aplica.
   - `red_coautoria(filtro, codigo_grupo=None, min_coautorias=2)`: cálculo de parejas de coautoría, filtro de aristas, algoritmo de Brandes para intermediación normalizada, métricas de grado y densidad, e inclusión de coautores externos participantes.
   - `datos_ficha_grupo(codigo, filtro)` y `datos_ficha_investigador(codigo, filtro)`: DTOs consolidados con conteo de estudiantes, productos avalados, años con producción y grado de coautorías.

6. **Contrato de Paridad C++ (`brain/20-Diseno/GUI-paridad.md`)**:
   - Se documentó la deuda técnica de paridad funcional para la futura reimplementación en C++17.

7. **Pruebas Unitarias (`tests/unit/test_servicios_nuevos.py`)**:
   - 14 pruebas que cubren: casos normales, vacío, un solo nodo, filtros temporales, grupos inexistentes, deshacer de edición de producto, y compensación ante fallo de persistencia simulado con `@responses.activate`.

## Verificación

- `ruff check src tests`: 0 errores.
- `pytest tests/unit`: 86 pruebas pasadas, 1 deseleccionada (red), 0 fallas en 10.93s.
- `python tools/brain/verificar_brain.py`: Bóveda íntegra (76 notas inspeccionadas, 0 errores, 0 advertencias).
