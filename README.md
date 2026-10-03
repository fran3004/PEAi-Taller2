# PEA-i · Programa Estadístico de Análisis de Investigación

**Universidad Popular del Cesar (UPC)**  
*Facultad de Ingenierías y Tecnologías — Ingeniería de Sistemas*  
*Asignatura: Estructura de Datos (Taller 2)*

---

## 1. Descripción del Proyecto
PEA-i (Programa Estadístico de Análisis de Investigación) es una solución integral diseñada para capturar, estructurar, persistir y analizar la producción académica y científica de grupos de investigación e investigadores, tomando como fuente de verdad normativa el **Modelo de Reconocimiento y Medición de Minciencias 2024** (M601PR04G01) y la plataforma **SCIENTI** (GrupLAC y CvLAC).

El sistema consta de dos aplicaciones de escritorio independientes pero con paridad arquitectónica y visual:
- **PEA-i Python**: Desarrollada en **Python 3.12** utilizando **PySide6** (Qt 6).
- **PEA-i C++**: Desarrollada en **C++17** utilizando **Qt 6 Widgets**, compilada mediante **CMake** y **Ninja**.

Ambas aplicaciones comparten una única base de datos relacional PostgreSQL alojada en la nube mediante **Supabase**, comunicándose de manera exclusiva a través de protocolos seguros **HTTPS** (REST y RPC), sin conexiones directas al puerto PostgreSQL y sin persistencia de credenciales en disco.

---

## 2. Arquitectura del Sistema
El proyecto implementa una arquitectura en capas estrictamente desacoplada:

```
[ Capa de Presentación / GUI ]
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

---

## 4. Ejecución y Pruebas

### Ejecución de Pruebas Automatizadas
Para ejecutar la suite integral de verificación (Bóveda Obsidian, Pruebas Python y Pruebas C++):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verificar.ps1
```

### Ejecutables
- **Python CLI**: `python -m pea.cli --version`
- **Python GUI**: `python -m pea.gui`
- **C++ CLI**: `.\cpp\build\pea-cpp.exe --version`
- **C++ GUI**: `.\cpp\build\pea-cpp.exe`

---

## 5. Licencia y Créditos
Desarrollado para fines académicos en la Universidad Popular del Cesar. Prohibida su distribución no autorizada.
