@echo off
echo =========================================
echo  Iniciando Jornada Backend
echo =========================================

set VENV_PATH=.venv
set PYTHON_VENV=%VENV_PATH%\Scripts\python.exe

REM Verifica se a pasta .venv ja existe, senao cria
IF NOT EXIST "%PYTHON_VENV%" (
    echo [1/3] Criando ambiente virtual em '%VENV_PATH%'...
    python -m venv %VENV_PATH%
    if %errorlevel% neq 0 (
        echo Erro ao criar ambiente virtual. Verifique as permissoes.
        pause
        exit /b %errorlevel%
    )
) ELSE (
    echo [1/3] Ambiente virtual '%VENV_PATH%' ja encontrado.
)

echo.
echo [2/3] Instalando dependencias via modulo python...
"%PYTHON_VENV%" -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Subindo servidor FastAPI via Uvicorn...
"%PYTHON_VENV%" -m uvicorn main:app --reload --port 7734

pause
