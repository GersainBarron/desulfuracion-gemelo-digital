# Lanza la extraccion en segundo plano con wsl.exe oculto (mantiene viva la sesion de WSL).
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }   # distro de WSL con OpenFOAM
function RutaWsl([string]$p) { (wsl -d $distro -- wslpath -a ($p -replace '\\', '/')).Trim() }
$script = RutaWsl "$PSScriptRoot\extraer_y_lineas.sh"
Start-Process wsl -WindowStyle Hidden -ArgumentList "-d $distro -- bash `"$script`""
