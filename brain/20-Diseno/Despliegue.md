---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-21
relacionado:
  - "[[_Indice]]"
  - "[[Arquitectura]]"
  - "[[GUI-paridad]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[ADR-0023-Entrega-reproducible-Windows]]"
origen: "Entrega mediante repositorio GitHub solicitada por el usuario"
---

# Despliegue y empaquetado Windows

## Alcance

La distribución se dirige a Windows 10/11 x64. El README raíz es la guía de
instalación y evaluación. Se conserva el código, las pruebas y la documentación;
los ejecutables se adjuntan a una Release. Se mantiene el proyecto Supabase existente.

## Construcción desde cero

`scripts/preparar.ps1` crea un entorno CPython Windows de 64 bits, instala
`.[dev]` aplicando `requirements/windows.txt`, verifica dependencias y compila
C++ Release con MSYS2 UCRT64. El parámetro `-Empaquetado` instala también
PyInstaller y build. Estas herramientas solo son necesarias para los desarrolladores.

Python 3.12 es la versión elegida para GitHub Actions; el entorno de desarrollo
local usa Python 3.14. No se presenta la compilación en una máquina de desarrollo
como prueba de instalación limpia: CI comienza desde checkout y dependencias nuevas.

## Distribución portable

`scripts/empaquetar.ps1` genera `dist/PEAi-Windows-x64.zip`:

```
PEAi-Windows-x64/
  Iniciar-Python.cmd
  Iniciar-Cpp.cmd
  Iniciar-Cpp-demo.cmd
  README.md
  scripts/iniciar-con-base.ps1
  config/pea.config.json
  PEAi-Python/
    pea-gui.exe
    pea-cli.exe
    _internal/
  PEAi-Cpp/
    pea-cpp.exe
    Qt6Core.dll
    Qt6Network.dll
    tls/
    ... DLL transitivas de UCRT64 y OpenSSL, licencias ...
```

PyInstaller conserva los recursos gráficos y las fuentes Inter. La GUI no tiene
consola; la CLI empaquetada ejecuta la comparación con C++, evitando interpretar
un ejecutable congelado como si fuera el intérprete Python.

C++ usa FTXUI y Qt Core/Network, sin GUI de Qt. `windeployqt6` copia complementos;
se añaden OpenSSL y las DLL transitivas encontradas con `objdump`. No se copian
DLL del sistema operativo. `diagnostico-tls` prueba la disponibilidad local de TLS
sin credenciales ni conexión de red.

## Configuración y acceso

Los ejecutables cargan `config/pea.config.json` junto a las carpetas del paquete.
Solo contiene URL, clave publicable y opción automática. La GUI Python conecta
al abrir; C++ también autentica automáticamente. Auth genera tokens mantenidos
solo en memoria y los clientes los renuevan durante el uso.

El propietario autorizó acceso completo a los datos reales tras explicar que
cualquier descargador tendría esos mismos permisos. La migración 007 retira las
restricciones de evaluación 005/006; RLS sigue activo con las políticas originales
para authenticated. No es aislamiento por profesor ni protección de datos privados.
Véase [[ADR-0025-Acceso-academico-completo]]. Auth y migración 007 se aplicaron y
verificaron en pea-prod después de un respaldo completo de 20 tablas y 3073 filas.

`scripts/iniciar-con-base.ps1` conserva la conexión manual opcional de desarrollo.
No forma parte del recorrido del profesor. No se incluye contraseña universal.

## Comprobaciones y publicación

- `scripts/verificar.ps1`: bóveda, pruebas Python, compilación/CTest y TUI.
- CTest incluye una regresión para asegurar que el catálogo conectado conserva
  la referencia al hipercubo después de moverlo al iniciar la TUI.
- `tools/empaquetado/probar_portable.py`: versiones, TLS, comparación entre CLI,
  autopruebas Python/C++ y arranque de GUI, sin Python/MSYS2 en PATH.
- CI Windows: instalación limpia, pruebas y generación de artefactos.
- La Release adjunta ZIP, SHA256 y versiones de dependencias resueltas.

La comprobación sin toolchain en PATH no equivale a haber probado todos los
Windows del profesor. La autenticación, RLS y disponibilidad de Supabase requieren
una comprobación remota separada; no se certifican por pruebas sin red.
La evidencia concreta se registra en [[2026-10-21-codex-entrega-reproducible]].
