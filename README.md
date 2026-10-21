# PEA-i · Taller 2 de Estructura de Datos

Universidad Popular del Cesar · Ingeniería de Sistemas · Grupo 8

PEA-i gestiona grupos, investigadores y productos de investigación. Incluye dos
aplicaciones: **Python con interfaz gráfica PySide6** y **C++17 con terminal
interactiva FTXUI**. Comparten PostgreSQL en Supabase mediante HTTPS, Auth y RLS.

La entrega portable se conecta automáticamente a **pea-prod**, la base compartida
de Supabase. No hay que escribir claves, crear cuentas, configurar variables ni
instalar herramientas de desarrollo. Solo necesita Windows x64 e Internet.

## 1. Para el profesor: descargar, extraer y abrir

Entorno de entrega: **Windows 10/11 de 64 bits (x64)**. Se recomienda Windows
Terminal para C++ y una pantalla de al menos 1100 × 700 píxeles lógicos para Python.

1. Abra [la última entrega descargable](https://github.com/fran3004/PEAi-Taller2/releases/latest).
2. Descargue **`PEAi-Windows-x64.zip`** de **Assets**. **Code → Download ZIP**
   descarga código fuente, no los ejecutables.
3. Use **Extraer todo** y abra la carpeta `PEAi-Windows-x64`. No ejecute dentro del
   ZIP ni separe los `.exe` de sus carpetas `_internal`, DLL y complementos.
4. Abra `Iniciar-Python.cmd`. La ventana inicia la conexión automáticamente;
   espere a que termine de cargar los datos de Supabase.
5. Abra `Iniciar-Cpp.cmd` para la versión de terminal, conectada a la misma base.

El paquete incluye Python, PySide6, fuentes, iconos y las DLL de Qt Core/Network,
OpenSSL y MinGW. No necesita instalar Python, CMake, Qt, PostgreSQL, Node.js,
Docker ni Supabase CLI para ejecutarlo.

Ambas aplicaciones permiten trabajar con los datos reales y guardar cambios.
No aplique migraciones ni cree otra base. `Iniciar-Cpp-demo.cmd` es una alternativa
opcional sin red: usa datos ficticios en memoria y **no** representa Supabase.

Por decisión expresa del propietario, el acceso académico permite leer y modificar
los datos compartidos sin identificar al profesor. **Cualquier persona que obtenga
el paquete tiene los mismos permisos**, incluida la eliminación según las reglas
de la aplicación. No es una distribución adecuada para información privada.

Puede comprobar el ZIP con `Get-FileHash .\PEAi-Windows-x64.zip -Algorithm SHA256`
y compararlo con `SHA256SUMS.txt` de la misma Release. Los ejecutables académicos
no tienen firma digital. Ante una advertencia de Windows, verifique primero el
origen y la suma; no desactive el antivirus.

## 2. Conexión incluida y alternativa para desarrolladores

El archivo `config/pea.config.json` contiene únicamente la URL de pea-prod,
su clave **publicable** y la opción de acceso automático. Ambas aplicaciones
portables lo encuentran junto a sus carpetas, independientemente del directorio
actual. Supabase Auth crea una sesión anónima autenticada; los tokens se mantienen
solo en memoria y se renuevan durante el uso. No se incluyen contraseñas ni claves
administrativas. RLS permanece activo con los permisos académicos documentados en
[ADR-0025](brain/30-Decisiones/ADR-0025-Acceso-academico-completo.md).

**El profesor puede saltar los comandos siguientes.** Para desarrolladores que
ejecuten desde código o quieran usar una cuenta personal, existe este iniciador
opcional; requiere la clave publicable y una cuenta de Supabase Auth.

En PowerShell, situado en la carpeta extraída del paquete:

```powershell
# Solicita clave publicable, correo y contraseña oculta; abre Python.
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar-con-base.ps1 -Aplicacion Python
```

Para C++, abra otra ventana de PowerShell en la misma carpeta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\iniciar-con-base.ps1 -Aplicacion Cpp
```

El iniciador usa `https://wdmchsncexayqbjueamb.supabase.co`, mantiene las credenciales
en el entorno del proceso mientras está abierto y no las escribe en archivos.
Funciona también desde el repositorio después de la instalación del apartado 4.
No se admite `service_role` ni una clave `sb_secret_…`.

Se requiere Internet HTTPS (puerto 443). Si la cuenta no tiene permisos, la sesión
vence, el servicio está pausado o no hay conexión, se muestra el error. Un paquete
correctamente instalado no sustituye la disponibilidad de esos servicios.

Las variables de desarrollo son `PEA_SUPABASE_URL`, `PEA_SUPABASE_PUBLISHABLE_KEY`,
`PEA_USUARIO_CORREO` y `PEA_USUARIO_CLAVE`. Tienen prioridad sobre la configuración
portable. Desde código Python, el JSON portable no se carga automáticamente;
use el iniciador de desarrollo. Esto no afecta al paquete descargable.

## 3. Recorrido de evaluación

1. **Python**: Inicio → Grupos → Investigadores → Productos → Análisis de redes.
   Seleccione filas para ver fichas, cambie filtros anuales y pruebe exportaciones.
2. **C++**: use las pestañas y el mouse. En directorios, `/` busca; `n` crea;
   `e` edita; `t` activa/desactiva; `x` elimina con confirmación; `v` abre una ficha;
   `u` deshace; `r` recarga. Los formularios usan Tab, Enter y Escape. La búsqueda
   admite, por ejemplo, `categoria:A1`. Ventana recomendada: 100 columnas × 28 filas.
3. **Persistencia**: con la conexión automática, cree un registro de evaluación, edítelo
   y recargue. En la otra aplicación compruebe **La base de datos cambió** y
   recargue. La revisión C++ se consulta cada 30 segundos.
4. **Importación**: use CSV o URL SCIENTI y revise el informe de filas rechazadas.
   C++ ofrece `i` para CSV y `w` para URL. Los fixtures ficticios de
   `tests/fixtures/` y `cpp/tests/fixtures/` permiten revisar el procesamiento sin
   descargar datos personales. Las fuentes remotas pueden estar indisponibles.
5. **Interoperabilidad**: en Configuración de Python ejecute la verificación
   cruzada. El paquete localiza C++ en la carpeta hermana `PEAi-Cpp` y compara
   escenarios sin red mediante ambas CLI.

No todos los flujos tienen la misma cobertura en ambas interfaces. La ingesta PDF
C++ y otras diferencias están en la [matriz de paridad](brain/60-Pruebas/Paridad-Python-Cpp.md).
La compilación correcta no implica que todos los requisitos funcionales pendientes
estén cerrados.

## 4. Instalar desde el código fuente

### Descargar

```powershell
git clone https://github.com/fran3004/PEAi-Taller2.git
cd PEAi-Taller2
```

También puede usar **Code → Download ZIP** y extraerlo. Ejecute los comandos desde
la raíz que contiene `README.md` y `pyproject.toml`.

### Requisitos de desarrollo

| Componente | Requisito |
|---|---|
| Python | [CPython 3.12 x64](https://www.python.org/downloads/windows/) recomendado, con pip y lanzador `py`; no el Python de MSYS2 |
| C++ | [MSYS2](https://www.msys2.org/) UCRT64, normalmente en `C:\msys64` |
| Descargas iniciales | Internet para PyPI, MSYS2 y GitHub (FTXUI) |
| Git | Para clonar y para la descarga de FTXUI por CMake |

En la consola **MSYS2 UCRT64**:

```bash
pacman -Syu
# Si pide cerrar, cierre la consola, abra UCRT64 y repita pacman -Syu.
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-qt6-base mingw-w64-ucrt-x86_64-doctest mingw-w64-ucrt-x86_64-openssl git
```

C++ usa Qt6 **Core + Network**. FTXUI `v5.0.0` se descarga en la primera configuración
si no hay un paquete instalado. No mezcle DLL o compiladores MINGW64, UCRT64 y MSVC.

### Preparar ambas aplicaciones

Regrese a **PowerShell**, en la raíz:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preparar.ps1
```

El script crea `.venv`, instala `.[dev]` con las versiones de
`requirements/windows.txt`, comprueba dependencias y configura/compila C++ Release.
No requiere activar el entorno virtual. Para solo Python, añada `-SoloPython`.
Si MSYS2 está en otra ubicación, añada `-Msys2 D:\msys64` a los scripts que lo usan.
Sin lanzador `py`, añada `-PythonExe C:\ruta\Python312\python.exe`.

Equivalente manual para Python:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements/windows.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

### Iniciar

```powershell
# Ventana Python: Configuración → Cargar datos de demostración.
.\.venv\Scripts\python.exe -m pea.gui

# Terminal C++ en demostración.
$env:PATH = "C:\msys64\ucrt64\bin;" + $env:PATH
.\cpp\build\pea-cpp.exe --demo

# Ayuda de las interfaces de consola.
.\.venv\Scripts\python.exe -m pea.cli --help
.\cpp\build\pea-cpp.exe --help
```

Para Supabase use el apartado 2. `--ascii` y `--sin-color` adaptan la TUI a terminales
con menos capacidades.

## 5. Comprobar la instalación

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verificar.ps1
```

Valida documentación, ejecuta pruebas Python, recompila C++, ejecuta CTest y
renderiza la autoprueba TUI. Devuelve código 0 cuando esos pasos aprueban. Las
pruebas de red se excluyen por defecto. `-ConRed` se reserva a los autores con
cuenta de pruebas autorizada; no hace falta para comprobar la instalación.

Comprobaciones individuales (mantenga UCRT64 en `PATH` para C++ desde código):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
ctest --test-dir cpp/build --output-on-failure
.\cpp\build\pruebas_cpp.exe --no-version
.\cpp\build\pea-cpp.exe diagnostico-tls
.\cpp\build\pea-cpp.exe --autoprueba
.\.venv\Scripts\python.exe -m pea.gui --autoprueba
```

GitHub Actions repite instalación, compilación, pruebas y empaquetado en un Windows
nuevo, usando solo los archivos versionados. Las dependencias Python directas están
fijadas en `requirements/windows.txt`; el informe `dependencias-python.txt` registra
las transitivas resueltas en CI. También se registran las versiones de MSYS2.

## 6. Regenerar los ejecutables

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preparar.ps1 -Empaquetado
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verificar.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\empaquetar.ps1
```

Salida: `dist/PEAi-Windows-x64.zip` y `dist/SHA256SUMS.txt`. Se comprueban CLI, TLS,
interoperabilidad y ambas interfaces con un `PATH` sin Python ni MSYS2 y desde
un directorio temporal. Para regenerar, mueva primero la salida anterior.
Los binarios se publican en **Releases**, no se versionan en Git.

## 7. Contenido de la entrega

| Ruta | Contenido |
|---|---|
| `src/pea/` | GUI/CLI, servicios, estructuras propias, ingesta y repositorios Python |
| `cpp/` | TUI/CLI, CMake, servicios, estructuras y pruebas C++ |
| `tests/` | Pruebas Python y fixtures ficticios |
| `supabase/migrations/` | Esquema SQL histórico; no aplicarlo para conectarse al proyecto existente |
| `scripts/`, `tools/empaquetado/`, `requirements/` | Instalación, conexión, verificación y empaquetado |
| `entrega/Taller2_FF_SM.py`, `entrega/Taller2_FF_SM.cpp` | Entradas académicas e índice; necesitan el proyecto modular completo |
| `entrega/Especificacion_Tecnica_PEAi.docx` | Especificación técnica en Word |
| `entrega/integrantes.txt` | Identificación de autores |
| `docs/entrada/` | Enunciado y Modelo Minciencias 2024 |
| `brain/` | Requisitos, diseño, decisiones, manuales y evidencia |

Listas dobles, multilistas, pila, cola e hipercubo están implementados a mano.
Las estadísticas salen del hipercubo; la presentación llama a servicios y los
repositorios usan REST/RPC. No hay base SQLite local.

Agentes, preferencias del editor, entornos virtuales, cachés, capturas,
exportaciones y secretos quedan fuera de Git. La documentación académica se
conserva. El video exigido por el enunciado debe entregarse mediante su enlace
real; el repositorio no inventa una URL ni sustituye esa entrega.

## 8. Solución de problemas

| Situación | Qué comprobar |
|---|---|
| `No module named pea` | Instale el proyecto y use `.venv\Scripts\python.exe` |
| Faltan pytest o responses | Instale `.[dev]`, como hace `preparar.ps1` |
| Faltan Qt6Config.cmake o doctest | Instale los paquetes UCRT64 y use ese CMake |
| Error descargando FTXUI | Revise acceso a GitHub y que Git esté instalado |
| Falta DLL o fuente Inter | Extraiga el ZIP completo; desde código añada UCRT64 a PATH |
| `401`, `403` o sesión vencida | Cierre y abra de nuevo; si persiste, los autores deben verificar Auth/permisos en pea-prod |
| Sin conexión o proyecto pausado | Revise Internet; los autores deben reactivar pea-prod si fue pausado |
| Base de datos cambió | Recargue antes de guardar |
| PowerShell bloquea scripts | Use los comandos con `-ExecutionPolicy Bypass`, limitado a ese proceso |
| Verificación cruzada no encuentra C++ | Conserve las carpetas hermanas PEAi-Python y PEAi-Cpp, o configure PEA_CPP_EXE |
| `WinError 5` en temporales pytest | Ejecute en una sesión con acceso a su carpeta temporal de usuario |

El flujo programado `keep-alive.yml` consulta la disponibilidad cada tres días,
sin modificar datos. Depende de que GitHub Actions esté habilitado; no garantiza
disponibilidad continua ni evita todas las causas de pausa del plan gratuito.

Desarrollado con fines académicos. Las dependencias conservan sus propias licencias.
Véanse [diseño de despliegue](brain/20-Diseno/Despliegue.md) y
[evidencia de entrega](brain/50-Bitacora/2026-10-21-codex-entrega-reproducible.md).
