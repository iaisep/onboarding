# Coolify Deployment Guide for BNP Django App

## 📋 Opciones de Despliegue Coolify

Este proyecto ofrece **DOS opciones** para despliegue en Coolify:

### 🏗️ **Opción 1: Con Base de Datos Incluida**
- **Archivo**: `docker-compose.coolify.yml`
- **Incluye**: Django + PostgreSQL
- **Ideal para**: Proyectos nuevos, desarrollo

### 🔗 **Opción 2: Con Base de Datos Externa**
- **Archivo**: `docker-compose.coolify-external-db.yml`
- **Incluye**: Solo Django
- **Usa**: Base de datos PostgreSQL externa
- **Ideal para**: Producción, BD centralizada

---

## 🚀 Despliegue Rápido

### Para BD Incluida (Tradicional):
```bash
# Usar configuración existente
git push origin main
# Configurar en Coolify con docker-compose.coolify.yml
```

### Para BD Externa (Recomendado):
```bash
# Preparar configuración
./coolify-external-db.bat  # Windows
./coolify-external-db.sh   # Linux

# Subir cambios
git add .
git commit -m "config: Coolify external DB setup"
git push origin main

# Configurar en Coolify con docker-compose.coolify-external-db.yml
```

---

## 📋 Pre-requisitos

1. **Coolify** instalado y configurado
2. **GitHub/GitLab** repository con el código
3. **Base de datos PostgreSQL** (incluida o externa)
4. **Credenciales AWS** para S3 y Rekognition

## 🏗️ Opción 1: Despliegue con BD Incluida

### 1. Preparar el Repository

Asegúrate de que tu repository tenga estos archivos:
- ✅ `Dockerfile`
- ✅ `docker-compose.coolify.yml`
- ✅ `requirements.txt`
- ✅ `.env.example`
- ✅ `docker-entrypoint.sh`

### 2. Crear Nuevo Proyecto en Coolify

1. **Login** a tu instancia de Coolify
2. **Create New Project** 
3. **Select Repository** (conecta tu GitHub/GitLab)
4. **Choose** "Docker Compose" como tipo de deployment
5. **Set Docker Compose file** a `docker-compose.coolify.yml`

### 3. Configurar Variables de Entorno - BD Incluida

En Coolify, agrega estas variables de entorno:

#### Django Configuration
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

#### Database Configuration (BD Incluida)
```
DB_NAME=bnp
DB_USER=postgres_user
DB_PASSWORD=strong_password_here
DB_HOST=db
DB_PORT=5432
```

#### AWS Configuration
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REKOGNITION_ACCESS_KEY_ID=your_rekognition_key
AWS_REKOGNITION_SECRET_ACCESS_KEY=your_rekognition_secret
AWS_DEFAULT_REGION=us-east-1
AWS_S3_FACE_BUCKET=your-face-bucket
AWS_S3_IMAGE_BUCKET=your-image-bucket
```

#### Superuser Configuration (Opcional)
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=secure_admin_password
```

### 4. Configurar Docker Compose

En Coolify:
1. **Set Docker Compose file** a `docker-compose.coolify.yml`
2. **Configure Port** - usualmente 8000
3. **Set Health Check** - endpoint `/admin/login/`

### 5. Configurar Base de Datos

**Opción A: Base de Datos Externa**
- Configura `DB_HOST` con la IP/URL de tu servidor PostgreSQL
- Asegúrate de que el firewall permita conexiones

**Opción B: Base de Datos en Coolify**
- Coolify creará automáticamente el servicio PostgreSQL
- Usa `DB_HOST=db` (como está configurado)

### 6. Deploy

1. **Save Configuration** en Coolify
2. **Click Deploy**
3. **Monitor Logs** durante el deployment

### 7. Post-Deployment

#### Verificar Servicios
```bash
# En Coolify logs, deberías ver:
✅ Database is ready!
🔄 Running database migrations...
📁 Collecting static files...
👤 Creating superuser if needed...
🎉 Setup complete! Starting application...
```

#### Acceder a la Aplicación
- **Web App**: `https://your-domain.com`
- **Admin Panel**: `https://your-domain.com/admin`

## � Opción 2: Despliegue con BD Externa (Recomendado)

### 1. Preparar Configuración para BD Externa

```bash
# Ejecutar script de preparación
./coolify-external-db.bat  # Windows
./coolify-external-db.sh   # Linux/macOS
```

Este script:
- ✅ Verifica configuración de BD externa
- ✅ Valida credenciales AWS
- ✅ Crea archivo `.env.coolify` con variables
- ✅ Prueba conexión a BD externa

### 2. Archivos para BD Externa

