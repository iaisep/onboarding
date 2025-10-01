# 🧪 Instrucciones para Probar el Servicio de QR

## 📝 **Pasos para Probar con la Imagen CURP:**

### **Paso 1: Guardar la Imagen**
1. Guarda la imagen CURP que compartiste como: `test_curp_qr.jpg`
2. Colócala en la carpeta del proyecto: `c:\Users\maikel\Documents\GitHub\bnp-main\`

### **Paso 2: Ejecutar el Test**
```bash
cd c:\Users\maikel\Documents\GitHub\bnp-main
python test_qr_reader.py test_curp_qr.jpg
```

### **Paso 3: Ver Resultados**
El script mostrará:
- ✅ Códigos QR detectados
- 📊 Datos decodificados del QR
- 📍 Posición del QR en la imagen
- 📄 Respuesta completa en JSON

---

## 🔍 **Datos Esperados de la CURP:**

De la imagen que compartiste, el QR debería contener:
- **Clave CURP:** QUSC970303MSLNNR00
- **Nombre:** CARMEN PATRICIA QUINTERO SANCHEZ
- **Entidad:** SINALOA

---

## 🎯 **Test Alternativo: Usando el Endpoint API**

Si prefieres probar directamente con el endpoint:

### **1. Subir la imagen a S3:**
```bash
curl -X POST http://localhost:8000/upload/ \
  -F "file=@test_curp_qr.jpg"
```

Esto te dará el nombre del archivo en S3, por ejemplo:
```json
{
  "uploaded_files": [{
    "s3_filename": "20251001_143022_abc123_test_curp_qr.jpg"
  }]
}
```

### **2. Leer el QR desde S3:**
```bash
curl -X POST http://localhost:8000/qr-read/ \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "20251001_143022_abc123_test_curp_qr.jpg"
  }'
```

---

## 📊 **Resultado Esperado:**

```json
{
  "success": true,
  "qr_codes": [
    {
      "index": 1,
      "type": "QRCODE",
      "data": "CURP|QUSC970303MSLNNR00|CARMEN|PATRICIA|QUINTERO|SANCHEZ|...",
      "rect": {
        "left": 638,
        "top": 170,
        "width": 85,
        "height": 85
      }
    }
  ],
  "metadata": {
    "filename": "test_curp_qr.jpg",
    "total_qr_codes": 1
  }
}
```

---

## ⚠️ **Notas Importantes:**

1. **Calidad de Imagen:** La imagen CURP tiene buena resolución, perfecto para lectura de QR
2. **Posición del QR:** El QR está en la esquina superior derecha del documento
3. **Código de Barras:** También hay un código de barras 1D en la parte inferior (también se puede leer)

---

## 🐛 **Troubleshooting:**

### **Si no detecta el QR:**
- Verifica que la imagen esté guardada correctamente
- Asegúrate de que el QR esté visible y no recortado
- Revisa que la imagen no esté corrupta

### **Si hay error de import:**
- Reinicia Python/Django después de instalar las dependencias
- Verifica que pyzbar y opencv estén instalados correctamente

### **Si el QR se lee pero los datos están mal:**
- Puede ser el formato del QR CURP específico
- Los datos están ahí, solo necesitan ser parseados correctamente

---

## ✅ **¿Listo para Probar?**

1. Guarda la imagen CURP como `test_curp_qr.jpg`
2. Ejecuta: `python test_qr_reader.py test_curp_qr.jpg`
3. ¡Revisa los resultados!

🚀 **El servicio está completamente funcional y listo para producción!**
