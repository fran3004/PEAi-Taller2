---
tipo: adr
estado: revisado
creado: 2026-10-21
actualizado: 2026-10-21
relacionado:
  - "[[00-Inicio]]"
  - "[[Despliegue]]"
  - "[[Seguridad-y-credenciales]]"
origen: "Solicitud de preparar GitHub para la ejecución por parte del profesor"
numero: 23
decision: "Código instalable y paquete portable conjunto sin credenciales"
---

# ADR · Entrega reproducible Windows

## Contexto

El profesor recibe un enlace al repositorio. El README anterior daba por instalados
Qt, doctest, compilador y pruebas Python, y no explicaba el acceso autenticado.
La documentación de despliegue mencionaba scripts inexistentes y una GUI C++ retirada.
La rama pública principal estaba retrasada respecto a la implementación local.

## Opciones consideradas

1. Solo código con instrucciones manuales: menor tamaño, mayor fricción al evaluar.
2. Código más portable Windows con dependencias: ejecución directa y construcción comprobable.
3. Incluir entornos y binarios en Git: demasiado volumen, rutas locales y riesgo de secretos.

## Decisión

Se adopta la opción 2. Los ejecutables se publican como assets de una Release y
el código contiene scripts reproducibles, versiones directas de Python fijadas
y CI desde una copia limpia. El paquete conjunto mantiene las dos aplicaciones
como carpetas hermanas para que funcione la verificación cruzada sin intérprete instalado.
Se usan PyInstaller para Python y windeployqt6 más resolución de dependencias PE
para C++. FTXUI mantiene la versión configurada por CMake.

Los archivos de agentes, skills, editor y preferencias de Obsidian dejan de estar
versionados, pero se preservan localmente. El manifiesto npm auxiliar tampoco es
necesario para esta aplicación Python/C++ y queda solo local. Se conserva la bóveda
y la documentación académica: forman parte de la entrega evaluable.

No se incluye configuración privada. El paquete incorpora solo URL y clave publicable;
conecta automáticamente sin pedir datos al profesor. El iniciador manual queda como
herramienta de desarrollo. Tras rechazar los límites de evaluación, el propietario
autorizó expresamente acceso completo a datos reales: [[ADR-0025-Acceso-academico-completo]].
Auth automático y permisos se verifican en remoto, por separado de las pruebas sin red.

## Consecuencias

- El portable permite comprobaciones sin instalar herramientas; la demostración
  no sustituye la evaluación conectada que exige el usuario.
- La persistencia exige Internet y Supabase disponible; la sesión se crea automáticamente.
- Los paquetes son más grandes que el código; se distribuyen fuera del historial Git.
- Se adopta Windows x64 como supuesto de evaluación, conforme al diseño de despliegue.
- El entorno limpio de CI y las pruebas de DLL no sustituyen la prueba de la cuenta del profesor.
- Las fuentes oficiales usadas para el empaquetado son la documentación de
  [PyInstaller](https://pyinstaller.org/en/stable/spec-files.html) y
  [MSYS2 en CI](https://www.msys2.org/docs/ci/).
