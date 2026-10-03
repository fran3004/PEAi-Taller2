---
tipo: bitacora
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[Contrato-de-datos]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[ADR-0002-Unico-proyecto-Supabase]]"
  - "[[ADR-0008-Modelo-de-autenticacion-y-rls]]"
  - "[[ADR-0009-RPC-y-control-de-revision-optimista]]"
  - "[[Trazabilidad]]"
origen: "Creación del contrato PostgreSQL Supabase y herramientas tools/db"
---

# Bitácora · Creación del Contrato Real PostgreSQL / Supabase

## Objetivo
Implementar y formalizar el contrato real de base de datos relacional PostgreSQL en Supabase para PEA-i conforme al Modelo Minciencias 2024, la SPEC y las directrices normativas de `AGENTS.md`.

## Qué se hizo
1. **Migración SQL oficial hacia adelante**:
   - Generada en `supabase/migrations/20261003055532_001_esquema_inicial.sql`.
   - Creadas las tablas: `meta`, `grupos`, `investigadores`, `integrantes_grupo`, `productos`, `producto_autores`, `producto_grupos`, `proyectos`, `semilleros`, `auditoria_cambios`.
   - Estandarización de identificadores con `id bigint generated always as identity primary key` y columnas obligatorias (`activo`, `es_ejemplo`, `creado_en`, `actualizado_en`).
   - Claves naturales únicas normalizadas (`codigo_gruplac`, `codigo_rh`, `codigo_identificador`).
2. **Mecanismo de Concurrencia y Revisión (`meta.revision`)**:
   - Triggers `AFTER STATEMENT` en todas las tablas del dominio que incrementan `meta.revision` automáticamente tras cada sentencia `INSERT`, `UPDATE` o `DELETE`.
   - Triggers `BEFORE UPDATE` para actualizar la marca temporal `actualizado_en` a nivel de fila.
3. **Procedimientos Almacenados (RPC) Transaccionales**:
   - `ping()`: Inspección rápida y keep-alive de conectividad.
   - `obtener_revision_actual()`: Consulta optimizada de versión.
   - `transaccion_crear_producto(...)`: Creación atómica de producto con autores y grupos, exigiendo `p_revision_esperada` (lanza `CONFLICTO_REVISION` si difiere).
   - `transaccion_desactivar_nodo(...)`: Desactivación lógica reversible (`activo = false`).
   - `transaccion_eliminar_cascada(...)`: Eliminación física controlada.
   - `reiniciar_datos_prueba(p_confirmacion)`: Limpieza segura restringida exclusivamente a filas `es_ejemplo = true` con prefijo `PRUEBA-`.
4. **Seguridad, Auth y Row Level Security (RLS)**:
   - RLS habilitado en el 100% de las tablas.
   - Privilegios revocados a `anon` en tablas de dominio y `meta` (sin sesión: acceso denegado).
   - Permiso de ejecución otorgado a `anon` y `authenticated` para `ping()` y `obtener_revision_actual()`.
   - Permisos y políticas completas otorgadas exclusivamente al rol `authenticated`.
5. **Sembrado Ficticio de Prueba (`seed`)**:
   - Integrado en la migración con prefijo `PRUEBA-` y `es_ejemplo = true` (1 grupo, 2 investigadores, 2 integrantes, 2 productos y sus relaciones).
6. **Herramientas de Base de Datos (`tools/db/`)**:
   - `ping.py`: Comprobador de latencia y estado remoto.
   - `respaldar.py`: Respaldo paginado en JSON fechado en `datos/respaldos/`.
   - `volcar.py`: Volcado canónico ordenado para paridad.
   - `comparar.py`: Comparador estructurado campo por campo.
   - `sembrar.py`: Inserción de entidades de prueba mediante sesión autorizada.
   - `reiniciar_prueba.py`: Operación segura de limpieza que rechaza tocar datos de producción.
7. **Pruebas Automatizadas y Configuración**:
   - Implementado `tests/contrato/test_contrato_postgresql.py` con 8 pruebas estáticas de contrato y 1 prueba de red marcada con `@pytest.mark.red`.
   - Creado `pytest.ini` para aislar pruebas que requieren red remota por defecto.

## Comandos y resultados
- `pytest`: 13 pruebas pasadas, 1 deseleccionada (red), 0 fallas en 0.44s.
- `python tools/db/respaldar.py`: Respaldo exitoso generado en `datos/respaldos/respaldo_20261003_060720.json`.
- `npx supabase db push --dry-run`: Simulación exitosa contra la base remota de Supabase (`pea-prod` / `wdmchsncexayqbjueamb`), reconociendo la migración `20261003055532_001_esquema_inicial.sql`.
- `powershell -File scripts/verificar.ps1`: Todo en verde (Bóveda 65 notas íntegras, Pruebas Python 13/13 OK).

## Decisiones
- Se adoptó `id bigint generated always as identity` para todas las entidades del dominio de acuerdo con la instrucción explícita del prompt y la skill `postgresql-supabase`.
- Se configuró la lectura segura de credenciales de Supabase soportando `PEA_SUPABASE_URL_PROD` y `PEA_SUPABASE_KEY_PROD` conforme al contrato de proyecto único.

## Pendientes y siguiente paso
- Presentar el reporte al usuario con el resultado del dry-run y solicitar su confirmación explícita para la ejecución de `npx supabase db push` definitivo.
