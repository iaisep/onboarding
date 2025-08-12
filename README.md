# 🎯 Onboarding API - Django OCR & Face Recognition

> **Sistema de procesamiento de documentos con OCR y reconocimiento facial usando AWS Rekognition**

![Django](https://img.shields.io/badge/Django-4.2.16-green.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![AWS](https://img.shields.io/badge/AWS-Rekognition-orange.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## 🚀 Características Principales

- **✅ OCR Inteligente**: Extracción de datos de cédulas panameñas usando AWS Rekognition
- **👤 Comparación Facial**: Verificación de identidad con AWS Rekognition
- **🔒 Seguridad**: Gestión segura de credenciales AWS con variables de entorno
- **📊 Sistema de Logs**: Monitoreo completo de errores y operaciones
- **🐳 Docker**: Listo para despliegue con Docker y Coolify
- **🗄️ PostgreSQL**: Base de datos robusta y escalable
- **⚡ REST API**: Endpoints RESTful con Django REST Framework

## 📋 Requisitos

- Python 3.12+
- PostgreSQL 12+
- Docker (opcional)
- Credenciales AWS (Rekognition, S3)

## 🛠️ Instalación Rápida

### Opción 1: Setup Local

```bash
# Clonar repositorio
git clone https://github.com/iaisep/onboarding.git
cd onboarding

# Ejecutar setup automático
./quick-start.bat
```

### Opción 2: Docker

```bash
# Clonar y ejecutar con Docker
git clone https://github.com/iaisep/onboarding.git
cd onboarding

# Desplegar con Docker Compose
docker-compose up -d
```

## ⚙️ Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura:

```env
# Database
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=tu_host
DB_PORT=5432

# AWS Credentials
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_S3_BUCKET=tu_bucket
AWS_DEFAULT_REGION=us-east-1
```

## 📚 API Endpoints

| Endpoint | Método | Descripción |
|----------|---------|-------------|
| `/health/` | GET | Estado de la API |
| `/ocr/` | POST | Procesamiento OCR (procesado) |
| `/ocr-raw/` | POST | OCR con respuesta completa de AWS |
| `/face/` | POST | Comparación facial |
| `/lists/` | POST | Lista de sancionados |

### Ejemplo de Uso - OCR Procesado

```bash
curl -X POST http://localhost:8000/ocr/ \
  -H "Content-Type: application/json" \
  -d '{
    "faceselfie": "imagen.jpg",
    "ocrident": "documento.jpg"
  }'
```

### Ejemplo de Uso - OCR Raw (Respuesta Completa AWS)

```bash
curl -X POST http://localhost:8000/ocr-raw/ \
  -H "Content-Type: application/json" \
  -d '{
    "faceselfie": "imagen.jpg",
    "ocrident": "documento.jpg"
  }'
```

**Respuesta OCR Raw:**
```json
{
  "success": true,
  "error": null,
  "error_code": null,
  "raw_response": {
    "TextDetections": [
      {
        "DetectedText": "REPUBLICA DE PANAMA",
        "Type": "LINE",
        "Id": 0,
        "Confidence": 99.8,
        "Geometry": {
          "BoundingBox": {
            "Width": 0.6234,
            "Height": 0.0341,
            "Left": 0.1883,
            "Top": 0.1234
          }
        }
      }
    ]
  },
  "metadata": {
    "photo": "cedula.jpg",
    "bucket": "onboarding-uisep",
    "text_detections_count": 25,
    "processing_type": "raw_response"
  }
}
```

## 📊 Sistema de Monitoreo

### Ver Logs en Tiempo Real
```bash
# Monitor general
monitor-logs.bat

# Análisis de logs
python log_analyzer.py --summary
python log_analyzer.py --level ERROR
```

### Archivos de Logs
- `logs/django.log`: Logs generales
- `logs/aws_errors.log`: Logs específicos de AWS

## 🐳 Despliegue

### Coolify
```bash
# Usar configuración incluida
./docker-deploy.sh
```

### Docker Compose
```bash
docker-compose -f docker-compose.yml up -d
```

### Manual
```bash
# Setup base de datos
./setup-db.bat

# Inicializar datos
./init-data.bat

# Ejecutar servidor
./start-local.bat
```

## 🔧 Herramientas de Desarrollo

- `setup_logging.py`: Configurar sistema de logs
- `debug_ocr_params.py`: Debugging de OCR
- `log_analyzer.py`: Análisis avanzado de logs
- `fix_pandas.py`: Corrección de dependencias

## 📁 Estructura del Proyecto

```
onboarding/
├── apibase/           # Configuración Django
├── apirest/           # API REST
│   ├── AWSocr.py     # Procesamiento OCR
│   ├── AWScompare.py # Comparación facial
│   └── views.py      # Endpoints API
├── logs/              # Sistema de logs
├── requirements.txt   # Dependencias
├── Dockerfile        # Docker configuration
└── docker-compose.yml
```

## 🛡️ Seguridad

- ✅ Credenciales AWS en variables de entorno
- ✅ Validación de parámetros de entrada
- ✅ Manejo seguro de errores
- ✅ Logs de auditoría completos

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📋 Estado del Proyecto

- [x] ✅ Migración a PostgreSQL
- [x] ✅ Integración AWS segura
- [x] ✅ Sistema de logging completo
- [x] ✅ Docker y Coolify ready
- [x] ✅ OCR de cédulas panameñas
- [x] ✅ Comparación facial
- [ ] 🔄 Tests automatizados
- [ ] 🔄 CI/CD pipeline

## 📞 Soporte

- 📧 Email: maikel@universidadisep.com
- 🌐 Web: universidadisep.com

---

**⭐ Si este proyecto te ayuda, ¡dale una estrella!**
