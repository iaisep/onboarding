#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para leer códigos QR
Prueba la funcionalidad del servicio QR con una imagen local
"""

import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apirest.AWSQRReader import QRCodeReader
import json

def test_qr_from_file(image_path):
    """
    Prueba la lectura de QR desde un archivo local
    """
    print("="*80)
    print("🔍 TEST DE LECTURA DE CÓDIGO QR")
    print("="*80)
    print(f"\n📁 Archivo: {image_path}\n")
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_content = f.read()
        
        print(f"✅ Imagen cargada: {len(image_content)} bytes\n")
        
        # Initialize QR Reader
        print("🔧 Inicializando lector de QR...")
        qr_reader = QRCodeReader()
        print("✅ Lector inicializado\n")
        
        # Process QR
        print("🔍 Procesando imagen para detectar códigos QR...\n")
        result = qr_reader.read_qr_from_upload(image_content, os.path.basename(image_path))
        
        # Display results
        print("="*80)
        print("📊 RESULTADOS")
        print("="*80)
        print(f"\n✅ Success: {result['success']}")
        print(f"📊 Total QR Codes: {result['metadata']['total_qr_codes']}\n")
        
        if result['success'] and result['qr_codes']:
            for qr in result['qr_codes']:
                print("-"*80)
                print(f"🔢 QR Code #{qr['index']}")
                print(f"   Type: {qr['type']}")
                print(f"   Data: {qr['data']}")
                print(f"   Position: Left={qr['rect']['left']}, Top={qr['rect']['top']}, "
                      f"Width={qr['rect']['width']}, Height={qr['rect']['height']}")
                if qr.get('quality'):
                    print(f"   Quality: {qr['quality']}")
                if qr.get('orientation'):
                    print(f"   Orientation: {qr['orientation']}")
                print("-"*80)
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            print(f"   Error Code: {result.get('error_code', 'N/A')}")
        
        print("\n" + "="*80)
        print("📄 RESPUESTA COMPLETA (JSON)")
        print("="*80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("="*80)
        
        return result
        
    except FileNotFoundError:
        print(f"❌ Error: Archivo no encontrado: {image_path}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Default test image path
    test_image = "test_curp_qr.jpg"
    
    # Check if image path is provided as argument
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(test_image):
        print(f"❌ Error: El archivo '{test_image}' no existe")
        print(f"\nUso: python test_qr_reader.py <ruta_imagen>")
        print(f"Ejemplo: python test_qr_reader.py curp_image.jpg")
        sys.exit(1)
    
    # Run test
    result = test_qr_from_file(test_image)
    
    # Exit with appropriate code
    if result and result.get('success'):
        print("\n✅ Test completado exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Test falló!")
        sys.exit(1)
