# Lanza (o relanza) la cadena de uno o varios casos en segundo plano.
# Uso: .\lanzar_cadena.ps1 c03 c12
$bl = $PSScriptRoot
foreach ($c in $args) {
  Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    ? { $_.CommandLine -match "-File .*cadena_caso\.ps1.* -Caso $c\b" } |
    % { Stop-Process -Id $_.ProcessId -Force; "detenida la cadena anterior de $c" }
  Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$bl\cadena_caso.ps1`" -Caso $c"
  "cadena de $c lanzada"
}
