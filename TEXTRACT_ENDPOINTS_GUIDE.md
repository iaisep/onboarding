# 📄 AWS Textract Endpoints - Guía Completa

## 🎯 Nuevos Endpoints de Textract

Se han agregado dos nuevos endpoints para extraer texto de documentos usando Amazon Textract:

### 🆔 `/textract-id/` - Análisis de Documentos de Identidad
### 📄 `/textract-general/` - Análisis General de Documentos

---

## 🆔 Endpoint: `/textract-id/`

### ✨ Características Principales
- **🔬 Análisis especializado** para documentos de identidad (cédulas, pasaportes, licencias)
- **🎯 Extracción estructurada** de campos específicos (nombre, fecha de nacimiento, número de documento)
- **🤖 API optimizada** usando `analyze_id` de AWS Textract
- **📊 Formato consistente** compatible con otros endpoints
- **🔍 Valores normalizados** para fechas y otros campos estructurados

### 📋 Tipos de Documento Soportados
- **Cédulas de identidad**
- **Pasaportes**
- **Licencias de conducir**
- **Tarjetas de identificación oficiales**
- **Documentos de inmigración**

### 🚀 Ejemplo de Uso

```bash
curl -X POST http://localhost:8000/textract-id/ \
  -H "Content-Type: application/json" \
  -d "{
    \"document_name\": \"20250812_143022_a1b2c3d4_cedula.jpg\",
    \"analysis_type\": \"id_document\"
  }"
```

### 📊 Respuesta Exitosa

```json
{
  "success": true,
  "document_name": "20250812_143022_a1b2c3d4_cedula.jpg",
  "document_metadata": {
    "Pages": 1
  },
  "extracted_fields": [
    {
      "field_type": "FIRST_NAME",
      "field_confidence": 99.8,
      "field_value": "JUAN CARLOS",
      "value_confidence": 99.2,
      "normalized_value": {}
    },
    {
      "field_type": "LAST_NAME", 
      "field_confidence": 99.5,
      "field_value": "RODRIGUEZ MARTINEZ",
      "value_confidence": 98.7,
      "normalized_value": {}
    },
    {
      "field_type": "DOCUMENT_NUMBER",
      "field_confidence": 99.9,
      "field_value": "1234567890",
      "value_confidence": 99.1,
      "normalized_value": {}
    },
    {
      "field_type": "DATE_OF_BIRTH",
      "field_confidence": 98.2,
      "field_value": "15/03/1985",
      "value_confidence": 97.8,
      "normalized_value": {
        "Value": "1985-03-15",
        "ValueType": "Date"
      }
    }
  ],
  "identity_documents": [
    {
      "document_index": 1,
      "identity_document_fields": [...],
      "blocks": [...]
    }
  ],
  "dataframe_results": [
    {
      "0": {
        "document_name": "20250812_143022_a1b2c3d4_cedula.jpg",
        "field_type": "FIRST_NAME",
        "field_value": "JUAN CARLOS",
        "field_confidence": 99.8,
        "value_confidence": 99.2,
        "normalized_value": ""
      }
    }
  ],
  "raw_response": {...}
}
```

---

## 📄 Endpoint: `/textract-general/`

### ✨ Características Principales  
- **📝 Extracción completa** de todo el texto del documento
- **🔍 Análisis detallado** de bloques, líneas y palabras
- **📊 Estadísticas completas** del contenido extraído
- **🎯 Compatible** con cualquier tipo de documento
- **⚡ Optimizado** para PDFs, formularios, contratos, facturas

### 📋 Tipos de Documento Soportados
- **PDFs multipágina**
- **Formularios**
- **Contratos y documentos legales** 
- **Facturas y recibos**
- **Certificados**
- **Cualquier documento con texto**

### 🚀 Ejemplo de Uso

```bash
curl -X POST http://localhost:8000/textract-general/ \
  -H "Content-Type: application/json" \
  -d "{
    \"document_name\": \"20250812_143022_b1c2d3e4_contrato_page_1.jpg\",
    \"analysis_type\": \"general_document\"
  }"
```

