# PEA-i · Programa Estadístico de Análisis de Investigación

**Universidad Popular del Cesar (UPC)**  
*Facultad de Ingenierías y Tecnologías — Ingeniería de Sistemas*  
*Asignatura: Estructura de Datos (Taller 2)*

---

## 1. Descripción del Proyecto
PEA-i (Programa Estadístico de Análisis de Investigación) es una solución integral diseñada para capturar, estructurar, persistir y analizar la producción académica y científica de grupos de investigación e investigadores, tomando como fuente de verdad normativa el **Modelo de Reconocimiento y Medición de Minciencias 2024** (M601PR04G01) y la plataforma **SCIENTI** (GrupLAC y CvLAC).

El sistema consta de dos aplicaciones con paridad arquitectónica:
- **PEA-i Python**: Aplicación de escritorio desarrollada en **Python 3.12** con **PySide6** (Qt 6).
- **PEA-i C++**: Aplicación de terminal desarrollada en **C++17** con **FTXUI**; usa **Qt Core y Network** exclusivamente para JSON y HTTPS.

Ambas aplicaciones comparten una única base de datos relacional PostgreSQL alojada en la nube mediante **Supabase**, comunicándose de manera exclusiva a través de protocolos seguros **HTTPS** (REST y RPC), sin conexiones directas al puerto PostgreSQL y sin persistencia de credenciales en disco.

---

## 2. Arquitectura del Sistema
El proyecto implementa una arquitectura en capas estrictamente desacoplada:

```
[ Presentación: GUI Python / TUI C++ ]
       ↓
[ Capa de Servicios / Aplicación ]
       ↓
[ Capa de Estructuras Hechas a Mano ]
  • Lista doblemente enlazada
  • Multilista (Producto compartido)
  • Hipercubo multidimensional (Estadísticas en memoria)
  • Pila de deshacer (Undo) / Cola de eventos
       ↓
[ Repositorios REST / RPC ]
       ↓ (HTTPS / TLS 1.3)
[ PostgreSQL en Supabase ] (RLS + Auth)
```

---

## 3. Requisitos y Configuración de Entornos

### Entorno Python (3.12+)
```powershell
# Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias en modo editable
pip install -e .
```

### Entorno C++ (MSYS2 UCRT64 / Qt 6)
```powershell
# Configurar y compilar con CMake y Ninja
$env:PATH = "C:\msys64\ucrt64\bin;" + $env:PATH
cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build cpp/build
```

Si FTXUI no está disponible como paquete del entorno, CMake descarga la versión
fijada `v5.0.0` mediante FetchContent. La compilación requiere acceso a GitHub
solo durante la configuración inicial si la dependencia aún no está en caché.

---

## 4. Ejecución y Pruebas

### Ejecución de Pruebas Automatizadas
Para ejecutar la suite integral de verificación (Bóveda Obsidian, Pruebas Python y Pruebas C++):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verificar.ps1
```

### PEA-i Python
Con el entorno virtual activado, la interfaz gráfica se inicia con:
```powershell
python -m pea.gui
```

Comandos de consola:
```powershell
python -m pea.cli --version
python -m pea.cli resumen
python -m pea.cli importar-url --url "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=<codigo>" --privado
python -m pea.cli importar-url --archivo-grupos datos/fuentes/grupos_upc.txt --privado
```

Para la importación por lote, crea localmente `datos/fuentes/grupos_upc.txt` con un código GrupLAC autorizado por línea. Se omiten líneas vacías y comentarios que comiencen con `#`; los códigos repetidos se procesan una sola vez. No se incluyen códigos de grupos en el repositorio. `--privado` guarda las transcripciones completas en la carpeta privada de salida; si se van a compartir archivos, añade `--anonimizar`. La opción `--privado` no anonimiza por sí sola.

### PEA-i C++
- **Terminal interactiva**: `.\cpp\build\pea-cpp.exe` (opcional `--demo`, `--ascii`, `--sin-color`). En los directorios, pulse `/` para buscar, Enter para conservar el filtro y Escape para borrarlo.
- **CLI no interactiva**: `.\cpp\build\pea-cpp.exe --version` o `.\cpp\build\pea-cpp.exe --help`.
- **Autoprueba de pantallas**: `.\cpp\build\pea-cpp.exe --autoprueba` (escribe capturas en `datos/capturas/terminal/`).
- La TUI actual incluye navegación, resumen y directorios; algunas vistas y acciones de gestión aún no están implementadas. Consulte la matriz de paridad antes de considerar C++ equivalente a Python.

---

## 5. Licencia y Créditos
Desarrollado para fines académicos en la Universidad Popular del Cesar. Prohibida su distribución no autorizada.
