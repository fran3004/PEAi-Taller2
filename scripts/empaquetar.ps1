param([string]$Msys2 = "C:\msys64", [string]$DirectorioCpp = "cpp/build")

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location $raiz
try {
    $python = Join-Path $raiz ".venv\Scripts\python.exe"
    $bin = Join-Path $Msys2 "ucrt64\bin"
    if (-not (Test-Path $python)) { throw "Ejecute scripts\preparar.ps1 -Empaquetado primero." }
    $ejecutableCpp = Join-Path $DirectorioCpp "pea-cpp.exe"
    if (-not (Test-Path $ejecutableCpp)) { throw "Falta compilar C++ en modo Release." }
    $env:PATH = "$bin;$env:PATH"
    $salida = Join-Path $raiz "dist\PEAi-Windows-x64"
    if (Test-Path $salida) { throw "Ya existe $salida. Conserve o mueva la salida anterior antes de regenerar." }
    & $python -m PyInstaller tools/empaquetado/pea.spec --distpath $salida --workpath build/empaquetado --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "Fallo al empaquetar Python." }
    & $python tools/empaquetado/licencias_python.py "$salida\PEAi-Python\licencias"
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron recopilar los avisos de terceros de Python." }
    $cpp = Join-Path $salida "PEAi-Cpp"
    New-Item -ItemType Directory -Path $cpp | Out-Null
    Copy-Item $ejecutableCpp $cpp
    & "$bin\windeployqt6.exe" --release --force-openssl --no-translations --no-system-d3d-compiler --no-opengl-sw "$cpp\pea-cpp.exe"
    if ($LASTEXITCODE -ne 0) { throw "Fallo al desplegar Qt Core/Network." }
    # OpenSSL se carga dinamicamente; no siempre aparece en la tabla de importaciones PE.
    foreach ($patron in @("libssl-*-x64.dll", "libcrypto-*-x64.dll")) {
        $archivos = @(Get-ChildItem -Path (Join-Path $bin $patron))
        if ($archivos.Count -eq 0) { throw "Falta OpenSSL UCRT64: $patron" }
        $archivos | Copy-Item -Destination $cpp
    }
    & $python tools/empaquetado/copiar_dependencias.py $cpp $bin
    if ($LASTEXITCODE -ne 0) { throw "Quedan dependencias C++ sin resolver." }
    Copy-Item README.md $salida
    # Evidencia remota y documentos académicos de la misma versión del programa.
    New-Item -ItemType Directory -Path "$salida\docs\evidencias" -Force | Out-Null
    Copy-Item docs/verificacion-autorias-csv.md,docs/entrega-0.1.7.md "$salida\docs"
    Copy-Item docs/evidencias/autorias-csv-20261025-*.json "$salida\docs\evidencias"
    New-Item -ItemType Directory -Path "$salida\entrega" | Out-Null
    Copy-Item entrega/Especificacion_Tecnica_PEAi.docx,entrega/integrantes.txt,entrega/Taller2_FF_SM.py,entrega/Taller2_FF_SM.cpp "$salida\entrega"
    $commit = (git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "No se pudo identificar el commit de la entrega." }
    $version = (& $python -c "from pea.version import APP_VERSION; print(APP_VERSION)").Trim()
    if ($LASTEXITCODE -ne 0) { throw "No se pudo identificar la version Python." }
    $manifiesto = [ordered]@{
        programa = "PEA-i"
        version = $version
        commit = $commit
        plataforma = "Windows x64"
        generado_utc = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $salida "VERSION-ENTREGA.json"), "$manifiesto`n", [Text.UTF8Encoding]::new($false))
    foreach ($nota in @("brain/20-Diseno/Despliegue.md", "brain/60-Pruebas/Paridad-Python-Cpp.md", "brain/30-Decisiones/ADR-0025-Acceso-academico-completo.md", "brain/50-Bitacora/2026-10-21-codex-entrega-reproducible.md")) {
        $destinoNota = Join-Path $salida $nota
        New-Item -ItemType Directory -Path (Split-Path -Parent $destinoNota) -Force | Out-Null
        Copy-Item $nota $destinoNota
    }
    New-Item -ItemType Directory -Path "$salida\scripts" | Out-Null
    Copy-Item scripts/iniciar-con-base.ps1 "$salida\scripts"
    Copy-Item tools/empaquetado/Iniciar-Python.cmd,tools/empaquetado/Iniciar-Cpp.cmd,tools/empaquetado/Iniciar-Cpp-demo.cmd $salida
    New-Item -ItemType Directory -Path "$salida\config" | Out-Null
    Copy-Item config/pea.config.json "$salida\config"
    # Textos de licencias del toolchain y de FTXUI, sin copiar configuracion local.
    Copy-Item (Join-Path $Msys2 "ucrt64\share\licenses") "$cpp\licencias" -Recurse
    $licenciasQt = Join-Path $Msys2 "ucrt64\share\qt6\LICENSES"
    if (Test-Path $licenciasQt) { Copy-Item $licenciasQt "$cpp\licencias-qt" -Recurse }
    $licenciaFtxui = Join-Path $DirectorioCpp "_deps\ftxui-src\LICENSE"
    if (Test-Path $licenciaFtxui) {
        Copy-Item $licenciaFtxui "$cpp\licencias\FTXUI.txt"
    }
    & $python tools/empaquetado/probar_portable.py $salida
    if ($LASTEXITCODE -ne 0) { throw "El paquete no supero las pruebas sin toolchain en PATH." }
    & $python tools/interop/buscar_secretos.py --paquete $salida
    if ($LASTEXITCODE -ne 0) { throw "Hay posibles credenciales en la entrega; no se publica." }
    $zip = Join-Path $raiz "dist\PEAi-Windows-x64.zip"
    if (Test-Path $zip) { throw "Ya existe $zip; no se sobrescribe una entrega anterior." }
    Compress-Archive -Path $salida -DestinationPath $zip -CompressionLevel Optimal
    $hash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path $raiz "dist\SHA256SUMS.txt"), "$hash  PEAi-Windows-x64.zip`n", [Text.UTF8Encoding]::new($false))
    Write-Host "Paquete validado: $zip"
} finally { Pop-Location }
