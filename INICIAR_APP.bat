@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

title Chamba AI - Community Edition
color 0A

echo ================================================================
echo          CHAMBA AI - Autonomous Job Hunter and ATS Resume
echo                      Community Edition
echo ================================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: 1. Check if virtual environment already exists
if exist "venv\Scripts\python.exe" (
    echo [OK] Entorno virtual detectado en carpeta venv.
    goto ACTIVATE_VENV
)

:: 2. Search for a working Python executable
set "PY_CMD="

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto CREATE_VENV
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if !errorlevel! equ 0 (
        set "PY_CMD=python"
        goto CREATE_VENV
    )
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto CREATE_VENV
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto CREATE_VENV
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto CREATE_VENV
)

if exist "C:\Python312\python.exe" (
    set "PY_CMD=C:\Python312\python.exe"
    goto CREATE_VENV
)

echo [ERROR] No se detecto una instalacion valida de Python 3.10 o superior.
echo Por favor instala Python desde: https://www.python.org/downloads/
echo (Asegurate de marcar la casilla "Add python.exe to PATH")
echo.
pause
exit /b 1

:CREATE_VENV
echo [1/3] Creando entorno virtual con: %PY_CMD%...
%PY_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual venv.
    pause
    exit /b 1
)

:ACTIVATE_VENV
echo [2/3] Verificando dependencias del proyecto...
call venv\Scripts\activate.bat

python -c "import fastapi, curl_cffi, playwright, openai" >nul 2>nul
if %errorlevel% neq 0 (
    echo Instalando paquetes requeridos en requirements.txt...
    pip install -r requirements.txt --quiet
    echo Instalando navegador Chromium para Playwright...
    playwright install chromium --quiet
)

echo [3/3] Iniciando servidor web de Chamba AI...
echo.
echo ================================================================
echo   Abre tu navegador en: http://localhost:8000
echo   (Presiona Ctrl+C en esta ventana para detener el servidor)
echo ================================================================
echo.

python run_server.py
pause
