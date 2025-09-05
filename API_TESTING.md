# 🧪 Guía de Pruebas para API OCR

## ✅ **Correcciones Implementadas**

### Problema Original:
- **Error 404**: Archivo no existe en S3
- **AttributeError**: `'consult45' object has no attribute 'sancionados'`

### Solución Implementada:
1. **Manejo de errores en S3**: Si el archivo no existe, se crea un DataFrame de error
2. **Manejo de errores en Rekognition**: Si falla OCR, se crea un DataFrame de error  
3. **Manejo de errores en View**: Try-catch para prevenir AttributeError

## 🚀 **Endpoints Disponibles**

### 1. Health Check
```bash
GET http://127.0.0.1:8000/health/
```
**Respuesta esperada:**
```json
{
    "status": "OK",
    "message": "API funcionando correctamente",
    "timestamp": "2025-08-11 23:30:00"
}
```

### 2. OCR Processing
```bash
POST http://127.0.0.1:8000/ocr/
Content-Type: application/json

{
    "faceselfie": "nombre_archivo_selfie.jpg",
    "ocrident": "nombre_bucket_s3"
}
```

### 3. Restricted List Check
```bash
POST http://127.0.0.1:8000/lists/
Content-Type: application/json

{
    "string_income": "Nombre a verificar"
}
```

### 4. Face Comparison
```bash
POST http://127.0.0.1:8000/face/
Content-Type: application/json

{
    "faceselfie": "imagen1.jpg",
    "ocrident": "imagen2.jpg"
}
```

## 📋 **Casos de Prueba**

### Caso 1: Archivo Existe en S3 ✅
- **Input**: Archivo válido en S3
- **Esperado**: Procesamiento OCR exitoso
- **Respuesta**: Datos extraídos del documento

### Caso 2: Archivo No Existe en S3 ❌ → ✅
- **Input**: Archivo inexistente en S3  
- **Error Anterior**: `AttributeError: 'consult45' object has no attribute 'sancionados'`
- **Ahora**: Retorna error controlado
```json
{
    "cod": "400_Bad_Quality_image",
    "error": "No se pudo acceder al archivo en S3: An error occurred (404) when calling the HeadObject operation: Not Found"
}
```

### Caso 3: Error de Permisos AWS ❌ → ✅
- **Input**: Credenciales sin permisos
- **Error Anterior**: 403 Forbidden crash
- **Ahora**: Error controlado con mensaje descriptivo

### Caso 4: Error en OCR Processing ❌ → ✅
- **Input**: Imagen corrupta o no procesable
- **Error Anterior**: Crash de Rekognition
- **Ahora**: Error controlado

## 🧪 **Pruebas con curl**

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/health/
```

### 2. OCR Procesado (AWS Rekognition)
```bash
curl -X POST http://127.0.0.1:8000/ocr/ \
  -H "Content-Type: application/json" \
  -d '{
    "faceselfie": "imagen.jpg",
    "ocrident": "documento.jpg"
  }'
```

### 3. OCR Raw (Respuesta completa de AWS)
```bash
curl -X POST http://127.0.0.1:8000/ocr-raw/ \
  -H "Content-Type: application/json" \
  -d '{
    "faceselfie": "imagen.jpg",
    "ocrident": "documento.jpg"
  }'
```

### 4. Subida de Archivos a S3
```bash
curl -X POST http://127.0.0.1:8000/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf"
```

### 5. Comparación Facial
```bash
curl -X POST http://127.0.0.1:8000/face/ \
  -H "Content-Type: application/json" \
  -d '{
    "faceselfie": "foto1.jpg",
    "ocrident": "foto2.jpg"
  }'
```

### 6. Lista restrictiva (funcionalidad básica)
```bash
curl -X POST http://127.0.0.1:8000/lists/ \
  -H "Content-Type: application/json" \
  -d '{
    "string_income": "Juan Perez"
  }'
```

### 7. Análisis de Documento de Identidad (Textract ID)
```bash
curl -X POST http://127.0.0.1:8000/textract-id/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "cedula.jpg",
    "analysis_type": "id_document",
    "bucket_name": "onboarding-uisep"
  }'
```

### 8. Análisis General de Documento (Textract General)
```bash
curl -X POST http://127.0.0.1:8000/textract-general/ \
  -H "Content-Type: application/json" \
  -d '{
    "document_name": "contrato.pdf",
    "bucket_name": "onboarding-uisep"
  }'
```

## 🔧 **Debugging**

### Ver logs del servidor:
- Los errores se imprimen en consola
- Buscar mensajes como "Error accessing S3 file" o "Error with Rekognition"

### Variables de entorno requeridas:
```env
AWS_ACCESS_KEY_ID=tu_key
AWS_SECRET_ACCESS_KEY=tu_secret
AWS_REKOGNITION_ACCESS_KEY_ID=tu_rekognition_key
AWS_REKOGNITION_SECRET_ACCESS_KEY=tu_rekognition_secret
AWS_DEFAULT_REGION=us-east-1
```

### Buckets S3 configurados:
- `bucket-getapp-t` (imagen processing)
- `onboarding-repo` (face recognition)

## ✅ **Estado Actual**
- ✅ **Base de datos**: Migrada y con datos iniciales
- ✅ **Manejo de errores**: Implementado para S3 y Rekognition
- ✅ **API**: Funcionando sin crashes
- ✅ **Health check**: Disponible
- ✅ **Pandas**: Actualizado (no más warnings de .append)

## 🎯 **Próximos Pasos**
1. **Probar con archivos reales** en S3
2. **Verificar permisos** AWS si es necesario
3. **Optimizar respuestas** de error
4. **Agregar logging** más detallado

¡La API ahora maneja errores graciosamente y no debería crashear! 🚀