El script genera:
- ✅ `docker-compose.coolify-external-db.yml`
- ✅ `.env.coolify` (variables para copiar a Coolify)

### 3. Crear Proyecto en Coolify - BD Externa

1. **Login** a tu instancia de Coolify
2. **Create New Project**
3. **Select Repository** (conecta tu GitHub/GitLab)
4. **Choose** "Docker Compose"
5. **Set Docker Compose file** a `docker-compose.coolify-external-db.yml`

### 4. Configurar Variables de Entorno - BD Externa

Copia las variables de `.env.coolify` a Coolify:

#### Django Configuration
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

#### Database Configuration (BD Externa)
```
DB_NAME=bnp
DB_USER=bnp_user
DB_PASSWORD=Veronica023_
DB_HOST=coolify.universidadisep.com
DB_PORT=3001
```

#### AWS Configuration
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REKOGNITION_ACCESS_KEY_ID=your_rekognition_key
AWS_REKOGNITION_SECRET_ACCESS_KEY=your_rekognition_secret
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=onboarding-uisep
AWS_S3_FACE_BUCKET=onboarding-uisep
AWS_S3_IMAGE_BUCKET=onboarding-uisep
```

#### OCR Configuration
```
OCR_MIN_CONFIDENCE=80
FACE_MIN_CONFIDENCE=95
```

#### Coolify Specific
```
PORT=8000
COOLIFY_URL=${COOLIFY_FQDN}
COOLIFY_BRANCH=main
```

### 5. Configurar Red y Seguridad

**Importante para BD Externa:**
- ✅ Asegurar que Coolify puede acceder a `coolify.universidadisep.com:3001`
- ✅ Configurar firewall para permitir conexiones desde IP de Coolify
- ✅ Verificar que las credenciales sean correctas
- ✅ Probar conexión antes del despliegue

### 6. Deploy con BD Externa

1. **Save Configuration** en Coolify
2. **Click Deploy**
3. **Monitor Logs** - debe mostrar:
   ```
   ✅ External database connection established
   🔄 Running database migrations on external DB...
   📁 Collecting static files...
   👤 Creating superuser if needed...
   🎉 Setup complete! Starting application...
   ```

### 7. Ventajas de BD Externa

- ✅ **Menor uso de recursos** en Coolify
- ✅ **Base de datos centralizada** y gestionada
- ✅ **Backups externos** automatizados
- ✅ **Escalabilidad** independiente de la aplicación
- ✅ **Alta disponibilidad** con BD replicada

---

## �🔧 Configuración Avanzada

### SSL/HTTPS
Coolify maneja automáticamente SSL con Let's Encrypt. Solo asegúrate de:
- **Domain** correctamente configurado
- **DNS** apuntando a tu servidor Coolify

### Monitoreo
- **Health Checks**: Configurado automáticamente
- **Logs**: Disponibles en Coolify dashboard
- **Metrics**: CPU, RAM, storage usage

### Backup
Configura backup automático en Coolify para:
- **Database**: PostgreSQL data
- **Static Files**: Si es necesario

## 🐛 Troubleshooting

### Error: Database Connection
```bash
# Verificar variables de entorno
echo $DB_HOST $DB_NAME $DB_USER

# Verificar conexión desde el container
nc -z $DB_HOST $DB_PORT
```

### Error: Static Files
```bash
# Ejecutar collectstatic manualmente
python manage.py collectstatic --noinput
```

### Error: AWS Permissions
```bash
# Verificar credenciales AWS
aws configure list
aws s3 ls s3://your-bucket-name
```

### Error: Migration Issues
```bash
# Reset migrations si es necesario
python manage.py migrate --fake-initial
```

## 📊 Estructura de Archivos Optimizada

```
bnp-main/
├── Dockerfile                    # Build configuration
├── docker-compose.yml          # Local development
├── docker-compose.coolify.yml  # Coolify deployment
├── docker-entrypoint.sh        # Startup script
├── nginx.conf                  # Nginx config (opcional)
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── .dockerignore              # Docker build optimization
├── apibase/
│   ├── settings.py            # Django settings
│   └── ...
└── apirest/
    └── ...
```

## 🔒 Security Checklist

- ✅ **SECRET_KEY** único y seguro
- ✅ **DEBUG=False** en producción
- ✅ **ALLOWED_HOSTS** configurado correctamente
- ✅ **Database password** fuerte
- ✅ **AWS credentials** con permisos mínimos
- ✅ **HTTPS** habilitado
- ✅ **.env** no incluido en git

## 📞 Soporte

Si encuentras problemas:
1. **Check Coolify logs** primero
2. **Verify environment variables**
3. **Test database connectivity**
4. **Check AWS permissions**

¡Listo para producción! 🎉
