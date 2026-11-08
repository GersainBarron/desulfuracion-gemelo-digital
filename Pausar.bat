@echo off
type nul > "%~dp0orquestador\PAUSA"
echo.
echo  Pausa solicitada.
echo  OpenFOAM guardara el instante actual y se detendra en unos segundos.
echo  ESTADO.txt dira "EN PAUSA" cuando termine de guardar.
echo  No se pierde nada de lo calculado. Para seguir: Reanudar.bat
echo.
pause
