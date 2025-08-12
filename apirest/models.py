
from django.db import models
from django.core.validators import MinLengthValidator


class Lista(models.Model):
    Lista_name = models.CharField(max_length=10)
    author_name = models.CharField(max_length=10)
    Lista_price = models.IntegerField()
    Lista_quantity = models.IntegerField()

    class Meta:
        db_table = 'apirest_lista'

    def __str__(self):
        return self.Lista_name

class llegadas(models.Model):
    String = models.CharField(max_length=255)
    check_status = models.IntegerField()  # Renamed from 'check' to avoid conflict

    class Meta:
        db_table = 'apirest_llegadas'

    def __str__(self):
        return self.String

class llegadas2(models.Model):
    string_income = models.CharField(max_length=255, validators=[MinLengthValidator(7)])

    class Meta:
        db_table = 'apirest_llegadas2'

    def __str__(self):
        return self.string_income


class resultados(models.Model):
    index = models.IntegerField()
    nombres = models.CharField(max_length=255)
    Puntos = models.IntegerField()
    Lista_Sanciones = models.CharField(max_length=255)
    Prospecto = models.CharField(max_length=255)

    class Meta:
        db_table = 'apirest_resultados'

    def __str__(self):
        return self.nombres

class restrictiva(models.Model):
    name = models.CharField(max_length=255)
    also_known_as = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    program = models.CharField(max_length=255, blank=True, null=True)
    list = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.CharField(max_length=255, blank=True, null=True)
    edad = models.CharField(max_length=255, blank=True, null=True)
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)
    nationality = models.CharField(max_length=255, blank=True, null=True)
    citizenship = models.CharField(max_length=255, blank=True, null=True)
    addresses = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state_province = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    sanction_list = models.CharField(max_length=255, blank=True, null=True)
    hiperlik = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'apirest_restrictiva'

    def __str__(self):
        return self.name


class puntaje(models.Model):
    puntaje_Max = models.IntegerField()

    class Meta:
        db_table = 'apirest_puntaje'

    def __str__(self):
        return str(self.puntaje_Max)


class puntaje_ocr(models.Model):
    puntaje_Max = models.IntegerField()

    class Meta:
        db_table = 'apirest_puntaje_ocr'

    def __str__(self):
        return str(self.puntaje_Max)


class puntaje_face(models.Model):
    puntaje_Max = models.IntegerField()

    class Meta:
        db_table = 'apirest_puntaje_face'

    def __str__(self):
        return str(self.puntaje_Max)


class llegaface(models.Model):
    faceselfie = models.CharField(max_length=255)
    ocrident = models.CharField(max_length=255)

    class Meta:
        db_table = 'apirest_llegaface'

    def __str__(self):
        return f"Face: {self.faceselfie} - OCR: {self.ocrident}"


