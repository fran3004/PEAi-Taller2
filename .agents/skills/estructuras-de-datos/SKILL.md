---
name: estructuras-de-datos
description: Usar al diseñar, implementar o revisar la lista doble, la multilista, la pila, la cola o el hipercubo de PEA-i, en Python o en C++, y al buscar sus casos borde.
---
# Estructuras de datos hechas a mano

Se usa en: diseño (P2), núcleos de Python y C++ (P5, P6), hipercubo y estadísticas, y cualquier revisión de QA.

## Regla base
Los datos de grupos, investigadores y productos viven en estas estructuras. Los contenedores nativos (list, dict, vector, map, deque) solo sirven para variables temporales o índices auxiliares que estén documentados en un ADR.

## Lista doblemente enlazada
- Nodo con dato, anterior y siguiente. La lista guarda cabeza, cola y tamaño.
- Operaciones: insertar al inicio, al final y en posición; eliminar un nodo; buscar; recorrer en los dos sentidos. Insertar en los extremos y eliminar un nodo conocido son O(1); buscar es O(n).
- Casos borde: vacía, un solo elemento, insertar y eliminar en los extremos, eliminar el único elemento, posición fuera de rango.
- Python: `__iter__` y `__len__`. C++: plantilla de solo cabeceras con regla de los cinco.

## Multilista
- Un producto es UN solo nodo. Lo enlazan la lista de productos de su grupo y la de su investigador. Nunca se copia el producto.
- Los integrantes de un grupo apuntan a investigadores que ya existen.
- Cascadas (documentarlas en brain/20-Diseno/Estructuras.md): al eliminar un producto sale de las dos listas; al eliminar un investigador se decide qué pasa con sus productos; al eliminar un grupo igual. Nunca deben quedar punteros colgantes.
- Desactivar no cambia los enlaces: solo `activo=false`.

## Pila (deshacer)
- Cada operación guarda su operación inversa (qué hacer para volver atrás).
- Al deshacer se aplica la inversa a las estructuras y luego se sincroniza con la base.
- Casos borde: deshacer con la pila vacía; deshacer cuando la base cambió por el otro programa.

## Cola (importación)
- Primero en entrar, primero en salir. Estados de cada fuente: pendiente, procesando, terminada, con errores.
- Casos borde: sacar de una cola vacía; una fuente que falla a la mitad no bloquea las demás.

## Hipercubo
- Dimensiones: Grupo × Investigador × Categoría × Año × Validación. Medida: cantidad de productos ACTIVOS.
- Operaciones: acumular, rebanada (fijar una dimensión), subcubo por ventana de años, enrollar (sumar una dimensión).
- Debe dar el mismo resultado que una consulta GROUP BY de PostgreSQL (se compara en las pruebas).
- Casos borde: cubo vacío, ventana de años sin datos, producto inactivo, categoría o validación nueva.

## Lista de comprobación
- [ ] Ninguna entidad se guarda en un contenedor nativo como almacenamiento principal.
- [ ] Cada estructura tiene pruebas con: vacía, un elemento, extremos y duplicados.
- [ ] Eliminar y desactivar no dejan referencias colgantes.
- [ ] Python y C++ dan el mismo resultado con la misma entrada.
- [ ] La complejidad de cada operación está escrita en la nota de diseño.
