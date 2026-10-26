# Actualiza índice, numeración y campos de un documento Word y exporta una copia PDF.
# Uso: powershell -NoProfile -File tools/actualizar_word.ps1 -Documento entrega/Especificacion_Tecnica_PEAi.docx -Pdf salida.pdf
param(
    [Parameter(Mandatory = $true)][string]$Documento,
    [string]$Pdf = ""
)
$ErrorActionPreference = "Stop"
$ruta = (Resolve-Path $Documento).Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($ruta)
    $doc.Repaginate()
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Save()
    if ($Pdf -ne "") {
        $doc.ExportAsFixedFormat((Join-Path (Split-Path -Parent $ruta) "_tmp.pdf"), 17)
        Move-Item -Force (Join-Path (Split-Path -Parent $ruta) "_tmp.pdf") $Pdf
    }
    Write-Host ("Páginas: " + $doc.ComputeStatistics(2))
    $doc.Close()
}
finally {
    $word.Quit()
}
