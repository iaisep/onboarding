@echo off
echo ===============================================
echo    Coolify - Despliegue con BD Externa
echo ===============================================
echo.
echo Este script prepara la aplicacion para Coolify
echo usando una base de datos PostgreSQL externa.
echo.

echo Configuracion actual desde .env:
echo - Host BD: %DB_HOST%
echo - Puerto BD: %DB_PORT%
echo - Base de datos: %DB_NAME%
echo - Usuario BD: %DB_USER%
echo - AWS Bucket: %AWS_S3_BUCKET%
echo - Allowed Hosts: %ALLOWED_HOSTS%
echo.

set /p confirm="¿Continuar con la preparacion para Coolify? (y/N): "
if /i not "%confirm%"=="y" (
    echo Preparacion cancelada.
    exit /b 0
)

echo.
echo [1/6] Verificando archivo .env...
if not exist .env (
    echo ERROR: Archivo .env no encontrado.
    echo Copia .env.example a .env y configura las credenciales.
    pause
    exit /b 1
)

echo [2/6] Verificando configuracion de BD externa...
if "%DB_HOST%"=="" (
    echo ERROR: DB_HOST no configurado en .env
    pause
    exit /b 1
)
if "%DB_PORT%"=="" (
    echo ERROR: DB_PORT no configurado en .env
    pause
    exit /b 1
)
if "%DB_NAME%"=="" (
    echo ERROR: DB_NAME no configurado en .env
    pause
    exit /b 1
)

echo [3/6] Verificando configuracion AWS...
if "%AWS_ACCESS_KEY_ID%"=="" (
    echo ERROR: AWS_ACCESS_KEY_ID no configurado en .env
    pause
    exit /b 1
)
if "%AWS_S3_BUCKET%"=="" (
    echo ERROR: AWS_S3_BUCKET no configurado en .env
    pause
    exit /b 1
)

echo [4/6] Probando conexion a base de datos externa...
docker --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    docker run --rm postgres:15-alpine pg_isready -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo WARNING: No se pudo verificar la conexion a BD externa.
        echo Asegurate de que la BD este accesible desde Coolify.
        echo Host: %DB_HOST%:%DB_PORT%
        echo.
    ) else (
        echo OK Conexion a BD externa verificada exitosamente.
    )
) else (
    echo INFO: Docker no disponible, saltando verificacion de BD.
)

echo [5/6] Creando archivo de configuracion para Coolify...

(
echo # ===========================================
echo #  CONFIGURACION PARA COOLIFY - BD EXTERNA
echo # ===========================================
echo # 
echo # Copia estas variables a tu proyecto Coolify:
echo # Configuracion ^> Environment Variables
echo.
echo # Django Core
echo DEBUG=False
echo SECRET_KEY=%SECRET_KEY%
echo.
echo # Base de Datos Externa
echo DB_NAME=%DB_NAME%
echo DB_USER=%DB_USER%
echo DB_PASSWORD=%DB_PASSWORD%
echo DB_HOST=%DB_HOST%
echo DB_PORT=%DB_PORT%
echo.
echo # AWS Configuration
echo AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID%
echo AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY%
echo AWS_REKOGNITION_ACCESS_KEY_ID=%AWS_REKOGNITION_ACCESS_KEY_ID%
echo AWS_REKOGNITION_SECRET_ACCESS_KEY=%AWS_REKOGNITION_SECRET_ACCESS_KEY%
echo AWS_DEFAULT_REGION=%AWS_DEFAULT_REGION%
echo AWS_S3_BUCKET=%AWS_S3_BUCKET%
echo AWS_S3_FACE_BUCKET=%AWS_S3_FACE_BUCKET%
echo AWS_S3_IMAGE_BUCKET=%AWS_S3_IMAGE_BUCKET%
echo.
echo # OCR Configuration
echo OCR_MIN_CONFIDENCE=%OCR_MIN_CONFIDENCE%
echo FACE_MIN_CONFIDENCE=%FACE_MIN_CONFIDENCE%
echo.
echo # Security
echo ALLOWED_HOSTS=%ALLOWED_HOSTS%
echo.
echo # Django Admin ^(opcional^)
echo DJANGO_SUPERUSER_USERNAME=%DJANGO_SUPERUSER_USERNAME%
echo DJANGO_SUPERUSER_EMAIL=%DJANGO_SUPERUSER_EMAIL%
echo DJANGO_SUPERUSER_PASSWORD=%DJANGO_SUPERUSER_PASSWORD%
echo.
echo # Coolify Specific
echo PORT=8000
echo COOLIFY_URL=${COOLIFY_FQDN}
echo COOLIFY_BRANCH=main
) > .env.coolify

echo OK Archivo .env.coolify creado con tu configuracion.

echo [6/6] Validando Docker Compose para Coolify...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    docker-compose -f docker-compose.coolify-external-db.yml config >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo OK Archivo docker-compose.coolify-external-db.yml validado.
    ) else (
        echo WARNING: Error en docker-compose.coolify-external-db.yml
    )
) else (
    echo INFO: docker-compose no disponible, saltando validacion.
)

echo.
echo ===============================================
echo     PREPARACION PARA COOLIFY COMPLETADA
echo ===============================================
echo.
echo PASOS PARA COOLIFY:
echo.
echo 1. SUBIR CODIGO:
echo    - git add .
echo    - git commit -m "config: Coolify external DB setup"
echo    - git push origin main
echo.
echo 2. CONFIGURAR EN COOLIFY:
echo    - Crear nuevo proyecto desde GitHub
echo    - Seleccionar: Docker Compose
echo    - Docker Compose file: docker-compose.coolify-external-db.yml
echo    - Copiar variables de .env.coolify a Coolify Environment
echo.
echo 3. DESPLEGAR:
echo    - Click en Deploy en Coolify
echo    - Verificar logs de despliegue
echo    - Probar endpoints de la API
echo.
echo ARCHIVOS GENERADOS:
echo    OK docker-compose.coolify-external-db.yml
echo    OK .env.coolify ^(variables para Coolify^)
echo.
echo CONFIGURACION BD EXTERNA:
echo    Host: %DB_HOST%
echo    Puerto: %DB_PORT%
echo    Base datos: %DB_NAME%
echo    Usuario: %DB_USER%
echo.
echo IMPORTANTE:
echo    - Asegurate de que Coolify pueda acceder a %DB_HOST%:%DB_PORT%
echo    - Configura firewall si es necesario
echo    - Verifica que las credenciales sean correctas
echo.
echo Documentacion completa en:
echo    - COOLIFY_DEPLOYMENT.md
echo    - DOCKER_DEPLOYMENT_OPTIONS.md

pause
