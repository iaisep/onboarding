# 📊 Test de Resolución PDF → Imagen (600 DPI)

## 🎯 **Objetivo del Test**
Probar conversión de PDF a imagen con **resolución doble (600 DPI)** para evaluar mejoras en calidad OCR.

---

## 🔧 **Cambios Aplicados**

### **Fecha:** 1 de Octubre, 2025

### **Archivo Modificado:**
- `apirest/AWSUpload.py` - Método `_convert_pdf_to_images()`

### **Parámetros de Conversión:**

| Parámetro | Valor Anterior | Valor de Test | Cambio |
|-----------|---------------|---------------|--------|
| **Zoom Factor** | 3.0x | 6.0x | +100% |
| **DPI Efectivo** | 300 DPI | 600 DPI | +100% |
| **JPEG Quality** | 95 | 95 | Sin cambio |
| **Sharpening** | 1.2x | 1.2x | Sin cambio |

### **Código Modificado:**

```python
# ANTES (300 DPI):
mat = fitz.Matrix(3.0, 3.0)  # 3x zoom = ~300 DPI
img.save(output, format='JPEG', quality=95, optimize=True, dpi=(300, 300))

# AHORA (600 DPI - TEST):
mat = fitz.Matrix(6.0, 6.0)  # 6x zoom = ~600 DPI
img.save(output, format='JPEG', quality=95, optimize=True, dpi=(600, 600))
```

---

## 📈 **Impacto Esperado**

### **Ventajas:**
- ✅ **Mucho mejor** para texto muy pequeño
- ✅ **Excelente** para documentos de baja calidad escaneados
- ✅ **Máxima precisión** OCR en condiciones óptimas
- ✅ **Ideal** para documentos con detalles finos

### **Desventajas:**
- ⚠️ **Tamaño de archivo:** 3-4x más grande
- ⚠️ **Tiempo de procesamiento:** 2-3x más lento
- ⚠️ **Consumo de memoria:** ~4x más RAM durante conversión
- ⚠️ **Ancho de banda:** Mayor uso de S3 storage

---

## 🧪 **Métricas a Evaluar**

### **1. Calidad OCR:**
- Precisión en texto pequeño
- Detección de caracteres especiales
- Reconocimiento en documentos de baja calidad

### **2. Performance:**
- Tiempo de conversión por página
- Tamaño de archivo resultante
- Uso de memoria durante conversión

### **3. Costos:**
- Almacenamiento S3 (archivos más grandes)
- Transferencia de datos (mayor bandwidth)
- Tiempo de procesamiento (mayor CPU)

---

## 📊 **Comparación Estimada**

| Métrica | 300 DPI | 600 DPI (Test) | Diferencia |
|---------|---------|----------------|------------|
| Tamaño promedio/página | ~200-300 KB | ~800-1200 KB | +300-400% |
| Tiempo conversión/página | ~1-2 seg | ~3-6 seg | +200-300% |
| Memoria RAM usada | ~50-100 MB | ~200-400 MB | +300-400% |
| Precisión OCR (texto normal) | ~98% | ~98-99% | +0-1% |
| Precisión OCR (texto pequeño) | ~85-90% | ~95-98% | +10-15% |

---

## 🔄 **Instrucciones de Reversión**

Si la resolución 600 DPI no funciona o causa problemas, revertir a 300 DPI:

### **Cambios a Revertir en `apirest/AWSUpload.py`:**

```python
# Línea ~140: Cambiar de 6.0 a 3.0
mat = fitz.Matrix(3.0, 3.0)  # Revertir a 3x zoom = ~300 DPI

# Línea ~155: Cambiar DPI de 600 a 300
img.save(output, format='JPEG', quality=95, optimize=True, dpi=(300, 300))

# Línea ~169: Actualizar mensaje de log
logger.debug(f"Converted page {page_num + 1} to {len(img_data)} bytes at 300 DPI")

# Línea ~172: Actualizar mensaje de log
logger.info(f"High-quality PDF conversion completed - {len(converted_images)} images generated at 300 DPI")
```

---

## ✅ **Criterios de Éxito del Test**

### **El test es exitoso SI:**
1. Mejora significativa en OCR de texto pequeño (+10% precisión)
2. Tiempo de conversión aceptable (<5 seg/página)
3. Tamaño de archivo manejable (<1.5 MB/página promedio)
4. Sin errores de memoria o timeouts

### **El test FALLA SI:**
1. Timeouts frecuentes en conversión
2. Errores de memoria (OOM)
3. Archivos demasiado grandes (>2 MB/página promedio)
4. No hay mejora significativa en OCR (<5% precisión)

---

## 📝 **Notas de Prueba**

### **Fecha de Test:**
- Inicio: 1 de Octubre, 2025
- Estado: En evaluación

### **Resultados:**
_[Agregar resultados aquí después de las pruebas]_

- ✅/❌ Calidad OCR mejorada: 
- ✅/❌ Performance aceptable:
- ✅/❌ Tamaños de archivo manejables:
- ✅/❌ Sin errores de memoria:

### **Decisión Final:**
_[Mantener 600 DPI / Revertir a 300 DPI / Probar valor intermedio (400 DPI)]_

---

## 🎯 **Valores Recomendados por Tipo de Documento**

| Tipo de Documento | DPI Recomendado | Zoom Factor |
|-------------------|----------------|-------------|
| Texto normal (libro, contrato) | 300 DPI | 3.0x |
| Texto pequeño (facturas, formularios) | 400-600 DPI | 4.0-6.0x |
| Documentos escaneados de baja calidad | 600 DPI | 6.0x |
| Imágenes con texto integrado | 400 DPI | 4.0x |
| Documentos técnicos (planos, diagramas) | 600 DPI | 6.0x |

---

## 💡 **Alternativa: Resolución Dinámica**

Si 600 DPI es demasiado para documentos normales, considerar implementar:

```python
# Detección automática de calidad de documento
if document_quality < threshold:
    zoom_factor = 6.0  # 600 DPI para baja calidad
else:
    zoom_factor = 3.0  # 300 DPI para calidad normal
```

---

**Estado Actual:** 🔬 **EN PRUEBA - 600 DPI**
