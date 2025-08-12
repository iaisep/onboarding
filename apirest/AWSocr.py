# -*- coding: utf-8 -*-
import boto3
import pandas as pd
from PIL import Image
from os import remove
import io
from unidecode import unidecode
from decouple import config
from apirest.models import puntaje_ocr
import logging

# Configure logger for AWS OCR operations
logger = logging.getLogger('apirest.ocr')

class consult45:
    photo = ''
    photoviene = 'x'
    photova=""
    # Remove hardcoded bucket - will use from environment variables
    response1 =''

    def __init__(self):
        logger.info("Initializing consult45 class")
        try:
            # Initialize AWS credentials from environment
            self.aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY') 
            self.aws_session_token = config('AWS_SESSION_TOKEN', default=None)
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET')
            
            logger.info(f"AWS Config loaded - Region: {self.region_name}, Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error loading AWS configuration: {str(e)}")
            raise

    def detect_text(self, photo, bucket):
        logger.info(f"Starting OCR detection for photo: '{photo}' in bucket: '{bucket}'")
        logger.debug(f"Method parameters - photo type: {type(photo)}, bucket type: {type(bucket)}")
        
        # Validate parameters
        if not photo or not isinstance(photo, str):
            logger.error(f"Invalid photo parameter: '{photo}' (type: {type(photo)})")
            error_response = {
                'cod': '400_Invalid_Parameters',
                'error': f'Invalid photo parameter: {photo}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            return error_response
            
        if not bucket or not isinstance(bucket, str):
            logger.error(f"Invalid bucket parameter: '{bucket}' (type: {type(bucket)})")
            error_response = {
                'cod': '400_Invalid_Parameters', 
                'error': f'Invalid bucket parameter: {bucket}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            return error_response
        
        ancho = ""
        
        try:
            # Configurar cliente S3 con credenciales
            logger.debug("Configuring S3 client with credentials")
            s3_client = boto3.client('s3',
                                    aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                    aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
                                    region_name=config('AWS_DEFAULT_REGION', default='us-east-1'))
            
            photoviene = 'x' + photo
            photova = 'xx' + photo
            
            logger.debug(f"Generated temp filenames: {photoviene}, {photova}")
            
            # Verificar si el archivo existe en S3
            logger.debug(f"Checking if file exists in S3: {bucket}/{photo}")
            s3_client.head_object(Bucket=bucket, Key=photo)
            logger.info(f"File found in S3, downloading: {bucket}/{photo}")
            
            # Descargar archivo desde S3
            s3_client.download_file(bucket, photo, photoviene)
            logger.info(f"Successfully downloaded file to: {photoviene}")
            
        except Exception as e:
            logger.error(f"Error accessing S3 file {bucket}/{photo}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            
            # Crear respuesta de error y asignarla a self.sancionados
            error_response = {
                'cod': '400_Bad_Quality_image',
                'Numero_de_Documento': '',
                'Expedicion': '',
                'Expira': '',
                'Pais_de_Residencia': '',
                'Nombres': '',
                'Apellidos': '',
                'Fecha_de_Nacimiento': '',
                'Lugar_de_Nacimiento': '',
                'Genero': '',
                'Nacionalidad': '',
                'error': f'No se pudo acceder al archivo en S3: {str(e)}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            logger.debug("Created error DataFrame and assigned to self.sancionados")
            return error_response
        
        try:
            logger.debug(f"Opening image file: {photoviene}")
            image = Image.open(photoviene)
            ancho = image.size
            logger.debug(f"Image dimensions: {ancho}")
            
            image_binary = ''
            _ancho = .50
            _alto = .50
            logger.debug(f"Resizing image with factors: {_ancho}, {_alto}")
            image.thumbnail((ancho[0] * _ancho, ancho[1] * _alto))
            image.save(photoviene)
            ancho = image.size
            logger.debug(f"New image dimensions after resize: {ancho}")
            
            if ancho[0] > ancho[1] and (ancho[0]-ancho[1] >= (ancho[1]/4)):
                logger.debug("Image is landscape, rotating -90 degrees")
                image_rot_180 = image.rotate(-90)
                image_rot_180.save(photoviene)
                # prueba
                image = Image.open(open(photoviene, 'rb'))
                stream = io.BytesIO()
                image.save(stream, format=image.format)
                image_binary = stream.getvalue()

                logger.debug(f"Uploading rotated image to S3: {photova}")
                s3_client.upload_file(photoviene, bucket, photova)
                #remove('/home/maguzman/bnp/'+ photoviene)

            elif ancho[0] < ancho[1]:
                logger.debug("Image is portrait, processing without rotation")
                #prueba
                image = Image.open(open(photoviene, 'rb'))
                stream = io.BytesIO()
                image.save(stream, format=image.format)
                image_binary = stream.getvalue()

                logger.debug(f"Uploading portrait image to S3: {photova}")
                s3_client.upload_file(photoviene, bucket, photova)
                #remove('/home/maguzman/bnp/' + photoviene)

        except Exception as e:
            logger.error(f"Error processing image {photoviene}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            # Create error response
            error_response = {
                'cod': '400_Bad_Quality_image',
                'Numero_de_Documento': '',
                'Expedicion': '',
                'Expira': '',
                'Pais_de_Residencia': '',
                'Nombres': '',
                'Apellidos': '',
                'Fecha_de_Nacimiento': '',
                'Lugar_de_Nacimiento': '',
                'Genero': '',
                'Nacionalidad': '',
                'error': f'Error procesando imagen: {str(e)}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            return error_response

        x = '400_Bad Quality_image'
        y = 'NACIONALIDAD'
        z = "EXPEDIDA"
        ciudadania = ""
        Id = ""
        listonombre = ""
        Tipo_Ciudadania = ""
        Nombre = ""
        Apellidos = ""
        Fecha_de_Nacimiento = ""
        Lugar_de_Nacimiento = ""
        expedida = ""
        expira = ""
        Nacionalidad = ""
        subcadena2 = ""
        sex_ = ""
        logger.debug("Initializing OCR variables and configuration")
        
        sexo = ""
        Idword = ""
        Idwordexpedida = ""
        Idwordexpira = ""
        id_guion = ""
        v = "-"
        indices = [0]
        Id_prox = 0
        Id_prox2 = 0
        Id_prox3 = 0

        avgconf = {'avg': 0}
        sancionados = {'cod': "",
                       'Numero_de_Documento': '',
                       'Expedicion': '',
                       'Expira': '',
                       'Nombres': "",
                       'Apellidos': '',
                       'Fecha_de_Nacimiento': '',
                       'Pais_de_Residencia': "",
                       'Lugar_de_Nacimiento': '',
                       'Genero': '',
                       'Nacionalidad':''}

        try:
            logger.debug("Fetching OCR score threshold from database")
            puntos = int(puntaje_ocr.objects.get(pk=1).puntaje_Max)
            logger.debug(f"OCR threshold loaded: {puntos}")
        except puntaje_ocr.DoesNotExist:
            logger.warning("OCR threshold not found in database, using default value 80")
            # Si no existe el registro, usar valor por defecto
            puntos = 80
            # O crear el registro por defecto
            puntaje_ocr.objects.create(pk=1, puntaje_Max=80)
            logger.debug("Created default OCR threshold record")
        except Exception as e:
            logger.error(f"Error fetching OCR threshold: {str(e)}")
            puntos = 80
        
        logger.debug("Creating initial DataFrames for OCR processing")
        df = pd.DataFrame(data=sancionados, index=indices)
        df2 = pd.DataFrame(data=avgconf, index=indices)

        try:
            # Configurar cliente Rekognition con credenciales
            logger.debug("Configuring AWS Rekognition client")
            rekognition_client = boto3.client('rekognition',
                                            aws_access_key_id=config('AWS_REKOGNITION_ACCESS_KEY_ID'),
                                            aws_secret_access_key=config('AWS_REKOGNITION_SECRET_ACCESS_KEY'),
                                            region_name=config('AWS_DEFAULT_REGION', default='us-east-1'))
            logger.debug("Rekognition client configured successfully")
        
        except Exception as e:
            logger.error(f"Error configuring Rekognition client: {str(e)}")
            # Create error response
            error_response = {
                'cod': '500_AWS_Error',
                'Numero_de_Documento': '',
                'Expedicion': '',
                'Expira': '',
                'Pais_de_Residencia': '',
                'Nombres': '',
                'Apellidos': '',
                'Fecha_de_Nacimiento': '',
                'Lugar_de_Nacimiento': '',
                'Genero': '',
                'Nacionalidad': '',
                'error': f'Error configurando cliente Rekognition: {str(e)}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            return error_response
        
        try:
            logger.info("Starting AWS Rekognition text detection")
            #prueba
            response = rekognition_client.detect_text(Image={'Bytes': image_binary})
            logger.info(f"Rekognition response received with {len(response.get('TextDetections', []))} text detections")
            
        except Exception as e:
            logger.error(f"Error with Rekognition text detection: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            
            # Crear respuesta de error y asignarla a self.sancionados
            error_response = {
                'cod': '400_Bad_Quality_image',
                'Numero_de_Documento': '',
                'Expedicion': '',
                'Expira': '',
                'Pais_de_Residencia': '',
                'Nombres': '',
                'Apellidos': '',
                'Fecha_de_Nacimiento': '',
                'Lugar_de_Nacimiento': '',
                'Genero': '',
                'Nacionalidad': '',
                'error': f'Error en OCR: {str(e)}'
            }
            df_error = pd.DataFrame([error_response], index=indices)
            self.sancionados = df_error
            logger.debug("Created error DataFrame for Rekognition failure")
            return error_response

        #response = client.detect_text(Image={'S3Object': {'Bucket': bucket, 'Name': photova}})

        textDetections = response['TextDetections']
        for text in textDetections:
            cadena = text['DetectedText']
            Tipo = text['Type']
            Rep = (cadena.find("BLICA DE PA"))
            Rep2 = (cadena.find("REPUBLICA"))
            Rep3 = cadena
            name1 = cadena[2:4]
            carnet = (cadena.find("CARNE DE RESIDENTE"))
            Tribuna = (cadena.find("AL ELECTO"))
            fecha_Nac = (cadena.find("FECHA DE NACIMIENTO"))
            Lugar_Nac = (cadena.find("LUGAR DE NACIMIENTO"))
            Nacional_ = (cadena.find(y))
            expe_expi = (cadena.find(z))
            sex_ = (cadena.find("SEXO: "))
            id_guion = (cadena.find(v))

            if cadena.count('-') > 0:
                indice_g1 = cadena.index('-') + 1
                indice_g2 = indice_g1 + 3
                Id_verifica = cadena[indice_g1:indice_g2]
            if Id_prox > 0: Id_prox = 1 + Id_prox
            if Id_prox2 > 0: Id_prox2 = 1 + Id_prox2
            if Id_prox3 > 0: Id_prox3 = 0 + Id_prox3
            if "PANAM" in Rep3 and Tipo == 'LINE' and not Nacionalidad:  ## cambio
                Nacionalidad = "REPUBLICA DE PANAMA"
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)

            elif "CARNE" in Rep3 and Tipo == 'LINE' and not Tipo_Ciudadania:
                Tipo_Ciudadania = 'CEDULA EXTRANJERO'
                ciudadania = ''
                x = '200_OK'
                # indice_=  int(text['Id']) + 1
                listonombre = 1
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif ("TRIBUNA" in Rep3 or "ELECTO" in Rep3) and Tipo == 'LINE' and not Tipo_Ciudadania:
                Tipo_Ciudadania = 'CEDULA PANAMEÑA'
                ciudadania = 'PANAMEÑA'
                x = '200_OK'
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif name1.islower() and not Nombre:
                Nombre = (text['DetectedText'])
                names1 = Nombre.split(' ')
                if len(names1) > 1:
                    Nombre = names1[0] + " " + names1[1]
                    if len(names1) > 2:
                        Nombre = Nombre + " " + names1[2]
                        if len(names1) > 3:
                            Nombre = Nombre + " " + names1[3]
                else:
                    Nombre = names1[0]
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif name1.islower() and not Apellidos:
                Apellidos = (text['DetectedText'])
                Apellidos1 = Apellidos.split(' ')
                if len(Apellidos1) > 1:
                    Apellidos = Apellidos1[0] + " " + Apellidos1[1]
                else:
                    Apellidos = Apellidos1[0]
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)

            elif "NACIMIENTO:" in Rep3 and Tipo == 'LINE' and not Lugar_de_Nacimiento:
                if not Tipo_Ciudadania == "CEDULA PANAMEÑA":
                    indice_az = 0
                    indice_bz = 0
                    indice_cz = 0
                    indice_dz = 0
                    Lugar_Nac_toda = (text['DetectedText'])
                    if Lugar_Nac_toda.count('DE DE') > 0:
                        indice_az = Lugar_Nac_toda.index('NACIMIENTO: NACIMIENTO:') + 23
                        indice_bz = indice_az + 12
                        Lugar_de_Nacimiento = cadena[indice_az + 1:indice_bz]
                    elif Lugar_Nac_toda.count('LUGAR DE NACIMIENTO') > 0:
                        Lugar_Nac_toda1 = Lugar_Nac_toda.split(' ')
                        if len(Lugar_Nac_toda1) > 1:
                            if Id_verifica.isalpha():
                                Lugar_de_Nacimiento = Lugar_Nac_toda1[3]
                                x = '200_OK'
                                avg = int(text['Confidence'])
                                avgconf = {'avg': avg}
                                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                else:
                    Lugar_de_Nacimiento = 'PANAMA'
            elif 'EXPEDIDA' in Rep3 and Tipo == 'LINE' and not expedida:
                if ':' in Rep3:
                    expedida_ = Rep3.split(':')
                    expedida = expedida_[1][1:12]  # (text['DetectedText'])
                    if len(expedida_) > 2:
                        expira = expedida_[2][1:12]
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif "NACIONA" in Rep3 and Tipo == 'LINE' and not ciudadania:
                Nacionalidad_toda = (text['DetectedText'])
                # if Nacionalidad_toda.count('NACIONA') > 0:
                #   Nacionalidad_toda1 = Nacionalidad_toda.split(' ')
                #  if not Nacionalidad_toda1.count('SEXO:') > 0:
                #     if len(Nacionalidad_toda1) > 1:
                #        ciudadania = Nacionalidad_toda1[1]
                #   else:
                #      ciudadania = Nacionalidad_toda1[0]
                # x = '200_OK'
                # avg = int(text['Confidence'])
                # avgconf = {'avg': avg}
                # df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif "SEX" in Rep3 and Tipo == 'LINE':
                sex_todo = (text['DetectedText'])
                if sex_todo.count('SEXO') > 0:
                    sex_todo1 = sex_todo.split(' ')
                    if len(sex_todo1) > 1 and len(sex_todo1[1]) == 1:
                        if sex_todo1[1] == 'F' or sex_todo1[1] == 'M':
                            sexo = sex_todo1[1]
                            x = '200_OK'
                            avg = int(text['Confidence'])
                            avgconf = {'avg': avg}
                            df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                        elif sex_todo1[1] == 'I' or sex_todo1[1] == 'l':
                            sexo = 'F'
                            x = '200_OK'
                            avg = int(text['Confidence'])
                            avgconf = {'avg': avg}
                            df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                        elif sex_todo1[1] == 'N' or sex_todo1[1] == 'H':
                            sexo = 'M'
                            x = '200_OK'
                            avg = int(text['Confidence'])
                            avgconf = {'avg': avg}
                            df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                    elif len(sex_todo1) == 1:
                        if sex_todo1[0] == 'SEXO:M':
                            #sexo = 'M'
                            x = '200_OK'
                            #avg = int(text['Confidence'])
                            #avgconf = {'avg': avg}
                            #df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                        elif sex_todo1[0] == 'SEXO:F':
                            sexo = 'F'
                            #x = '200_OK'
                            #avg = int(text['Confidence'])
                            #avgconf = {'avg': avg}
                            #df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)

            # --------------------------Palabras -----------------------------------
            elif "-" in Rep3 and Tipo == 'WORD' and not Fecha_de_Nacimiento and Id_verifica.isalpha():
                indice_g1 = Rep3.split('-')

                Id_verifica = indice_g1[1]  # cadena[indice_g1:indice_g2]
                mes = unidecode(Id_verifica, errors='preserve')
                if 'OST' in mes:
                    mes = 'OCT'
                # elif 'NOV' in mes:
                #    mes = 'NOV'
                # elif 'DEC' in mes:
                #   mes = 'DIC'
                # elif 'DIC' in mes:
                #    mes = 'DIC'
                # elif 'ENE' in mes:
                #    mes = 'ENE'
                # elif 'DIC' in mes:
                #    mes = 'DIC'
                # elif 'DOC' in mes:
                #   mes = 'DIC'
                # elif 'DUC' in mes:
                #   mes = 'DIC'
                # elif 'DLC' in mes:
                #   mes = 'DIC'

                if Id_verifica.isalpha():
                    if "NACIMIENTO:" in indice_g1[0]:
                        indice_g1[0] = indice_g1[0].split(':')
                        Fecha_de_Nacimiento = indice_g1[0][1] + '-' + mes + '-' + indice_g1[2]

                    else:
                        Fecha_de_Nacimiento = indice_g1[0] + '-' + mes + '-' + indice_g1[2]
                        # Fecha_de_Nacimiento = (text['DetectedText'])
                x = '200_OK'
                avg = int(text['Confidence'])
                avgconf = {'avg': avg}
                df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif "-" in Rep3 and Tipo == 'WORD' and not Id:
                indice_g1 = Rep3.index('-') + 1
                indice_g2 = indice_g1 + 3
                Id_verifica = cadena[indice_g1:indice_g2]
                if not Id_verifica.isalpha():
                    Id = (text['DetectedText'])
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif 'EXPEDIDA' in Rep3 and Tipo == 'WORD' and not expedida:
                    Idwordexpedida = (text['ParentId'])
            elif Tipo == 'WORD' and (text['ParentId']) == Idwordexpedida and not expedida:
                    expedida = Rep3[0:11]  # (text['DetectedText'])
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif 'EXPIRA' in Rep3 and Tipo == 'WORD' and not expira:
                    Idwordexpira = (text['ParentId'])
            elif Tipo == 'WORD' and (text['ParentId']) == Idwordexpira and not expira:
                    expira = Rep3[0:11]  # (text['DetectedText'])
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
            elif "LUGAR" in Rep3 and Tipo == 'WORD' and not Lugar_de_Nacimiento:
                Id_prox = 1 + Id_prox
            elif Id_prox == 4 and Tipo == 'WORD' and not Lugar_de_Nacimiento:
                if not Tipo_Ciudadania == 'CEDULA PANAMEÑA':
                    Lugar_de_Nacimiento = (text['DetectedText'])
                    Id_prox = 0
                else:
                    Lugar_de_Nacimiento = 'PANAMA'
            elif "NACIONALIDAD" in Rep3 and Tipo == 'WORD' and not ciudadania:
                #Id_prox2 = 1 + Id_prox2
                Idword = (text['ParentId'])
            elif Tipo == 'WORD' and (text['ParentId']) == Idword and not ciudadania:
                ciudadania = (text['DetectedText'])
                Tipo_Ciudadania = 'CEDULA EXTRANJERA'
                #Id_prox = 0
            elif "SEXO" in Rep3 and Tipo == 'WORD' and not sexo:
                Idword = (text['ParentId'])
            elif Tipo == 'WORD' and (text['ParentId']) == Idword and not sexo:
                sex_todo = (text['DetectedText'])
                if sex_todo == 'F' or sex_todo == 'M':
                    sexo = sex_todo
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                elif sex_todo == 'I' or sex_todo == 'l':
                    sexo = 'F'
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
                elif sex_todo == 'N' or sex_todo == 'H':
                    sexo = 'M'
                    x = '200_OK'
                    avg = int(text['Confidence'])
                    avgconf = {'avg': avg}
                    df2 = pd.concat([df2, pd.DataFrame([avgconf])], ignore_index=True)
        datos = Nacionalidad + "|" + Tipo_Ciudadania + "|" + Nombre + "|" + Apellidos + "|"\
                + Fecha_de_Nacimiento + "|" + Lugar_de_Nacimiento + "|" + Id + "|" + ciudadania +\
                "|" + expedida + "|" + expira + "|" + sexo
        df2 = df2[(df2['avg'] != 0)]
        xx = df2['avg'].mean()
        if not Id or not Tipo_Ciudadania or not Nombre or not Apellidos or not Fecha_de_Nacimiento \
                or not Lugar_de_Nacimiento or not expedida or not expira or not sexo or not ciudadania:
            x = '400_Bad Quality_image'
        else:
            x = '200_OK'
        if xx < puntos:
            x = '400_Bad Quality_image'
        nuevo_registro = {'cod': str(x), 'Numero_de_Documento': str(Id),
                          'Expedicion': str(expedida),
                          'Expira': str(expira),
                          'Pais_de_Residencia': str(Nacionalidad),
                          'Nombres': str(Nombre),
                          'Apellidos': str(Apellidos),
                          'Fecha_de_Nacimiento': str(Fecha_de_Nacimiento),
                          'Lugar_de_Nacimiento': str(Lugar_de_Nacimiento),
                          'Genero': str(sexo),
                          'Nacionalidad': str(ciudadania)}
        df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
        df = df[(df['cod'] != '')]
        self.sancionados = df
        return sancionados