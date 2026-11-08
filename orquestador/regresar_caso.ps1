# Regresa un caso a la cola sin perder calculo: pausa limpia, detiene el orquestador,
# deja el caso en "pendiente" (con su paso de tiempo original) y rearranca.
# Uso: .\regresar_caso.ps1 c06
param([Parameter(Mandatory)][string]$Caso)
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }   # distro de WSL con OpenFOAM
function RutaWsl([string]$p) { (wsl -d $distro -- wslpath -a ($p -replace '\\', '/')).Trim() }
$r = Split-Path -Parent $PSScriptRoot
New-Item -ItemType File -Force "$r\orquestador\PAUSA" | Out-Null
for ($i = 0; $i -lt 120; $i++) {
  $cola = Get-Content "$r\orquestador\cola.json" -Raw | ConvertFrom-Json
  if (-not ($cola.casos | Where-Object { $_.estado -eq 'corriendo' })) { break }
  Start-Sleep 5
}
wsl -d $distro -- bash (RutaWsl "$PSScriptRoot\detener_orquestador.sh")
for ($i = 0; $i -lt 60 -and (Get-ScheduledTask -TaskName 'Desulfuracion-Orquestador').State -eq 'Running'; $i++) { Start-Sleep 2 }
$ruta = "$r\orquestador\cola.json"
$cola = Get-Content $ruta -Raw | ConvertFrom-Json
$c = $cola.casos | Where-Object { $_.id -eq $Caso }
$c.estado = 'pendiente'; $c.intentos = 0; $c.factor_maxCo = 1.0
# el caso que se pauso para esto vuelve a "pendiente" para que el regresado corra primero (orden de la cola)
$cola.casos | Where-Object { $_.estado -eq 'pausado' } | ForEach-Object { $_.estado = 'pendiente' }
[IO.File]::WriteAllText($ruta, ($cola | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding $false))
Write-Host "$Caso regresado a la cola desde el instante $($c.ultimo_instante)"
Remove-Item "$r\orquestador\PAUSA"
Start-ScheduledTask -TaskName 'Desulfuracion-Orquestador'
Write-Host "Orquestador rearrancado"
