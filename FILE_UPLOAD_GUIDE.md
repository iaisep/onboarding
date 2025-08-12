# 📁 File Upload Endpoint - Guía Completa

## 🎯 Características del Endpoint `/upload/`

### ✨ Funcionalidades Principales
- **🔄 Conversión Automática**: Convierte PDF y DOCX a imágenes JPG de alta calidad
- **🖼️ Optimización de Imágenes**:### 📁 Dependencias

#### Windows Development Environment
```bash
pip install PyMuPDF==1.24.10    # PDF conversion
pip install docx2pdf==0.1.8     # DOCX conversion  
pip install pywin32==306        # Windows COM for DOCX
```

#### Linux/Docker Production Environment
```bash
pip install PyMuPDF==1.24.10    # PDF conversion only
# Note: DOCX conversion not supported on Linux
```

### ⚙️ Variables de Entorno
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_S3_BUCKET=tu_bucket_name
AWS_DEFAULT_REGION=us-east-1
```

### 🖥️ Plataformas Soportadas

#### ✅ Windows (Funcionalidad Completa)
- **PDF Conversion**: ✅ PyMuPDF
- **DOCX Conversion**: ✅ docx2pdf + pywin32 COM
- **Ambiente**: Desarrollo y producción local

#### ⚠️ Linux/Docker (Funcionalidad Limitada)  
- **PDF Conversion**: ✅ PyMuPDF
- **DOCX Conversion**: ❌ **No soportada**
  - Motivo: Requiere Microsoft Office COM (Windows-only)
  - Error devuelto: "DOCX conversion is not supported on Linux platforms"
  - Solución: Convertir DOCX a PDF antes de subir

#### 🚀 Recomendaciones de Despliegue
- **Desarrollo**: Windows con funcionalidad completa
- **Producción**: Linux/Docker con conversión PDF únicamente
- **Flujo de trabajo**: Convertir DOCX → PDF → Subir en ambientes Linuxmiza imágenes automáticamente  
- **☁️ Subida a S3**: Almacena archivos en AWS S3 con nombres únicos
- **📊 Metadata Completa**: Proporciona información detallada sobre cada archivo
- **🛡️ Validaciones**: Verifica tipos de archivo y tamaños máximos
- **📝 Logging Completo**: Registra todo el proceso para debugging

---

## 📋 Tipos de Archivo Soportados

### 🖼️ Imágenes (Subida Directa)
- **JPG/JPEG**: ✅ Optimización automática
- **PNG**: ✅ Conversión a JPG para mejor rendimiento
- **BMP**: ✅ Conversión a JPG
- **TIFF**: ✅ Conversión a JPG

### 📄 Documentos (Conversión a Imágenes)
- **PDF**: ✅ Cada página → imagen JPG individual
- **DOCX**: ✅ Conversión vía PDF intermedio → imágenes JPG
- **DOC**: ✅ Conversión vía PDF intermedio → imágenes JPG

### 📏 Límites y Restricciones
- **Tamaño máximo**: 50MB por archivo
- **Calidad**: Conversión sin pérdida significativa
- **Resolución**: Máximo 2048px en el lado más largo
- **Formato de salida**: JPG optimizado (calidad 85%)

---

## 🚀 Ejemplos de Uso

### 1. Subir Imagen Directa

```bash
curl -X POST http://localhost:8000/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@cedula.jpg"
```

**Respuesta:**
```json
{
  "success": true,
  "uploaded_files": [
    {
      "original_filename": "cedula.jpg",
      "s3_filename": "20250812_143022_a1b2c3d4_cedula.jpg",
      "file_type": "image",
      "size": 187392,
      "url": "https://onboarding-uisep.s3.us-east-1.amazonaws.com/20250812_143022_a1b2c3d4_cedula.jpg"
    }
  ]
}
```

### 2. Subir PDF Multipágina

```bash
curl -X POST http://localhost:8000/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "success": true,
  "uploaded_files": [
    {
      "original_filename": "documento.pdf",
      "s3_filename": "20250812_143022_a1b2c3d4_documento_page_1.jpg",
      "file_type": "converted_image",
      "page_number": 1,
      "size": 245760,
      "url": "https://onboarding-uisep.s3.us-east-1.amazonaws.com/20250812_143022_a1b2c3d4_documento_page_1.jpg"
    },
    {
      "original_filename": "documento.pdf",
      "s3_filename": "20250812_143022_b2c3d4e5_documento_page_2.jpg", 
      "file_type": "converted_image",
      "page_number": 2,
      "size": 198432,
      "url": "https://onboarding-uisep.s3.us-east-1.amazonaws.com/20250812_143022_b2c3d4e5_documento_page_2.jpg"
    }
  ],
  "metadata": {
    "total_files_uploaded": 2,
    "original_file_type": "document"
  }
}
```

### 3. Subir DOCX

```bash
curl -X POST http://localhost:8000/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@formulario.docx"
```

---

## 📊 Estructura de Respuesta

### ✅ Respuesta Exitosa
```json
{
  "success": true,
  "error": null,
  "error_code": null,
  "uploaded_files": [
    {
      "original_filename": "archivo.ext",
      "s3_filename": "timestamp_uuid_archivo_page_N.jpg",
      "file_type": "image|converted_image",
      "page_number": 1,
      "size": 123456,
      "url": "https://bucket.s3.region.amazonaws.com/filename.jpg"
    }
  ],
  "metadata": {
    "original_filename": "archivo.ext",
    "original_file_type": "image|document",
    "original_extension": ".ext",
    "original_mime_type": "mime/type",
    "total_files_uploaded": 1,
    "bucket": "onboarding-uisep",
    "region": "us-east-1",
    "upload_timestamp": "2025-08-12T14:30:22"
  }
}
```

### ❌ Respuesta de Error
```json
{
  "success": false,
  "error": "Descripción del error",
  "error_code": "400_Error_Code",
  "uploaded_files": [],
  "metadata": {
    "original_filename": "archivo.ext",
    "error_details": {
      "exception_type": "ValueError",
      "exception_message": "Detalle específico"
    }
  }
}
```

---

## 🔧 Códigos de Error Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| `400_Upload_Validation_Error` | Archivo no válido | Verificar tipo y tamaño |
| `500_Upload_Error` | Error en S3/conversión | Revisar credenciales AWS |
| `500_Upload_Unexpected_Error` | Error inesperado | Contactar soporte |

### Errores de Validación
```json
{
  "success": false,
  "error": "Invalid file upload data",
  "error_code": "400_Upload_Validation_Error",
  "validation_errors": {
    "file": ["File too large. Maximum size is 50MB, got 75.23MB"]
  }
}
```

---

## 🔗 Integración con OCR

### Flujo Recomendado
1. **Subir archivo** usando `/upload/`
2. **Obtener URLs** de las imágenes generadas  
3. **Procesar con OCR** usando `/ocr/` o `/ocr-raw/`

### Ejemplo Completo
```bash
# 1. Subir PDF
RESPONSE=$(curl -s -X POST http://localhost:8000/upload/ \
  -F "file=@documento.pdf")

