#!/usr/bin/env python
"""
Script para inicializar datos básicos en la base de datos
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apibase.settings')
django.setup()

from apirest.models import puntaje, puntaje_ocr, puntaje_face

def create_initial_data():
    """Crear datos iniciales necesarios para la aplicación"""
    
    # Crear registro de puntaje para comparaciones generales
    puntaje_obj, created = puntaje.objects.get_or_create(
        pk=1,
        defaults={'puntaje_Max': 75}
    )
    if created:
        print("✅ Creado puntaje general con valor 75")
    else:
        print(f"✅ Puntaje general ya existe: {puntaje_obj.puntaje_Max}")

    # Crear registro de puntaje para OCR
    puntaje_ocr_obj, created = puntaje_ocr.objects.get_or_create(
        pk=1,
        defaults={'puntaje_Max': 80}
    )
    if created:
        print("✅ Creado puntaje OCR con valor 80")
    else:
        print(f"✅ Puntaje OCR ya existe: {puntaje_ocr_obj.puntaje_Max}")

    # Crear registro de puntaje para reconocimiento facial
    puntaje_face_obj, created = puntaje_face.objects.get_or_create(
        pk=1,
        defaults={'puntaje_Max': 85}
    )
    if created:
        print("✅ Creado puntaje facial con valor 85")
    else:
        print(f"✅ Puntaje facial ya existe: {puntaje_face_obj.puntaje_Max}")

if __name__ == '__main__':
    create_initial_data()
    print("\n🎉 Inicialización de datos completada!")