### 📊 Respuesta Exitosa

```json
{
  "success": true,
  "document_name": "20250812_143022_b1c2d3e4_contrato_page_1.jpg",
  "document_metadata": {
    "Pages": 1
  },
  "text_blocks": [
    {
      "block_type": "LINE",
      "text": "CONTRATO DE SERVICIOS",
      "confidence": 99.1,
      "geometry": {...}
    },
    {
      "block_type": "LINE", 
      "text": "Entre la empresa ABC S.A.S. y el cliente XYZ",
      "confidence": 98.7,
      "geometry": {...}
    }
  ],
  "lines": [
    "CONTRATO DE SERVICIOS",
    "Entre la empresa ABC S.A.S. y el cliente XYZ",
    "Por medio del presente documento..."
  ],
  "words": [
    {"text": "CONTRATO", "confidence": 99.2},
    {"text": "DE", "confidence": 98.9},
    {"text": "SERVICIOS", "confidence": 99.1}
  ],
  "full_text": "CONTRATO DE SERVICIOS\nEntre la empresa ABC S.A.S. y el cliente XYZ\nPor medio del presente documento...",
  "total_blocks": 45,
  "total_lines": 23,
  "total_words": 156,
  "analysis_summary": {
    "total_text_blocks": 45,
    "total_lines": 23,
    "total_words": 156,
    "full_text_length": 1245,
    "document_type": "general_document"
  },
  "dataframe_results": [...],
  "raw_response": {...}
}
```

---

## 📋 Parámetros de Entrada

### 🔧 Parámetros Requeridos
- **`document_name`** (string): Nombre del archivo en el bucket S3
  - Ejemplo: `"20250812_143022_a1b2c3d4_cedula.jpg"`
  - Debe existir en el bucket S3 configurado

### ⚙️ Parámetros Opcionales  
- **`analysis_type`** (string): Tipo de análisis
  - `"id_document"`: Para documentos de identidad (default)
  - `"general_document"`: Para análisis general de texto
- **`bucket_name`** (string): Bucket S3 específico
  - Si no se especifica, usa el bucket configurado en variables de entorno

---

## 🔧 Configuración Requerida

### 📦 Variables de Entorno
```env
# AWS Textract requiere las mismas credenciales que otros servicios AWS
AWS_ACCESS_KEY_ID=your_textract_access_key
AWS_SECRET_ACCESS_KEY=your_textract_secret_key  
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=your_bucket_name
```

### 🔑 Permisos de IAM Necesarios
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeID", 
        "textract:DetectDocumentText",
        "s3:GetObject"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🔗 Flujo de Trabajo Recomendado

### 1. 📤 Subir Documento
```bash
curl -X POST http://localhost:8000/upload/ \
  -F "file=@cedula.jpg"
```
**Respuesta:** `s3_filename: "20250812_143022_a1b2c3d4_cedula.jpg"`

### 2. 🔍 Analizar con Textract ID
```bash
curl -X POST http://localhost:8000/textract-id/ \
  -H "Content-Type: application/json" \
  -d '{"document_name": "20250812_143022_a1b2c3d4_cedula.jpg"}'
```

### 3. 📊 Procesar Resultados
Los resultados incluyen:
- **Campos estructurados** para documentos de identidad
- **Texto completo** para análisis general  
- **Datos en formato DataFrame** para compatibilidad
- **Respuesta raw de AWS** para análisis avanzado

---

## 🆚 Comparación de Endpoints

| Característica | `/textract-id/` | `/textract-general/` | `/ocr/` | `/ocr-raw/` |
|----------------|-----------------|---------------------|---------|-------------|
| **Servicio AWS** | Textract analyze_id | Textract detect_document_text | Rekognition | Rekognition |
| **Especialización** | Documentos de identidad | Cualquier documento | Imágenes generales | Imágenes generales |
| **Campos estructurados** | ✅ Sí | ❌ No | ❌ No | ❌ No |
| **Texto completo** | ✅ Sí | ✅ Sí | ✅ Sí | ✅ Sí |
| **Confianza por campo** | ✅ Sí | ✅ Sí | ✅ Sí | ✅ Sí |
| **Valores normalizados** | ✅ Sí (fechas) | ❌ No | ❌ No | ❌ No |
| **Documentos multipágina** | ✅ Sí | ✅ Sí | ❌ No | ❌ No |