# 2. Extraer nombre de archivo
FILENAME=$(echo $RESPONSE | jq -r '.uploaded_files[0].s3_filename')

# 3. Procesar con OCR
curl -X POST http://localhost:8000/ocr/ \
  -H "Content-Type: application/json" \
  -d "{\"faceselfie\": \"$FILENAME\", \"ocrident\": \"onboarding-uisep\"}"
```

---

## 📁 Gestión de Archivos

### 🏷️ Nomenclatura de Archivos
- **Formato**: `YYYYMMDD_HHMMSS_UUID8_original_name[_page_N].jpg`
- **Ejemplo**: `20250812_143022_a1b2c3d4_documento_page_1.jpg`
- **Único**: Evita colisiones usando timestamp + UUID

### 📂 Organización en S3
```
bucket/
├── 20250812_143022_a1b2c3d4_cedula.jpg
├── 20250812_143022_b2c3d4e5_documento_page_1.jpg  
├── 20250812_143022_c3d4e5f6_documento_page_2.jpg
└── ...
```

### 🔄 Conversión de Calidad
- **PDF**: Matrix 2x zoom para alta resolución
- **DOCX**: Conversión vía LibreOffice/Word COM
- **Optimización**: Calidad JPEG 85%, compresión inteligente
- **Redimensionado**: Máximo 2048px, mantiene aspect ratio

---

## ⚡ Consideraciones de Rendimiento

### 📊 Tiempos Estimados
- **Imagen (2MB)**: ~1-2 segundos
- **PDF (10 páginas)**: ~5-8 segundos  
- **DOCX (5 páginas)**: ~8-12 segundos

### 💾 Uso de Recursos
- **Memoria**: ~50MB por archivo procesado
- **Disco temporal**: Archivos temporales auto-limpiados
- **CPU**: Intensivo durante conversión PDF/DOCX

### 🚀 Optimizaciones
- **Conversión paralela**: Una página a la vez
- **Limpieza automática**: Archivos temporales eliminados
- **Compresión inteligente**: Balance calidad/tamaño

---

## 🛠️ Configuración Requerida

### 📦 Dependencias
```bash
pip install PyMuPDF==1.24.10    # PDF conversion
pip install docx2pdf==0.1.8     # DOCX conversion  
pip install pywin32==306        # Windows COM for DOCX
```

### ⚙️ Variables de Entorno
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_S3_BUCKET=tu_bucket_name
AWS_DEFAULT_REGION=us-east-1
```

