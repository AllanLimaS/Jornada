@echo off
echo =========================================
echo  Iniciando Jornada Backend
echo =========================================

REM Verifica se a pasta .venv já existe, senão cria
IF NOT EXIST ".venv\Scripts\activate.bat" (
    echo [1/3] Criando ambiente virtual em '.venv'...
    python -m venv .venv
) ELSE (
    echo [1/3] Ambiente virtual '.venv' ja encontrado.
)

echo.
echo [2/3] Ativando ambiente virtual e instalando dependencias...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [3/3] Subindo servidor FastAPI via Uvicorn...
uvicorn main:app --reload

pause
