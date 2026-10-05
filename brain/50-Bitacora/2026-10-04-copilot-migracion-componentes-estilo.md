---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-tokens-estilo]]"
origen: "Solicitud de eliminar colores y tamaños literales en componentes, gráficos, red y diálogos"
agente: "Copilot"
rama: "master"
commit: ""
---

# Bitácora · Migración de estilos en componentes

## Objetivo
Eliminar colores hexadecimales, transparencias y tamaños de fuente escritos directamente en los componentes Python indicados, usando los tokens de `estilo.py` sin alterar lógica de dibujo ni datos.

## Qué se hizo
- Migrados colores y tamaños de `tabla.py`, `ficha_lateral.py`, `popover_historial.py`, `filtro_anios.py`, `toast.py`, `avatar.py` y `estado_vacio.py`.
- Migrados los gráficos `barras_apiladas.py`, `serie_anual.py`, `base.py`, `dona_doble.py`, `mini_red.py` y `minigrafico.py`.
- Migrados `red/vista_red.py`, `red/nodo.py`, `red/arista.py` y `dialogos.py`.
- Los textos funcionales usan `TAMANO_CUERPO`; leyendas, escalas, pies y chips usan `TAMANO_AUXILIAR`; el total destacado de la dona usa `TAMANO_KPI`.
- Los tamaños de 8, 8.5 y 9 pt de red se elevaron a `TAMANO_AUXILIAR` según la especificación.
- Se añadieron a `estilo.py` los tokens semánticos que faltaban para superficies de gráficos, estados suaves, bordes y tooltip.
- Se mantuvo la lógica de dibujo, las geometrías, los filtros, las cascadas, el deshacer y la importación.

## Verificación del guardián
El informe dirigido a los archivos de esta tarea terminó con:

```text
GUARDIAN_TARGETED: sin literales encontrados
```

No quedan en esos archivos coincidencias de:
- `#RRGGBB`
- `rgba(...)`
- `font-size: número`
- `setPointSize(número)`

## Comandos y resultados
- `ruff check src tests`: `All checks passed!`.
- `pytest tests/unit -v`: `172 passed, 1 deselected, 1 xfailed in 65.11s`.
- `QT_QPA_PLATFORM=offscreen PEA_SIN_ANIMACIONES=1 python -m pea.gui --autoprueba`: código 0; 24 capturas regeneradas.
- `python -m compileall -q src/pea/gui`: correcto.
- Guardián dirigido: sin literales encontrados.
- `tools/brain/verificar_brain.py`: se ejecutará después de normalizar esta nota a finales de línea LF.

## Pendientes y límites
- El guardián global continúa marcado como `xfail` porque todavía existen literales en otros módulos de `src/pea/gui` no incluidos en esta tarea.
- No se modificó `cpp/`.
