#!/bin/bash
# Script de instalación de dependencias para el servicio de lectura de QR

echo "🔧 Instalando dependencias para lectura de códigos QR..."

# Instalar librerías Python
pip install pyzbar==0.1.9
pip install opencv-python-headless==4.10.0.84

echo "✅ Dependencias instaladas correctamente"
echo ""
echo "📝 Nota para Linux/Docker:"
echo "Si estás en Linux o Docker, también necesitas instalar:"
echo "  sudo apt-get update"
echo "  sudo apt-get install -y libzbar0 libzbar-dev"
echo ""
echo "🚀 El servicio de QR está listo para usar!"
