@echo off
if "%1"=="" (start cmd /k "%~f0" run & exit)
title Iniciando Sistema Contable...
cd /d "%~dp0"

:: ── COMPROBAR SI PYTHON ESTA INSTALADO ──
python --version >nul 2>&1
if errorlevel 1 (
    echo ============================================================
    echo   Python no esta instalado. Descargando e instalando...
    echo   Se necesitaran permisos de administrador.
    echo   Por favor acepta la ventana que aparezca.
    echo ============================================================
    echo.

    echo Descargando Python...
    curl -L -o "%TEMP%\python_installer.exe" https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe
    if errorlevel 1 (
        echo ERROR: No se pudo descargar Python. Comprueba tu conexion a internet.
        pause
        exit /b 1
    )

    echo Instalando Python (puede tardar un momento)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    if errorlevel 1 (
        echo ERROR: No se pudo instalar Python automaticamente.
        echo Por favor instalalo manualmente desde https://www.python.org
        echo y marca la casilla "Add Python to PATH".
        pause
        exit /b 1
    )

    set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    echo Python instalado correctamente.
    echo.
) else (
    for /f "tokens=*" %%i in ('where python') do set PYTHON_EXE=%%i
)

:: ── PRIMERA VEZ: crear venv e instalar dependencias ──
if not exist "venv\Scripts\activate.bat" (
    echo ============================================================
    echo   PREPARANDO LA APLICACION POR PRIMERA VEZ
    echo   Esto puede tardar unos minutos, no cierres esta ventana...
    echo ============================================================
    echo.

    echo [1/2] Creando entorno virtual...
    "%PYTHON_EXE%" -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )

    echo [2/2] Instalando librerias (puede tardar 1-2 minutos)...
    venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las librerias.
        pause
        exit /b 1
    )

    echo.
    echo Instalacion completada correctamente.
    echo.
)

:: ── ARRANCAR STREAMLIT ──
echo Abriendo la aplicacion en el navegador...
echo (Puedes minimizar esta ventana, pero no cerrarla)
echo.

start "" /b cmd /c "timeout /t 3 >nul && start http://localhost:8501"
venv\Scripts\streamlit run app.py --server.headless true --server.port 8501

pause