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


class TextractAnalysisSerializer(serializers.Serializer):
    """
    Serializer para análisis de documentos con AWS Textract
    Procesa documentos ya subidos al bucket S3
    """
    document_name = serializers.CharField(
        max_length=255,
        help_text="Nombre del archivo en el bucket S3 (ej: 20250812_143022_a1b2c3d4_cedula.jpg)",
        required=True
    )
    
    analysis_type = serializers.ChoiceField(
        choices=[
            ('id_document', 'Análisis de documento de identidad (analyze_id)'),
            ('general_document', 'Análisis de documento general (detect_document_text)')
        ],
        default='id_document',
        help_text="Tipo de análisis a realizar",
        required=False
    )
    
    bucket_name = serializers.CharField(
        max_length=255,
        help_text="Nombre del bucket S3 (opcional, usa el bucket por defecto si no se especifica)",
        required=False,
        allow_blank=True
    )
    
    def validate_document_name(self, value):
        """Validate document name format"""
        if not value:
            raise serializers.ValidationError("Document name cannot be empty")
        
        # Check for valid file extensions for Textract
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_extension = f".{value.lower().split('.')[-1]}"
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(f"Unsupported file type for Textract: {file_extension}. Allowed: {allowed_extensions}")
        
        return value


