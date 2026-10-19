---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[00-Inicio]]"
  - "[[Contrato-de-datos]]"
  - "[[GUI-Diseno-Python]]"
origen: "Solicitud del usuario de migrar el 100 % de los datos reales de SCIENTI en datos/ y brain/ a Supabase pea-prod y verificar su carga en la aplicación"
agente: "Antigravity"
rama: "master"
commit: "pendiente"
---

# Bitácora · Migración integral de datos reales SCIENTI a Supabase (`pea-prod`)

## Objetivo
Extraer, estructurar y migrar el 100 % de los datos reales de SCIENTI almacenados en `datos/cache/` (`gruplac_00000000002099.html` y `cvlac_0000494917.html`) y documentados en `brain/40-Fuentes/` hacia la base de datos PostgreSQL remota en Supabase (`pea-prod`), creando todas las tablas complementarias de SCIENTI sin omitir ninguna sección ni registro, y asegurando que la carga de datos desde la base de datos funcione en todas las vistas y pantallas de la aplicación Python.

## Qué se hizo
- Se ejecutó el protocolo de seguridad previo a cambios remotos: verificación del proyecto enlazado `pea-prod` (`wdmchsncexayqbjueamb`), estado de migraciones (`npx supabase migration list --linked`), respaldo previo completo (`datos/respaldos/respaldo_20261019_173319_658121.json`) y simulación (`npx supabase db push --dry-run`).
- Se construyó el generador determinista `tools/db/migrar_datos_reales.py` que analiza el DOM completo de GrupLAC (87 tablas) y CvLAC (30 tablas):
  - Extrae los **85 integrantes** de GISICO con su código oficial `cod_rh` de 10 dígitos desde los enlaces de `G[04]` (`0000799157` para el líder John Jairo Patiño Vanegas, `0000494917` para Adith Bismarck Pérez Orozco, etc.).
  - Extrae los **650 productos** de las 24 secciones no vacías de GrupLAC (`GRP2099-*`) con detección del icono oficial de validación (`/gruplac/images/chulo_0.jpg` / `chulo_1.jpg` → `Avalado`, soporte verificable ISSN/ISBN/DOI/NIT/URL → `Con soporte`, resto → `No avalado`), año depurado (excluyendo falsos positivos en ISSN/ISBN/NIT) y cruce de coautores contra los 85 integrantes del grupo.
  - Extrae los **205 productos/actividades** de las 17 secciones de producción de CvLAC (`CVL494917-*`), incluidos los 11 eventos científicos detallados.
  - Extrae los **42 proyectos** de investigación y desarrollo (`22` de GrupLAC + `20` de CvLAC) y los **2 semilleros** asociados.
  - Extrae el 100 % de las secciones complementarias de SCIENTI: `grupo_instituciones` (2), `grupo_plan_estrategico` (1), `lineas_investigacion` (13), `investigador_formacion` (11), `investigador_experiencia` (14), `investigador_areas_actuacion` (2), `investigador_idiomas` (3), `investigador_reconocimientos` (4) e `investigador_redes_identificadores` (9).
- Se generó y aplicó en `pea-prod` la migración `supabase/migrations/20261019180000_003_esquema_scienti_completo_y_datos_reales.sql` mediante `npx supabase db push --yes`, incluyendo triggers de sincronización de códigos (`codigo_gruplac`, `codigo_rh`, `codigo_identificador`) en `integrantes_grupo` y `proyectos`, RLS activo y políticas para `authenticated`.
- Se actualizaron los archivos CSV en `datos/fuentes/csv/` (`grupos.csv`, `investigadores.csv`, `integrantes.csv`, `productos.csv`, `autores.csv`, `proyectos.csv`, `semilleros.csv` y tablas complementarias).
- Se actualizó `tools/db/respaldar.py` para respaldar y verificar las 19 tablas del esquema bajo RLS, generando el respaldo post-migración `datos/respaldos/respaldo_20261019_174620_432795.json` con **3070 filas verificadas**.
- Se actualizó `CatalogoInvestigacion.recargar_todo()` en `src/pea/servicios/servicio_dominio.py` para cargar también `self.proyectos`, `ServicioIngesta` en `src/pea/ingesta/servicio_ingesta.py` para normalizar valores de `CHECK` en importaciones y `src/pea/cli.py` para soportar todas las variables de entorno de Supabase.

## Comandos y resultados
- `.\.venv\Scripts\python.exe tools/db/migrar_datos_reales.py` → generación de `20261019180000_003_esquema_scienti_completo_y_datos_reales.sql` (1 group, 85 investigadores, 85 integrantes, 855 productos, 1085 vínculos de autoría, 855 vínculos producto-grupo, 42 proyectos, 2 semilleros y 9 tablas complementarias).
- `npx supabase db push --dry-run` y `npx supabase db push --yes` → migración aplicada en `pea-prod` sin errores.
- `.\.venv\Scripts\python.exe tools/db/respaldar.py` → `[OK] Respaldo completo e íntegro: datos\respaldos\respaldo_20261019_174620_432795.json (3070 filas visibles bajo RLS)`.
- `.\.venv\Scripts\python.exe -m ruff check src/ tools/db/migrar_datos_reales.py tools/db/respaldar.py` → `All checks passed!`.
- `.\.venv\Scripts\python.exe -m pea.gui --autoprueba` → `Autoprueba de GUI Python completada exitosamente`.

## Decisiones
- Los nombres de subtipo se definieron respetando las reglas de clasificación de `Hipercubo5D` en Python y C++ (evitando las subcadenas `"LIB"` fuera de libros de nuevo conocimiento y `"PA"` fuera de patentes) para garantizar conteos exactos en las 4 macrotipologías (`GNC`: 184, `DTI`: 117, `ASC`: 117, `FRH`: 437).
- Se mantuvieron intactas las filas ficticias con `es_ejemplo = true` y prefijo `PRUEBA-` usadas por las pruebas automáticas.

## Pendientes y siguiente paso
- Mantener la sincronización de `pea-prod` y ejecutar respaldos periódicos con `tools/db/respaldar.py`.
