@echo off
echo 🚀 Iniciando BNP Django App localmente...
echo ========================================

REM Activar entorno virtual
echo ⚡ Activando entorno virtual...
call venv\Scripts\activate.bat

REM Verificar que las dependencias están instaladas
python -c "import django; print(f'Django {django.get_version()}')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Django no está instalado
    echo 🔧 Ejecuta primero: setup-local.bat
    pause
    exit /b 1
)

REM Verificar configuración
echo 🔍 Verificando configuración...
python manage.py check --deploy >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Advertencias de configuración detectadas
    python manage.py check --deploy
    echo.
    echo ¿Continuar de todas formas? (y/n)
    set /p continue=
    if /i not "%continue%"=="y" exit /b 1
)

REM Aplicar migraciones pendientes
echo 🔄 Verificando migraciones...
python manage.py migrate --check >nul 2>&1
if %errorlevel% neq 0 (
    echo 📝 Aplicando migraciones pendientes...
    python manage.py migrate
)

REM Recolectar archivos estáticos
echo 📁 Recolectando archivos estáticos...
python manage.py collectstatic --noinput

REM Mostrar información del sistema
echo.
echo 📊 Información del sistema:
python -c "
import django
from django.conf import settings
django.setup()
print(f'✅ Django {django.get_version()}')
print(f'✅ Base de datos: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'✅ Debug: {settings.DEBUG}')
print(f'✅ Hosts permitidos: {settings.ALLOWED_HOSTS}')
"

echo.
echo 🌐 Iniciando servidor de desarrollo...
echo 📱 URLs disponibles:
echo    - Aplicación: http://127.0.0.1:8000/
echo    - Admin Panel: http://127.0.0.1:8000/admin/
echo.
echo 🛑 Presiona Ctrl+C para detener el servidor
echo.

REM Iniciar servidor
python manage.py runserver 0.0.0.0:8000
