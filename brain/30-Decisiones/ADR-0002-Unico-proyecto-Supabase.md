---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Contrato-de-datos]]"
  - "[[Seguridad-y-credenciales]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0002 · Proyecto Único de Supabase con Particionamiento Lógico para Pruebas

## Contexto
El plan gratuito de Supabase impone restricciones de recursos y pausa proyectos inactivos tras 7 días. Crear proyectos independientes para desarrollo, pruebas y producción multiplica la sobrecarga administrativa y agota la cuota gratuita. Además, mantener esquemas sincronizados entre múltiples proyectos añade riesgo de divergencia.

## Opciones consideradas
1. **Múltiples proyectos remotos (producción y pruebas)**: Aísla físicamente los datos, pero duplica el mantenimiento y supera las cuotas gratuitas de Supabase.
2. **Base de datos SQLite local para pruebas**: Viola el contrato fundacional de AGENTS.md ("no SQLite, la base oficial es PostgreSQL en Supabase") y oculta diferencias de dialecto SQL y funciones RPC.
3. **Proyecto único con particionamiento lógico (`es_ejemplo = true` y prefijo `PRUEBA-`)**: Un único clúster PostgreSQL en Supabase (`pea-prod`) que aísla los datos de prueba mediante campos booleanos y convenciones de nomenclatura.

## Decisión
Se adopta un **único proyecto de Supabase (`pea-prod`)**.
Todas las pruebas automáticas operan exclusivamente sobre filas marcadas con `es_ejemplo = true` y prefijo `PRUEBA-` en sus códigos identificadores. La limpieza de pruebas (`test_reset()`) borra únicamente estos registros transitorios sin tocar datos de producción ni datos de ejemplo oficiales. No existe `pea-test`.

## Consecuencias
- **Positivas**: Cero costos adicionales de hosting; consistencia total de esquema, funciones RPC, RLS y triggers de revisión; pruebas ejecutadas sobre la infraestructura real de red.
- **Riesgos / Mitigaciones**: Riesgo de borrado accidental de datos reales, mitigado con políticas RLS y filtros estrictos en scripts de limpieza que exigen `es_ejemplo = true AND codigo LIKE 'PRUEBA-%'`.
