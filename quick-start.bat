@echo off
echo 🚀 INICIO RÁPIDO - BNP Django Local
echo =================================

echo 🔧 Paso 1: Activando entorno virtual...
call venv\Scripts\activate.bat

echo 🔧 Paso 2: Verificando dependencias básicas...
pip show django >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Instalando Django...
    pip install Django==4.2.16 python-decouple psycopg2-binary
)

echo 🔧 Paso 3: Configuración rápida para SQLite (temporal)...
python -c "
import os
from pathlib import Path

# Crear settings temporales para SQLite
settings_content = '''
from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = \"django-insecure-temp-key-for-testing\"
DEBUG = True
ALLOWED_HOSTS = [\"127.0.0.1\", \"localhost\"]

INSTALLED_APPS = [
    \"django.contrib.admin\",
    \"django.contrib.auth\",
    \"django.contrib.contenttypes\",
    \"django.contrib.sessions\",
    \"django.contrib.messages\",
    \"django.contrib.staticfiles\",
    \"rest_framework\",
    \"corsheaders\",
    \"apirest.apps.ApirestConfig\",
]

MIDDLEWARE = [
    \"django.middleware.security.SecurityMiddleware\",
    \"django.contrib.sessions.middleware.SessionMiddleware\",
    \"corsheaders.middleware.CorsMiddleware\",
    \"django.middleware.common.CommonMiddleware\",
    \"django.middleware.csrf.CsrfViewMiddleware\",
    \"django.contrib.auth.middleware.AuthenticationMiddleware\",
    \"django.contrib.messages.middleware.MessageMiddleware\",
    \"django.middleware.clickjacking.XFrameOptionsMiddleware\",
]

ROOT_URLCONF = \"apibase.urls\"
WSGI_APPLICATION = \"apibase.wsgi.application\"

DATABASES = {
    \"default\": {
        \"ENGINE\": \"django.db.backends.sqlite3\",
        \"NAME\": BASE_DIR / \"db.sqlite3\",
    }
}

TEMPLATES = [
    {
        \"BACKEND\": \"django.template.backends.django.DjangoTemplates\",
        \"DIRS\": [],
        \"APP_DIRS\": True,
        \"OPTIONS\": {
            \"context_processors\": [
                \"django.template.context_processors.debug\",
                \"django.template.context_processors.request\",
                \"django.contrib.auth.context_processors.auth\",
                \"django.contrib.messages.context_processors.messages\",
            ],
        },
    },
]

STATIC_URL = \"/static/\"
STATIC_ROOT = os.path.join(BASE_DIR, \"static\")

USE_TZ = True
LANGUAGE_CODE = \"en-us\"
TIME_ZONE = \"UTC\"

REST_FRAMEWORK = {
    \"DEFAULT_AUTHENTICATION_CLASSES\": [
        \"rest_framework.authentication.TokenAuthentication\"
    ]
}

CORS_ORIGIN_WHITELIST = [
    \"http://localhost:3000\",
    \"http://127.0.0.1:3000\",
]
'''

# Hacer backup del settings original
import shutil
if os.path.exists('apibase/settings.py'):
    shutil.copy('apibase/settings.py', 'apibase/settings.py.backup')

# Escribir configuración temporal
with open('apibase/settings_temp.py', 'w') as f:
    f.write(settings_content)

print('✅ Configuración temporal creada')
"

echo 🔧 Paso 4: Usando configuración temporal...
set DJANGO_SETTINGS_MODULE=apibase.settings_temp

echo 🔧 Paso 5: Creando base de datos SQLite y migraciones...
python manage.py makemigrations
python manage.py migrate

echo 🔧 Paso 6: Creando superusuario...
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@test.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Usuario ya existe') | python manage.py shell

echo 🔧 Paso 7: Recolectando archivos estáticos...
python manage.py collectstatic --noinput

echo.
echo ✅ ¡Configuración rápida completada!
echo 🌐 Iniciando servidor en modo de prueba...
echo.
echo 📱 URLs disponibles:
echo    - Aplicación: http://127.0.0.1:8000/
echo    - Admin Panel: http://127.0.0.1:8000/admin/
echo    - Usuario: admin / Contraseña: admin123
echo.
echo 🔍 NOTA: Esta es una configuración temporal con SQLite
echo 🔍 Para producción, configura PostgreSQL usando setup-local.bat
echo.

python manage.py runserver
