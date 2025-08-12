# � LOG Y MONITOREO DE ERRORES AWS

## Sistema de Logging Implementado

Se ha implementado un sistema completo de logging para monitorear todos los errores de AWS y operaciones del sistema.

### 📁 Estructura de Logs

```
logs/
├── django.log       # Logs generales de Django
├── aws_errors.log   # Logs específicos de AWS (OCR, Face, S3)
└── .gitkeep        # Mantiene el directorio en git
```

### 🔍 Loggers Configurados

1. **django**: Logs generales del framework
2. **apirest.aws**: Logs de endpoints y API
3. **apirest.ocr**: Logs específicos de OCR (Rekognition)
4. **apirest.face**: Logs específicos de comparación facial

### �🛠 Herramientas de Monitoreo

#### 1. Monitor en Tiempo Real
```bash
monitor-logs.bat
```
- Opción 1: Ver logs de Django
- Opción 2: Ver logs de AWS
- Opción 3: Ver ambos logs
- Opción 4: Limpiar logs

#### 2. Analizador de Logs
```bash
python log_analyzer.py                    # Resumen de errores
python log_analyzer.py --tail 100         # Últimas 100 líneas
python log_analyzer.py --level ERROR      # Solo errores
python log_analyzer.py --keyword "S3"     # Buscar por palabra clave
python log_analyzer.py --file aws_errors.log  # Archivo específico
python log_analyzer.py --summary          # Solo resumen
```

#### 3. Configurador de Sistema
```bash
python setup_logging.py
```
Configura y prueba todo el sistema de logging.

### 📊 Niveles de Log

- **🔴 ERROR**: Errores críticos (conexiones AWS fallidas, archivos no encontrados)
- **🟡 WARNING**: Advertencias (valores por defecto, archivos faltantes)
- **🔵 INFO**: Información general (inicio de procesos, resultados)
- **🟣 DEBUG**: Información detallada (parámetros, estados internos)

### 🔍 Ejemplos de Logs Generados

#### OCR Processing:
```
INFO 2025-01-11 10:30:15 AWSocr Starting OCR detection for photo: documento.jpg in bucket: bucket-getapp-t
DEBUG 2025-01-11 10:30:15 AWSocr Configuring S3 client with credentials
ERROR 2025-01-11 10:30:16 AWSocr Error accessing S3 file bucket-getapp-t/documento.jpg: NoSuchKey
```

#### Face Comparison:
```
INFO 2025-01-11 10:32:20 AWScompare Starting face comparison - Source: selfie.jpg, Target: cedula.jpg
DEBUG 2025-01-11 10:32:20 AWScompare Loading AWS Rekognition credentials
INFO 2025-01-11 10:32:25 AWScompare Face comparison completed - 1 results found
```

### 🚨 Detección de Errores Común

Los logs ahora capturan automáticamente:

1. **Errores de S3**: Archivos no encontrados, permisos
2. **Errores de Rekognition**: Problemas de API, límites
3. **Errores de Procesamiento**: AttributeError, DataFrame issues
4. **Errores de Configuración**: Credenciales, variables de entorno

### 📈 Monitoring Dashboard

Para ver el estado actual del sistema:

```bash
python log_analyzer.py --summary
```

Ejemplo de salida:
```
🔍 RESUMEN DE ERRORES ENCONTRADOS
==================================================
📄 django.log: 2 errores, 5 warnings
📄 aws_errors.log: 8 errores, 12 warnings
--------------------------------------------------
📈 TOTAL: 10 errores, 17 warnings
```

---

# 🛠 HISTORIAL DE FIXES ANTERIORES

## ❌ **Error Original:**
```
botocore.exceptions.ClientError: An error occurred (403) when calling the HeadObject operation: Forbidden
```

## ✅ **Problemas Identificados y Solucionados:**

### 1. **Falta de Migraciones**
- **Problema**: No existían migraciones para la app `apirest`
- **Solución**: 
  ```bash
  python manage.py makemigrations apirest
  python manage.py migrate
  ```

