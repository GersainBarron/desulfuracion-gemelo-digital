# Cadena completa para un caso, sin intervencion:
#   espera a que la CFD termine -> extraccion (WSL) -> lineas y vistas -> datos para Blender
#   -> render de la animacion (Cycles en la RTX) -> video MP4.
# Reanudable: cada paso se salta si su resultado ya existe.
# Uso: .\cadena_caso.ps1 c12      (normalmente lanzado oculto con Start-Process)
param([Parameter(Mandatory)][string]$Caso)
# 'Continue': los avisos que Blender y WSL escriben en stderr no son errores; cada paso se
# verifica por su resultado (archivo esperado) y si falta se lanza el error a mano.
$ErrorActionPreference = 'Continue'
$distro = if ($env:DESULF_WSL) { $env:DESULF_WSL } else { 'Ubuntu-24.04' }   # distro de WSL con OpenFOAM
function RutaWsl([string]$p) { (wsl -d $distro -- wslpath -a ($p -replace '\\', '/')).Trim() }

$r = Split-Path -Parent $PSScriptRoot
$bl = "$r\blender"; $ext = "$r\extraccion"
$log = "$bl\cadena_$Caso.log"
$py = if ($env:DESULF_PYTHON) { $env:DESULF_PYTHON } else { 'python' }   # Python con numpy y Pillow
$blender = if ($env:BLENDER) { $env:BLENDER } else { 'blender' }
function Anota($m) { "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m | Add-Content $log }
function Aviso($m) { Anota $m; "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m | Add-Content "$r\AVISOS.txt" }
try {
  Anota "inicia cadena de $Caso"
  while ($true) {
    $c = ((Get-Content "$r\orquestador\cola.json" -Raw | ConvertFrom-Json).casos | ? id -eq $Caso)
    if ($c.estado -eq 'terminado') { break }
    if ($c.estado -eq 'fallido') { Aviso "cadena de ${Caso}: el caso fallo en la CFD; no se renderiza"; exit 1 }
    Start-Sleep 300
  }
  Anota "CFD terminada"
  # Extraccion con reintentos: si WSL esta arrancando o se reinicia, la primera llamada puede fallar.
  for ($intento = 1; -not (Test-Path "$ext\$Caso\COMPLETO") -and $intento -le 3; $intento++) {
    Anota "extraccion (intento $intento)"
    wsl -d $distro -- bash (RutaWsl "$ext\extraer_todo.sh") $Caso 2>&1 |
      Select-Object -Last 20 | % { "    wsl: $_" } | Add-Content $log
    if (-not (Test-Path "$ext\$Caso\COMPLETO")) { Anota "la extraccion no termino; se reintenta en 2 min"; Start-Sleep 120 }
  }
  if (-not (Test-Path "$ext\$Caso\COMPLETO")) { throw "la extraccion no termino tras 3 intentos; ver extraccion\extraccion.log" }
  Push-Location $ext
  if (-not (Test-Path "$ext\$Caso\lineas3d.json")) { Anota "lineas de corriente"; & $py lineas.py $Caso | Add-Content $log }
  & $py vista_control.py $Caso | Out-Null; & $py vista_lineas.py $Caso | Out-Null
  Pop-Location
  Push-Location $bl
  if (-not (Test-Path "$bl\datos\$Caso\escena.json") -or -not (Test-Path "$bl\datos\$Caso\corte_0000.png")) {
    Anota "datos para Blender"; & $py preparar_datos.py $Caso 4 | Add-Content $log
  }
  $n = (Get-Content "$bl\datos\$Caso\escena.json" -Raw | ConvertFrom-Json).n_cuadros
  $hechos = @(Get-ChildItem "$bl\render\$Caso" -Filter 'cuadro_*.png' -ErrorAction SilentlyContinue).Count
  if ($hechos -lt $n) {
    Anota "render de $n cuadros"
    & $blender -b --factory-startup --python escena.py -- $Caso animacion 2>&1 | Select-String 'Error|Traceback|ESCENA_OK' | % Line | Add-Content $log
    $hechos = @(Get-ChildItem "$bl\render\$Caso" -Filter 'cuadro_*.png' -ErrorAction SilentlyContinue).Count
    if ($hechos -lt $n) { throw "el render dejo $hechos de $n cuadros" }
  }
  Anota "rotulos"; & $py rotular.py $Caso | Add-Content $log
  Anota "video"
  & $blender -b --factory-startup --python video.py -- "$bl\render\$Caso" "$bl\render\$Caso.mp4" 24 rotulado_ 2>&1 | Select-String 'Error|Traceback|VIDEO_OK' | % Line | Add-Content $log
  Pop-Location
  if (Test-Path "$bl\render\$Caso.mp4") { Aviso "cadena de ${Caso}: video listo en blender\render\$Caso.mp4" }
  else { Aviso "cadena de ${Caso}: no se genero el video; ver blender\cadena_$Caso.log" }
} catch { Aviso "cadena de ${Caso}: error: $($_.Exception.Message)" }
