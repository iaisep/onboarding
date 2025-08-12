# 🐳 Opciones de Despliegue Docker

## 📋 Resumen de Opciones

Este proyecto ofrece **DOS opciones** de despliegue con Docker según tus necesidades de base de datos:

### 1. 🏗️ **Despliegue Completo** (Base de datos incluida)
- **Archivo**: `docker-compose.yml`
- **Incluye**: Django + PostgreSQL + Nginx
- **Ideal para**: Desarrollo, testing, despliegues desde cero

### 2. 🔗 **Despliegue con BD Externa** (Base de datos externa)
- **Archivo**: `docker-compose.external-db.yml`
- **Incluye**: Django + Nginx
- **Usa**: Base de datos PostgreSQL externa ya configurada
- **Ideal para**: Producción, cuando ya tienes una BD configurada

---

## 🚀 Opción 1: Despliegue Completo

### Características:
- ✅ Incluye contenedor PostgreSQL
- ✅ Configuración automática de BD
- ✅ Datos persistentes con volúmenes
- ✅ Red interna para comunicación

### Comandos:
```bash
# Windows
docker-deploy.bat

# Linux/macOS
./deploy.sh

# Manual
docker-compose up -d
```

### Servicios Incluidos:
```yaml
services:
  web:     # Django application
  db:      # PostgreSQL 15
  nginx:   # Reverse proxy
```

---

## 🔗 Opción 2: Despliegue con Base de Datos Externa

### Características:
- ✅ Usa BD externa (configurada en .env)
- ✅ Menor consumo de recursos
- ✅ Ideal para producción escalable
- ✅ Conexión segura a BD remota

### Configuración Requerida (.env):
```env
DB_HOST=tu-servidor-bd.com
DB_PORT=5432
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password
```

### Comandos:
```bash
# Windows
deploy-external-db.bat

# Linux/macOS
./deploy-external-db.sh

# Manual
docker-compose -f docker-compose.external-db.yml up -d
```

### Servicios Incluidos:
```yaml
services:
  web:     # Django application
  nginx:   # Reverse proxy
  # NO incluye servicio 'db'
```

---

## 📊 Comparación de Opciones

| Característica | Completo | Externa BD |
|----------------|----------|------------|
| **Base de datos** | ✅ Incluida | 🔗 Externa |
| **Recursos** | 🔶 Alto | ✅ Bajo |
| **Configuración** | ✅ Simple | 🔶 Media |
| **Producción** | 🔶 Básico | ✅ Escalable |
| **Backup/Restore** | 🔶 Manual | ✅ Externo |
| **Alta disponibilidad** | ❌ No | ✅ Posible |

---

## 🛠️ Configuración Detallada

### Para Base de Datos Externa

#### 1. Verificar Credenciales
Asegúrate de que tu archivo `.env` tiene:
```env
# Configuración actual en tu .env
DB_NAME=bnp
DB_USER=bnp_user  
DB_PASSWORD=Veronica023_
DB_HOST=coolify.universidadisep.com
DB_PORT=3001
```

#### 2. Probar Conexión
```bash
# Desde línea de comandos
psql -h coolify.universidadisep.com -p 3001 -U bnp_user -d bnp

# O usando Docker
docker run --rm postgres:15-alpine psql -h coolify.universidadisep.com -p 3001 -U bnp_user -d bnp
```

#### 3. Aplicar Migraciones (Solo primera vez)
```bash
# El script lo hace automáticamente, pero manualmente sería:
docker-compose -f docker-compose.external-db.yml run --rm web python manage.py migrate
```

---

## 🚀 Guías de Despliegue Paso a Paso

### Despliegue Completo (Con BD Local)

```bash
# 1. Clonar repositorio
git clone https://github.com/iaisep/onboarding.git
cd onboarding

# 2. Configurar .env (opcional para desarrollo)
cp .env.example .env
# Editar .env con tus credenciales AWS

# 3. Desplegar
./docker-deploy.bat  # Windows
# o
./deploy.sh         # Linux/macOS
```

### Despliegue con BD Externa

```bash
# 1. Clonar repositorio  
git clone https://github.com/iaisep/onboarding.git
cd onboarding

# 2. Configurar .env con BD externa
# IMPORTANTE: DB_HOST debe apuntar a tu servidor de BD
DB_HOST=tu-servidor-bd.com
DB_PORT=5432
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# 3. Desplegar
./deploy-external-db.bat  # Windows
# o
./deploy-external-db.sh   # Linux/macOS
```

