@echo off
rem Extrae (o completa) todos los casos en segundo plano, con la ventana oculta.
rem Reanudable: los casos ya extraidos se saltan. Progreso en extraccion\extraccion.log
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lanzar_extraccion.ps1"
echo Extraccion lanzada en segundo plano. Progreso: extraccion\extraccion.log
