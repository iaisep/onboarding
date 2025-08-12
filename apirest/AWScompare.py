import boto3
import pandas as pd
from PIL import Image
import io
from decouple import config
from apirest.models import puntaje_face
import logging

# Configure logger for AWS Face operations
logger = logging.getLogger('apirest.face')

class consult46:

    source_file = ''
    target_file = ''
    error = ''

    def __init__(self):
        logger.info("Initializing AWS Face Comparison service (consult46)")
        try:
            # Load AWS credentials from environment
            self.aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
            self.aws_session_token = config('AWS_SESSION_TOKEN', default=None)
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            
            logger.info(f"AWS Face service configured - Region: {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error initializing AWS Face Comparison: {str(e)}")
            raise

    def compare_faces(self, sourceFile, targetFile):
        logger.info(f"Starting face comparison - Source: {sourceFile}, Target: {targetFile}")
        
        try:
            # Get AWS credentials from environment variables
            logger.debug("Loading AWS Rekognition credentials")
            aws_access_key_id = config('AWS_REKOGNITION_ACCESS_KEY_ID')
            aws_secret_access_key = config('AWS_REKOGNITION_SECRET_ACCESS_KEY')
            region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            bucket = config('AWS_S3_FACE_BUCKET')
            
            logger.debug(f"Configuring Rekognition client for region: {region_name}, bucket: {bucket}")
            
            client = boto3.client('rekognition',
                                  aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key,
                                  region_name=region_name)
            Bucket = bucket

            # ---------Comentar en  produccion

            indices = [0]
            comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "No Match"}
            
            logger.debug("Fetching face comparison threshold from database")
            puntos = int(puntaje_face.objects.get(pk=1).puntaje_Max)
            logger.debug(f"Face comparison threshold: {puntos}")
            
            df = pd.DataFrame(data=comparar, index=indices)
            # self.comparar = df
            error = ""

            xsourceFile = 'y' + sourceFile
            logger.debug(f"Downloading source file from S3: {bucket}/{sourceFile} to {xsourceFile}")
            
            s3_client = boto3.client('s3')
            s3_client.download_file(Bucket, sourceFile, xsourceFile)
            logger.debug(f"Successfully downloaded source file")
            
            image = Image.open(xsourceFile)
            ancho = image.size
            logger.debug(f"Source image dimensions: {ancho}")
            
        except Exception as e:
            logger.error(f"Error setting up face comparison: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            # Return error response
            error_response = {
                'cod': '500_AWS_Error',
                'coincidencia': f'Error: {str(e)}'
            }
            indices = [0]
            df_error = pd.DataFrame([error_response], index=indices)
            self.comparar = df_error
            return error_response
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
                                                       SummarizationAttributes={'MinConfidence': 80,
                                                                                'RequiredEquipmentTypes': ['FACE_COVER',
                                                                                                           ]})

        for person in response2['Persons']:
            found_mask = False
            for body_part in person['BodyParts']:
                ppe_items = body_part['EquipmentDetections']

                for ppe_item in ppe_items:
                    # found a mask
                    if ppe_item['Type'] == 'FACE_COVER' and ppe_item['CoversBodyPart']['Value'] is True:
                        found_mask = True
                        error = True
                        comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "Mascarillas"}
                        df = df[(df['coincidencia'] != 'No Match')]
                        df = df.append(comparar, ignore_index=True)
                        # df = df[(df['coincidencia'] != 'No Match')]
        response3 = client.detect_faces(Image={"S3Object": {"Bucket": Bucket, "Name": sourceFile, }},
                                        Attributes=['ALL'])
        for faceDetail in response3['FaceDetails']:
            if faceDetail['Eyeglasses']['Value'] is True or faceDetail['Sunglasses']['Value'] is True:
                error = True
                comparar = {'cod': "400_Bad Quality_image", 'coincidencia': "Lentes"}
                df = df[(df['coincidencia'] != 'No Match')]
                df = df.append(comparar, ignore_index=True)
                # df = df[(df['coincidencia'] != 'No Match')]
        if not error:

            response = client.compare_faces(SimilarityThreshold=80,
                                            SourceImage={"S3Object": {"Bucket": Bucket, "Name": sourceFile, }},
                                            TargetImage={"S3Object": {"Bucket": Bucket, "Name": targetFile, }})

            for faceMatch in response['FaceMatches']:
                if int(faceMatch['Similarity']) >= puntos:
                    similarity = str(faceMatch['Similarity'])
                    nuevo_registro = {'cod': "200_OK", 'coincidencia': similarity + '% confidence'}
                    df = df.append(nuevo_registro, ignore_index=True)
                    df = df[(df['coincidencia'] != 'No Match')]
                # else:
                # nuevo_registro = {'cod': "400_Bad Quality_image", 'coincidencia': "No Match"}
                # df = df.append(nuevo_registro, ignore_index=True)
                # df = df[(df['coincidencia'] != 'No Match')]

        self.comparar = df
        return comparar

