@echo off
echo 🗄️ BNP Django - Configuración de Base de Datos
echo ============================================

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Cargar variables de entorno
for /f "delims=" %%x in (.env) do (set "%%x")

echo 🔍 Verificando conexión a PostgreSQL...

REM Test de conexión básica
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "SELECT version();" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ No se puede conectar a PostgreSQL
    echo 🔧 Verifica que PostgreSQL esté ejecutándose
    echo 🔧 Usuario/password correctos
    pause
    exit /b 1
)

echo ✅ Conexión a PostgreSQL OK

echo 🏗️ Creando base de datos y usuario...
echo.
echo IMPORTANTE: Ingresa la contraseña del usuario 'postgres'
echo.

REM Crear base de datos y usuario
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "CREATE DATABASE %DB_NAME%;" 2>nul
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "CREATE USER %DB_USER% WITH PASSWORD '%DB_PASSWORD%';" 2>nul
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE %DB_NAME% TO %DB_USER%;" 2>nul
psql -h %DB_HOST% -p %DB_PORT% -U postgres -c "ALTER USER %DB_USER% CREATEDB;" 2>nul

echo 🔄 Ejecutando migraciones...
python manage.py makemigrations
python manage.py migrate

REM Verificar que las migraciones se aplicaron
python manage.py migrate --check >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error en migraciones
    pause
    exit /b 1
)

echo ✅ Migraciones aplicadas correctamente

echo 👤 ¿Quieres crear un superusuario? (y/n)
set /p create_superuser=
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo 📁 Recolectando archivos estáticos...
python manage.py collectstatic --noinput

echo 🧪 Verificando configuración...
python manage.py check

echo ✅ ¡Base de datos configurada correctamente!
echo 🚀 Ahora puedes ejecutar: start-local.bat
echo.
pause
