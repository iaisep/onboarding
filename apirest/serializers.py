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


