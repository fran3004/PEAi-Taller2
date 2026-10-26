param(
    [string]$PythonExe = "py",
    [string]$Msys2 = "C:\msys64",
    [string]$DirectorioCpp = "cpp/build",
    [switch]$SoloPython,
    [switch]$Empaquetado
)

# No requiere activar el entorno virtual ni privilegios de administrador.
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location $raiz
try {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        if ($PythonExe -eq "py") {
            & $PythonExe -3.12 -m venv .venv
        } else {
            & $PythonExe -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw "Instale CPython 3.12 x64 o use -PythonExe con su ruta completa." }
    }
    $python = Join-Path $raiz ".venv\Scripts\python.exe"
    & $python -c "import sys, sysconfig; assert sys.version_info >= (3,12) and sysconfig.get_platform() == 'win-amd64', 'Se requiere CPython Windows x64, version 3.12 o posterior'"
    if ($LASTEXITCODE -ne 0) { throw "El entorno .venv no es compatible con esta entrega Windows." }
    $extras = if ($Empaquetado) { ".[dev,empaquetado]" } else { ".[dev]" }
    & $python -m pip install -c requirements/windows.txt -e $extras
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias Python. Revise la conexion a PyPI." }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Hay dependencias Python incompatibles." }

    if (-not $SoloPython) {
        $bin = Join-Path $Msys2 "ucrt64\bin"
        foreach ($herramienta in @("cmake.exe", "ninja.exe", "g++.exe", "Qt6Core.dll", "pdftotext.exe")) {
            if (-not (Test-Path (Join-Path $bin $herramienta))) {
                throw "Falta $herramienta en $bin. Instale los paquetes MSYS2 UCRT64 indicados en README.md."
            }
        }
        $env:PATH = "$bin;$env:PATH"
        & "$bin\cmake.exe" -S cpp -B $DirectorioCpp -G Ninja -DCMAKE_BUILD_TYPE=Release
        if ($LASTEXITCODE -ne 0) { throw "CMake no pudo configurar C++. Revise Qt6, doctest y el acceso a GitHub para FTXUI." }
        & "$bin\cmake.exe" --build $DirectorioCpp --parallel 4
        if ($LASTEXITCODE -ne 0) { throw "La compilacion C++ fallo." }
    }
    Write-Host "Preparacion completada. Inicie Python con .venv\Scripts\python.exe -m pea.gui"
    Write-Host "Para comprobar ambas aplicaciones: powershell -ExecutionPolicy Bypass -File scripts\verificar.ps1"
} finally {
    Pop-Location
}
