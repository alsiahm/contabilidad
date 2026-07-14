@echo off
cd /d "%~dp0"

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python no instalado
    pause
    exit /b 1
)

:: Crear venv si no existe
if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Instalando dependencias...
    venv\Scripts\python -m pip install --upgrade pip
    venv\Scripts\pip install -r depts.txt
    venv\Scripts\pip install pywebview
)

:: Ejecutar launcher
venv\Scripts\python launcher.py
pause