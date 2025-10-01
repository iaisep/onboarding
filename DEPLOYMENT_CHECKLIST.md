# Checklist de Deployment - QR Service en Coolify

## Pre-Deployment ✅

- [x] `requirements-docker.txt` incluye pyzbar==0.1.9
- [x] `requirements-docker.txt` incluye opencv-python-headless==4.10.0.84
- [x] `Dockerfile.coolify` instala libzbar0 y libzbar-dev
- [x] `Dockerfile.coolify` instala dependencias de OpenCV (libgl1-mesa-glx, libglib2.0-0, libsm6, libxext6, libxrender-dev)
- [x] `Dockerfile.coolify` ejecuta ldconfig después de instalar zbar
- [x] `Dockerfile.coolify` verifica instalación de pyzbar antes de continuar
- [x] `Dockerfile.coolify` verifica instalación de opencv antes de continuar
- [x] Script de diagnóstico `verify-qr-dependencies.py` creado

## Deployment Steps 📦

```bash
# 1. Commit cambios
git status
git add Dockerfile.coolify requirements-docker.txt *.md verify-qr-dependencies.py
git commit -m "Fix: Add zbar system libraries for QR code reading in Coolify"
git push origin main

# 2. Deploy en Coolify (UI)
# - Navega a tu servicio en Coolify
# - Click en "Redeploy"
# - O espera auto-deploy si está configurado
```

## Durante el Build 🔍

Busca estas líneas en los logs de Coolify:

```
✅ DEBERÍAS VER:
/usr/lib/x86_64-linux-gnu/libzbar.so.0
libzbar: /usr/lib/x86_64-linux-gnu/libzbar.so.0
✅ pyzbar loaded successfully
✅ opencv loaded successfully, version: 4.10.0.84

❌ NO DEBERÍAS VER:
ModuleNotFoundError: No module named 'pyzbar'
ImportError: Unable to find zbar shared library
```

## Post-Deployment Verification ✅

### 1. Health Check
```bash
# Verificar que el contenedor está corriendo
curl https://tu-dominio.com/admin/login/
# Debería devolver HTML del login, no error 500
```

### 2. Verificación Manual (Opcional)
```bash
# Conectarse al contenedor
docker exec -it <container-id> bash

# Ejecutar diagnóstico
python verify-qr-dependencies.py

# Salir
exit
```

### 3. Test del Endpoint QR
```bash
# Test con archivo desde S3
curl -X POST https://tu-dominio.com/qr-read/ \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3",
    "filename": "test_curp_qr.jpg"
  }'

# Respuesta esperada:
{
  "success": true,
  "total_codes": 3,
  "codes": [...]
}
```

### 4. Test con Upload (Si tienes archivo local)
```bash
curl -X POST https://tu-dominio.com/qr-read/ \
  -F "file=@test_curp_qr.jpg"
```

## Troubleshooting 🔧

### Si ves "Unable to find zbar shared library":

```bash
# 1. Verificar que libzbar está instalado
docker exec -it <container-id> bash
dpkg -l | grep libzbar
# Deberías ver: libzbar0 y libzbar-dev

# 2. Verificar que la librería existe
find /usr -name "libzbar.so*"
# Debería mostrar: /usr/lib/x86_64-linux-gnu/libzbar.so.0

# 3. Ejecutar ldconfig
ldconfig

# 4. Verificar que Python puede encontrarla
python -c "from ctypes.util import find_library; print(find_library('zbar'))"
# Debería imprimir: /usr/lib/x86_64-linux-gnu/libzbar.so.0
```

### Si el build falla en pip install:

1. Revisa conectividad DNS en Coolify
2. Incrementa timeout del build
3. Revisa logs completos del build

### Si los endpoints no responden:

1. Verifica variables de entorno AWS (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET)
2. Revisa logs de Django: `docker logs <container-id>`
3. Verifica que el bucket S3 existe y tiene las imágenes

## Success Indicators ✅

- ✅ Build completa sin errores
- ✅ Container inicia correctamente
- ✅ Health check pasa (login admin accesible)
- ✅ Logs no muestran ImportError
- ✅ Endpoint `/qr-read/` responde con JSON
- ✅ QR codes son detectados correctamente

## Rollback Plan 🔄

Si algo sale mal:

```bash
# 1. Revertir commit
git revert HEAD
git push origin main

# 2. O hacer rollback en Coolify UI
# - Ir a "Deployments"
# - Seleccionar deployment anterior exitoso
# - Click en "Redeploy"

# 3. Investigar logs
docker logs <container-id> --tail 100
```

## Notas Importantes 📝

1. **No elimines** los endpoints QR (/qr-read/, /qr-batch/) si otros servicios los están usando
2. **Backup** de las variables de entorno antes de redeploy
3. **Monitoring**: Observa métricas de CPU/RAM después del deploy (OpenCV puede usar más recursos)
4. **Testing**: Prueba con varios tipos de imágenes (QR, códigos de barras, mixtos)

## Tiempos Estimados ⏱️

- Build: ~5-8 minutos (depende de caché de Docker)
- Deploy: ~1-2 minutos
- Verificación: ~2-3 minutos
- **Total**: ~10-15 minutos

## Contacto en Caso de Problemas 🆘

Si encuentras errores:

1. Captura logs completos del build
2. Ejecuta `verify-qr-dependencies.py` dentro del container
3. Revisa los archivos de documentación:
   - `QR_COOLIFY_DEPLOYMENT.md`
   - `QR_ZBAR_FIX.md`
   - `QR_SERVICE_GUIDE.md`

---

**Última actualización**: 1 de octubre de 2025
**Status**: ✅ Listo para deployment
