import boto3
import pandas as pd
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
        logger.info(f"Starting optimized face comparison - Source: {sourceFile}, Target: {targetFile}")
        
        try:
            # Get AWS credentials from environment variables
            logger.debug("Loading AWS Rekognition credentials")
            aws_access_key_id = config('AWS_REKOGNITION_ACCESS_KEY_ID')
            aws_secret_access_key = config('AWS_REKOGNITION_SECRET_ACCESS_KEY')
            region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            bucket = config('AWS_S3_FACE_BUCKET', default=config('AWS_S3_BUCKET'))
            
            logger.debug(f"Configuring Rekognition client for region: {region_name}, bucket: {bucket}")
            
            # Initialize Rekognition client
            client = boto3.client('rekognition',
                                  aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key,
                                  region_name=region_name)
            
            # Initialize response dataframe
            indices = [0]
            comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "No Match"}
            
            logger.debug("Fetching face comparison threshold from database")
            puntos = int(puntaje_face.objects.get(pk=1).puntaje_Max)
            logger.debug(f"Face comparison threshold: {puntos}")
            
            df = pd.DataFrame(data=comparar, index=indices)
            error = False

            # OPTIMIZACIÓN: Usar imágenes directamente del bucket S3 sin descargar
            logger.info("Processing images directly from S3 bucket (no local downloads)")
            
            # 1. Detectar equipos de protección (mascarillas) usando S3Object
            logger.debug(f"Checking for face masks in source image: {sourceFile}")
            response2 = client.detect_protective_equipment(
                Image={"S3Object": {"Bucket": bucket, "Name": sourceFile}},
                SummarizationAttributes={
                    'MinConfidence': 80,
                    'RequiredEquipmentTypes': ['FACE_COVER']
                }
            )

            # Verificar si hay mascarillas
            for person in response2['Persons']:
                for body_part in person['BodyParts']:
                    ppe_items = body_part['EquipmentDetections']
                    for ppe_item in ppe_items:
                        if ppe_item['Type'] == 'FACE_COVER' and ppe_item['CoversBodyPart']['Value'] is True:
                            logger.warning(f"Face mask detected in {sourceFile}")
                            error = True
                            comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "Mascarillas"}
                            df = df[(df['coincidencia'] != 'No Match')]
                            df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)
                            break

            # 2. Detectar accesorios faciales (lentes) usando S3Object
            logger.debug(f"Checking for eyewear in source image: {sourceFile}")
            response3 = client.detect_faces(
                Image={"S3Object": {"Bucket": bucket, "Name": sourceFile}},
                Attributes=['ALL']
            )
            
            for faceDetail in response3['FaceDetails']:
                if faceDetail['Eyeglasses']['Value'] is True or faceDetail['Sunglasses']['Value'] is True:
                    logger.warning(f"Eyewear detected in {sourceFile}")
                    error = True
                    comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "Lentes"}
                    df = df[(df['coincidencia'] != 'No Match')]
                    df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)
                    break

            # 3. Si no hay errores, realizar comparación facial usando S3Objects
            if not error:
                logger.info(f"Performing face comparison between {sourceFile} and {targetFile}")
                response = client.compare_faces(
                    SimilarityThreshold=80,
                    SourceImage={"S3Object": {"Bucket": bucket, "Name": sourceFile}},
                    TargetImage={"S3Object": {"Bucket": bucket, "Name": targetFile}}
                )

                # Procesar resultados de comparación
                matches_found = False
                for faceMatch in response['FaceMatches']:
                    similarity = faceMatch['Similarity']
                    logger.debug(f"Face match found with {similarity}% similarity")
                    
                    if int(similarity) >= puntos:
                        logger.info(f"Face match above threshold: {similarity}% >= {puntos}%")
                        nuevo_registro = {'cod': "200_OK", 'coincidencia': f"{similarity:.2f}% confidence"}
                        df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                        df = df[(df['coincidencia'] != 'No Match')]
                        matches_found = True
                        break

                if not matches_found:
                    logger.info("No face matches found above threshold")
                    # Mantener el resultado "No Match" original
            
            # Limpiar DataFrame final
            self.comparar = df
            logger.info(f"Face comparison completed - Final result: {df.iloc[-1]['coincidencia'] if not df.empty else 'No results'}")
            
            return comparar

        except Exception as e:
            logger.error(f"Error in optimized face comparison: {str(e)}")
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

