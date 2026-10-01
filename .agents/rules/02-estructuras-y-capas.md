---
trigger: always_on
description: Capas y estructuras de datos hechas a mano
---
# Estructuras y capas
- Capas iguales en Python y C++: GUI → servicios → estructuras propias → repositorios REST/RPC → HTTPS → Supabase.
- La GUI nunca toca estructuras, red ni SQL directamente: siempre pasa por los servicios.
- Los datos viven en estructuras hechas a mano: lista doblemente enlazada, multilista, pila, cola e hipercubo.
- No uses list, dict, vector, map ni deque nativos como almacenamiento principal de entidades.
- Un producto es UN solo nodo, enlazado desde su grupo y desde su investigador (multilista).
- Las estadísticas salen del hipercubo, no de consultas SQL.
- Si guardar en la base falla, se revierte la estructura y se muestra el error.
- Desactivar es activo=false; eliminar saca de las estructuras y de la base. Todo cambio va a la pila de deshacer.

El contrato completo está en AGENTS.md.
