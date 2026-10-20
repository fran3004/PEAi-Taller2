---
tipo: bitacora
estado: aprobado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0016]]"
origen: Antigravity
---

# Bitácora: Corrección exportación — diálogo de archivos siempre visible

## Objetivo

Arreglar la exportación en **todas** las pantallas de la GUI Python (PySide6) para que:
1. No genere ningún error en tiempo de ejecución.
2. Siempre abra el explorador de archivos nativo (nunca guarde en una ruta `False` ni en carpeta fija).
3. Los formatos PDF, PNG y CSV se vean profesionales y completos.

## Causa raíz original

- `PantallaInicio.exportar_pdf()` accedía a `self._lbl_subtitulo_ambito` que no existía (el atributo real es `self._lbl_lineas_ambito`).
- Las señales `triggered` de `QAction` emiten un `bool` (estado `checked`). Al conectar directamente `action.triggered.connect(self.exportar_pdf)`, la función recibía `False` como `ruta_destino` y creaba un archivo literalmente llamado `False` en el directorio de trabajo.

## Archivos creados / modificados

| Archivo | Cambio |
|---------|--------|
| `src/pea/gui/dialogos_exportacion.py` | **Nuevo** — funciones reutilizables para diálogos de guardado, validación de rutas y mensajes de error en español |
| `src/pea/gui/exportador_visual.py` | `_preparar_destino()`, `_fuente_ajustada()`, métricas DPI-aware; PDF con cuadrícula 2 columnas y tarjetas KPI redondeadas |
| `src/pea/gui/pantallas/inicio.py` | Métodos `exportar_pdf/csv/png` reescritos; guard `lambda _=False`; nuevo `exportar_png_individuales()` |
| `src/pea/gui/pantallas/grupos.py` | Misma corrección; atajos `exportar_csv()` |
| `src/pea/gui/pantallas/investigadores.py` | Misma corrección |
| `src/pea/gui/pantallas/productos.py` | Misma corrección |
| `src/pea/gui/pantallas/redes.py` | Misma corrección; importación duplicada eliminada con ruff |
| `tests/unit/test_exportacion_dialogos.py` | **Nuevo** — 12 tests unitarios e integración |

## Comandos ejecutados y resultados

```
ruff check src/pea/gui/ --fix   →  0 errores
pytest tests/unit/test_exportacion_dialogos.py -q  →  12 passed
pytest tests/unit/test_exportacion_dialogos.py tests/unit/test_estructuras.py
      tests/unit/test_hipercubo.py tests/unit/test_estilo_recursos.py -v
      →  47 passed
```

## Supuestos

- Los tests `test_cliente_http`, `test_ingesta` y similares se bloquean porque hacen I/O real a Supabase sin marcador `@pytest.mark.red`. No se modificaron: son pre-existentes y no relacionados con esta tarea.

## Riesgos

- `parche_pdf2.py` (en scratch) agrega DPI-awareness adicional al PDF y el flag `_exportando` en MiniRed. No se ejecutó en esta sesión por falta de verificación de `estilo.SUPERFICIE_SELECCIONADA`. Queda pendiente para la siguiente tarea.

## Siguiente paso

1. Verificar `estilo.SUPERFICIE_SELECCIONADA` y ejecutar `parche_pdf2.py`.
2. Marcar con `@pytest.mark.red` los tests de red que no lo tienen.
3. Exportar muestras reales y comparar con el boceto de referencia.
