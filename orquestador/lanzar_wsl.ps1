# Lanza un script de bash en WSL en segundo plano (wsl.exe oculto mantiene viva la sesion).
# Uso: .\lanzar_wsl.ps1 "/ruta/en/wsl/script.sh" [argumentos]
param([Parameter(Mandatory)][string]$Script, [string]$Argumentos = "")
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }
Start-Process wsl -WindowStyle Hidden -ArgumentList "-d $distro -- bash `"$Script`" $Argumentos"
