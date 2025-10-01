# 📱 Servicio de Lectura de Códigos QR

## 🎯 **Descripción**

Servicio completo para leer y decodificar códigos QR de imágenes almacenadas en S3 o subidas directamente. Soporta múltiples códigos QR en una sola imagen y procesamiento en batch.

---

## 🚀 **Endpoints Disponibles**

### 1. **Lectura Individual de QR** - `/qr-read/`

Lee códigos QR de una imagen en S3.

#### **Request:**
```bash
POST http://localhost:8000/qr-read/
Content-Type: application/json

{
  "filename": "documento_qr.jpg",
  "bucket_name": "onboarding-uisep"  // Opcional
}
```

#### **Response Exitosa:**
```json
{
  "success": true,
  "error": null,
  "error_code": null,
  "qr_codes": [
    {
      "index": 1,
      "type": "QRCODE",
      "data": "https://example.com/documento/12345",
      "raw_data": "68747470733a2f2f6578616d706c652e636f6d...",
      "quality": 50,
      "orientation": "UP",
      "rect": {
        "left": 120,
        "top": 85,
        "width": 200,
        "height": 200
      },
      "polygon": [
        {"x": 120, "y": 85},
        {"x": 320, "y": 85},
        {"x": 320, "y": 285},
        {"x": 120, "y": 285}
      ]
    }
  ],
  "metadata": {
    "filename": "documento_qr.jpg",
    "image_size": {
      "width": 1024,
      "height": 768
    },
    "image_mode": "RGB",
    "total_qr_codes": 1,
    "processing_type": "qr_code_detection"
  }
}
```

#### **Response Sin QR Detectado:**
```json
{
  "success": false,
  "error": "No QR codes detected in image",
  "error_code": "404_No_QR_Found",
  "qr_codes": [],
  "metadata": {
    "filename": "documento_qr.jpg",
    "image_size": {
      "width": 1024,
      "height": 768
    },
    "image_mode": "RGB",
    "total_qr_codes": 0,
    "processing_type": "qr_code_detection"
  }
}
```

---

### 2. **Lectura Batch de QR** - `/qr-batch/`

Lee códigos QR de múltiples imágenes en batch.

#### **Request:**
```bash
POST http://localhost:8000/qr-batch/
Content-Type: application/json

{
  "file_list": [
    "documento_qr_1.jpg",
    "documento_qr_2.jpg",
    "documento_qr_3.jpg"
  ],
  "bucket_name": "onboarding-uisep"  // Opcional
}
```

#### **Response:**
```json
{
  "success": true,
  "files_processed": 3,
  "files_successful": 3,
  "files_failed": 0,
  "total_qr_codes": 5,
  "results": [
    {
      "success": true,
      "qr_codes": [...],
      "metadata": {...}
    },
    {
      "success": true,
      "qr_codes": [...],
      "metadata": {...}
    },
    {
      "success": true,
      "qr_codes": [...],
      "metadata": {...}
    }
  ],
  "errors": []
}
```

---

## 📊 **Información de los QR Detectados**

### **Campos del QR Code:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `index` | int | Número de orden del QR en la imagen |
| `type` | string | Tipo de código (QRCODE, DATAMATRIX, etc.) |
| `data` | string | Datos decodificados del QR (texto legible) |
| `raw_data` | string | Datos en formato hexadecimal |
| `quality` | int | Calidad de la detección (0-100) |
| `orientation` | string | Orientación del QR (UP, DOWN, LEFT, RIGHT) |
| `rect` | object | Rectángulo delimitador del QR |
| `polygon` | array | Coordenadas de los 4 vértices del QR |

---

## 🔧 **Tipos de Códigos Soportados**

- ✅ **QR Code** - Códigos QR estándar
- ✅ **Data Matrix** - Códigos 2D de alta densidad
- ✅ **Aztec Code** - Códigos 2D compactos
- ✅ **PDF417** - Códigos de barras 2D
- ✅ **Micro QR** - QR codes miniatura
- ✅ **EAN/UPC** - Códigos de barras 1D
- ✅ **Code 128** - Códigos de barras alfanuméricos

---

## 🎯 **Casos de Uso**

### **1. Validación de Documentos**
```json
{
  "filename": "cedula_con_qr.jpg"
}
```
→ Lee el QR de una cédula para validar autenticidad

### **2. Procesamiento de Facturas**
```json
{
  "file_list": ["factura_1.jpg", "factura_2.jpg", "factura_3.jpg"]
}
```
→ Extrae información de múltiples facturas con QR

