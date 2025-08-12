#!/bin/bash

echo "==============================================="
echo "   Coolify - Despliegue con BD Externa"
echo "==============================================="
echo
echo "Este script prepara la aplicacion para Coolify"
echo "usando una base de datos PostgreSQL externa."
echo

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "Configuracion actual desde .env:"
echo "- Host BD: ${DB_HOST:-'no configurado'}"
echo "- Puerto BD: ${DB_PORT:-'no configurado'}"
echo "- Base de datos: ${DB_NAME:-'no configurado'}"
echo "- Usuario BD: ${DB_USER:-'no configurado'}"
echo "- AWS Bucket: ${AWS_S3_BUCKET:-'no configurado'}"
echo "- Allowed Hosts: ${ALLOWED_HOSTS:-'no configurado'}"
echo

read -p "¿Continuar con la preparacion para Coolify? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Preparacion cancelada."
    exit 0
fi

echo
echo "[1/6] Verificando archivo .env..."
if [ ! -f .env ]; then
    echo "ERROR: Archivo .env no encontrado."
    echo "Copia .env.example a .env y configura las credenciales."
    exit 1
fi

echo "[2/6] Verificando configuracion de BD externa..."
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
    echo "ERROR: Configuracion de BD externa incompleta."
    echo "Asegurate de tener en .env:"
    echo "  DB_HOST=tu-servidor-bd.com"
    echo "  DB_PORT=puerto"
    echo "  DB_NAME=nombre_bd"
    echo "  DB_USER=usuario_bd"
    echo "  DB_PASSWORD=password_bd"
    exit 1
fi

echo "[3/6] Verificando configuracion AWS..."
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_S3_BUCKET" ]; then
    echo "ERROR: Configuracion AWS incompleta."
    echo "Asegurate de tener en .env:"
    echo "  AWS_ACCESS_KEY_ID=tu_access_key"
    echo "  AWS_SECRET_ACCESS_KEY=tu_secret_key"
    echo "  AWS_S3_BUCKET=tu_bucket"
    exit 1
fi

echo "[4/6] Probando conexion a base de datos externa..."
if command -v docker &> /dev/null; then
    docker run --rm postgres:15-alpine pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "WARNING: No se pudo verificar la conexion a BD externa."
        echo "Asegurate de que la BD esté accesible desde Coolify."
        echo "Host: $DB_HOST:$DB_PORT"
        echo
    else
        echo "✅ Conexion a BD externa verificada exitosamente."
    fi
else
    echo "INFO: Docker no disponible, saltando verificacion de BD."
fi

echo "[5/6] Creando archivo de configuracion para Coolify..."

# Create Coolify-specific environment template
cat > .env.coolify << EOF
# ===========================================
#  CONFIGURACION PARA COOLIFY - BD EXTERNA
# ===========================================
# 
# Copia estas variables a tu proyecto Coolify:
# Configuracion > Environment Variables

# Django Core
DEBUG=False
SECRET_KEY=${SECRET_KEY}

# Base de Datos Externa
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

# AWS Configuration
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_REKOGNITION_ACCESS_KEY_ID=${AWS_REKOGNITION_ACCESS_KEY_ID:-$AWS_ACCESS_KEY_ID}
AWS_REKOGNITION_SECRET_ACCESS_KEY=${AWS_REKOGNITION_SECRET_ACCESS_KEY:-$AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
AWS_S3_BUCKET=${AWS_S3_BUCKET}
AWS_S3_FACE_BUCKET=${AWS_S3_FACE_BUCKET:-$AWS_S3_BUCKET}
AWS_S3_IMAGE_BUCKET=${AWS_S3_IMAGE_BUCKET:-$AWS_S3_BUCKET}

# OCR Configuration
OCR_MIN_CONFIDENCE=${OCR_MIN_CONFIDENCE:-80}
FACE_MIN_CONFIDENCE=${FACE_MIN_CONFIDENCE:-95}

# Security
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# Django Admin (opcional)
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin123}

# Coolify Specific
PORT=8000
COOLIFY_URL=\${COOLIFY_FQDN}
COOLIFY_BRANCH=main
EOF

echo "✅ Archivo .env.coolify creado con tu configuracion."

echo "[6/6] Validando Docker Compose para Coolify..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.coolify-external-db.yml config > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Archivo docker-compose.coolify-external-db.yml validado."
    else
        echo "WARNING: Error en docker-compose.coolify-external-db.yml"
    fi
else
    echo "INFO: docker-compose no disponible, saltando validacion."
fi

echo
echo "==============================================="
echo "    PREPARACION PARA COOLIFY COMPLETADA"
echo "==============================================="
echo
echo "📋 PASOS PARA COOLIFY:"
echo
echo "1. 📁 SUBIR CODIGO:"
echo "   - git add ."
echo "   - git commit -m 'config: Coolify external DB setup'"  
echo "   - git push origin main"
echo
echo "2. ⚙️  CONFIGURAR EN COOLIFY:"
echo "   - Crear nuevo proyecto desde GitHub"
echo "   - Seleccionar: Docker Compose"
echo "   - Docker Compose file: docker-compose.coolify-external-db.yml"
echo "   - Copiar variables de .env.coolify a Coolify Environment"
echo
echo "3. 🚀 DESPLEGAR:"
echo "   - Click en Deploy en Coolify"
echo "   - Verificar logs de despliegue"
echo "   - Probar endpoints de la API"
echo
echo "📁 ARCHIVOS GENERADOS:"
echo "   ✅ docker-compose.coolify-external-db.yml"
echo "   ✅ .env.coolify (variables para Coolify)"
echo
echo "🔗 CONFIGURACION BD EXTERNA:"
echo "   Host: $DB_HOST"
echo "   Puerto: $DB_PORT"
echo "   Base datos: $DB_NAME"
echo "   Usuario: $DB_USER"
echo
echo "⚠️  IMPORTANTE:"
echo "   - Asegurate de que Coolify pueda acceder a $DB_HOST:$DB_PORT"
echo "   - Configura firewall si es necesario"
echo "   - Verifica que las credenciales sean correctas"
echo
echo "📚 Documentacion completa en:"
echo "   - COOLIFY_DEPLOYMENT.md"
echo "   - DOCKER_DEPLOYMENT_OPTIONS.md"
