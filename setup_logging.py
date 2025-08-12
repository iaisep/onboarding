#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script para configurar el sistema de logging
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

import logging
from django.conf import settings

def test_logging_configuration():
    """Prueba la configuración de logging"""
    print("🔧 PROBANDO CONFIGURACIÓN DE LOGGING")
    print("=" * 50)
    
    # Test general Django logger
    django_logger = logging.getLogger('django')
    print("✅ Logger de Django configurado")
    
    # Test AWS loggers
    aws_logger = logging.getLogger('apirest.aws')
    ocr_logger = logging.getLogger('apirest.ocr')
    face_logger = logging.getLogger('apirest.face')
    
    print("✅ Logger de AWS configurado")
    print("✅ Logger de OCR configurado") 
    print("✅ Logger de Face configurado")
    
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
        print("📁 Directorio de logs creado")
    else:
        print("📁 Directorio de logs ya existe")
    
    # Test log writing
    print("\n🧪 PROBANDO ESCRITURA DE LOGS")
    print("-" * 30)
    
    try:
        django_logger.info("Test message from Django logger")
        print("✅ Django logger: OK")
    except Exception as e:
        print(f"❌ Django logger error: {e}")
    
    try:
        aws_logger.info("Test message from AWS logger")
        print("✅ AWS logger: OK")
    except Exception as e:
        print(f"❌ AWS logger error: {e}")
    
    try:
        ocr_logger.debug("Test debug message from OCR logger")
        ocr_logger.info("Test info message from OCR logger")
        ocr_logger.warning("Test warning message from OCR logger")
        ocr_logger.error("Test error message from OCR logger")
        print("✅ OCR logger: OK (todos los niveles)")
    except Exception as e:
        print(f"❌ OCR logger error: {e}")
    
    try:
        face_logger.debug("Test debug message from Face logger")
        face_logger.info("Test info message from Face logger")
        face_logger.warning("Test warning message from Face logger")
        face_logger.error("Test error message from Face logger")
        print("✅ Face logger: OK (todos los niveles)")
    except Exception as e:
        print(f"❌ Face logger error: {e}")
    
    # Check if log files were created
    print("\n📄 VERIFICANDO ARCHIVOS DE LOGS")
    print("-" * 35)
    
    django_log = logs_dir / 'django.log'
    aws_log = logs_dir / 'aws_errors.log'
    
    if django_log.exists():
        size = django_log.stat().st_size
        print(f"✅ django.log creado ({size} bytes)")
    else:
        print("❌ django.log no encontrado")
    
    if aws_log.exists():
        size = aws_log.stat().st_size
        print(f"✅ aws_errors.log creado ({size} bytes)")
    else:
        print("❌ aws_errors.log no encontrado")

def show_log_samples():
    """Muestra ejemplos de los logs generados"""
    print("\n📖 MUESTRA DE LOGS GENERADOS")
    print("=" * 40)
    
    logs_dir = Path('logs')
    
    # Show Django log sample
    django_log = logs_dir / 'django.log'
    if django_log.exists():
        print("\n🔵 DJANGO LOG (últimas 3 líneas):")
        print("-" * 30)
        try:
            with open(django_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-3:]
                for line in lines:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Error leyendo django.log: {e}")
    
    # Show AWS log sample  
    aws_log = logs_dir / 'aws_errors.log'
    if aws_log.exists():
        print("\n🟠 AWS LOG (últimas 5 líneas):")
        print("-" * 25)
        try:
            with open(aws_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"❌ Error leyendo aws_errors.log: {e}")

def main():
    print("🚀 CONFIGURADOR DE SISTEMA DE LOGGING")
    print("=" * 60)
    print("Este script configura y prueba el sistema de logging para BNP")
    print()
    
    try:
        test_logging_configuration()
        show_log_samples()
        
        print("\n✨ CONFIGURACIÓN COMPLETADA")
        print("=" * 35)
        print("📌 Comandos útiles:")
        print("   python log_analyzer.py              # Análisis de logs")
        print("   monitor-logs.bat                   # Monitor en tiempo real")
        print("   python log_analyzer.py --summary   # Resumen de errores")
        print()
        print("📁 Archivos de logs en: ./logs/")
        print("   - django.log: Logs generales de Django")
        print("   - aws_errors.log: Logs específicos de AWS")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
