@echo off
rem Sirve la pagina en http://localhost:8810 (solo en esta computadora)
cd /d "%~dp0web"
start "" http://localhost:8810/
python -m http.server 8810 --bind 127.0.0.1
