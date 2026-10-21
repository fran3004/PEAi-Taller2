param([ValidateSet("Python", "Cpp")][string]$Aplicacion = "Python")

# La contrasena se solicita de forma oculta y solo se transmite al proceso hijo.
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location $raiz
try {
    $env:PEA_SUPABASE_URL = "https://wdmchsncexayqbjueamb.supabase.co"
    $env:PEA_SUPABASE_PUBLISHABLE_KEY = Read-Host "Clave PUBLICABLE de pea-prod entregada por los autores"
    if (-not $env:PEA_SUPABASE_PUBLISHABLE_KEY.StartsWith("sb_publishable_")) {
        throw "Use la clave publicable sb_publishable_, nunca una clave administrativa."
    }
    $env:PEA_USUARIO_CORREO = Read-Host "Correo de la cuenta de evaluacion"
    $secreto = Read-Host "Contrasena de la cuenta (no se guarda)" -AsSecureString
    $credencial = New-Object System.Management.Automation.PSCredential($env:PEA_USUARIO_CORREO, $secreto)
    $env:PEA_USUARIO_CLAVE = $credencial.GetNetworkCredential().Password

    if ($Aplicacion -eq "Python") {
        if (Test-Path "PEAi-Python\pea-gui.exe") {
            $proceso = Start-Process -FilePath ".\PEAi-Python\pea-gui.exe" -WorkingDirectory $raiz -WindowStyle Hidden -PassThru -Wait
            $resultado = $proceso.ExitCode
        } elseif (Test-Path ".venv\Scripts\python.exe") {
            & .\.venv\Scripts\python.exe -m pea.gui
            $resultado = $LASTEXITCODE
        } else { throw "Primero ejecute scripts\preparar.ps1 o descargue el paquete portable." }
    } else {
        if (Test-Path "PEAi-Cpp\pea-cpp.exe") {
            & .\PEAi-Cpp\pea-cpp.exe
        } elseif (Test-Path "cpp\build\pea-cpp.exe") {
            $bin = if ($env:PEA_MSYS2_BIN) { $env:PEA_MSYS2_BIN } else { "C:\msys64\ucrt64\bin" }
            $env:PATH = "$bin;$env:PATH"
            & .\cpp\build\pea-cpp.exe
        } else { throw "Primero compile C++ con scripts\preparar.ps1 o descargue el paquete portable." }
        $resultado = $LASTEXITCODE
    }
    if ($resultado -ne 0) { throw "La aplicacion termino con codigo $resultado. Revise el mensaje mostrado." }
} finally {
    # Estas variables pertenecen exclusivamente al proceso de este iniciador.
    Remove-Item Env:\PEA_USUARIO_CLAVE -ErrorAction SilentlyContinue
    Remove-Item Env:\PEA_USUARIO_CORREO -ErrorAction SilentlyContinue
    Remove-Item Env:\PEA_SUPABASE_PUBLISHABLE_KEY -ErrorAction SilentlyContinue
    $credencial = $null
    $secreto = $null
    Pop-Location
}
