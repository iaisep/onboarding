# 🚨 Solución: Error DNS en Coolify

## 🎯 Error Específico
```
ERROR: failed to do request: Head "https://registry-1.docker.io/v2/library/python/manifests/3.12-slim": 
dial tcp: lookup registry-1.docker.io on 127.0.0.53:53: server misbehaving
```

## 🔍 Causa del Problema
Este error indica que el servidor de Coolify no puede resolver nombres DNS correctamente, específicamente:
- No puede acceder al Docker Registry (registry-1.docker.io)
- El servidor DNS local (127.0.0.53:53) no está funcionando correctamente
- Problema común en servidores Ubuntu/Debian con systemd-resolved mal configurado

## 🛠️ Soluciones Implementadas

### 1. 📦 Dockerfile con DNS Fix
Actualizado `Dockerfile` con configuración DNS:
```dockerfile
# Fix DNS issues in Coolify environment
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf && \
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
```

### 2. 🐳 Docker Compose con DNS
Agregado DNS servers en `docker-compose.coolify-external-db.yml`:
```yaml
services:
  app:
    dns:
      - 8.8.8.8
      - 8.8.4.4
      - 1.1.1.1
```

### 3. 🔧 Dockerfile Alternativo para Coolify
Creado `Dockerfile.coolify` con:
- Múltiples servidores DNS (Google, Cloudflare)
- Reintentos automáticos para instalación de paquetes
- Tests de conectividad DNS
- Configuración específica de PyPI con mirrors

### 4. 📝 Script de Diagnóstico DNS
Creado `fix-coolify-dns.sh` para:
- Diagnosticar problemas DNS
- Aplicar fixes automáticamente
- Verificar conectividad

## 🚀 Pasos para Resolver

### Opción A: Usar Dockerfile.coolify (Recomendado)
1. En Coolify, cambiar el Build Context:
   ```
   Build Context: Dockerfile.coolify
   ```

### Opción B: Fix a Nivel de Servidor
1. Conectar al servidor Coolify via SSH:
   ```bash
   ssh root@tu-servidor-coolify
   ```

2. Ejecutar el script de fix:
   ```bash
   curl -o fix-dns.sh https://raw.githubusercontent.com/iaisep/onboarding/main/fix-coolify-dns.sh
   chmod +x fix-dns.sh
   ./fix-dns.sh
   ```

3. Reiniciar Docker service:
   ```bash
   systemctl restart docker
   ```

### Opción C: Configuración Manual DNS
1. En el servidor Coolify:
   ```bash
   # Editar resolv.conf
   sudo nano /etc/resolv.conf
   
   # Agregar:
   nameserver 8.8.8.8
   nameserver 8.8.4.4
   nameserver 1.1.1.1
   ```

2. Hacer permanente (Ubuntu/Debian):
   ```bash
   # Editar systemd-resolved
   sudo nano /etc/systemd/resolved.conf
   
   # Cambiar:
   DNS=8.8.8.8 8.8.4.4 1.1.1.1
   FallbackDNS=1.1.1.1
   
   # Reiniciar
   sudo systemctl restart systemd-resolved
   ```

## 🧪 Verificación

### Test DNS desde el servidor:
```bash
# Test resolución Docker Registry
nslookup registry-1.docker.io

# Test conectividad
ping -c 2 8.8.8.8

# Test build manual
docker build -t test-build .
```

### En Coolify UI:
1. Verificar logs del build
2. Buscar línea: "✅ Docker registry resolved"
3. Si aparece error DNS, aplicar Opción B

## 🔄 Reintentar Deployment

Después de aplicar cualquier solución:
1. En Coolify: ir a tu aplicación
2. Click en "Deploy"
3. Monitorear logs para confirmar resolución DNS

## 📋 Troubleshooting Adicional

### Si persiste el error:
1. **Verificar firewall del servidor**:
   ```bash
   ufw status
   # Si está activo, permitir salida DNS:
   ufw allow out 53
   ```

2. **Verificar conectividad de red**:
   ```bash
   curl -I https://registry-1.docker.io
   telnet registry-1.docker.io 443
   ```

3. **Usar mirrors alternativos**:
   - Configurar Docker para usar mirror registry
   - Usar imágenes base alternativas

### Configuración Coolify Avanzada:
1. En Coolify Settings → Server → Advanced
2. Agregar variables de entorno DNS:
   ```
   DOCKER_BUILDKIT_DNS=8.8.8.8,8.8.4.4
   ```

## ✅ Resultado Esperado
```
Successfully built abc123def456
Successfully tagged your-image:latest
✅ Build completed successfully
✅ Container started
✅ Health check passed
```

## 📞 Si Nada Funciona
1. Contactar proveedor del servidor (firewall/DNS corporativo)
2. Verificar configuración de red del servidor
3. Considerar usar Dockerfile con imagen base diferente
4. Usar registry privado o mirror local
