@echo off
echo 🚀 BNP Docker Deployment Script
echo ================================

REM Check if .env exists
if not exist .env (
    echo ❌ .env file not found!
    echo 📋 Creating .env from template...
    copy .env.example .env
    echo ✅ Please update .env file with your actual configuration values
    echo 🔧 Required variables:
    echo    - SECRET_KEY (generate a new one^)
    echo    - DB_NAME, DB_USER, DB_PASSWORD
    echo    - AWS credentials
    echo    - ALLOWED_HOSTS
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

echo 🔨 Building and starting containers...

REM Build and start services
docker-compose up -d --build

echo ⏳ Waiting for services to be healthy...
timeout /t 30 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Services are running!
    echo.
    echo 📊 Service Status:
    docker-compose ps
    echo.
    echo 🌐 Application URL: http://localhost:8000
    echo 🗄️  Database: PostgreSQL on localhost:5432
    echo 📱 Admin Panel: http://localhost:8000/admin
    echo.
    echo 📋 Default superuser credentials:
    echo    Username: admin
    echo    Password: admin123
    echo    (Change these in production!)
    echo.
    echo 📝 Useful commands:
    echo    - View logs: docker-compose logs -f
    echo    - Stop services: docker-compose down
    echo    - Restart: docker-compose restart
    echo.
) else (
    echo ❌ Some services failed to start. Check logs:
    docker-compose logs
)

pause
