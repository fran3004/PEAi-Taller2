---
description: Genera los paquetes descargables de Python y de C++
agent: orquestador
---
Genera los paquetes descargables. Alcance: $ARGUMENTS (si está vacío, ambos).

1. Pide a qa que ejecute scripts/verificar.ps1 antes de empaquetar. Si falla, DETENTE.
2. Delega en python el paquete con PyInstaller (carpeta onedir + ZIP) y en cpp el paquete con windeployqt6 (+ DLL de TLS si hacen falta) + ZIP.
3. Pide a seguridad que busque secretos dentro de los paquetes (python tools/interop/buscar_secretos.py).
4. Prueba cada ejecutable en una carpeta limpia: arranca, muestra el diálogo de conexión y la autoprueba termina con código 0.
5. Reporta tamaños, rutas de los ZIP y el contenido de la carpeta de cada paquete.
