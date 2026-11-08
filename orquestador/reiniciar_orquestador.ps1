# Reinicia el orquestador para cargar cambios de codigo sin perder calculo:
# pausa limpia -> espera a que el caso quede en pausa -> detiene el orquestador -> reanuda.
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }   # distro de WSL con OpenFOAM
function RutaWsl([string]$p) { (wsl -d $distro -- wslpath -a ($p -replace '\\', '/')).Trim() }
$r = Split-Path -Parent $PSScriptRoot
New-Item -ItemType File -Force "$r\orquestador\PAUSA" | Out-Null
Write-Host "Pausa solicitada; esperando a que OpenFOAM guarde el instante..."
for ($i = 0; $i -lt 120; $i++) {
  $cola = Get-Content "$r\orquestador\cola.json" -Raw | ConvertFrom-Json
  if (-not ($cola.casos | Where-Object { $_.estado -eq 'corriendo' })) { break }
  Start-Sleep 5
}
wsl -d $distro -- bash (RutaWsl "$PSScriptRoot\detener_orquestador.sh")
# esperar a que la tarea anterior termine; si sigue "Running", Windows ignoraria el nuevo arranque
for ($i = 0; $i -lt 60 -and (Get-ScheduledTask -TaskName 'Desulfuracion-Orquestador').State -eq 'Running'; $i++) { Start-Sleep 2 }
Remove-Item "$r\orquestador\PAUSA"
Start-ScheduledTask -TaskName 'Desulfuracion-Orquestador'
Write-Host "Orquestador reiniciado; el caso sigue desde el instante guardado."
