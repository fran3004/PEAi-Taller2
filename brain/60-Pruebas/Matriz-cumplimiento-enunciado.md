---
tipo: resultado-de-pruebas
estado: borrador
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[SPEC]]"
  - "[[Trazabilidad]]"
  - "[[Ingesta]]"
  - "[[GUI-Diseno-Python]]"
origen: "Verificación del código y criterios de entrega solicitados para el Taller 2"
---

# Matriz de cumplimiento del enunciado

## Alcance y limitaciones de trazabilidad

`docs/entrada/` no contiene el enunciado original numerado del 1 al 14. La fuente formal disponible, `brain/10-Requisitos/SPEC.md`, identifica los requisitos funcionales R0–R12 (13 entradas) y los criterios C1–C6. **Supuesto provisional de organización, no validado contra el enunciado:** los puntos 1–13 se relacionan en orden con R0–R12; el punto 14 queda pendiente de cotejo. La mención de C++ como pendiente procede de la instrucción de entrega de esta tarea, no de una atribución al enunciado ausente.

Los estados «cumple» se limitan a la evidencia local ejecutada. «Parcial» indica que existe implementación, pero falta una verificación requerida (por ejemplo, contra el servicio remoto o mediante inspección visual manual). No se declaran verificados los conteos remotos de Supabase.

| Punto | Requisito trazable | Módulo y función | Estado | Evidencia | Comentario |
|---:|---|---|---|---|---|
| 1 | R0 · Revisión y concurrencia | `src/pea/datos/revision.py` · `ControladorRevision.verificar_consistencia` | parcial | `tests/unit/test_cliente_http.py`; contrato remoto `tests/test_contrato_supabase.py` | Las pruebas locales cubren el cliente; el contrato real no se ejecutó porque no están disponibles las variables de sesión normal y clave publicable. |
| 2 | R1 · Grupos | `src/pea/servicios/servicio_dominio.py` · `CatalogoInvestigacion.crear_grupo` | parcial | Suite unitaria Python | La implementación local está presente; los conteos de grupos reales en `pea-prod` siguen sin confirmar. |
| 3 | R2 · Investigadores | `src/pea/servicios/servicio_dominio.py` · `CatalogoInvestigacion.crear_investigador` | parcial | Suite unitaria Python | La implementación local está presente; los conteos de investigadores reales siguen sin confirmar. |
| 4 | R3 · Productos | `src/pea/servicios/servicio_dominio.py` · `CatalogoInvestigacion.crear_producto` | parcial | Suite unitaria Python | La implementación local está presente; los conteos de productos reales siguen sin confirmar. |
| 5 | R4 · Multilista y coautoría | `src/pea/estructuras/multilista.py` · `Multilista.agregar_producto` | parcial | `tests/unit/test_estructuras.py`; suite unitaria Python | Estructura y pruebas locales presentes; no se declara verificada toda la aceptación de dominio contra datos remotos. |
| 6 | R5 · Lista doble | `src/pea/estructuras/lista_doble.py` · `ListaDoble.insertar_final` | parcial | `tests/unit/test_estructuras.py`; suite unitaria Python | Estructura manual disponible; falta cotejo con el enunciado original ausente. |
| 7 | R6 · Pila y deshacer | `src/pea/servicios/servicio_dominio.py` · `CatalogoInvestigacion.deshacer` | parcial | Suite unitaria Python | Se valida el comportamiento local; la sincronización de reversión remota no se verificó contra `pea-prod`. |
| 8 | R7 · Cola e importación por lotes | `src/pea/ingesta/servicio_ingesta.py` · `ServicioIngesta.procesar_todas`; `src/pea/cli.py` · `comando_importar_url_lote` | cumple | `tests/unit/test_cli_importar_url_lote.py` (fixture local, sin red) | Se valida la lectura del archivo, la validación del código y el flujo de lote sobre fixture. No se añadieron códigos reales de grupos. |
| 9 | R8 · Hipercubo | `src/pea/estructuras/hipercubo.py` · `Hipercubo5D.acumular` | parcial | `tests/unit/test_estructuras.py`; `tests/unit/test_hipercubo.py` | Implementación presente; el cotejo formal con el enunciado original queda pendiente. |
| 10 | R9 · Estadísticas desde hipercubo | `src/pea/servicios/servicio_estadisticas.py` · `ServicioEstadisticas.obtener_vista_institucional` | parcial | `tests/unit/test_graficos_seccion9.py`; suite unitaria Python | Las estadísticas e histogramas se calculan en memoria; falta comparar todos los criterios del enunciado original. |
| 11 | R10 · GUI Python | `src/pea/gui/__init__.py` · `main`; `src/pea/gui/ventana_principal.py` · `VentanaPrincipal` | parcial | `python -m pea.gui --autoprueba` y capturas de 8 pantallas × 3 resoluciones | Se revisaron visualmente las 24 capturas; se corrigió el solapamiento entre avatar y nombre de ficha. La autoprueba final reportó 0 hallazgos. Se mantiene parcial porque falta cotejar el punto con el enunciado original. |
| 12 | R11 · Persistencia atómica | `src/pea/datos/repositorios.py` · `RepositorioProductos.crear_con_rpc` | parcial | Suite unitaria Python; `tests/test_contrato_supabase.py` | La ruta local está cubierta; no se ejecutó la verificación remota de conteos. |
| 13 | R12 · Extracción e importación | `src/pea/ingesta/extractor_url.py` · `ExtractorURL.procesar_url` | parcial | `tests/unit/test_ingesta.py`; `tests/unit/test_cli_importar_url_lote.py` | Fixtures offline y lote probados; no se hizo una descarga de red en esta verificación. |
| 14 | Punto por cotejar; C++ | `cpp/` | pendiente | `cpp/` | La implementación C++ queda pendiente y se rehace en terminal. No se asocia este renglón a un requisito no disponible. |

## Entregables de la nota de entrega

| Entregable | Estado | Evidencia | Comentario |
|---|---|---|---|
| Entrada Python con encabezado, índice y apertura de GUI | cumple | `entrega/Taller2_FF_SM.py`; `python -m py_compile entrega/Taller2_FF_SM.py` | La asociación de puntos debe cotejarse con el enunciado original cuando se incorpore. |
| Especificación técnica Word | cumple | `entrega/Especificacion_Tecnica_PEAi.docx`; conversión de vuelta a texto con Pandoc | Su contenido se basa en `SPEC.md` y documentos de diseño. |
| Archivo de identificación del grupo | cumple | `entrega/integrantes.txt` | Copia local solicitada de `docs/entrada/identidad/integrantes.txt`; contiene información personal del equipo. GitHub reporta visibilidad pública, por lo que esta copia no está protegida por privacidad del repositorio. No se hizo `push`. |
| C++ | pendiente | `cpp/` | Se rehace en terminal, según la instrucción de entrega. |
| Video | excluido | — | Se ignora por instrucción. |
