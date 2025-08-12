@echo off
echo 📊 Inicializando datos básicos en la base de datos...

call .\.venv\Scripts\activate.bat

echo Creando registros de puntaje...

python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'apibase.settings'
import django
django.setup()
from apirest.models import puntaje_ocr, puntaje_face, puntaje

# Crear puntaje OCR
try:
    obj, created = puntaje_ocr.objects.get_or_create(pk=1, defaults={'puntaje_Max': 80})
    if created:
        print('✅ Puntaje OCR creado: 80')
    else:
        print(f'✅ Puntaje OCR ya existe: {obj.puntaje_Max}')
except Exception as e:
    print(f'❌ Error creando puntaje OCR: {e}')

# Crear puntaje facial
try:
    obj, created = puntaje_face.objects.get_or_create(pk=1, defaults={'puntaje_Max': 85})
    if created:
        print('✅ Puntaje facial creado: 85')
    else:
        print(f'✅ Puntaje facial ya existe: {obj.puntaje_Max}')
except Exception as e:
    print(f'❌ Error creando puntaje facial: {e}')

# Crear puntaje general
try:
    obj, created = puntaje.objects.get_or_create(pk=1, defaults={'puntaje_Max': 75})
    if created:
        print('✅ Puntaje general creado: 75')
    else:
        print(f'✅ Puntaje general ya existe: {obj.puntaje_Max}')
except Exception as e:
    print(f'❌ Error creando puntaje general: {e}')

print('🎉 Inicialización completada')
"

echo.
echo Datos iniciales configurados correctamente!
pause
