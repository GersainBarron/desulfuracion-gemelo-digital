# Registra la tarea programada que mantiene vivo el orquestador.
# - Arranca al iniciar sesion y se revisa cada 15 minutos (si ya corre, no hace nada).
# - Sin limite de tiempo; ventana oculta.
# Uso (PowerShell normal, no requiere administrador):  .\instalar_tarea.ps1
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }   # distro de WSL con OpenFOAM
function RutaWsl([string]$p) { (wsl -d $distro -- wslpath -a ($p -replace '\\', '/')).Trim() }
$nombre = "Desulfuracion-Orquestador"
$arrancar = RutaWsl "$PSScriptRoot\arrancar.sh"
$accion = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -WindowStyle Hidden -Command wsl -d $distro -- bash '$arrancar'"
$alIniciar = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$cada15 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)
$ajustes = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $alIniciar, $cada15 `
  -Settings $ajustes -Description "Cola CFD del gemelo de desulfuracion" -Force
Write-Host "Tarea '$nombre' registrada. Para quitarla: Unregister-ScheduledTask -TaskName $nombre"
