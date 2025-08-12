@echo off
echo 🚀 BNP Django - Setup Local (Sin Docker)
echo ========================================

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado o no está en el PATH
    echo 📥 Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar si PostgreSQL está instalado
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PostgreSQL no está instalado o no está en el PATH
    echo 📥 Descarga PostgreSQL desde: https://www.postgresql.org/download/
    pause
    exit /b 1
)

echo ✅ Python y PostgreSQL detectados

REM Crear entorno virtual si no existe
if not exist venv (
    echo 📦 Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
echo ⚡ Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo 🔄 Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo 📚 Instalando dependencias...
pip install -r requirements.txt

REM Verificar .env
if not exist .env (
    echo ⚙️ Creando archivo .env desde template...
    copy .env.example .env
    echo 🔧 IMPORTANTE: Edita el archivo .env con tus configuraciones
    echo    - Configurar credenciales de base de datos
    echo    - Verificar credenciales AWS
    pause
)

echo 🎯 Setup completado!
echo.
echo 📋 Próximos pasos:
echo    1. Configurar PostgreSQL (crear database 'bnp' y usuario)
echo    2. Editar .env con credenciales de DB
echo    3. Ejecutar: setup-db.bat
echo    4. Ejecutar: start-local.bat
echo.
pause
