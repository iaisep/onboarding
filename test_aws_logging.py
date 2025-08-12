#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script para generar logs reales de AWS
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.append(str(Path(__file__).parent))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apibase.settings')

# Setup Django
django.setup()

from apirest.AWSocr import consult45
from apirest.AWScompare import consult46
import logging

def test_ocr_logging():
    """Prueba el sistema de logging de OCR con un archivo inexistente"""
    print("🔍 PROBANDO LOGGING DE OCR")
    print("=" * 40)
    
    try:
        # Esto debería generar logs de error porque el archivo no existe
        ocr_processor = consult45()
        result = ocr_processor.detect_text('archivo_inexistente.jpg', 'bucket-inexistente')
        print("✅ OCR test completado - revisa los logs")
        
    except Exception as e:
        print(f"❌ Error en test OCR: {e}")

def test_face_logging():
    """Prueba el sistema de logging de Face comparison"""
    print("\n👤 PROBANDO LOGGING DE FACE COMPARISON")
    print("=" * 50)
    
    try:
        # Esto debería generar logs de error porque los archivos no existen
        face_processor = consult46()
        result = face_processor.compare_faces('selfie_inexistente.jpg', 'cedula_inexistente.jpg')
        print("✅ Face comparison test completado - revisa los logs")
        
    except Exception as e:
        print(f"❌ Error en test Face: {e}")

def show_generated_logs():
    """Muestra los logs generados por las pruebas"""
    print("\n📊 LOGS GENERADOS DURANTE LAS PRUEBAS")
    print("=" * 50)
    
    # Show AWS error logs
    aws_log_path = Path('logs/aws_errors.log')
    if aws_log_path.exists():
        print("\n🟠 AWS ERROR LOGS (últimas 10 líneas):")
        print("-" * 40)
        try:
            with open(aws_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-10:]
                for i, line in enumerate(lines, 1):
                    print(f"{i:2d}. {line.strip()}")
        except Exception as e:
            print(f"❌ Error leyendo logs: {e}")

def main():
    print("🧪 GENERADOR DE LOGS DE PRUEBA")
    print("=" * 45)
    print("Este script genera logs reales para probar el sistema")
    print()
    
    # Test OCR logging
    test_ocr_logging()
    
    # Test Face logging
    test_face_logging()
    
    # Show the generated logs
    show_generated_logs()
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. Ejecuta: python log_analyzer.py --summary")
    print("2. Ejecuta: python log_analyzer.py --level ERROR") 
    print("3. Ejecuta: monitor-logs.bat para ver logs en tiempo real")
    print()
    print("📁 Revisa los archivos en ./logs/ para ver todos los detalles")

if __name__ == '__main__':
    main()
