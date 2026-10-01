---
name: empaquetado-windows
description: Usar al generar los paquetes descargables para Windows de Python (PyInstaller) y de C++ (CMake y windeployqt6), incluir DLL de TLS, el archivo de configuración junto al ejecutable, y al probar en un computador limpio.
---
# Empaquetado para Windows

## Principios
- El profesor no instala Python, Qt, CMake ni PostgreSQL: cada paquete trae todo lo necesario.
- Junto al ejecutable va `config/pea.config.json` con la URL y la clave publishable. Nada más secreto.
- Los paquetes se entregan como ZIP: `PEAi-Python.zip` y `PEAi-Cpp.zip`.

## Python (PyInstaller)
- Modo carpeta (`--onedir`) y sin consola (`--windowed`). Preferir un archivo `.spec` guardado en el repositorio.
- Entrada: `python/Taller2_AB_PO_XX.py`. Incluir los datos necesarios (logo, iconos) con `--add-data`.
- Probar el ejecutable fuera del entorno virtual y comprobar que se ven tildes y ñ.

## C++ (CMake y windeployqt6)
- Compilar con el preset `ucrt64-release`.
- Desde `C:/msys64/ucrt64/bin`: `windeployqt6 <ruta a pea_gui.exe>` copia las DLL de Qt y los complementos.
- Para HTTPS: copiar también las DLL de OpenSSL (por ejemplo `libssl-3-x64.dll` y `libcrypto-3-x64.dll`) y las DLL de runtime de MinGW que falten.
- Verificar con una carpeta limpia: si no abre, buscar la DLL faltante.

## Avisos
- Los ejecutables sin firmar pueden mostrar SmartScreen o aviso del antivirus. Está explicado en `LEEME_EJECUCION.txt` (pasos: "Más información" y "Ejecutar de todos modos").
- Antes de empaquetar: `scripts/verificar.ps1` en verde. Después: `python tools/interop/buscar_secretos.py` sobre los paquetes.

## Prueba en computador limpio
1. Un Windows (o usuario) donde nunca se instaló nada del proyecto.
2. Descargar y descomprimir cada ZIP.
3. Abrir la aplicación, iniciar sesión, cargar datos de ejemplo y ver las tres vistas.
4. Abrir las dos aplicaciones a la vez y comprobar el aviso "La base de datos cambió".

## Lista de comprobación
- [ ] Cada paquete abre sin instalar nada.
- [ ] HTTPS funciona dentro del paquete C++.
- [ ] No hay credenciales administrativas en los paquetes.
- [ ] Tamaños anotados en brain/20-Diseno/Despliegue.md.
