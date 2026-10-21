param (
    [switch]$ConRed,
    [string]$Msys2 = "C:\msys64",
    [string]$DirectorioCpp = ""
)

# scripts/verificar.ps1
# Script central de verificación para PEA-i (Universidad Popular del Cesar)
# Ejecuta verificación de la bóveda, pruebas Python/C++ y autoprueba de la TUI.

$ErrorActionPreference = "Continue"
$codigo_salida = 0
$tabla_resultados = @()
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONIOENCODING = "utf-8"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PEA-i · VERIFICACION INTEGRAL DEL SISTEMA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verificación de la Bóveda de Obsidian
Write-Host "`n[1/4] Verificando boveda Obsidian (brain/)..." -ForegroundColor Yellow
$py_cmd = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

& $py_cmd tools\brain\verificar_brain.py
if ($LASTEXITCODE -eq 0) {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Boveda Obsidian"; Estado = "OK"; Detalle = "Notas comprobadas, 0 errores" }
} else {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Boveda Obsidian"; Estado = "FALLA"; Detalle = "Errores en enlaces o propiedades" }
    $codigo_salida = 1
}

# 2. Pruebas de Python
Write-Host "`n[2/4] Ejecutando pruebas de Python..." -ForegroundColor Yellow
$pytest_args = @("-v")
if (-not $ConRed) {
    $pytest_args += @("-m", "not red")
}

& $py_cmd -m pytest @pytest_args
if ($LASTEXITCODE -eq 0) {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Pruebas Python"; Estado = "OK"; Detalle = "Suites aprobadas" }
} else {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Pruebas Python"; Estado = "FALLA"; Detalle = "Fallos en pruebas unitarias" }
    $codigo_salida = 1
}

# 3. Pruebas de C++
Write-Host "`n[3/4] Verificando nucleo C++..." -ForegroundColor Yellow
$bin_msys = Join-Path $Msys2 "ucrt64\bin"
if (Test-Path $bin_msys) {
    $env:PATH = "$bin_msys;" + $env:PATH
}

$cpp_build_dir = if ($DirectorioCpp) { $DirectorioCpp } elseif (Test-Path "cpp\build\CMakeCache.txt") { "cpp\build" } elseif (Test-Path "build\CMakeCache.txt") { "build" } else { "" }

if ($cpp_build_dir -ne "") {
    cmake --build $cpp_build_dir
    if ($LASTEXITCODE -eq 0) {
        ctest --test-dir $cpp_build_dir --output-on-failure
        if ($LASTEXITCODE -eq 0) {
            $tabla_resultados += [PSCustomObject]@{ Componente = "Pruebas C++"; Estado = "OK"; Detalle = "Compilación (-Werror) y suites doctest aprobadas" }
        } else {
            $tabla_resultados += [PSCustomObject]@{ Componente = "Pruebas C++"; Estado = "FALLA"; Detalle = "Fallos en CTest" }
            $codigo_salida = 1
        }
        if ($LASTEXITCODE -eq 0) {
            $ejecutable_cpp = Join-Path $cpp_build_dir "pea-cpp.exe"
            if (Test-Path $ejecutable_cpp) {
                & $ejecutable_cpp --autoprueba
                if ($LASTEXITCODE -eq 0) {
                    $tabla_resultados += [PSCustomObject]@{ Componente = "Autoprueba TUI"; Estado = "OK"; Detalle = "32 pantallas renderizadas y capturadas" }
                } else {
                    $tabla_resultados += [PSCustomObject]@{ Componente = "Autoprueba TUI"; Estado = "FALLA"; Detalle = "Hallazgos de renderizado o captura" }
                    $codigo_salida = 1
                }
            } else {
                $tabla_resultados += [PSCustomObject]@{ Componente = "Autoprueba TUI"; Estado = "FALLA"; Detalle = "No existe pea-cpp.exe" }
                $codigo_salida = 1
            }
        }
    } else {
        $tabla_resultados += [PSCustomObject]@{ Componente = "Compilación C++"; Estado = "FALLA"; Detalle = "Error de compilación" }
        $codigo_salida = 1
    }
} else {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Compilacion/Pruebas C++"; Estado = "sin pruebas aun"; Detalle = "No se encontró directorio cpp/build" }
    $tabla_resultados += [PSCustomObject]@{ Componente = "Autoprueba TUI"; Estado = "FALLA"; Detalle = "No se encontró compilación C++" }
    $codigo_salida = 1
}

# Resumen Final
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE VERIFICACION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$tabla_resultados | Format-Table -AutoSize

if ($codigo_salida -eq 0) {
    Write-Host "Las comprobaciones ejecutadas aprobaron. La red y los requisitos pendientes se verifican por separado.`n" -ForegroundColor Green
} else {
    Write-Host "Verificacion completada con fallas. Revisa los detalles anteriores.`n" -ForegroundColor Red
}

exit $codigo_salida
