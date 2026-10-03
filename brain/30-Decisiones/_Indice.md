---
tipo: indice
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[SPEC]]"
  - "[[Arquitectura]]"
origen: "brain/50-Bitacora/AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# Registro de Decisiones Arquitectónicas (ADR)

Este registro documenta todas las decisiones no triviales de diseño, arquitectura, persistencia, estructuras de datos, seguridad e interoperabilidad de PEA-i.

| ADR | Título | Estado | Fecha | Vínculos de Diseño |
|---|---|---|---|---|
| [[ADR-0001-Boveda-viva]] | Bóveda viva Obsidian como única fuente documental | Aprobado | 2026-10-03 | [[00-Inicio]], [[Arquitectura]] |
| [[ADR-0002-Unico-proyecto-Supabase]] | Proyecto único de Supabase con particionamiento lógico | Aprobado | 2026-10-03 | [[Contrato-de-datos]], [[Seguridad-y-credenciales]] |
| [[ADR-0003-Corpus-fiel-del-Modelo]] | Corpus fiel del Modelo Minciencias 2024 y trazabilidad | Aprobado | 2026-10-03 | [[Modelo-2024-original]], [[Modelo-de-dominio]] |
| [[ADR-0004-Privacidad-de-fuentes-reales]] | Privacidad de datos personales de investigadores | Aprobado | 2026-10-03 | [[Seguridad-y-credenciales]], [[Ingesta]] |
| [[ADR-0005-Multilista-producto-compartido]] | Multilista con nodo único compartido de producto | Aprobado | 2026-10-03 | [[Multilista]], [[Estructuras]] |
| [[ADR-0006-Hipercubo-estadisticas-en-memoria]] | Cálculo estadístico en hipercubo 5D local | Aprobado | 2026-10-03 | [[Hipercubo]], [[Estructuras]] |
| [[ADR-0007-Compensacion-de-persistencia-reversion]] | Patrón de persistencia local primero con compensación | Aprobado | 2026-10-03 | [[Arquitectura]], [[Pila-deshacer]] |
| [[ADR-0008-Modelo-de-autenticacion-y-rls]] | Autenticación con Supabase Auth y RLS en base de datos | Aprobado | 2026-10-03 | [[Seguridad-y-credenciales]], [[Contrato-de-datos]] |
| [[ADR-0009-RPC-y-control-de-revision-optimista]] | Procedimientos RPC y bloqueo optimista por revisión | Aprobado | 2026-10-03 | [[Contrato-de-datos]], [[Arquitectura]] |
| [[ADR-0010-Limites-y-responsabilidad-de-ingesta]] | Restricciones éticas y técnicas de ingesta web | Aprobado | 2026-10-03 | [[Ingesta]], [[Cola-importacion]] |
| [[ADR-0011-Paridad-arquitectural-Python-Cpp]] | Paridad arquitectural y funcional Python / C++ | Aprobado | 2026-10-03 | [[Interoperabilidad]], [[Despliegue]] |
| [[ADR-0012-Diseno-GUI-y-navegacion]] | Diseño visual institucional y ergonomía en 4 zonas | Aprobado | 2026-10-03 | [[GUI-paridad]], [[SPEC]] |
| [[ADR-0013-Vistas-secundarias]] | Vistas secundarias: historial, cola y entidades | Aprobado | 2026-10-03 | [[GUI-paridad]], [[Pila-deshacer]], [[Cola-importacion]] |
| [[ADR-0014-Nomenclatura-del-dominio-y-base-de-datos]] | Nomenclatura del dominio en español y API snake_case | Aprobado | 2026-10-03 | [[Modelo-de-dominio]], [[Contrato-de-datos]] |
| [[ADR-0015-Analisis-de-red-nativo]] | Renderizado nativo del grafo de red de coautoría | Aprobado | 2026-10-03 | [[GUI-paridad]], [[Multilista]] |