---

## 🛠️ Casos de Uso Específicos

### 🆔 Para Documentos de Identidad (`/textract-id/`)
- **Onboarding de usuarios** con extracción automática de datos
- **Verificación de identidad** para procesos KYC
- **Digitalización masiva** de documentos oficiales
- **Integración con sistemas** de gestión de identidad

### 📄 Para Documentos Generales (`/textract-general/`)
- **Digitalización de contratos** y documentos legales
- **Extracción de información** de facturas y recibos
- **Análisis de formularios** no estructurados
- **Conversión PDF a texto** para procesamiento posterior

---

## 🔍 Campos Típicos Extraídos

### 🆔 Documentos de Identidad
- `FIRST_NAME`: Primer nombre
- `LAST_NAME`: Apellidos  
- `DOCUMENT_NUMBER`: Número de documento
- `DATE_OF_BIRTH`: Fecha de nacimiento
- `DATE_OF_ISSUE`: Fecha de expedición
- `DATE_OF_EXPIRY`: Fecha de vencimiento
- `PLACE_OF_BIRTH`: Lugar de nacimiento
- `ADDRESS`: Dirección
- `ID_TYPE`: Tipo de documento

### 📄 Documentos Generales
- `LINE`: Líneas de texto completas
- `WORD`: Palabras individuales con confianza
- `PAGE`: Información de página
- Texto completo estructurado por bloques

---

## ⚠️ Limitaciones y Consideraciones

### 📏 Límites de AWS Textract
- **Tamaño máximo**: 10MB por documento
- **Páginas**: Hasta 3000 páginas por documento
- **Formatos**: JPG, PNG, PDF, TIFF
- **Resolución**: Mínimo 150 DPI recomendado

### 💰 Costos
- **analyze_id**: ~$0.05 por página
- **detect_document_text**: ~$0.0015 por página
- Consultar precios actuales en AWS

### 🔒 Seguridad
- Documentos procesados temporalmente por AWS
- No se almacenan permanentemente en AWS Textract
- Cumple estándares de seguridad AWS

---

## 🐛 Debugging y Logs

### 📋 Logs Generados
```python
INFO: Textract ID Analysis endpoint accessed
INFO: Processing Textract ID analysis - Document: cedula.jpg
INFO: Textract analysis completed - Success: True
INFO: Added DataFrame results: 4 records
```

### 🔍 Comandos de Debug
```bash
# Ver logs de Textract
python log_analyzer.py --grep "Textract"

# Ver errores específicos
python log_analyzer.py --grep "Textract.*error"
```

---

## 🚀 Ejemplos Avanzados

### 📱 Análisis de Múltiples Documentos
```python
# Procesar varios documentos de identidad
documents = [
    "cedula_front.jpg", 
    "cedula_back.jpg",
    "passport.jpg"
]

for doc in documents:
    response = requests.post(
        "http://localhost:8000/textract-id/",
        json={"document_name": doc}
    )
    results = response.json()
    process_identity_data(results)
```

### 📊 Integración con Pandas
```python
import pandas as pd

# Convertir resultados a DataFrame
response = requests.post(
    "http://localhost:8000/textract-general/",
    json={"document_name": "contract.pdf"}
)

results = response.json()
df = pd.DataFrame(results['dataframe_results'])
print(df[['text', 'confidence']].head())
```

---

## 🎯 Próximas Funcionalidades

- **Análisis de formularios** estructurados (`analyze_document`)
- **Extracción de tablas** (`analyze_document` con TABLES)
- **OCR multiidioma** con detección automática
- **Validación de documentos** con reglas de negocio
- **API asíncrona** para documentos grandes

¡Los nuevos endpoints de Textract están listos para extraer texto de forma inteligente de tus documentos! 🚀
