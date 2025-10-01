#!/usr/bin/env python3
"""
Script de verificación de dependencias para QR Code Reader
Úsalo dentro del contenedor Docker para diagnosticar problemas de instalación
"""

import sys
import os
from pathlib import Path

def check_system_libraries():
    """Verifica las librerías del sistema"""
    print("=" * 60)
    print("🔍 VERIFICANDO LIBRERÍAS DEL SISTEMA")
    print("=" * 60)
    
    try:
        from ctypes.util import find_library
        
        libs_to_check = ['zbar', 'GL', 'glib-2.0', 'SM', 'Xext', 'Xrender']
        
        for lib in libs_to_check:
            location = find_library(lib)
            if location:
                print(f"✅ {lib:15} -> {location}")
            else:
                print(f"❌ {lib:15} -> NOT FOUND")
                
    except Exception as e:
        print(f"❌ Error checking system libraries: {e}")
    
    print()

def check_python_packages():
    """Verifica los paquetes de Python"""
    print("=" * 60)
    print("🐍 VERIFICANDO PAQUETES DE PYTHON")
    print("=" * 60)
    
    # Check pyzbar
    try:
        from pyzbar import pyzbar
        print("✅ pyzbar importado correctamente")
        
        # Try to get version
        try:
            from pyzbar.wrapper import zbar_version
            version = zbar_version()
            print(f"   Versión de ZBar: {version.decode() if isinstance(version, bytes) else version}")
        except Exception as e:
            print(f"   ⚠️  No se pudo obtener versión: {e}")
            
    except ImportError as e:
        print(f"❌ Error importando pyzbar: {e}")
    except Exception as e:
        print(f"❌ Error con pyzbar: {e}")
    
    # Check OpenCV
    try:
        import cv2
        print(f"✅ opencv (cv2) importado correctamente")
        print(f"   Versión: {cv2.__version__}")
        print(f"   Build info: {cv2.getBuildInformation()[:200]}...")
    except ImportError as e:
        print(f"❌ Error importando cv2: {e}")
    except Exception as e:
        print(f"❌ Error con cv2: {e}")
    
    # Check PIL/Pillow
    try:
        from PIL import Image
        import PIL
        print(f"✅ PIL/Pillow importado correctamente")
        print(f"   Versión: {PIL.__version__}")
    except ImportError as e:
        print(f"❌ Error importando PIL: {e}")
    except Exception as e:
        print(f"❌ Error con PIL: {e}")
    
    # Check numpy
    try:
        import numpy as np
        print(f"✅ numpy importado correctamente")
        print(f"   Versión: {np.__version__}")
    except ImportError as e:
        print(f"❌ Error importando numpy: {e}")
    
    print()

def check_qr_reader():
    """Verifica el módulo QRCodeReader"""
    print("=" * 60)
    print("📱 VERIFICANDO MÓDULO QR CODE READER")
    print("=" * 60)
    
    try:
        # Add parent directory to path if running from project root
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from apirest.AWSQRReader import QRCodeReader
        print("✅ QRCodeReader importado correctamente")
        
        # Try to instantiate
        try:
            reader = QRCodeReader()
            print("✅ QRCodeReader instanciado correctamente")
        except Exception as e:
            print(f"⚠️  Error al instanciar QRCodeReader: {e}")
            
    except ImportError as e:
        print(f"❌ Error importando QRCodeReader: {e}")
    except Exception as e:
        print(f"❌ Error con QRCodeReader: {e}")
    
    print()

def check_environment():
    """Verifica variables de entorno importantes"""
    print("=" * 60)
    print("🌍 VARIABLES DE ENTORNO")
    print("=" * 60)
    
    env_vars = [
        'LD_LIBRARY_PATH',
        'PYTHONPATH',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_BUCKET',
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Hide sensitive values
            if 'KEY' in var or 'SECRET' in var:
                display_value = '*' * 10
            else:
                display_value = value
            print(f"✅ {var:25} = {display_value}")
        else:
            print(f"⚠️  {var:25} = NOT SET")
    
    print()

def check_filesystem():
    """Verifica archivos y permisos"""
    print("=" * 60)
    print("📁 SISTEMA DE ARCHIVOS")
    print("=" * 60)
    
    paths_to_check = [
        '/app',
        '/app/apirest',
        '/app/apirest/AWSQRReader.py',
        '/app/logs',
        '/usr/lib/x86_64-linux-gnu/libzbar.so',
        '/usr/lib/x86_64-linux-gnu/libzbar.so.0',
    ]
    
    for path in paths_to_check:
        p = Path(path)
        if p.exists():
            print(f"✅ {path}")
            if p.is_file():
                stat = p.stat()
                print(f"   Tamaño: {stat.st_size} bytes, Permisos: {oct(stat.st_mode)[-3:]}")
        else:
            print(f"❌ {path} NO EXISTE")
    
    print()

def main():
    """Ejecuta todas las verificaciones"""
    print("\n")
    print("🔧 DIAGNÓSTICO DE DEPENDENCIAS PARA QR CODE READER")
    print(f"🐍 Python: {sys.version}")
    print(f"📍 Path: {sys.executable}")
    print("\n")
    
    check_environment()
    check_system_libraries()
    check_python_packages()
    check_filesystem()
    check_qr_reader()
    
    print("=" * 60)
    print("✅ DIAGNÓSTICO COMPLETO")
    print("=" * 60)
    print("\nSi ves errores arriba, revisa:")
    print("1. Dockerfile.coolify - instalación de librerías del sistema")
    print("2. requirements-docker.txt - pyzbar y opencv-python-headless")
    print("3. Permisos del usuario django")
    print("4. Variables de entorno AWS")
    print()

if __name__ == '__main__':
    main()
