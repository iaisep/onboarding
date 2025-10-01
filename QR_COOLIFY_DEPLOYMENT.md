# QR Service - Coolify Deployment Fix

## Problema Detectado

Al hacer deploy en Coolify, aparecía el error:
```
ModuleNotFoundError: No module named 'pyzbar'
```

Este error ocurría porque las nuevas dependencias del servicio de lectura de códigos QR no estaban incluidas en el Dockerfile de producción.

## Solución Implementada

### 1. Actualización de `requirements-docker.txt`

Se agregaron las siguientes dependencias:

```txt
# QR Code and Barcode Reading
pyzbar==0.1.9
opencv-python-headless==4.10.0.84
```

### 2. Actualización de `Dockerfile.coolify`

Se agregaron las librerías del sistema necesarias para que funcionen `pyzbar` y `opencv`:

```dockerfile
# Dependencias del sistema agregadas:
libzbar0          # Librería ZBar para lectura de códigos QR/barras
libzbar-dev       # Headers de desarrollo de ZBar
libgl1-mesa-glx   # OpenGL para opencv-python-headless
libglib2.0-0      # GLib para opencv-python-headless
```

## Dependencias del Sistema Explicadas

- **libzbar0 y libzbar-dev**: ZBar es la librería nativa que `pyzbar` utiliza para detectar y leer códigos QR y de barras. Sin estas librerías, `pyzbar` no puede funcionar.

- **libgl1-mesa-glx**: OpenCV requiere OpenGL para ciertas operaciones de procesamiento de imágenes, incluso en la versión "headless".

- **libglib2.0-0**: Librería de utilidades de GNOME requerida por OpenCV para operaciones de bajo nivel.

## Pasos para Redeploy en Coolify

1. Commit y push de los cambios:
   ```bash
   git add requirements-docker.txt Dockerfile.coolify
   git commit -m "Add QR code dependencies for Coolify deployment"
   git push origin main
   ```

2. En Coolify, hacer redeploy del servicio:
   - El build instalará las nuevas dependencias del sistema
   - Se instalarán los paquetes Python adicionales
   - El servicio de QR code estará disponible

3. Verificar logs de deployment:
   - Buscar que se instalen correctamente: `libzbar0`, `pyzbar`, `opencv-python-headless`
   - Confirmar que Django inicie sin errores de importación

## Endpoints Afectados

Los siguientes endpoints ahora funcionarán en Coolify:

- `POST /qr-read/` - Lectura de códigos QR individuales
- `POST /qr-batch/` - Lectura en lote de múltiples imágenes

## Testing Post-Deployment

Una vez deployado, puedes probar el servicio con:

```bash
# Test desde S3
curl -X POST https://tu-dominio.com/qr-read/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3",
    "filename": "ruta/a/imagen-con-qr.jpg"
  }'

# Test con archivo subido
curl -X POST https://tu-dominio.com/qr-read/ \
  -F "file=@imagen-qr.jpg"
```

## Notas Importantes

1. **opencv-python-headless vs opencv-python**: Usamos la versión "headless" porque no requiere X11/GUI, ideal para servidores Linux.

2. **Tamaño de la imagen Docker**: Las nuevas dependencias agregarán aproximadamente 50-70MB al tamaño final de la imagen.

3. **Compatibilidad**: Estas librerías son compatibles con Debian/Ubuntu, que es la base de `python:3.12-slim`.

## Verificación de Instalación

Dentro del contenedor, puedes verificar que todo esté instalado:

```bash
# Verificar zbar
dpkg -l | grep libzbar

# Verificar pyzbar
python -c "from pyzbar import pyzbar; print('pyzbar OK')"

# Verificar opencv
python -c "import cv2; print('opencv version:', cv2.__version__)"
```

## Fecha de Implementación

- **Fecha**: 1 de octubre de 2025
- **Versión Python**: 3.12.11
- **Base Image**: python:3.12-slim
