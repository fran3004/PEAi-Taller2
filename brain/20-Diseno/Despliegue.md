---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Arquitectura]]"
  - "[[GUI-paridad]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
origen: "brain/50-Bitacora/AUDITORIA-DISENO-PEAI.md - Fase 11"
---

# Despliegue y Empaquetado para Windows

## 1. Alcance de Distribución

PEA-i debe poder ejecutarse en estaciones de trabajo estándar con **Windows 10 y Windows 11 (x64)** sin necesidad de instalar entornos de desarrollo, compiladores ni intérpretes globales de Python.

El sistema genera dos entregables de escritorio independientes:
1. **Instalador / Carpeta Portable Python**: `dist/pea-python/pea-gui.exe`
2. **Instalador / Carpeta Portable C++**: `dist/pea-cpp/pea-cpp.exe`

## 2. Empaquetado de la Aplicación Python (PySide6)

Se utiliza **PyInstaller** configurado en modo directorio (`--onedir`) para optimizar tiempos de arranque y facilitar la actualización de recursos:

### 2.1. Estructura del Paquete
```
dist/pea-python/
├── pea-gui.exe               # Ejecutable principal sin consola
├── config/
│   └── pea.config.json       # Configuración con URL y clave publishable
├── recursos/
│   └── logo_upc.png          # Identidad institucional
├── _internal/                # DLLs de PySide6, librerías Python y C-runtimes
└── datos/                    # Directorio para caché local de ingesta
```

### 2.2. Script de Generación
El script `scripts/empaquetar-python.ps1` automatiza el empaquetado:
- Valida que el entorno virtual `.venv` esté activo.
- Invoca `pyinstaller tools/empaquetado/pea.spec --noconfirm --clean`.
- Copia `config/pea.config.example.json` a `dist/pea-python/config/pea.config.json` si no existe.
- Copia los recursos de identidad institucional.

## 3. Empaquetado de la Aplicación C++ (Qt 6 Widgets)

Se compila con la cadena de herramientas de **MSYS2 UCRT64** (GCC 13+ / MinGW-w64, CMake y Ninja) y se despliegan las dependencias mediante **windeployqt6**:

### 3.1. Estructura del Paquete
```
dist/pea-cpp/
├── pea-cpp.exe               # Binario C++ compilado en modo Release
├── config/
│   └── pea.config.json       # Configuración compartida
├── recursos/
│   └── logo_upc.png
├── Qt6Core.dll, Qt6Gui.dll, Qt6Widgets.dll, Qt6Network.dll
├── libssl-3-x64.dll, libcrypto-3-x64.dll   # Soporte OpenSSL TLS 1.3
├── plugins/                  # Plugins de plataforma (platforms/qwindows.dll, tls/)
└── datos/
```

### 3.2. Script de Generación
El script `scripts/empaquetar-cpp.ps1`:
1. Configura el build con CMake: `cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release`.
2. Compila el ejecutable con Ninja: `cmake --build build --config Release`.
3. Ejecuta `windeployqt6 --release --no-translations dist/pea-cpp/pea-cpp.exe`.
4. Copia las librerías dinámicas de OpenSSL requeridas por `QtNetwork` para HTTPS sobre TLS.
5. Inyecta la carpeta `config/` y `recursos/`.

## 4. Archivo de Configuración Local (`pea.config.json`)

Para evitar rutas absolutas y desacoplar las credenciales del código compilado, el ejecutable busca su configuración en orden de prelación:
1. Argumento de línea de comandos `--config <ruta>`.
2. Archivo `./config/pea.config.json` adyacente al ejecutable.
3. Variables de entorno del sistema (`PEA_SUPABASE_URL`, etc.).

Formato canónico:
```json
{
  "supabase": {
    "url": "https://xyzcompany.supabase.co",
    "anon_key": "eyJhbGciOi...",
    "timeout_segundos": 15
  },
  "ingesta": {
    "pausa_segundos": 1.0,
    "max_reintentos": 3,
    "cache_horas": 24
  },
  "ui": {
    "tema": "institucional",
    "idioma": "es"
  }
}
```

## 5. Criterios de Verificación en Entorno Limpio

Antes de la entrega final de cada versión empaquetada:
- Se prueba en una máquina virtual o sandbox sin Python, MSYS2 ni compiladores instalados.
- Se comprueba la conexión HTTPS a Supabase.
- Se verifica la carga del logo institucional y la ausencia de caracteres corruptos (UTF-8 verificado en consola y ventanas).
- Se ejecuta la suite de comprobación sin errores de DLL faltante.
