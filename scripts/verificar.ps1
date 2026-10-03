param (
    [switch]$ConRed
)

# scripts/verificar.ps1
# Script central de verificación para PEA-i (Universidad Popular del Cesar)
# Ejecuta verificación de la bóveda Obsidian, pruebas de Python y pruebas de C++.

$ErrorActionPreference = "Continue"
$codigo_salida = 0
$tabla_resultados = @()

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PEA-i · VERIFICACION INTEGRAL DEL SISTEMA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verificación de la Bóveda de Obsidian
Write-Host "`n[1/3] Verificando boveda Obsidian (brain/)..." -ForegroundColor Yellow
$py_cmd = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

& $py_cmd tools\brain\verificar_brain.py
if ($LASTEXITCODE -eq 0) {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Boveda Obsidian"; Estado = "OK"; Detalle = "31+ notas integras, 0 errores" }
} else {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Boveda Obsidian"; Estado = "FALLA"; Detalle = "Errores en enlaces o propiedades" }
    $codigo_salida = 1
}

# 2. Pruebas de Python
Write-Host "`n[2/3] Ejecutando pruebas de Python..." -ForegroundColor Yellow
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
Write-Host "`n[3/3] Verificando nucleo C++..." -ForegroundColor Yellow
if (Test-Path "C:\msys64\ucrt64\bin") {
    $env:PATH = "C:\msys64\ucrt64\bin;" + $env:PATH
}

$cpp_build_dir = if (Test-Path "cpp\build\CMakeCache.txt") { "cpp\build" } elseif (Test-Path "build\CMakeCache.txt") { "build" } else { "" }

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
    } else {
        $tabla_resultados += [PSCustomObject]@{ Componente = "Compilación C++"; Estado = "FALLA"; Detalle = "Error de compilación" }
        $codigo_salida = 1
    }
} else {
    $tabla_resultados += [PSCustomObject]@{ Componente = "Compilacion/Pruebas C++"; Estado = "sin pruebas aun"; Detalle = "No se encontró directorio cpp/build" }
}

# Resumen Final
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "RESUMEN DE VERIFICACION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$tabla_resultados | Format-Table -AutoSize

if ($codigo_salida -eq 0) {
    Write-Host "Todo en verde. Sistema integro conforme al contrato.`n" -ForegroundColor Green
} else {
    Write-Host "Verificacion completada con fallas. Revisa los detalles anteriores.`n" -ForegroundColor Red
}

exit $codigo_salida