### 2. **Credenciales AWS Mal Configuradas**
- **Problema**: Cliente S3 sin credenciales en `AWSocr.py`
- **Solución**: Configurar cliente con credenciales de variables de entorno
  ```python
  s3_client = boto3.client('s3',
                          aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
                          region_name=config('AWS_DEFAULT_REGION'))
  ```

### 3. **Pandas .append() Deprecado**
- **Problema**: Uso de `df.append()` que está deprecado en pandas modernas
- **Solución**: Reemplazado con `pd.concat()`
  ```python
  # Antes:
  df = df.append(nuevo_registro, ignore_index=True)
  
  # Después:
  df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
  ```

### 4. **Registros de Configuración Faltantes**
- **Problema**: No existían registros `puntaje_ocr`, `puntaje_face`, `puntaje`
- **Solución**: Creados registros iniciales
  ```python
  puntaje_ocr.objects.get_or_create(pk=1, defaults={'puntaje_Max': 80})
  puntaje_face.objects.get_or_create(pk=1, defaults={'puntaje_Max': 85})
  puntaje.objects.get_or_create(pk=1, defaults={'puntaje_Max': 75})
  ```

### 5. **Manejo de Errores Mejorado**
- **Problema**: Sin manejo de excepciones para S3 y Rekognition
- **Solución**: Agregados try-except blocks
  ```python
  try:
      s3_client.head_object(Bucket=bucket, Key=photo)
      s3_client.download_file(bucket, photo, photoviene)
  except Exception as e:
      return {'cod': '400_Bad_Quality_image', 'error': f'Error S3: {str(e)}'}
  ```

### 6. **Modelos Optimizados**
- **Problema**: Modelos sin `Meta` class y campos obligatorios sin `blank=True`
- **Solución**: Agregadas Meta classes y configuración de campos opcionales

## 🚀 **Para Probar la Aplicación:**

### Activar Entorno y Ejecutar:
```bash
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Verificar configuración
python manage.py check

# Iniciar servidor
python manage.py runserver
```

### Endpoints Disponibles:
- **OCR**: `POST /ocr/` - Procesar documentos con OCR
- **Face Compare**: `POST /face/` - Comparar rostros
- **Restricted List**: `POST /lists/` - Verificar listas restrictivas
- **Login**: `POST /login/` - Autenticación
- **Admin**: `/admin/` - Panel administrativo

## 🔧 **Variables de Entorno Requeridas:**
```env
# AWS S3 (para descargar imágenes)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_DEFAULT_REGION=us-east-1

# AWS Rekognition (para OCR y face recognition)
AWS_REKOGNITION_ACCESS_KEY_ID=tu_rekognition_key
AWS_REKOGNITION_SECRET_ACCESS_KEY=tu_rekognition_secret

# S3 Buckets
AWS_S3_FACE_BUCKET=tu_face_bucket
AWS_S3_IMAGE_BUCKET=tu_image_bucket
```

## 📊 **Datos Iniciales Creados:**
- ✅ `puntaje_ocr` (pk=1): Umbral mínimo de confianza OCR = 80%
- ✅ `puntaje_face` (pk=1): Umbral mínimo de confianza facial = 85%  
- ✅ `puntaje` (pk=1): Umbral mínimo general = 75%

## ⚠️ **Notas Importantes:**
1. **Permisos S3**: Verificar que las credenciales AWS tengan permisos para:
   - `s3:GetObject` - Leer archivos
   - `s3:PutObject` - Subir archivos
   - `s3:HeadObject` - Verificar existencia

2. **Permisos Rekognition**: Verificar permisos para:
   - `rekognition:DetectText` - OCR
   - `rekognition:CompareFaces` - Comparación facial
   - `rekognition:DetectFaces` - Detección facial

3. **Archivos Temporales**: La app crea archivos temporales (`x*`, `xx*`) - asegúrate de tener permisos de escritura

## 🎯 **Estado Actual:**
- ✅ Base de datos configurada y migrada
- ✅ Modelos corregidos y funcionales
- ✅ AWS clients configurados correctamente
- ✅ Manejo de errores implementado
- ✅ Pandas actualizado a sintaxis moderna
- ✅ Datos iniciales creados

**¡La aplicación está lista para funcionar!** 🚀
