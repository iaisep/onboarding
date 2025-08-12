@echo off
echo Starting BNP Django deployment...

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please update .env file with your actual configuration values
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Database migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

REM Create superuser (optional)
echo Do you want to create a superuser? (y/n)
set /p create_superuser=
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

echo Deployment completed successfully!
echo Run 'python manage.py runserver' to start the development server
echo Or use 'gunicorn apibase.wsgi:application' for production
pause
