@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
 echo Instala Python 3.11 o superior y agregalo a PATH.
 pause
 exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
 echo Instala FFmpeg y FFprobe y agregalos a PATH. Consulta docs/PRODUCCION.md.
 pause
 exit /b 1
)
where ffprobe >nul 2>nul
if errorlevel 1 (
 echo FFprobe no esta disponible en PATH.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install .
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m qaf_video doctor
.venv\Scripts\python.exe -m qaf_video serve --workspace projects
pause
