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
import json

# Configure logger for AWS OCR Raw operations
logger = logging.getLogger('apirest.ocr')

class consult45Raw:
    """
    Clase para OCR que devuelve la respuesta completa de AWS Rekognition
    sin procesamiento interno, para que sea procesada externamente
    """
    photo = ''
    photoviene = 'x'
    photova = ""
    response1 = ''
    
    def __init__(self):
        logger.info("Initializing consult45Raw class (Raw AWS Response)")
        try:
            # Initialize AWS credentials from environment
            self.aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY') 
            self.aws_session_token = config('AWS_SESSION_TOKEN', default=None)
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET')
            
            logger.info(f"AWS Raw OCR Config loaded - Region: {self.region_name}, Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Error loading AWS configuration for Raw OCR: {str(e)}")
            raise

    def detect_text_raw(self, photo, bucket):
        """
        Procesa la imagen con AWS Rekognition y devuelve la respuesta completa
        sin procesamiento interno
        """
        logger.info(f"Starting Raw OCR detection for photo: '{photo}' in bucket: '{bucket}'")
        logger.debug(f"Raw OCR method parameters - photo type: {type(photo)}, bucket type: {type(bucket)}")
        
        # Validate parameters
        if not photo or not isinstance(photo, str):
            logger.error(f"Invalid photo parameter in Raw OCR: '{photo}' (type: {type(photo)})")
            return {
                'success': False,
                'error': f'Invalid photo parameter: {photo}',
                'error_code': '400_Invalid_Parameters',
                'raw_response': None
            }
            
        if not bucket or not isinstance(bucket, str):
            logger.error(f"Invalid bucket parameter in Raw OCR: '{bucket}' (type: {type(bucket)})")
            return {
                'success': False,
                'error': f'Invalid bucket parameter: {bucket}',
                'error_code': '400_Invalid_Parameters',
                'raw_response': None
            }
        
        try:
            # Configurar cliente S3 con credenciales
            logger.debug("Configuring S3 client with credentials for Raw OCR")
            s3_client = boto3.client('s3',
                                    aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                    aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
                                    region_name=config('AWS_DEFAULT_REGION', default='us-east-1'))
            
            photoviene = 'x' + photo
            photova = 'xx' + photo
            
            logger.debug(f"Raw OCR generated temp filenames: {photoviene}, {photova}")
            
            # Verificar si el archivo existe en S3
            logger.debug(f"Raw OCR checking if file exists in S3: {bucket}/{photo}")
            s3_client.head_object(Bucket=bucket, Key=photo)
            logger.info(f"Raw OCR file found in S3, downloading: {bucket}/{photo}")
            
            # Descargar archivo desde S3
            s3_client.download_file(bucket, photo, photoviene)
            logger.info(f"Raw OCR successfully downloaded file to: {photoviene}")
            
        except Exception as e:
            logger.error(f"Raw OCR error accessing S3 file {bucket}/{photo}: {str(e)}")
            logger.error(f"Raw OCR exception type: {type(e).__name__}")
            
            return {
                'success': False,
                'error': f'No se pudo acceder al archivo en S3: {str(e)}',
                'error_code': '400_S3_Access_Error',
                'raw_response': None,
                'file_info': {
                    'photo': photo,
                    'bucket': bucket,
                    'full_path': f'{bucket}/{photo}'
                }
            }
        
        try:
            # Procesar imagen original sin modificaciones
            logger.debug(f"Raw OCR opening original image file: {photoviene}")
            image = Image.open(photoviene)
            ancho = image.size
            logger.debug(f"Raw OCR original image dimensions: {ancho}")
            
            # Usar la imagen original sin redimensionar ni rotar
            logger.debug("Raw OCR using original image without processing")
            with open(photoviene, 'rb') as image_file:
                image_binary = image_file.read()
            
            logger.info(f"Raw OCR using original image file: {photo} (no processing applied)")
                
        except Exception as e:
            logger.error(f"Raw OCR error processing image {photoviene}: {str(e)}")
            logger.error(f"Raw OCR exception type: {type(e).__name__}")
            
            return {
                'success': False,
                'error': f'Error procesando imagen: {str(e)}',
                'error_code': '400_Image_Processing_Error',
                'raw_response': None,
                'image_info': {
                    'photo': photo,
                    'temp_file': photoviene,
                    'original_dimensions': str(ancho) if 'ancho' in locals() else 'unknown'
                }
            }

        try:
            # Configurar cliente Rekognition con credenciales
            logger.debug("Raw OCR configuring AWS Rekognition client")
            rekognition_client = boto3.client('rekognition',
                                            aws_access_key_id=config('AWS_REKOGNITION_ACCESS_KEY_ID'),
                                            aws_secret_access_key=config('AWS_REKOGNITION_SECRET_ACCESS_KEY'),
                                            region_name=config('AWS_DEFAULT_REGION', default='us-east-1'))
            logger.debug("Raw OCR Rekognition client configured successfully")
        
        except Exception as e:
            logger.error(f"Raw OCR error configuring Rekognition client: {str(e)}")
            
            return {
                'success': False,
                'error': f'Error configurando cliente Rekognition: {str(e)}',
                'error_code': '500_AWS_Configuration_Error',
                'raw_response': None
            }
        
        try:
            # Llamar a AWS Rekognition
            logger.info("Raw OCR starting AWS Rekognition text detection")
            raw_response = rekognition_client.detect_text(Image={'Bytes': image_binary})
            logger.info(f"Raw OCR Rekognition response received with {len(raw_response.get('TextDetections', []))} text detections")
            
            # Limpiar archivos temporales (opcional)
            try:
                import os
                if os.path.exists(photoviene):
                    os.remove(photoviene)
                    logger.debug(f"Raw OCR cleaned up temporary file: {photoviene}")
            except Exception as cleanup_error:
                logger.warning(f"Raw OCR could not clean up temp file {photoviene}: {cleanup_error}")
            
            # Devolver respuesta completa
            result = {
                'success': True,
                'error': None,
                'error_code': None,
                'raw_response': raw_response,
                'metadata': {
                    'photo': photo,
                    'bucket': bucket,
                    'temp_files': {
                        'original': photoviene,
                        'processed': None  # No se procesó la imagen
                    },
                    'image_dimensions': {
                        'original': ancho,
                        'processing_applied': False
                    },
                    'text_detections_count': len(raw_response.get('TextDetections', [])),
                    'processing_type': 'raw_response_original_image'
                }
            }
            
            logger.info(f"Raw OCR processing completed successfully for {photo}")
            return result
            
        except Exception as e:
            logger.error(f"Raw OCR error with Rekognition text detection: {str(e)}")
            logger.error(f"Raw OCR exception type: {type(e).__name__}")
            
            return {
                'success': False,
                'error': f'Error en AWS Rekognition: {str(e)}',
                'error_code': '500_Rekognition_Error',
                'raw_response': None,
                'debug_info': {
                    'photo': photo,
                    'bucket': bucket,
                    'image_binary_size': len(image_binary) if 'image_binary' in locals() else 0
                }
            }

    def get_processing_info(self):
        """
        Devuelve información sobre la configuración actual del procesador
        """
        return {
            'processor_type': 'Raw OCR Response',
            'version': '1.0',
            'aws_region': self.region_name,
            'aws_bucket': self.bucket_name,
            'processing_mode': 'raw_response',
            'description': 'Returns complete AWS Rekognition response without internal processing'
        }
