# Script de Restauración y Salvaguarda · PEA-i
# Restaura el estado de trabajo al último commit limpio de Git y verifica la salud de la bóveda.

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SALVAGUARDA PEA-i: Restaurando archivos desde Git HEAD..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Ejecutar git restore para descartar corrupciones o vaciados accidentales
git restore .

# 2. Verificar el estado del árbol de trabajo
$status = git status --porcelain
if ($status) {
    Write-Host "AVISO: Archivos pendientes o no rastreados detectados:" -ForegroundColor Yellow
    git status -s
} else {
    Write-Host "Arbol de trabajo limpio: todos los archivos coinciden con HEAD." -ForegroundColor Green
}

# 3. Ejecutar verificador de la boveda
Write-Host "`nEjecutando verificacion de la boveda..." -ForegroundColor Cyan
if (Test-Path ".venv\Scripts\python.exe") {
    & .venv\Scripts\python.exe tools\brain\verificar_brain.py --restaurar
} else {
    python tools\brain\verificar_brain.py --restaurar
}

Write-Host "`nRestauracion y verificacion completadas con exito." -ForegroundColor Green
