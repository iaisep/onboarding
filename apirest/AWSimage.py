import boto3
import pandas as pd
from decouple import config
from apirest.models import puntaje_face
import logging

# Configure logger for AWS Image operations
logger = logging.getLogger('apirest.image')

class consult47:


    source_file = ''
    target_file = ''
    error = ''
    def __init__(self):
        logger.info("Initializing AWS Image Validation service (consult47)")
        try:
            # Load AWS credentials from environment
            self.aws_access_key_id = config('AWS_REKOGNITION_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_REKOGNITION_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket = config('AWS_S3_IMAGE_BUCKET', default=config('AWS_S3_BUCKET'))
            
            logger.info(f"AWS Image service configured - Region: {self.region_name}, Bucket: {self.bucket}")
            
        except Exception as e:
            logger.error(f"Error initializing AWS Image Validation: {str(e)}")
            raise

    def compare_faces(self, sourceFile):
        logger.info(f"Starting optimized image validation for: {sourceFile}")
        
        try:
            # Initialize Rekognition client
            logger.debug("Configuring AWS Rekognition client")
            client = boto3.client('rekognition',
                                  aws_access_key_id=self.aws_access_key_id,
                                  aws_secret_access_key=self.aws_secret_access_key,
                                  region_name=self.region_name)

            # Initialize response dataframe
            indices = [0]
            comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "No Match"}
            
            logger.debug("Fetching validation threshold from database")
            puntos = int(puntaje_face.objects.get(pk=1).puntaje_Max)
            logger.debug(f"Image validation threshold: {puntos}")
            
            df = pd.DataFrame(data=comparar, index=indices)
            error = False

            # OPTIMIZACIÓN: Usar imagen directamente del bucket S3 sin descargar
            logger.info(f"Processing image directly from S3 bucket: {self.bucket}/{sourceFile}")
            
            # 1. Detectar equipos de protección (mascarillas) usando S3Object
            logger.debug("Checking for face masks and protective equipment")
            response2 = client.detect_protective_equipment(
                Image={"S3Object": {"Bucket": self.bucket, "Name": sourceFile}},
                SummarizationAttributes={
                    'MinConfidence': 20,
                    'RequiredEquipmentTypes': ['FACE_COVER']
                }
            )

            # Verificar si hay personas detectadas
            if len(response2['Persons']) < 1:
                logger.warning(f"No persons detected in image: {sourceFile}")
                comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "no es una Selfie válida"}
                df = df[(df['coincidencia'] != 'No Match')]
                df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)
                error = True
            else:
                # Verificar mascarillas en personas detectadas
                for person in response2['Persons']:
                    for body_part in person['BodyParts']:
                        ppe_items = body_part['EquipmentDetections']
                        for ppe_item in ppe_items:
                            if (ppe_item['Type'] == 'FACE_COVER' and 
                                ppe_item['CoversBodyPart']['Value'] is True and 
                                ppe_item['Confidence'] > 95):
                                logger.warning(f"Face mask detected in {sourceFile} with confidence {ppe_item['Confidence']}%")
                                error = True
                                comparar = {'cod': "400_Bad_Quality_image", 'coincidencia': "No debe usar mascarillas en la selfie"}
                                df = df[(df['coincidencia'] != 'No Match')]
                                df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)
                                break

                # 2. Detectar características faciales y calidad usando S3Object
                logger.debug("Analyzing face details and image quality")
                response3 = client.detect_faces(
                    Image={"S3Object": {"Bucket": self.bucket, "Name": sourceFile}},
                    Attributes=['ALL']
                )
                
                for faceDetail in response3['FaceDetails']:
                    has_eyewear = faceDetail['Eyeglasses']['Value'] or faceDetail['Sunglasses']['Value']
                    low_brightness = faceDetail['Quality']['Brightness'] < 40
                    low_confidence = faceDetail['Confidence'] < 95
                    
                    if has_eyewear or low_brightness or low_confidence:
                        error = True
                        
                        if low_brightness:
                            logger.warning(f"Low brightness detected: {faceDetail['Quality']['Brightness']}")
                            comparar = {'cod': "400_Bad_Quality_image",
                                      'coincidencia': "Tome a selfie en un lugar mas iluminado"}
                        elif low_confidence:
                            logger.warning(f"Low face confidence: {faceDetail['Confidence']}%")
                            comparar = {'cod': "400_Bad_Quality_image", 
                                      'coincidencia': "debe ser una foto de un rostro"}
                        else:  # has_eyewear
                            logger.warning("Eyewear detected in selfie")
                            comparar = {'cod': "400_Bad_Quality_image", 
                                      'coincidencia': "No se acepta Selfie con Lentes"}
                        
                        df = df[(df['coincidencia'] != 'No Match')]
                        df = pd.concat([df, pd.DataFrame([comparar])], ignore_index=True)
                        break

            # 3. Si no hay errores, marcar como válida
            if not error:
                logger.info(f"Image validation successful for: {sourceFile}")
                nuevo_registro = {'cod': "200_OK", 'coincidencia': 'Selfie Sin Error'}
                df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                df = df[(df['coincidencia'] != 'No Match')]

            # Limpiar DataFrame final
            self.comparar = df
            logger.info(f"Image validation completed - Result: {df.iloc[-1]['coincidencia'] if not df.empty else 'No results'}")
            
            return comparar

        except Exception as e:
            logger.error(f"Error in optimized image validation: {str(e)}")
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
