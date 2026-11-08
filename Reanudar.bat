@echo off
if "%DESULF_WSL%"=="" set DESULF_WSL=Ubuntu-24.04
if exist "%~dp0orquestador\PAUSA" del "%~dp0orquestador\PAUSA"
schtasks /query /tn "Desulfuracion-Orquestador" >nul 2>&1
if %errorlevel%==0 (
  schtasks /run /tn "Desulfuracion-Orquestador" >nul 2>&1
) else (
  for /f "usebackq delims=" %%p in (`wsl -d %DESULF_WSL% -- wslpath -a "%~dp0orquestador/arrancar.sh"`) do set ARRANCAR=%%p
  start "Orquestador CFD" /min wsl -d %DESULF_WSL% -- bash "%ARRANCAR%"
)
echo.
echo  Reanudado. El caso sigue desde el ultimo instante guardado.
echo  Revisa ESTADO.txt en un minuto.
echo.
pause
