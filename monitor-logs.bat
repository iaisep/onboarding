@echo off
echo =============================================
echo    AWS Error Monitoring Tool
echo =============================================
echo.
echo Este script te permite ver los logs de AWS en tiempo real
echo.
echo Opciones disponibles:
echo 1. Ver logs generales de Django
echo 2. Ver logs específicos de AWS (errores y operaciones)
echo 3. Ver ambos logs al mismo tiempo
echo 4. Limpiar archivos de logs
echo.
set /p choice="Selecciona una opción (1-4): "

if "%choice%"=="1" (
    echo.
    echo Mostrando logs generales de Django...
    echo Presiona Ctrl+C para salir
    echo.
    powershell -Command "Get-Content logs\django.log -Wait"
) else if "%choice%"=="2" (
    echo.
    echo Mostrando logs específicos de AWS...
    echo Presiona Ctrl+C para salir
    echo.
    powershell -Command "Get-Content logs\aws_errors.log -Wait"
) else if "%choice%"=="3" (
    echo.
    echo Mostrando ambos logs al mismo tiempo...
    echo AWS logs aparecerán con prefijo [AWS]
    echo Django logs aparecerán con prefijo [DJANGO]
    echo Presiona Ctrl+C para salir
    echo.
    powershell -Command "Get-Content logs\django.log,logs\aws_errors.log -Wait"
) else if "%choice%"=="4" (
    echo.
    echo Limpiando archivos de logs...
    if exist logs\django.log del logs\django.log
    if exist logs\aws_errors.log del logs\aws_errors.log
    echo Logs limpiados exitosamente.
    echo.
) else (
    echo Opción inválida. Ejecuta el script nuevamente.
)

pause
