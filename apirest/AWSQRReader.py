# -*- coding: utf-8 -*-
"""
QR Code Reader Service
Reads QR codes from images stored in S3 or uploaded directly
Supports multiple QR codes in a single image
"""

import boto3
import logging
from PIL import Image
import io
from decouple import config
from pyzbar import pyzbar
import cv2
import numpy as np

# Configure logger for QR operations
logger = logging.getLogger('apirest.qr')


class QRCodeReader:
    """
    Clase para leer códigos QR de imágenes
    Soporta lectura desde S3 o desde archivos subidos
    """
    
    def __init__(self):
        logger.info("Initializing QR Code Reader service")
        try:
            # Load AWS credentials from environment
            self.aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info(f"QR Reader configured - Region: {self.region_name}, Bucket: {self.bucket}")
            
        except Exception as e:
            logger.error(f"Error initializing QR Code Reader: {str(e)}")
            raise

    def read_qr_from_s3(self, filename):
        """
        Lee códigos QR de una imagen almacenada en S3
        
        Args:
            filename (str): Nombre del archivo en S3
            
        Returns:
            dict: Resultado con códigos QR detectados
        """
        logger.info(f"Reading QR codes from S3 file: {filename}")
        
        try:
            # Initialize S3 client
            s3_client = boto3.client('s3',
                                    aws_access_key_id=self.aws_access_key_id,
                                    aws_secret_access_key=self.aws_secret_access_key,
                                    region_name=self.region_name)
            
            # Download image from S3
            logger.debug(f"Downloading image from S3: {self.bucket}/{filename}")
            response = s3_client.get_object(Bucket=self.bucket, Key=filename)
            image_content = response['Body'].read()
            
            # Process image for QR detection
            result = self._process_qr_image(image_content, filename)
            
            return result
            
        except s3_client.exceptions.NoSuchKey:
            logger.error(f"File not found in S3: {filename}")
            return {
                'success': False,
                'error': f'File not found in S3: {filename}',
                'error_code': '404_File_Not_Found',
                'qr_codes': [],
                'metadata': {
                    'filename': filename,
                    'bucket': self.bucket,
                    'total_qr_codes': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading QR from S3: {str(e)}")
            return {
                'success': False,
                'error': f'Error reading QR from S3: {str(e)}',
                'error_code': '500_S3_Error',
                'qr_codes': [],
                'metadata': {
                    'filename': filename,
                    'bucket': self.bucket,
                    'total_qr_codes': 0
                }
            }

    def read_qr_from_upload(self, file_content, filename):
        """
        Lee códigos QR de un archivo subido directamente
        
        Args:
            file_content (bytes): Contenido del archivo
            filename (str): Nombre del archivo
            
        Returns:
            dict: Resultado con códigos QR detectados
        """
        logger.info(f"Reading QR codes from uploaded file: {filename}")
        
        try:
            # Process image for QR detection
            result = self._process_qr_image(file_content, filename)
            return result
            
        except Exception as e:
            logger.error(f"Error reading QR from upload: {str(e)}")
            return {
                'success': False,
                'error': f'Error reading QR from upload: {str(e)}',
                'error_code': '500_Processing_Error',
                'qr_codes': [],
                'metadata': {
                    'filename': filename,
                    'total_qr_codes': 0
                }
            }

    def _process_qr_image(self, image_content, filename):
        """
        Procesa una imagen para detectar códigos QR
        
        Args:
            image_content (bytes): Contenido de la imagen
            filename (str): Nombre del archivo
            
        Returns:
            dict: Resultado con códigos QR detectados
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            logger.debug(f"Image loaded - Size: {image.size}, Mode: {image.mode}")
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Detect QR codes using pyzbar
            qr_codes = pyzbar.decode(opencv_image)
            
            logger.info(f"Detected {len(qr_codes)} QR code(s) in image")
            
            # Process detected QR codes
            qr_results = []
            for index, qr in enumerate(qr_codes):
                qr_data = {
                    'index': index + 1,
                    'type': qr.type,
                    'data': qr.data.decode('utf-8'),
                    'raw_data': qr.data.hex(),
                    'quality': qr.quality if hasattr(qr, 'quality') else None,
                    'orientation': qr.orientation if hasattr(qr, 'orientation') else None,
                    'rect': {
                        'left': qr.rect.left,
                        'top': qr.rect.top,
                        'width': qr.rect.width,
                        'height': qr.rect.height
                    },
                    'polygon': [{'x': point.x, 'y': point.y} for point in qr.polygon]
                }
                qr_results.append(qr_data)
                logger.debug(f"QR Code {index + 1}: Type={qr.type}, Data={qr_data['data'][:50]}...")
            
            # Build response
            result = {
                'success': True,
                'error': None,
                'error_code': None,
                'qr_codes': qr_results,
                'metadata': {
                    'filename': filename,
                    'image_size': {
                        'width': image.size[0],
                        'height': image.size[1]
                    },
                    'image_mode': image.mode,
                    'total_qr_codes': len(qr_codes),
                    'processing_type': 'qr_code_detection'
                }
            }
            
            if len(qr_codes) == 0:
                logger.warning(f"No QR codes detected in image: {filename}")
                result['success'] = False
                result['error'] = 'No QR codes detected in image'
                result['error_code'] = '404_No_QR_Found'
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing QR image: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            return {
                'success': False,
                'error': f'Error processing image for QR detection: {str(e)}',
                'error_code': '500_Image_Processing_Error',
                'qr_codes': [],
                'metadata': {
                    'filename': filename,
                    'total_qr_codes': 0
                }
            }

    def read_qr_batch(self, file_list):
        """
        Lee códigos QR de múltiples archivos en S3
        
        Args:
            file_list (list): Lista de nombres de archivos en S3
            
        Returns:
            dict: Resultado con códigos QR de todos los archivos
        """
        logger.info(f"Reading QR codes from {len(file_list)} files")
        
        batch_result = {
            'success': True,
            'files_processed': len(file_list),
            'files_successful': 0,
            'files_failed': 0,
            'total_qr_codes': 0,
            'results': [],
            'errors': []
        }
        
        for filename in file_list:
            try:
                result = self.read_qr_from_s3(filename)
                
                if result['success']:
                    batch_result['files_successful'] += 1
                    batch_result['total_qr_codes'] += result['metadata']['total_qr_codes']
                else:
                    batch_result['files_failed'] += 1
                    batch_result['errors'].append({
                        'filename': filename,
                        'error': result['error'],
                        'error_code': result['error_code']
                    })
                
                batch_result['results'].append(result)
                
            except Exception as e:
                batch_result['files_failed'] += 1
                batch_result['errors'].append({
                    'filename': filename,
                    'error': str(e),
                    'error_code': '500_Unexpected_Error'
                })
                logger.error(f"Error processing {filename}: {str(e)}")
        
        batch_result['success'] = batch_result['files_failed'] == 0
        
        logger.info(f"Batch QR reading completed - Success: {batch_result['files_successful']}, "
                   f"Failed: {batch_result['files_failed']}, Total QR: {batch_result['total_qr_codes']}")
        
        return batch_result