---

## 🔧 Comandos Útiles

### Gestión de Contenedores

```bash
# Ver estado de servicios
docker-compose ps
docker-compose -f docker-compose.external-db.yml ps

# Ver logs en tiempo real
docker-compose logs -f
docker-compose -f docker-compose.external-db.yml logs -f

# Reiniciar servicios
docker-compose restart
docker-compose -f docker-compose.external-db.yml restart

# Detener servicios
docker-compose down
docker-compose -f docker-compose.external-db.yml down

# Reconstruir imagen
docker-compose build --no-cache
docker-compose -f docker-compose.external-db.yml build --no-cache
```

### Acceso a Contenedores

```bash
# Acceder al contenedor web
docker-compose exec web bash
docker-compose -f docker-compose.external-db.yml exec web bash

# Ejecutar comandos Django
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py collectstatic

# Ver logs específicos
docker-compose exec web tail -f /app/logs/django.log
```

---

## 🌍 Variables de Entorno

### Comunes para Ambas Opciones
```env
# Django
DEBUG=False
SECRET_KEY=tu-secret-key

# AWS
AWS_ACCESS_KEY_ID=tu-access-key
AWS_SECRET_ACCESS_KEY=tu-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=tu-bucket

# Seguridad
ALLOWED_HOSTS=tu-dominio.com,localhost
```

### Específicas para BD Externa
```env
# Base de datos externa
DB_HOST=servidor-externo.com
DB_PORT=5432
DB_NAME=base_datos_existente
DB_USER=usuario_existente
DB_PASSWORD=password_existente
```

### Específicas para BD Local (Completa)
```env
# Base de datos local (Docker)
DB_HOST=db  # Nombre del servicio en Docker
DB_PORT=5432
DB_NAME=nombre_bd_local
DB_USER=usuario_local
DB_PASSWORD=password_local
```

---

## 🐛 Solución de Problemas

### Error: No se puede conectar a BD externa
```bash
# 1. Verificar credenciales
cat .env | grep DB_

# 2. Probar conexión directa
telnet coolify.universidadisep.com 3001

# 3. Verificar firewall/seguridad
# La BD debe aceptar conexiones desde la IP del contenedor
```

### Error: Puertos ocupados
```bash
# Ver qué proceso usa el puerto
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS

# Cambiar puerto en docker-compose
ports:
  - "8001:8000"  # Usar puerto 8001 en lugar de 8000
```

### Error: Falta memoria/recursos
```bash
# Para BD externa (menos recursos)
docker-compose -f docker-compose.external-db.yml up -d

# Limitar recursos
docker-compose up -d --scale web=1
```

---

## 📈 Recomendaciones por Entorno

### 🔧 Desarrollo Local
- **Usar**: `docker-compose.yml` (BD incluida)
- **Ventajas**: Setup rápido, datos aislados
- **Comando**: `docker-deploy.bat`

### 🧪 Testing/Staging
- **Usar**: `docker-compose.external-db.yml`
- **Ventajas**: Simula producción, BD compartida
- **Comando**: `deploy-external-db.bat`

### 🏭 Producción
- **Usar**: `docker-compose.external-db.yml`
- **Ventajas**: BD externa gestionada, escalabilidad
- **Extras**: Load balancer, monitoreo, backups

---

## 🔒 Consideraciones de Seguridad

### Base de Datos Externa
- ✅ Usar conexiones SSL/TLS
- ✅ Restringir IPs permitidas
- ✅ Credenciales en variables de entorno
- ✅ Backups automatizados
- ✅ Monitoreo de conexiones

### Redes Docker
- ✅ Red interna para servicios
- ✅ Exponer solo puertos necesarios
- ✅ Usar secrets para credenciales sensibles

---

## 📚 Archivos de Configuración

### Estructura de Archivos Docker
```
proyecto/
├── docker-compose.yml              # BD incluida
├── docker-compose.external-db.yml  # BD externa
├── docker-compose.coolify.yml      # Para Coolify
├── Dockerfile                      # Imagen aplicación
├── nginx.conf                      # Configuración Nginx
├── deploy.sh                       # Script Linux completo
├── docker-deploy.bat               # Script Windows completo
├── deploy-external-db.sh           # Script Linux BD externa  
└── deploy-external-db.bat          # Script Windows BD externa
```

¡Elige la opción que mejor se adapte a tu infraestructura! 🚀
