---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Arquitectura]]"
  - "[[Pila-deshacer]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0007 · Patrón de Persistencia Local Primero con Compensación y Reversión

## Contexto
En aplicaciones de escritorio conectadas a bases de datos en la nube mediante APIs HTTP, las operaciones de red pueden experimentar latencia, micro-cortes, caídas de señal o conflictos de concurrencia. Si una aplicación espera la respuesta del servidor antes de actualizar la memoria, la interfaz se vuelve lenta y poco responsiva; si actualiza la memoria sin mecanismos de rollback ante fallos del servidor, los datos en memoria divergen irreversiblemente de la base de datos remota.

## Opciones consideradas
1. **Remoto primero (Bloqueante)**: Esperar confirmación de red de Supabase antes de tocar las estructuras en memoria. Produce congelamientos de UI y mala experiencia de usuario ante latencia de red.
2. **Local primero sin reversión**: Aplicar en memoria y enviar en segundo plano sin control de fallos. Provoca inconsistencias graves si la petición remota falla con error 400, 409 o 500.
3. **Local primero con compensación de persistencia y reversión (*rollback*)**: La capa de servicios aplica la mutación en las estructuras en memoria inmediatamente para respuesta instantánea, y lanza la persistencia remota. Si la persistencia falla o es rechazada por conflicto de revisión, el servicio ejecuta inmediatamente la acción compensatoria inversa (rollback), restaurando el estado exacto anterior en las estructuras y notificando el error al usuario.

## Decisión
Se adopta el patrón **Local primero con compensación y reversión** formalizado en [[Arquitectura]] y soportado por la [[Pila-deshacer]].
Toda mutación aplicada en memoria genera un comando de reversión explícito. Si la llamada HTTP a Supabase no retorna código exitoso (`2xx`), el comando de reversión se dispara automáticamente en memoria, garantizando sincronía estricta con la base de datos remota.

## Consecuencias
- **Positivas**: Interfaz fluida y responsiva; garantía de consistencia matemática entre las estructuras en memoria y el almacenamiento remoto; reversibilidad sistemática de cambios.
- **Costos**: Cada operación del servicio debe definir formalmente su delta inverso complementario.
