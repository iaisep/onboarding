#!/bin/bash

echo "==============================================="
echo "   Docker Compose - Base de Datos Externa"
echo "==============================================="
echo
echo "Este script despliega la aplicacion usando una"
echo "base de datos PostgreSQL externa ya configurada."
echo

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

echo "Configuracion actual desde .env:"
echo "- Host: ${DB_HOST:-'no configurado'}"
echo "- Puerto: ${DB_PORT:-'no configurado'}"
echo "- Base de datos: ${DB_NAME:-'no configurado'}"
echo "- Usuario: ${DB_USER:-'no configurado'}"
echo

read -p "¿Continuar con el despliegue? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Despliegue cancelado."
    exit 0
fi

echo
echo "[1/5] Verificando archivo .env..."
if [ ! -f .env ]; then
    echo "ERROR: Archivo .env no encontrado."
    echo "Copia .env.example a .env y configura las credenciales."
    exit 1
fi

echo "[2/5] Construyendo imagen Docker..."
docker-compose -f docker-compose.external-db.yml build

if [ $? -ne 0 ]; then
    echo "ERROR: Fallo al construir la imagen Docker."
    exit 1
fi

echo "[3/5] Probando conexion a base de datos externa..."
docker-compose -f docker-compose.external-db.yml run --rm web python manage.py check --database default

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo conectar a la base de datos externa."
    echo "Verifica las credenciales en .env:"
    echo "- DB_HOST=${DB_HOST}"
    echo "- DB_PORT=${DB_PORT}"
    echo "- DB_NAME=${DB_NAME}"
    echo "- DB_USER=${DB_USER}"
    exit 1
fi

echo "[4/5] Aplicando migraciones a la base de datos..."
docker-compose -f docker-compose.external-db.yml run --rm web python manage.py migrate

if [ $? -ne 0 ]; then
    echo "ERROR: Fallo al aplicar migraciones."
    exit 1
fi

echo "[5/5] Iniciando servicios..."
docker-compose -f docker-compose.external-db.yml up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Fallo al iniciar los servicios."
    exit 1
fi

echo
echo "==============================================="
echo "          DESPLIEGUE COMPLETADO"
echo "==============================================="
echo
echo "La aplicacion esta corriendo en:"
echo "- http://localhost (Nginx)"
echo "- http://localhost:8000 (Django directo)"
echo
echo "Comandos utiles:"
echo "- Ver logs: docker-compose -f docker-compose.external-db.yml logs -f"
echo "- Detener: docker-compose -f docker-compose.external-db.yml down"
echo "- Reiniciar: docker-compose -f docker-compose.external-db.yml restart"
echo
echo "Estado de los servicios:"
docker-compose -f docker-compose.external-db.yml ps
