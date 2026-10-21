---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[00-Inicio]]"
origen: "Solicitud del usuario de retirar una integración de automatización y conservar skills y agentes"
agente: "Codex"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Limpieza de cliente y preservación de agentes

## Objetivo
Retirar del repositorio la configuración y los artefactos de un cliente de automatización, sin borrar las skills ni las configuraciones de agentes, y dejar el cambio en un commit aislado.

## Qué se hizo
- Se retiró la configuración raíz, sus comandos propios y sus dependencias locales ignoradas.
- Se conservaron las doce configuraciones de agentes en `.agent/agents/` y el protocolo compartido en `.agent/protocolos/`.
- Se actualizaron el contrato, la skill de flujo Git y las referencias documentales a las rutas compartidas.
- Se preservaron intactos los cambios ajenos que ya estaban presentes en la rama.

## Comandos y resultados
- `git status --short --branch`: confirmó la rama y cambios previos ajenos.
- Búsqueda por contenido y nombres relacionados con el cliente retirado: sin coincidencias residuales en el árbol de trabajo.
- Verificación de preservación: 12 de 12 configuraciones de agentes, 1 protocolo y 10 archivos de skills conservados.
- `python tools/brain/verificar_brain.py`: 158 notas, 0 errores y 1 advertencia ajena por el enlace pendiente a ADR-0016.
- `scripts/verificar.ps1`: el primer intento quedó invalidado por `WinError 5` del sandbox sobre el directorio temporal; repetido con acceso normal, aprobó 289 pruebas Python, omitió 3 de red, aprobó 1 de 1 suite CTest y validó 32 pantallas TUI sin hallazgos.
- Búsqueda final por contenido, nombres e índice preparado: sin coincidencias residuales; `git diff --cached --check` terminó sin errores.

## Decisiones
- Las configuraciones de agentes se trasladaron a la ubicación neutral `.agent/agents/` en vez de borrarse.
- Las skills existentes permanecieron en `.agent/skills/`; solo se generalizó una referencia de coordinación entre agentes.
- No se tocaron archivos funcionales de Python, C++, Supabase ni los cambios ajenos en curso.

## Pendientes y siguiente paso
- Crear el commit exclusivo de esta tarea, sin incluir cambios ajenos; no se requiere ninguna acción funcional adicional.
