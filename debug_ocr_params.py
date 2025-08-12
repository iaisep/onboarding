#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test directo del sistema OCR con logs
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
from decouple import config

def test_direct_ocr():
    """Test directo del OCR con parámetros correctos"""
    print("🧪 PRUEBA DIRECTA DEL OCR")
    print("=" * 40)
    
    try:
        # Get config
        bucket_name = config('AWS_S3_BUCKET')
        print(f"📁 Bucket desde .env: {bucket_name}")
        
        # Test with correct parameters
        print("🔍 Probando OCR con parámetros correctos:")
        print(f"  - Photo: 'CedulaNueva3.jpg'")
        print(f"  - Bucket: '{bucket_name}'")
        
        ocr_processor = consult45()
        result = ocr_processor.detect_text('CedulaNueva3.jpg', bucket_name)
        
        print("✅ OCR test completado")
        print(f"📊 Resultado: {result}")
        
        # Test with incorrect parameters (to see logs)
        print("\n⚠️  Probando OCR con parámetros intercambiados:")
        print(f"  - Photo: '{bucket_name}'")  
        print(f"  - Bucket: 'CedulaNueva3.jpg'")
        
        ocr_processor2 = consult45()
        result2 = ocr_processor2.detect_text(bucket_name, 'CedulaNueva3.jpg')
        
        print("✅ Test con parámetros intercambiados completado")
        print(f"📊 Resultado: {result2}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_recent_logs():
    """Muestra los logs más recientes"""
    print("\n📊 LOGS MÁS RECIENTES")
    print("=" * 30)
    
    logs_dir = Path('logs')
    aws_log = logs_dir / 'aws_errors.log'
    
    if aws_log.exists():
        try:
            with open(aws_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-15:]  # Last 15 lines
                
            print("🟠 AWS LOGS (últimas 15 líneas):")
            print("-" * 35)
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line:
                    print(f"{i:2d}. {line}")
                    
        except Exception as e:
            print(f"❌ Error leyendo logs: {e}")
    else:
        print("❌ No se encontró archivo de logs AWS")

if __name__ == '__main__':
    test_direct_ocr()
    show_recent_logs()