### **3. Control de Acceso**
```json
{
  "filename": "ticket_evento.jpg"
}
```
→ Lee QR de tickets o pases de acceso

### **4. Trazabilidad de Productos**
```json
{
  "file_list": ["producto_1.jpg", "producto_2.jpg"]
}
```
→ Rastrea productos mediante QR codes

---

## 📝 **Ejemplos de Uso**

### **Ejemplo 1: Leer QR de Cédula**

```bash
curl -X POST http://localhost:8000/qr-read/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "cedula_123456.jpg"
  }'
```

### **Ejemplo 2: Leer Múltiples Documentos**

```bash
curl -X POST http://localhost:8000/qr-batch/ \
  -H "Content-Type: application/json" \
  -d '{
    "file_list": [
      "doc_page_1.jpg",
      "doc_page_2.jpg",
      "doc_page_3.jpg"
    ]
  }'
```

### **Ejemplo 3: En n8n - Workflow**

```
1. Upload Image to S3 → FileUploadView
2. Get filename from response
3. Read QR Code → QRCodeReaderView
4. Process QR data → Your business logic
```

---

## 🛠️ **Dependencias Necesarias**

```bash
# Instalar librerías necesarias
pip install pyzbar==0.1.9
pip install opencv-python-headless==4.10.0.84
```

### **Para Windows:**
```bash
# Si pyzbar no funciona, instalar zbar manualmente
# Descargar desde: http://zbar.sourceforge.net/
```

### **Para Linux/Docker:**
```dockerfile
# Agregar al Dockerfile
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev
```

---

## ⚙️ **Configuración**

### **Variables de Entorno:**
```env
AWS_ACCESS_KEY_ID=tu_key
AWS_SECRET_ACCESS_KEY=tu_secret
AWS_S3_BUCKET=onboarding-uisep
AWS_DEFAULT_REGION=us-east-1
```

---

## 🎨 **Formatos de Imagen Soportados**

- ✅ JPEG / JPG
- ✅ PNG
- ✅ BMP
- ✅ TIFF
- ✅ GIF

---

## 📈 **Performance**

| Métrica | Valor Típico |
|---------|--------------|
| Tiempo de lectura | 0.5-2 seg/imagen |
| Tamaño máximo imagen | 10 MB |
| QR codes por imagen | Ilimitados |
| Resolución mínima | 200x200 px |

---

## ✅ **Validaciones**

- ✅ Extensión de archivo válida
- ✅ Archivo existe en S3
- ✅ Imagen legible
- ✅ Formato de imagen soportado
- ✅ Tamaño de imagen adecuado

---

## 🐛 **Errores Comunes**

### **404_No_QR_Found**
```json
{
  "error": "No QR codes detected in image",
  "error_code": "404_No_QR_Found"
}
```
**Solución:** Verificar que la imagen tenga un QR visible y de buena calidad

### **404_File_Not_Found**
```json
{
  "error": "File not found in S3: documento.jpg",
  "error_code": "404_File_Not_Found"
}
```
**Solución:** Verificar que el archivo existe en S3

### **500_Image_Processing_Error**
```json
{
  "error": "Error processing image for QR detection",
  "error_code": "500_Image_Processing_Error"
}
```
**Solución:** Verificar que la imagen no esté corrupta

---

## 💡 **Tips para Mejores Resultados**

1. **Calidad de Imagen:** Usar imágenes de al menos 300 DPI
2. **Contraste:** QR debe tener buen contraste con el fondo
3. **Iluminación:** Evitar sombras sobre el QR
4. **Nitidez:** Imagen debe estar enfocada
5. **Tamaño:** QR debe ocupar al menos 100x100 px en la imagen

---

## 🔐 **Seguridad**

- ✅ Autenticación AWS configurada
- ✅ Validación de extensiones de archivo
- ✅ Límite de archivos en batch (20 máximo)
- ✅ Validación de datos de entrada
- ✅ Logging completo de operaciones

---

## 📦 **Integración con Otros Endpoints**

### **Flujo Completo de Procesamiento:**

```
1. /upload/          → Subir documento con QR
2. /qr-read/         → Leer QR del documento
3. /textract-id/     → Extraer texto del documento
4. /lists/           → Validar datos contra listas
```

---

## 🎯 **Estado del Servicio**

- ✅ Lectura individual de QR
- ✅ Lectura batch de múltiples imágenes
- ✅ Soporte para múltiples tipos de códigos
- ✅ Detección de posición y orientación
- ✅ Logging completo
- ✅ Manejo de errores robusto

**Estado Actual:** 🟢 **PRODUCCIÓN - COMPLETAMENTE FUNCIONAL**