### 🖥️ Requisitos del Sistema
- **Windows**: Requerido para conversión DOCX (COM objects)
- **Linux**: PDF funciona, DOCX requiere LibreOffice
- **macOS**: PDF funciona, DOCX requiere configuración adicional

---

## 🔍 Debugging y Logs

### 📋 Logs Generados
```python
# Logs en logs/django.log
INFO: File upload endpoint accessed
INFO: Processing file upload - Name: documento.pdf, Size: 2048576 bytes
INFO: Starting PDF to image conversion for: documento.pdf
INFO: PDF has 3 pages
INFO: Converted page 1 to 245760 bytes
INFO: Upload successful - 3 files uploaded to S3
```

### 🐛 Debug Commands
```bash
# Ver logs de subida
python log_analyzer.py --grep "File upload"

# Ver errores de conversión  
python log_analyzer.py --grep "conversion error"

# Monitorear en tiempo real
monitor-logs.bat
```

---

## 🚀 Casos de Uso

### 1. 🆔 Procesamiento de Cédulas
- Subir foto/escaneo de cédula
- Conversión automática a JPG optimizado
- OCR para extraer datos personales

### 2. 📄 Documentos Legales
- Subir contratos PDF multipágina
- Cada página como imagen independiente
- OCR individual por página

### 3. 📋 Formularios DOCX
- Formularios completados en Word
- Conversión a imágenes para archivo
- OCR para validar campos completados

### 4. 📊 Reportes y Facturas
- PDFs de facturas/reportes
- Extracción de datos específicos
- Integración con sistemas contables

---

## 🔒 Seguridad y Mejores Prácticas

### 🛡️ Validaciones de Seguridad
- **Tipos MIME**: Validación estricta de tipos
- **Magic bytes**: Verificación de contenido real
- **Tamaño máximo**: Límite de 50MB
- **Sanitización**: Nombres de archivo seguros

### 🔐 Recomendaciones
- **Autenticación**: Descomentar `permission_classes` para producción
- **Rate limiting**: Implementar límites de requests
- **Virus scanning**: Considerar integración con antivirus
- **Encryption**: Archivos sensibles encriptados en S3

---

## 📈 Monitoreo y Métricas

### 📊 KPIs Importantes
- **Tiempo de conversión**: Promedio por tipo de archivo
- **Tasa de éxito**: % de subidas exitosas
- **Uso de storage**: Espacio ocupado en S3  
- **Calidad de conversión**: Feedback de usuarios

### 🔔 Alertas Sugeridas
- **Errores frecuentes**: >5% de fallos en 1 hora
- **Tiempo excesivo**: Conversiones >30 segundos
- **Espacio S3**: >80% de cuota utilizada
- **Dependencias**: Fallos de PyMuPDF o docx2pdf
