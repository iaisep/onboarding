import boto3
import pandas as pd
from PIL import Image
import io
from decouple import config
from apirest.models import puntaje_face

class consult47:


    source_file = ''
    target_file = ''
    error = ''
    def compare_faces(self, sourceFile):
        # Get AWS credentials from environment variables
        aws_access_key_id = config('AWS_REKOGNITION_ACCESS_KEY_ID')
        aws_secret_access_key = config('AWS_REKOGNITION_SECRET_ACCESS_KEY')
        region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
        bucket = config('AWS_S3_IMAGE_BUCKET')
        
        client = boto3.client('rekognition',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region_name)
        Bucket = bucket

        # ---------Comentar en  produccion



        indices = [0]
        comparar = {'cod':"400_Bad Quality_image",'coincidencia': "No Match"}
        puntos = int(puntaje_face.objects.get(pk=1).puntaje_Max)
        df = pd.DataFrame(data=comparar, index=indices)
        # self.comparar = df
        error=""

        xsourceFile = 'x' + sourceFile
        client = boto3.client('s3')
        client.download_file(Bucket, sourceFile, xsourceFile)
        image = Image.open(xsourceFile)
        ancho = image.size
        _ancho = .70
        _alto = .70
        image.thumbnail((ancho[0] * _ancho, ancho[1] * _alto))
        image.save(xsourceFile)
        if ancho[0] > ancho[1]:
            image = image.rotate(90)
            image.save(xsourceFile)
        image = Image.open(open(xsourceFile, 'rb'))
        stream = io.BytesIO()
        image.save(stream, format=image.format)
        image_binary = stream.getvalue()



        client = boto3.client('rekognition')
        response2 = client.detect_protective_equipment(Image={'Bytes': image_binary},
                                                       SummarizationAttributes={'MinConfidence': 20,
                                                                                'RequiredEquipmentTypes': ['FACE_COVER',
                                                                                                           ]})

        if len(response2['Persons']) < 1:

            comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "no es una Selfie válida"}
            df = df[(df['coincidencia'] != 'No Match')]
            df = df.append(comparar, ignore_index=True)

        else:

            for person in response2['Persons']:
                found_mask = False
                for body_part in person['BodyParts']:
                    ppe_items = body_part['EquipmentDetections']

                    for ppe_item in ppe_items:
                        # found a mask
                        if ppe_item['Type'] == 'FACE_COVER' and ppe_item['CoversBodyPart']['Value'] is True and ppe_item['Confidence'] > 95 :
                            found_mask = True
                            error = True
                            comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "No debe usar mascarillas en la selfie"}
                            df = df[(df['coincidencia'] != 'No Match')]
                            df = df.append(comparar, ignore_index=True)
                            #df = df[(df['coincidencia'] != 'No Match')]
            response3 = client.detect_faces(Image={"S3Object": {"Bucket": Bucket, "Name": sourceFile, }},
                                            Attributes=['ALL'])
            for faceDetail in response3['FaceDetails']:
                if faceDetail['Eyeglasses']['Value'] is True or faceDetail['Sunglasses']['Value'] is True or \
                        faceDetail['Quality']['Brightness'] < 40 or faceDetail['Confidence'] < 95:
                    error = True
                    if faceDetail['Quality']['Brightness'] < 40:
                        comparar = {'cod': "400_Bad Quality_image",
                                    'coincidencia': "Tome a selfie en un lugar mas iluminado"}
                        # comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "usted es demasiado fea"}
                        df = df[(df['coincidencia'] != 'No Match')]
                        df = df.append(comparar, ignore_index=True)
                        # df = df[(df['coincidencia'] != 'No Match')]
                    elif faceDetail['Confidence'] < 95:
                        comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "debe ser una foto de un rostro"}
                        # comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "usted es demasiado fea"}
                        df = df[(df['coincidencia'] != 'No Match')]
                        df = df.append(comparar, ignore_index=True)
                    else:
                        comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "No se acepta Selfie con Lentes"}
                        df = df[(df['coincidencia'] != 'No Match')]
                        df = df.append(comparar, ignore_index=True)
                        # df = df[(df['coincidencia'] != 'No Match')]
            if not error :

                #response = client.compare_faces(SimilarityThreshold=20,
                                                #SourceImage={"S3Object": {"Bucket": Bucket, "Name": sourceFile, }},
                                                #TargetImage={"S3Object": {"Bucket": Bucket, "Name": sourceFile, }})

                #for faceMatch in response['FaceMatches']:
                    #if int(faceMatch['Similarity']) >= puntos:
                        #similarity = str(faceMatch['Similarity'])
                        nuevo_registro = {'cod': "200_OK" ,'coincidencia':'Selfie Sin Error'} #: similarity + '% confidence'}
                        df = df.append(comparar, ignore_index=True)
                        df = df[(df['coincidencia'] != 'No Match')]

        self.comparar = df
        return comparar
