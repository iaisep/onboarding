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
libsm6            # Session management library para OpenCV
libxext6          # X11 extensions para OpenCV
libxrender-dev    # X Rendering Extension para OpenCV
```

**IMPORTANTE**: Se eliminó la limpieza de `apt/lists` para mantener las referencias a las librerías compartidas.

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

### Método 1: Script de Diagnóstico Completo

Ejecuta el script de diagnóstico dentro del contenedor:

```bash
# Desde dentro del contenedor
python verify-qr-dependencies.py
```

Este script verificará:
- ✅ Librerías del sistema (zbar, OpenGL, etc.)
- ✅ Paquetes de Python (pyzbar, opencv, PIL)
- ✅ Variables de entorno AWS
- ✅ Permisos y archivos del sistema
- ✅ Importación del módulo QRCodeReader

### Método 2: Verificación Manual

Dentro del contenedor, puedes verificar componentes individuales:

```bash
# Verificar zbar
dpkg -l | grep libzbar
find /usr -name "libzbar.so*"

# Verificar pyzbar
python -c "from pyzbar import pyzbar; print('pyzbar OK')"

# Verificar opencv
python -c "import cv2; print('opencv version:', cv2.__version__)"

# Verificar librería compartida zbar
python -c "from ctypes.util import find_library; print('libzbar:', find_library('zbar'))"
```

### Método 3: Logs de Build

Durante el build de Docker, busca estas líneas de éxito:

```
✅ pyzbar loaded successfully
✅ opencv loaded successfully, version: 4.10.0
```

Si ves estos mensajes, las dependencias están correctamente instaladas.

## Troubleshooting

### Error: "Unable to find zbar shared library"

Este error indica que `pyzbar` no puede encontrar `libzbar.so`. Soluciones:

1. **Verificar instalación de libzbar**:
   ```bash
   dpkg -l | grep libzbar
   # Deberías ver: libzbar0 y libzbar-dev
   ```

2. **Verificar ubicación de la librería**:
   ```bash
   find /usr -name "libzbar.so*"
   # Debería mostrar: /usr/lib/x86_64-linux-gnu/libzbar.so.0
   ```

3. **Ejecutar ldconfig**:
   ```bash
   ldconfig
   # Actualiza el caché de librerías compartidas
   ```

4. **Verificar permisos**: Asegúrate de que las librerías se instalaron ANTES de cambiar al usuario `django`.

### Error: OpenCV no puede cargar librerías GUI

Si ves errores sobre `libGL` o `libglib`, asegúrate de que estas dependencias estén instaladas:
- `libgl1-mesa-glx`
- `libglib2.0-0`
- `libsm6`
- `libxext6`
- `libxrender-dev`

### Build se Queda Atascado

Si el build se detiene en pip install:
1. Verifica la conectividad DNS
2. Aumenta el timeout del build en Coolify
3. Revisa los logs en tiempo real

## Fecha de Implementación

- **Fecha**: 1 de octubre de 2025
- **Versión Python**: 3.12.11
- **Base Image**: python:3.12-slim
- **Librerías Críticas**: libzbar0 0.23.92, opencv 4.10.0.84, pyzbar 0.1.9
