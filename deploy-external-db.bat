@echo off
echo ===============================================
echo   Docker Compose - Base de Datos Externa
echo ===============================================
echo.
echo Este script despliega la aplicacion usando una
echo base de datos PostgreSQL externa ya configurada.
echo.
echo Configuracion actual desde .env:
echo - Host: %DB_HOST%
echo - Puerto: %DB_PORT% 
echo - Base de datos: %DB_NAME%
echo - Usuario: %DB_USER%
echo.

set /p confirm="¿Continuar con el despliegue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Despliegue cancelado.
    exit /b 0
)

echo.
echo [1/5] Verificando archivo .env...
if not exist .env (
    echo ERROR: Archivo .env no encontrado.
    echo Copia .env.example a .env y configura las credenciales.
    pause
    exit /b 1
)

echo [2/5] Construyendo imagen Docker...
docker-compose -f docker-compose.external-db.yml build

if %ERRORLEVEL% neq 0 (
    echo ERROR: Fallo al construir la imagen Docker.
    pause
    exit /b 1
)

echo [3/5] Probando conexion a base de datos externa...
docker-compose -f docker-compose.external-db.yml run --rm web python manage.py check --database default

if %ERRORLEVEL% neq 0 (
    echo ERROR: No se pudo conectar a la base de datos externa.
    echo Verifica las credenciales en .env:
    echo - DB_HOST=%DB_HOST%
    echo - DB_PORT=%DB_PORT%
    echo - DB_NAME=%DB_NAME% 
    echo - DB_USER=%DB_USER%
    pause
    exit /b 1
)

echo [4/5] Aplicando migraciones a la base de datos...
docker-compose -f docker-compose.external-db.yml run --rm web python manage.py migrate

if %ERRORLEVEL% neq 0 (
    echo ERROR: Fallo al aplicar migraciones.
    pause
    exit /b 1
)

echo [5/5] Iniciando servicios...
docker-compose -f docker-compose.external-db.yml up -d

if %ERRORLEVEL% neq 0 (
    echo ERROR: Fallo al iniciar los servicios.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo          DESPLIEGUE COMPLETADO
echo ===============================================
echo.
echo La aplicacion esta corriendo en:
echo - http://localhost (Nginx)
echo - http://localhost:8000 (Django directo)
echo.
echo Comandos utiles:
echo - Ver logs: docker-compose -f docker-compose.external-db.yml logs -f
echo - Detener: docker-compose -f docker-compose.external-db.yml down
echo - Reiniciar: docker-compose -f docker-compose.external-db.yml restart
echo.
echo Estado de los servicios:
docker-compose -f docker-compose.external-db.yml ps

pause
