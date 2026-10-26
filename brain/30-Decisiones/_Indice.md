---
tipo: indice
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-21
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
| [[ADR-0012-Diseno-GUI-y-navegacion]] | Diseño visual institucional y navegación por barra superior | Revisado | 2026-10-03 | [[GUI-Diseno-Python]], [[SPEC]] |
| [[ADR-0013-Vistas-secundarias]] | Vistas secundarias: historial, cola, formularios y verificación cruzada | Revisado | 2026-10-03 | [[GUI-Diseno-Python]], [[Pila-deshacer]], [[Cola-importacion]] |
| [[ADR-0014-Nomenclatura-del-dominio-y-base-de-datos]] | Nomenclatura del dominio en español y API snake_case | Aprobado | 2026-10-03 | [[Modelo-de-dominio]], [[Contrato-de-datos]] |
| [[ADR-0015-Analisis-de-red-nativo]] | Renderizado nativo del grafo de red de coautoría | Revisado | 2026-10-03 | [[GUI-Diseno-Python]], [[Multilista]] |
| [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]] | Qué pantallas y datos del boceto se adoptan y cuáles se reemplazan | Revisado | 2026-10-03 | [[GUI-Diseno-Python]], [[Modelo-de-dominio]] |
| [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]] | Qt Widgets, QSS, QPainter y QtSvg; sin QML ni matplotlib | Revisado | 2026-10-03 | [[GUI-Diseno-Python]], [[ADR-0015-Analisis-de-red-nativo]] |
| [[ADR-0018-Histogramas-desde-hipercubo]] | Histogramas calculados desde el hipercubo y renderizados con Qt | Revisado | 2026-10-20 | [[Hipercubo]], [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]] |
| [[ADR-0019-Cpp-terminal-con-ftxui]] | C++ pasa a terminal moderna con FTXUI y sin Qt Widgets/Gui | Aprobado | 2026-10-20 | [[Arquitectura]], [[GUI-paridad]], [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]] |
| [[ADR-0020-Revision-remota-periodica-cpp]] | Revisión remota periódica en C++ con cliente HTTPS aislado por hilo | Aprobado | 2026-10-20 | [[Arquitectura]], [[TUI-Diseno-Cpp]], [[ADR-0009-RPC-y-control-de-revision-optimista]] |
| [[ADR-0021-Actualizacion-atomica-grupo-producto]] | Reasignación de grupo de producto con RPC atómica en C++ | Aprobado | 2026-10-20 | [[GUI-paridad]], [[Paridad-Python-Cpp]], [[ADR-0009-RPC-y-control-de-revision-optimista]] |
| [[ADR-0022-Interpretacion-categoria-legada-csv]] | Interpretar categorías descriptivas del CSV legado de productos | Aprobado | 2026-10-20 | [[Ingesta]], [[SPEC]], [[Modelo-Productos]], [[Paridad-Python-Cpp]] |
| [[ADR-0023-Entrega-reproducible-Windows]] | Entrega Windows instalable y portable en GitHub sin credenciales | Revisado | 2026-10-21 | [[Despliegue]], [[Seguridad-y-credenciales]] |
| [[ADR-0024-Acceso-automatico-evaluacion]] | Sesión automática, lectura real y escritura limitada a evaluación | Revisado | 2026-10-21 | [[Despliegue]], [[Seguridad-y-credenciales]] |
| [[ADR-0025-Acceso-academico-completo]] | Acceso completo automático solicitado para la calificación | Aprobado | 2026-10-21 | [[ADR-0024-Acceso-automatico-evaluacion]], [[Seguridad-y-credenciales]] |
| [[ADR-0026-Indicadores-parcial-y-archivos-locales]] | Indicadores, catálogo normativo y archivos locales del Parcial 2 | Aprobado | 2026-10-25 | [[Arquitectura]], [[Paridad-Python-Cpp]] |
