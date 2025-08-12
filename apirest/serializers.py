from rest_framework import serializers
from .models import llegadas, resultados, llegadas2, llegaface, puntaje, puntaje_ocr, puntaje_face, restrictiva


class llegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = llegadas
        fields = '__all__'


class ResulSerializer(serializers.ModelSerializer):
    class Meta:
        model = resultados
        fields = '__all__'


class llegaSerializer2(serializers.ModelSerializer):
    class Meta:
        model = llegadas2
        fields = '__all__'


class llegafaceSerializer2(serializers.ModelSerializer):
    class Meta:
        model = llegaface
        fields = ('faceselfie', 'ocrident')


class PuntajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = puntaje
        fields = '__all__'


class PuntajeOcrSerializer(serializers.ModelSerializer):
    class Meta:
        model = puntaje_ocr
        fields = '__all__'


class PuntajeFaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = puntaje_face
        fields = '__all__'


class RestrictivaSerializer(serializers.ModelSerializer):
    class Meta:
        model = restrictiva
        fields = '__all__'


class FileUploadSerializer(serializers.Serializer):
    """
    Serializer para manejar la subida de archivos
    Acepta archivos PDF, DOCX, DOC, JPG, JPEG, PNG
    """
    file = serializers.FileField(
        help_text="Archivo a subir (PDF, DOCX, DOC, JPG, JPEG, PNG)",
        required=True
    )
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File too large. Maximum size is 50MB, got {value.size / 1024 / 1024:.2f}MB")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(f"Unsupported file type: .{file_extension}. Allowed: {allowed_extensions}")
        
        return value


