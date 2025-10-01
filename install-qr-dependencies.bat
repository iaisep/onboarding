@echo off
REM Script de instalación de dependencias para el servicio de lectura de QR (Windows)

echo 🔧 Instalando dependencias para lectura de códigos QR...
echo.

REM Instalar librerías Python
pip install pyzbar==0.1.9
pip install opencv-python-headless==4.10.0.84

echo.
echo ✅ Dependencias instaladas correctamente
echo.
echo 📝 Nota para Windows:
echo Si pyzbar no funciona correctamente, puede necesitar instalar zbar manualmente:
echo   Descargar desde: http://zbar.sourceforge.net/
echo   O usar: pip install pyzbar-upright
echo.
echo 🚀 El servicio de QR está listo para usar!
pause
