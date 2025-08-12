# 🚀 Guía de Ejecución Local (Sin Docker)

## 📋 Pre-requisitos

### 1. Python y PostgreSQL
- **Python 3.8+** (recomendado 3.12)
- **PostgreSQL 12+** instalado localmente
- **Git** para clonar el repositorio

### 2. Verificar Instalaciones
```bash
python --version
psql --version
```

## 🛠️ Pasos de Instalación

### 1. Preparar el Entorno Virtual

```bash
# Navegar al directorio del proyecto
cd c:\Users\maikel\Documents\GitHub\bnp-main

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (CMD)
venv\Scripts\activate.bat
# Linux/Mac
source venv/bin/activate
```

### 2. Instalar Dependencias

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Base de Datos PostgreSQL

#### Opción A: Con psql (Command Line)
```bash
# Conectar a PostgreSQL como superuser
psql -U postgres

# Crear base de datos y usuario
CREATE DATABASE bnp;
CREATE USER bnp_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE bnp TO bnp_user;
ALTER USER bnp_user CREATEDB;
\q
```

#### Opción B: Con pgAdmin
1. **Abrir pgAdmin**
2. **Crear Database**: `bnp`
3. **Crear User**: `bnp_user` con password
4. **Asignar permisos** al user sobre la database

### 4. Actualizar Variables de Entorno

Edita el archivo `.env`:
```env
# Cambiar DEBUG para desarrollo local
DEBUG=True

# Configurar base de datos local
DB_NAME=bnp
DB_USER=bnp_user
DB_PASSWORD=tu_password_seguro
DB_HOST=localhost
DB_PORT=5432

# Mantener tus credenciales AWS actuales
# (ya están configuradas correctamente)
```

### 5. Ejecutar Migraciones

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Verificar que las tablas se crearon
python manage.py dbshell
\dt  # Listar tablas (en PostgreSQL)
\q   # Salir
```

### 6. Crear Superusuario

```bash
python manage.py createsuperuser
# Seguir las instrucciones para crear usuario admin
```

### 7. Recopilar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 8. Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

## 🌐 Acceder a la Aplicación

- **Aplicación Web**: http://127.0.0.1:8000/
- **Panel Admin**: http://127.0.0.1:8000/admin/
- **API Rest**: Según tus endpoints configurados

## 🧪 Verificar Configuración

### Test de Conexión a Base de Datos
```bash
python manage.py dbshell
SELECT version();
\q
```

### Test de Django
```bash
python manage.py check
python manage.py check --deploy
```

### Test de AWS (Opcional)
```python
# En Python shell
python manage.py shell

# Probar conexión AWS
import boto3
from decouple import config

client = boto3.client(
    'rekognition',
    aws_access_key_id=config('AWS_REKOGNITION_ACCESS_KEY_ID'),
    aws_secret_access_key=config('AWS_REKOGNITION_SECRET_ACCESS_KEY'),
    region_name=config('AWS_DEFAULT_REGION')
)
print("AWS Connection OK")
```

## 🐛 Solución de Problemas Comunes

### Error: PostgreSQL Connection
```bash
# Verificar que PostgreSQL esté ejecutándose
# Windows
Get-Service postgresql*

# Iniciar servicio si está parado
Start-Service postgresql-x64-15  # Ajustar versión
```

### Error: pip install psycopg2
```bash
# Instalar binary version
pip install psycopg2-binary
```

### Error: Static Files
```bash
# Crear directorio static si no existe
mkdir static

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

### Error: Port Already in Use
```bash
# Usar puerto diferente
python manage.py runserver 8001

# O encontrar proceso usando puerto 8000
netstat -ano | findstr :8000
# Terminar proceso si es necesario
taskkill /PID <PID_NUMBER> /F
```

## 📝 Comandos Útiles para Desarrollo

### Gestión de Base de Datos
```bash
# Ver migraciones
python manage.py showmigrations

# Migración específica
python manage.py migrate apirest 0001

# Crear datos de prueba (si tienes fixtures)
python manage.py loaddata fixtures/sample_data.json
```

### Debugging
```bash
# Django shell interactivo
python manage.py shell

# Verificar configuración
python manage.py diffsettings

# Limpiar sesiones expiradas
python manage.py clearsessions
```

### Logs y Monitoreo
```bash
# Ver logs en tiempo real (si tienes logging configurado)
tail -f logs/django.log

# Verificar configuración de email (si aplica)
python manage.py sendtestemail admin@example.com
```

## ⚡ Script de Inicio Rápido

Crea un archivo `start-local.bat`:
```batch
@echo off
echo 🚀 Iniciando BNP Django App localmente...

echo ✅ Activando entorno virtual...
call venv\Scripts\activate.bat

echo 🔄 Aplicando migraciones...
python manage.py migrate

echo 📁 Recolectando archivos estáticos...
python manage.py collectstatic --noinput

echo 🌐 Iniciando servidor de desarrollo...
python manage.py runserver

pause
```

O para Linux/Mac `start-local.sh`:
```bash
#!/bin/bash
echo "🚀 Iniciando BNP Django App localmente..."

echo "✅ Activando entorno virtual..."
source venv/bin/activate

echo "🔄 Aplicando migraciones..."
python manage.py migrate

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🌐 Iniciando servidor de desarrollo..."
python manage.py runserver
```

## 🎯 Siguiente Paso

Una vez que todo funcione localmente:
1. **Test todas las funcionalidades** (OCR, reconocimiento facial, etc.)
2. **Verificar API endpoints**
3. **Probar con datos reales**
4. **Optimizar configuraciones** según necesidades

¡Tu aplicación Django debería estar ejecutándose perfectamente! 🎉
