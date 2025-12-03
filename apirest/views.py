from __future__ import unicode_literals
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from apirest.serializers import llegaSerializer2, llegafaceSerializer2, FileUploadSerializer, TextractAnalysisSerializer, BatchOCRSerializer, QRCodeSerializer, QRCodeBatchSerializer
from django.http import HttpResponse
from .codeorm import consult2
from .AWSocr import consult45
from .AWSocrRaw import consult45Raw
from .AWScompare import consult46
from .AWSUpload import FileUploadS3
from .AWSTextract import TextractIDAnalyzer
from .AWSQRReader import QRCodeReader
from .AWSTextractBirthCertificate import TextractBirthCertificateAnalyzer
from .AWSTextractPassport import TextractPassportAnalyzer
from .AWSTextractCertificado import TextractCertificadoAnalyzer
from .AWSTextractTitulo import TextractUniversityTitleAnalyzer
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging
from decouple import config

# Configure logger for API views
logger = logging.getLogger('apirest.aws')

@api_view(['GET'])
def health_check(request):
    """Endpoint de salud para verificar que la API funciona"""
    logger.info("Health check endpoint accessed")
    return Response({
        'status': 'OK',
        'message': 'API funcionando correctamente',
        'timestamp': str(timezone.now())
    })

@api_view(['POST'])
def login(request):
    username=request.POST.get('username')
    password = request.POST.get('password')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response('usuario Invalido')

    pwd_valid = check_password(password,user.password)
    if not pwd_valid:
        return Response('PSS invalido')
    token, created = Token.objects.get_or_create(user=user)

    return Response(token.key)









class restric(generics.CreateAPIView):
    serializer_class = llegaSerializer2
    #permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        serializer = llegaSerializer2(data=request.data)
        if serializer.is_valid():
            serializer.save()
            str1 = serializer.data.get("string_income")
            """llamo a la clase code()"""
            index2 = consult2()
            index2.comparar(str1)
            """recibo los datos en sancionados y los mando a un diccionario"""
            df_dicts = index2.sancionados.T.to_dict().values()
            """obtengo la longitud del diccionario"""
            lendic = len(df_dicts)
            if lendic == 0:
                return Response('200_OK_no results found', status=status.HTTP_200_OK, )
                #return Response('{success_: True} , status=status.HTTP_201_CREATED -no results found')
            return Response(df_dicts, status=status.HTTP_200_OK,)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#------------desde aqui las consultas a Face AWS

class ocr2(generics.CreateAPIView):
    serializer_class = llegafaceSerializer2
    #permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        logger.info("OCR endpoint accessed")
        logger.debug(f"Request data keys: {list(request.data.keys())}")
        
        serializer = llegafaceSerializer2(data=request.data)
        if serializer.is_valid():
            logger.debug("Serializer validation successful")
            serializer.save()
            str1 = serializer.data.get("faceselfie")
            str2 = serializer.data.get("ocrident")
            
            logger.info(f"Processing OCR request - faceselfie: {str1}, ocrident: {str2}")
            
            # Log detailed parameter analysis
            logger.debug(f"Parameter analysis:")
            logger.debug(f"  str1 (faceselfie): '{str1}' - appears to be: {'image file' if str1 and '.' in str1 else 'not a file'}")
            logger.debug(f"  str2 (ocrident): '{str2}' - appears to be: {'image file' if str2 and '.' in str2 else 'not a file'}")
            
            # Determine correct parameters for OCR
            # OCR needs: photo filename, bucket name
            # It seems the parameters might be mixed up, let's use the one that looks like a filename
            if str1 and '.' in str1 and str1.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_file = str1
                logger.debug(f"Using str1 as photo file: {photo_file}")
            elif str2 and '.' in str2 and str2.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_file = str2  
                logger.debug(f"Using str2 as photo file: {photo_file}")
            else:
                logger.error(f"Neither parameter looks like an image file: str1='{str1}', str2='{str2}'")
                return Response({'error': f'No valid image file found in parameters: faceselfie={str1}, ocrident={str2}'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            """llamo a la clase """
            try:
                logger.debug("Initializing consult45 OCR class")
                index2 = consult45()
                
                logger.debug("Calling detect_text method")
                # Use bucket from environment variables instead of hardcoded value
                bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                logger.debug(f"Using bucket from config: {bucket_name}")
                logger.info(f"Calling OCR with photo='{photo_file}' and bucket='{bucket_name}'")
                index2.detect_text(photo_file, bucket_name)
                
                logger.debug("OCR processing completed, checking for sancionados attribute")
                if not hasattr(index2, 'sancionados'):
                    logger.error("OCR class does not have 'sancionados' attribute after processing")
                    return Response({'error': 'OCR processing failed - no results generated'}, 
                                  status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                logger.debug("Converting OCR results to dictionary format")
                df_dicts = index2.sancionados.T.to_dict().values()
                lendic = len(df_dicts)
                
                logger.info(f"OCR processing completed - {lendic} results found")
                
                if lendic == 0:
                    logger.warning("No OCR results found")
                    return Response('200_OK_no results found', status=status.HTTP_200_OK)
                
                logger.info("Returning OCR results successfully")
                return Response(df_dicts, status=status.HTTP_200_OK)
                
            except AttributeError as e:
                logger.error(f"AttributeError in OCR processing: {str(e)}")
                return Response({'error': f'OCR processing error: {str(e)}'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Unexpected error in OCR processing: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                return Response({'error': f'Unexpected OCR error: {str(e)}'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Compare3(generics.CreateAPIView):
        serializer_class = llegafaceSerializer2
        #permission_classes = [IsAuthenticated]
        def post(self, request, format=None):
            logger.info("Face comparison endpoint accessed")
            logger.debug(f"Request data keys: {list(request.data.keys())}")
            
            serializer = llegafaceSerializer2(data=request.data)
            if serializer.is_valid():
                logger.debug("Serializer validation successful for face comparison")
                serializer.save()
                str1 = serializer.data.get("faceselfie")
                str2 = serializer.data.get("ocrident")
                
                logger.info(f"Processing face comparison - faceselfie: {str1}, ocrident: {str2}")
                
                """llamo a la clase """
                try:
                    logger.debug("Initializing consult46 face comparison class")
                    index3 = consult46()
                    
                    logger.debug("Calling compare_faces method")
                    index3.compare_faces(str1, str2)
                    
                    logger.debug("Face comparison completed, processing results")
                    """recibo los datos en sancionados y los mando a un diccionario"""
                    df_dicts = index3.comparar.T.to_dict().values()

                    """obtengo la longitud del diccionario"""
                    lendic = len(df_dicts)
                    logger.info(f"Face comparison completed - {lendic} results found")
                    
                except Exception as e:
                    logger.error(f"Error in face comparison: {str(e)}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    return Response({'error': f'Face comparison error: {str(e)}'}, 
                                  status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                if lendic == 0:
                    return HttpResponse('{success_: True} , status.HTTP_200_OK -no results found')
                return Response(df_dicts, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ocrRaw(generics.CreateAPIView):
    """
    Endpoint para OCR que devuelve la respuesta completa de AWS Rekognition
    sin procesamiento interno, ideal para análisis detallado
    """
    serializer_class = llegafaceSerializer2
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("OCR Raw endpoint accessed")
        logger.debug(f"Raw OCR request data keys: {list(request.data.keys())}")
        
        serializer = llegafaceSerializer2(data=request.data)
        if serializer.is_valid():
            logger.debug("Serializer validation successful for Raw OCR")
            serializer.save()
            str1 = serializer.data.get("faceselfie")
            str2 = serializer.data.get("ocrident")
            
            logger.info(f"Processing Raw OCR request - faceselfie: {str1}, ocrident: {str2}")
            
            # Log detailed parameter analysis
            logger.debug(f"Raw OCR parameter analysis:")
            logger.debug(f"  str1 (faceselfie): '{str1}' - appears to be: {'image file' if str1 and '.' in str1 else 'not a file'}")
            logger.debug(f"  str2 (ocrident): '{str2}' - appears to be: {'image file' if str2 and '.' in str2 else 'not a file'}")
            
            # Determine correct parameters for OCR
            # OCR needs: photo filename, bucket name
            if str1 and '.' in str1 and str1.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_file = str1
                logger.debug(f"Raw OCR using str1 as photo file: {photo_file}")
            elif str2 and '.' in str2 and str2.lower().endswith(('.jpg', '.jpeg', '.png')):
                photo_file = str2  
                logger.debug(f"Raw OCR using str2 as photo file: {photo_file}")
            else:
                logger.error(f"Raw OCR: Neither parameter looks like an image file: str1='{str1}', str2='{str2}'")
                return Response({
                    'success': False,
                    'error': f'No valid image file found in parameters: faceselfie={str1}, ocrident={str2}',
                    'error_code': '400_Invalid_Image_Parameters',
                    'raw_response': None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.debug("Initializing consult45Raw OCR class")
                raw_ocr = consult45Raw()
                
                # Get bucket name from environment variables
                bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                logger.debug(f"Raw OCR using bucket from config: {bucket_name}")
                logger.info(f"Calling Raw OCR with photo='{photo_file}' and bucket='{bucket_name}'")
                
                # Call the raw OCR method that returns complete AWS response
                result = raw_ocr.detect_text_raw(photo_file, bucket_name)
                
                logger.info(f"Raw OCR processing completed - Success: {result.get('success', False)}")
                
                if result.get('success'):
                    logger.info("Raw OCR successful - returning complete AWS response")
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Raw OCR failed: {result.get('error', 'Unknown error')}")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Raw OCR processing: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'error': f'Unexpected Raw OCR error: {str(e)}',
                    'error_code': '500_Unexpected_Error',
                    'raw_response': None,
                    'debug_info': {
                        'photo_file': photo_file if 'photo_file' in locals() else 'unknown',
                        'exception_type': type(e).__name__
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Raw OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Invalid request data',
                'error_code': '400_Validation_Error',
                'validation_errors': serializer.errors,
                'raw_response': None
            }, status=status.HTTP_400_BAD_REQUEST)


class FileUploadView(generics.CreateAPIView):
    """
    Endpoint para subir archivos a S3 con conversión automática
    Acepta: PDF, DOCX, DOC, JPG, JPEG, PNG, BMP, TIFF
    Convierte documentos a imágenes JPG de alta calidad
    """
    serializer_class = FileUploadSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("File upload endpoint accessed")
        logger.debug(f"Upload request files: {list(request.FILES.keys())}")
        
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("File upload serializer validation successful")
            
            try:
                # Get uploaded file
                uploaded_file = serializer.validated_data['file']
                filename = uploaded_file.name
                file_content = uploaded_file.read()
                
                logger.info(f"Processing file upload - Name: {filename}, Size: {len(file_content)} bytes")
                logger.debug(f"File details - Content type: {uploaded_file.content_type}, Size: {uploaded_file.size}")
                
                # Initialize file upload handler
                logger.debug("Initializing FileUploadS3 class")
                uploader = FileUploadS3()
                
                # Upload file with automatic conversion
                logger.info(f"Starting upload process for: {filename}")
                result = uploader.upload_file(file_content, filename)
                
                logger.info(f"Upload process completed - Success: {result.get('success', False)}")
                
                if result.get('success'):
                    uploaded_files = result.get('uploaded_files', [])
                    logger.info(f"Upload successful - {len(uploaded_files)} files uploaded to S3")
                    
                    # Log each uploaded file
                    for file_info in uploaded_files:
                        logger.info(f"Uploaded: {file_info['s3_filename']} ({file_info['size']} bytes)")
                    
                    return Response(result, status=status.HTTP_201_CREATED)
                else:
                    logger.error(f"Upload failed: {result.get('error', 'Unknown error')}")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in file upload: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'error': f'Unexpected upload error: {str(e)}',
                    'error_code': '500_Upload_Unexpected_Error',
                    'uploaded_files': [],
                    'metadata': {
                        'filename': filename if 'filename' in locals() else 'unknown',
                        'exception_type': type(e).__name__
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"File upload serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Invalid file upload data',
                'error_code': '400_Upload_Validation_Error',
                'validation_errors': serializer.errors,
                'uploaded_files': []
            }, status=status.HTTP_400_BAD_REQUEST)


class TextractIDAnalysisView(generics.CreateAPIView):
    """
    Endpoint para análisis de documentos de identidad con AWS Textract
    Utiliza la función analyze_id optimizada para cédulas, pasaportes, licencias
    """
    serializer_class = TextractAnalysisSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Textract ID Analysis endpoint accessed")
        logger.debug(f"Textract ID request data: {request.data}")
        
        serializer = TextractAnalysisSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Textract ID serializer validation successful")
            
            try:
                # Get validated data
                document_name = serializer.validated_data['document_name']
                analysis_type = serializer.validated_data.get('analysis_type', 'id_document')
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                logger.info(f"Processing Textract ID analysis - Document: {document_name}, Type: {analysis_type}")
                logger.debug(f"Bucket: {bucket_name or 'default bucket'}")
                
                # Initialize Textract analyzer
                logger.debug("Initializing TextractIDAnalyzer")
                analyzer = TextractIDAnalyzer()
                
                # Perform analysis based on type
                if analysis_type == 'id_document':
                    logger.info("Performing ID document analysis with analyze_id")
                    result = analyzer.analyze_id_document(document_name, bucket_name)
                else:
                    logger.info("Performing general document analysis with detect_document_text")
                    result = analyzer.analyze_general_document(document_name, bucket_name)
                
                logger.info(f"Textract analysis completed - Success: {result.get('success', False)}")
                
                if result.get('success'):
                    # Add DataFrame results for consistency with other endpoints
                    if hasattr(analyzer, 'extracted_data') and not analyzer.extracted_data.empty:
                        df_dicts = analyzer.extracted_data.T.to_dict().values()
                        result['dataframe_results'] = list(df_dicts)
                        logger.info(f"Added DataFrame results: {len(result['dataframe_results'])} records")
                    else:
                        result['dataframe_results'] = []
                        logger.info("No DataFrame results available")
                    
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Textract analysis failed: {result.get('error', 'Unknown error')}")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Textract ID analysis: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'error': f'Unexpected Textract error: {str(e)}',
                    'error_code': '500_Textract_Unexpected_Error',
                    'document_name': document_name if 'document_name' in locals() else 'unknown',
                    'extracted_fields': [],
                    'raw_response': None
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Textract ID serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Invalid request data for Textract analysis',
                'error_code': '400_Textract_Validation_Error',
                'validation_errors': serializer.errors,
                'extracted_fields': []
            }, status=status.HTTP_400_BAD_REQUEST)


class TextractGeneralAnalysisView(generics.CreateAPIView):
    """
    Endpoint para análisis general de documentos con AWS Textract
    Utiliza detect_document_text para extraer todo el texto de cualquier documento
    """
    serializer_class = TextractAnalysisSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Textract General Analysis endpoint accessed")
        logger.debug(f"Textract General request data: {request.data}")
        
        serializer = TextractAnalysisSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Textract General serializer validation successful")
            
            try:
                # Get validated data
                document_name = serializer.validated_data['document_name']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                logger.info(f"Processing Textract general analysis - Document: {document_name}")
                logger.debug(f"Bucket: {bucket_name or 'default bucket'}")
                
                # Initialize Textract analyzer
                logger.debug("Initializing TextractIDAnalyzer for general analysis")
                analyzer = TextractIDAnalyzer()
                
                # Perform general document analysis
                logger.info("Performing general document analysis with detect_document_text")
                result = analyzer.analyze_general_document(document_name, bucket_name)
                
                logger.info(f"Textract general analysis completed - Success: {result.get('success', False)}")
                
                if result.get('success'):
                    # Add DataFrame results for consistency
                    if hasattr(analyzer, 'extracted_data') and not analyzer.extracted_data.empty:
                        df_dicts = analyzer.extracted_data.T.to_dict().values()
                        result['dataframe_results'] = list(df_dicts)
                        logger.info(f"Added DataFrame results: {len(result['dataframe_results'])} records")
                    else:
                        result['dataframe_results'] = []
                        logger.info("No DataFrame results available")
                    
                    # Add summary statistics
                    result['analysis_summary'] = {
                        'total_text_blocks': result.get('total_blocks', 0),
                        'total_lines': result.get('total_lines', 0),
                        'total_words': result.get('total_words', 0),
                        'full_text_length': len(result.get('full_text', '')),
                        'document_type': 'general_document'
                    }
                    
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Textract general analysis failed: {result.get('error', 'Unknown error')}")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Textract general analysis: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'error': f'Unexpected Textract error: {str(e)}',
                    'error_code': '500_Textract_General_Unexpected_Error',
                    'document_name': document_name if 'document_name' in locals() else 'unknown',
                    'text_blocks': [],
                    'full_text': '',
                    'raw_response': None
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Textract General serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Invalid request data for Textract general analysis',
                'error_code': '400_Textract_General_Validation_Error',
                'validation_errors': serializer.errors,
                'text_blocks': [],
                'full_text': ''
            }, status=status.HTTP_400_BAD_REQUEST)


class BatchOCRRawView(generics.CreateAPIView):
    """
    Endpoint para procesamiento batch de OCR Raw
    Procesa múltiples archivos de forma secuencial y devuelve resultado combinado
    Ideal para PDFs divididos en páginas o lotes de imágenes
    """
    serializer_class = BatchOCRSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch Raw OCR endpoint accessed")
        logger.debug(f"Batch request data: {request.data}")
        
        serializer = BatchOCRSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Batch OCR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing batch OCR for {len(file_list)} files in bucket: {bucket_name}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize batch processor
                logger.debug("Initializing consult45Raw for batch processing")
                processor = consult45Raw()
                
                # Process files in batch
                logger.info("Starting batch OCR processing")
                result = processor.detect_text_batch(file_list, bucket_name)
                
                logger.info(f"Batch OCR completed - Success: {result['success']}, "
                          f"Processed: {result['files_processed']}, "
                          f"Successful: {result['files_successful']}, "
                          f"Failed: {result['files_failed']}")
                
                # Determine response status based on results
                if result['success']:
                    # All files processed successfully
                    logger.info("All files processed successfully")
                    return Response(result, status=status.HTTP_200_OK)
                elif result['files_successful'] > 0:
                    # Some files processed successfully, some failed
                    logger.warning(f"Partial success: {result['files_failed']} files failed")
                    return Response(result, status=status.HTTP_207_MULTI_STATUS)
                else:
                    # All files failed
                    logger.error("All files failed to process")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Batch OCR endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'error': f'Unexpected batch processing error: {str(e)}',
                    'error_code': '500_Batch_OCR_Unexpected_Error',
                    'combined_response': {
                        'TextDetections': [],
                        'BatchMetadata': []
                    },
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Batch_OCR_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }],
                    'metadata': {
                        'processing_type': 'batch_raw_ocr',
                        'total_text_detections': 0,
                        'bucket': bucket_name if 'bucket_name' in locals() else 'unknown'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Batch OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'error': 'Invalid request data for batch OCR processing',
                'error_code': '400_Batch_OCR_Validation_Error',
                'validation_errors': serializer.errors,
                'combined_response': {
                    'TextDetections': [],
                    'BatchMetadata': []
                },
                'errors': [],
                'metadata': {
                    'processing_type': 'batch_raw_ocr',
                    'total_text_detections': 0
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class QRCodeReaderView(generics.CreateAPIView):
    """
    Endpoint para leer códigos QR de imágenes en S3
    Lee códigos QR y devuelve los datos decodificados en JSON
    """
    serializer_class = QRCodeSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("QR Code Reader endpoint accessed")
        logger.debug(f"QR request data: {request.data}")
        
        serializer = QRCodeSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("QR Code serializer validation successful")
            
            try:
                # Get validated data
                filename = serializer.validated_data['filename']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Reading QR codes from file: {filename} in bucket: {bucket_name}")
                
                # Initialize QR reader
                logger.debug("Initializing QRCodeReader")
                qr_reader = QRCodeReader()
                
                # Read QR codes
                logger.info("Starting QR code detection")
                result = qr_reader.read_qr_from_s3(filename)
                
                logger.info(f"QR reading completed - Success: {result['success']}, "
                          f"QR Codes found: {result['metadata']['total_qr_codes']}")
                
                # Determine response status based on results
                if result['success']:
                    logger.info(f"QR codes detected successfully: {result['metadata']['total_qr_codes']} code(s)")
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"QR reading failed: {result['error']}")
                    return Response(result, status=status.HTTP_404_NOT_FOUND if '404' in result['error_code'] else status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in QR Reader endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'error': f'Unexpected QR reading error: {str(e)}',
                    'error_code': '500_QR_Unexpected_Error',
                    'qr_codes': [],
                    'metadata': {
                        'filename': serializer.validated_data.get('filename', 'unknown'),
                        'total_qr_codes': 0,
                        'processing_type': 'qr_code_detection'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"QR Code serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Invalid request data for QR code reading',
                'error_code': '400_QR_Validation_Error',
                'validation_errors': serializer.errors,
                'qr_codes': [],
                'metadata': {
                    'total_qr_codes': 0,
                    'processing_type': 'qr_code_detection'
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class QRCodeBatchView(generics.CreateAPIView):
    """
    Endpoint para leer códigos QR de múltiples imágenes en batch
    Procesa múltiples archivos y devuelve todos los códigos QR encontrados
    """
    serializer_class = QRCodeBatchSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch QR Code Reader endpoint accessed")
        logger.debug(f"Batch QR request data: {request.data}")
        
        serializer = QRCodeBatchSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Batch QR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing batch QR reading for {len(file_list)} files in bucket: {bucket_name}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize QR reader
                logger.debug("Initializing QRCodeReader for batch processing")
                qr_reader = QRCodeReader()
                
                # Process files in batch
                logger.info("Starting batch QR code detection")
                result = qr_reader.read_qr_batch(file_list)
                
                logger.info(f"Batch QR reading completed - Success: {result['success']}, "
                          f"Processed: {result['files_processed']}, "
                          f"Successful: {result['files_successful']}, "
                          f"Failed: {result['files_failed']}, "
                          f"Total QR Codes: {result['total_qr_codes']}")
                
                # Determine response status
                if result['success']:
                    logger.info("All files processed successfully")
                    return Response(result, status=status.HTTP_200_OK)
                elif result['files_successful'] > 0:
                    logger.warning(f"Partial success: {result['files_failed']} files failed")
                    return Response(result, status=status.HTTP_207_MULTI_STATUS)
                else:
                    logger.error("All files failed to process")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Batch QR Reader endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'total_qr_codes': 0,
                    'error': f'Unexpected batch QR reading error: {str(e)}',
                    'error_code': '500_Batch_QR_Unexpected_Error',
                    'results': [],
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Batch_QR_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }]
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Batch QR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'total_qr_codes': 0,
                'error': 'Invalid request data for batch QR reading',
                'error_code': '400_Batch_QR_Validation_Error',
                'validation_errors': serializer.errors,
                'results': [],
                'errors': []
            }, status=status.HTTP_400_BAD_REQUEST)


class BatchBirthCertificateOCRView(generics.CreateAPIView):
    """
    Endpoint especializado para procesamiento OCR de Actas de Nacimiento (Birth Certificates)
    
    Utiliza AWS Textract detect_document_text con preprocesamiento de imagen optimizado
    para mejor reconocimiento de texto en documentos oficiales mexicanos.
    
    Este endpoint está diseñado específicamente para actas de nacimiento y proporciona:
    - Preprocesamiento de imagen (contraste, nitidez, etc.)
    - Mayor precisión en documentos oficiales
    - Compresión adaptativa para cumplir límites de Textract
    
    Request body:
    {
        "file_list": ["archivo1.jpg", "archivo2.jpg"],  # Lista de archivos en S3
        "bucket_name": "nombre-bucket",                  # Opcional, usa default si no se especifica
        "preprocess": true                               # Opcional, default true
    }
    """
    serializer_class = BatchOCRSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch Birth Certificate OCR endpoint accessed (Textract)")
        logger.debug(f"Birth Certificate request data: {request.data}")
        
        serializer = BatchOCRSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Birth Certificate OCR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Get optional preprocess flag (default to True for birth certificates)
                preprocess = request.data.get('preprocess', True)
                if isinstance(preprocess, str):
                    preprocess = preprocess.lower() in ('true', '1', 'yes')
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing birth certificate OCR for {len(file_list)} files "
                          f"in bucket: {bucket_name}, preprocess: {preprocess}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize birth certificate processor
                logger.debug("Initializing TextractBirthCertificateAnalyzer for batch processing")
                processor = TextractBirthCertificateAnalyzer()
                
                # Process files in batch using Textract
                logger.info("Starting batch birth certificate OCR processing with Textract")
                result = processor.analyze_birth_certificate_batch(
                    file_list, 
                    bucket_name, 
                    preprocess=preprocess
                )
                
                logger.info(f"Birth Certificate OCR completed - Success: {result['success']}, "
                          f"Processed: {result['files_processed']}, "
                          f"Successful: {result['files_successful']}, "
                          f"Failed: {result['files_failed']}, "
                          f"Avg Confidence: {result['metadata'].get('average_confidence', 0)}%")
                
                # Determine response status based on results
                if result['success']:
                    # All files processed successfully
                    logger.info("All birth certificate files processed successfully")
                    return Response(result, status=status.HTTP_200_OK)
                elif result['files_successful'] > 0:
                    # Some files processed successfully, some failed
                    logger.warning(f"Partial birth certificate success: {result['files_failed']} files failed")
                    return Response(result, status=status.HTTP_207_MULTI_STATUS)
                else:
                    # All files failed
                    logger.error("All birth certificate files failed to process")
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Birth Certificate OCR endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'error': f'Unexpected birth certificate processing error: {str(e)}',
                    'error_code': '500_Birth_Certificate_Unexpected_Error',
                    'combined_response': {
                        'Lines': [],
                        'Words': [],
                        'FullText': '',
                        'BatchMetadata': []
                    },
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Birth_Certificate_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }],
                    'metadata': {
                        'processing_type': 'batch_birth_certificate_textract',
                        'total_lines': 0,
                        'total_words': 0,
                        'bucket': bucket_name if 'bucket_name' in locals() else 'unknown'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Birth Certificate OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'error': 'Invalid request data for birth certificate OCR processing',
                'error_code': '400_Birth_Certificate_Validation_Error',
                'validation_errors': serializer.errors,
                'combined_response': {
                    'Lines': [],
                    'Words': [],
                    'FullText': '',
                    'BatchMetadata': []
                },
                'errors': [],
                'metadata': {
                    'processing_type': 'batch_birth_certificate_textract',
                    'total_lines': 0,
                    'total_words': 0
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class BatchPassportOCRView(generics.CreateAPIView):
    """
    Endpoint especializado para procesamiento OCR de Pasaportes
    
    Utiliza AWS Textract detect_document_text con preprocesamiento de imagen optimizado
    para mejor reconocimiento de texto en pasaportes internacionales.
    
    Este endpoint está diseñado específicamente para pasaportes y proporciona:
    - Detección y corrección automática de rotación
    - Preprocesamiento optimizado (contraste, nitidez) para zona MRZ
    - Detección de zona MRZ (Machine Readable Zone)
    - Compresión adaptativa para cumplir límites de Textract
    
    Request body:
    {
        "file_list": ["pasaporte1.jpg", "pasaporte2.jpg"],  # Lista de archivos en S3
        "bucket_name": "nombre-bucket"                       # Opcional, usa default si no se especifica
    }
    """
    serializer_class = BatchOCRSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch Passport OCR endpoint accessed (Textract)")
        logger.debug(f"Passport request data: {request.data}")
        
        serializer = BatchOCRSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Passport OCR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing passport OCR for {len(file_list)} files in bucket: {bucket_name}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize passport processor
                logger.debug("Initializing TextractPassportAnalyzer for batch processing")
                processor = TextractPassportAnalyzer()
                
                # Process files in batch using Textract
                logger.info("Starting batch passport OCR processing with Textract")
                result = processor.batch_analyze(file_list, bucket_name)
                
                # Format response similar to birth certificate endpoint
                combined_lines = []
                combined_words = []
                full_texts = []
                batch_metadata = []
                errors = []
                
                for item in result.get('results', []):
                    photo = item.get('photo', '')
                    item_result = item.get('result', {})
                    
                    if item_result.get('success'):
                        extracted = item_result.get('extracted_data', {})
                        lines = extracted.get('lines', [])
                        words = extracted.get('words', [])
                        
                        for line in lines:
                            combined_lines.append({
                                'Text': line.get('text', ''),
                                'Confidence': line.get('confidence', 0),
                                'Geometry': line.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        for word in words:
                            combined_words.append({
                                'Text': word.get('text', ''),
                                'Confidence': word.get('confidence', 0),
                                'Geometry': word.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        full_texts.append(extracted.get('full_text', ''))
                        
                        batch_metadata.append({
                            'photo': photo,
                            'line_count': extracted.get('line_count', 0),
                            'word_count': extracted.get('word_count', 0),
                            'average_confidence': extracted.get('average_confidence', 0),
                            'mrz_detected': item_result.get('mrz_analysis', {}).get('mrz_detected', False),
                            'mrz_lines': item_result.get('mrz_analysis', {}).get('mrz_lines', [])
                        })
                    else:
                        errors.append({
                            'photo': photo,
                            'error': item_result.get('error', 'Unknown error'),
                            'error_code': item_result.get('error_code', '500_Unknown')
                        })
                
                # Calculate overall statistics
                total_lines = len(combined_lines)
                total_words = len(combined_words)
                confidences = [line.get('Confidence', 0) for line in combined_lines]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                response_data = {
                    'success': result.get('successful', 0) > 0,
                    'files_processed': result.get('total_processed', 0),
                    'files_successful': result.get('successful', 0),
                    'files_failed': result.get('errors', 0),
                    'combined_response': {
                        'Lines': combined_lines,
                        'Words': combined_words,
                        'FullText': '\n\n--- PAGE BREAK ---\n\n'.join(full_texts),
                        'BatchMetadata': batch_metadata
                    },
                    'errors': errors,
                    'metadata': {
                        'processing_type': 'batch_passport_textract',
                        'total_lines': total_lines,
                        'total_words': total_words,
                        'average_confidence': round(avg_confidence, 2),
                        'bucket': bucket_name
                    }
                }
                
                logger.info(f"Passport OCR completed - Success: {response_data['success']}, "
                          f"Processed: {response_data['files_processed']}, "
                          f"Successful: {response_data['files_successful']}, "
                          f"Failed: {response_data['files_failed']}, "
                          f"Avg Confidence: {avg_confidence:.2f}%")
                
                # Determine response status
                if response_data['files_failed'] == 0:
                    return Response(response_data, status=status.HTTP_200_OK)
                elif response_data['files_successful'] > 0:
                    return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
                else:
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Passport OCR endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'error': f'Unexpected passport processing error: {str(e)}',
                    'error_code': '500_Passport_Unexpected_Error',
                    'combined_response': {
                        'Lines': [],
                        'Words': [],
                        'FullText': '',
                        'BatchMetadata': []
                    },
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Passport_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }],
                    'metadata': {
                        'processing_type': 'batch_passport_textract',
                        'total_lines': 0,
                        'total_words': 0,
                        'bucket': bucket_name if 'bucket_name' in locals() else 'unknown'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Passport OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'error': 'Invalid request data for passport OCR processing',
                'error_code': '400_Passport_Validation_Error',
                'validation_errors': serializer.errors,
                'combined_response': {
                    'Lines': [],
                    'Words': [],
                    'FullText': '',
                    'BatchMetadata': []
                },
                'errors': [],
                'metadata': {
                    'processing_type': 'batch_passport_textract',
                    'total_lines': 0,
                    'total_words': 0
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class BatchCertificadoOCRView(generics.CreateAPIView):
    """
    Endpoint especializado para procesamiento OCR de Certificados de Notas/Calificaciones
    
    Utiliza AWS Textract analyze_document con detección de TABLAS para extraer
    información estructurada de certificados académicos.
    
    Este endpoint está diseñado específicamente para certificados y proporciona:
    - Detección automática de tablas (códigos, asignaturas, calificaciones)
    - Extracción de información del estudiante (nombre, matrícula, programa)
    - Preprocesamiento optimizado para documentos impresos
    
    Request body:
    {
        "file_list": ["certificado1.jpg", "certificado2.jpg"],
        "bucket_name": "nombre-bucket"  # Opcional
    }
    """
    serializer_class = BatchOCRSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch Certificado OCR endpoint accessed (Textract Tables)")
        logger.debug(f"Certificado request data: {request.data}")
        
        serializer = BatchOCRSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Certificado OCR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing certificado OCR for {len(file_list)} files in bucket: {bucket_name}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize certificado processor
                logger.debug("Initializing TextractCertificadoAnalyzer for batch processing")
                processor = TextractCertificadoAnalyzer()
                
                # Process files in batch
                logger.info("Starting batch certificado OCR processing with Textract Tables")
                result = processor.batch_analyze(file_list, bucket_name)
                
                # Format response
                combined_lines = []
                combined_words = []
                full_texts = []
                batch_metadata = []
                all_tables = []
                all_grades = []
                student_info = {}
                errors = []
                
                for item in result.get('results', []):
                    photo = item.get('photo', '')
                    item_result = item.get('result', {})
                    
                    if item_result.get('success'):
                        extracted = item_result.get('extracted_data', {})
                        lines = extracted.get('lines', [])
                        words = extracted.get('words', [])
                        
                        for line in lines:
                            combined_lines.append({
                                'Text': line.get('text', ''),
                                'Confidence': line.get('confidence', 0),
                                'Geometry': line.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        for word in words:
                            combined_words.append({
                                'Text': word.get('text', ''),
                                'Confidence': word.get('confidence', 0),
                                'Geometry': word.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        full_texts.append(extracted.get('full_text', ''))
                        
                        # Collect tables
                        tables = item_result.get('tables', [])
                        all_tables.extend(tables)
                        
                        # Collect grades
                        grades = item_result.get('grades', [])
                        all_grades.extend(grades)
                        
                        # Get student info (from first successful page)
                        if not student_info.get('nombre'):
                            student_info = item_result.get('student_info', {})
                        
                        batch_metadata.append({
                            'photo': photo,
                            'line_count': extracted.get('line_count', 0),
                            'word_count': extracted.get('word_count', 0),
                            'average_confidence': extracted.get('average_confidence', 0),
                            'tables_found': len(tables),
                            'grades_extracted': len(grades)
                        })
                    else:
                        errors.append({
                            'photo': photo,
                            'error': item_result.get('error', 'Unknown error'),
                            'error_code': item_result.get('error_code', '500_Unknown')
                        })
                
                # Calculate overall statistics
                total_lines = len(combined_lines)
                total_words = len(combined_words)
                confidences = [line.get('Confidence', 0) for line in combined_lines]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Format grades for easy consumption
                formatted_grades = []
                for grade in all_grades:
                    formatted_grades.append({
                        'Codigo': grade.get('codigo', ''),
                        'Asignatura': grade.get('asignatura', ''),
                        'Calificacion': grade.get('calificacion', ''),
                        'RawData': grade.get('raw_row', [])
                    })
                
                response_data = {
                    'success': result.get('successful', 0) > 0,
                    'files_processed': result.get('total_processed', 0),
                    'files_successful': result.get('successful', 0),
                    'files_failed': result.get('errors', 0),
                    'combined_response': {
                        'Lines': combined_lines,
                        'Words': combined_words,
                        'FullText': '\n\n--- PAGE BREAK ---\n\n'.join(full_texts),
                        'BatchMetadata': batch_metadata
                    },
                    'student_info': student_info,
                    'grades': formatted_grades,
                    'tables_data': all_tables,
                    'errors': errors,
                    'metadata': {
                        'processing_type': 'batch_certificado_textract_tables',
                        'total_lines': total_lines,
                        'total_words': total_words,
                        'average_confidence': round(avg_confidence, 2),
                        'total_tables_found': len(all_tables),
                        'total_grades_extracted': len(formatted_grades),
                        'bucket': bucket_name
                    }
                }
                
                logger.info(f"Certificado OCR completed - Success: {response_data['success']}, "
                          f"Processed: {response_data['files_processed']}, "
                          f"Tables: {len(all_tables)}, Grades: {len(formatted_grades)}, "
                          f"Avg Confidence: {avg_confidence:.2f}%")
                
                # Determine response status
                if response_data['files_failed'] == 0:
                    return Response(response_data, status=status.HTTP_200_OK)
                elif response_data['files_successful'] > 0:
                    return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
                else:
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Certificado OCR endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'error': f'Unexpected certificado processing error: {str(e)}',
                    'error_code': '500_Certificado_Unexpected_Error',
                    'combined_response': {
                        'Lines': [],
                        'Words': [],
                        'FullText': '',
                        'BatchMetadata': []
                    },
                    'student_info': {},
                    'grades': [],
                    'tables_data': [],
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Certificado_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }],
                    'metadata': {
                        'processing_type': 'batch_certificado_textract_tables',
                        'total_lines': 0,
                        'total_words': 0,
                        'bucket': bucket_name if 'bucket_name' in locals() else 'unknown'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Certificado OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'error': 'Invalid request data for certificado OCR processing',
                'error_code': '400_Certificado_Validation_Error',
                'validation_errors': serializer.errors,
                'combined_response': {
                    'Lines': [],
                    'Words': [],
                    'FullText': '',
                    'BatchMetadata': []
                },
                'student_info': {},
                'grades': [],
                'tables_data': [],
                'errors': [],
                'metadata': {
                    'processing_type': 'batch_certificado_textract_tables',
                    'total_lines': 0,
                    'total_words': 0
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class BatchTituloOCRView(generics.CreateAPIView):
    """
    Endpoint especializado para procesamiento OCR de Títulos Universitarios/Licenciaturas
    
    Utiliza AWS Textract analyze_document con detección de TABLAS para extraer
    información estructurada de títulos universitarios y certificados de estudios.
    
    Este endpoint está diseñado específicamente para títulos universitarios y proporciona:
    - Detección automática de tablas (códigos de materias, créditos, calificaciones)
    - Extracción de información del título (nombre del programa, institución, fecha)
    - Extracción de materias con formato de código (ej: PSY101, MAT201)
    - Preprocesamiento optimizado para documentos oficiales
    
    Request body:
    {
        "file_list": ["titulo1.jpg", "titulo2.jpg"],
        "bucket_name": "nombre-bucket"  # Opcional
    }
    """
    serializer_class = BatchOCRSerializer
    #permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logger.info("Batch Titulo OCR endpoint accessed (Textract Tables)")
        logger.debug(f"Titulo request data: {request.data}")
        
        serializer = BatchOCRSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Titulo OCR serializer validation successful")
            
            try:
                # Get validated data
                file_list = serializer.validated_data['file_list']
                bucket_name = serializer.validated_data.get('bucket_name', None)
                
                # Use default bucket if not specified
                if not bucket_name:
                    bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
                
                logger.info(f"Processing titulo OCR for {len(file_list)} files in bucket: {bucket_name}")
                logger.debug(f"Files to process: {file_list}")
                
                # Initialize titulo processor
                logger.debug("Initializing TextractUniversityTitleAnalyzer for batch processing")
                processor = TextractUniversityTitleAnalyzer()
                
                # Process files in batch
                logger.info("Starting batch titulo OCR processing with Textract Tables")
                result = processor.analyze_batch(file_list, bucket_name)
                
                # Format response
                combined_lines = []
                combined_words = []
                full_texts = []
                batch_metadata = []
                all_tables = []
                all_courses = []
                degree_info = {}
                errors = []
                
                for item in result.get('results', []):
                    photo = item.get('photo', '')
                    item_result = item.get('result', {})
                    
                    if item_result.get('success'):
                        extracted = item_result.get('extracted_data', {})
                        lines = extracted.get('lines', [])
                        words = extracted.get('words', [])
                        
                        for line in lines:
                            combined_lines.append({
                                'Text': line.get('text', ''),
                                'Confidence': line.get('confidence', 0),
                                'Geometry': line.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        for word in words:
                            combined_words.append({
                                'Text': word.get('text', ''),
                                'Confidence': word.get('confidence', 0),
                                'Geometry': word.get('geometry', {}),
                                'SourceFile': photo
                            })
                        
                        full_texts.append(extracted.get('full_text', ''))
                        
                        # Collect tables
                        tables = item_result.get('tables', [])
                        all_tables.extend(tables)
                        
                        # Collect courses
                        courses = item_result.get('courses', [])
                        all_courses.extend(courses)
                        
                        # Get degree info (from first successful page)
                        if not degree_info.get('titulo_nombre'):
                            degree_info = item_result.get('degree_info', {})
                        
                        batch_metadata.append({
                            'photo': photo,
                            'line_count': extracted.get('line_count', 0),
                            'word_count': extracted.get('word_count', 0),
                            'average_confidence': extracted.get('average_confidence', 0),
                            'tables_found': len(tables),
                            'courses_extracted': len(courses)
                        })
                    else:
                        errors.append({
                            'photo': photo,
                            'error': item_result.get('error', 'Unknown error'),
                            'error_code': item_result.get('error_code', '500_Unknown')
                        })
                
                # Calculate overall statistics
                total_lines = len(combined_lines)
                total_words = len(combined_words)
                confidences = [line.get('Confidence', 0) for line in combined_lines]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # Format courses for easy consumption
                formatted_courses = []
                for course in all_courses:
                    formatted_courses.append({
                        'Codigo': course.get('codigo', ''),
                        'Materia': course.get('nombre_materia', ''),
                        'Creditos': course.get('creditos', ''),
                        'Calificacion': course.get('calificacion', ''),
                        'RawData': course.get('raw_row', [])
                    })
                
                response_data = {
                    'success': result.get('successful', 0) > 0,
                    'files_processed': result.get('total_processed', 0),
                    'files_successful': result.get('successful', 0),
                    'files_failed': result.get('errors', 0),
                    'combined_response': {
                        'Lines': combined_lines,
                        'Words': combined_words,
                        'FullText': '\n\n--- PAGE BREAK ---\n\n'.join(full_texts),
                        'BatchMetadata': batch_metadata
                    },
                    'degree_info': degree_info,
                    'courses': formatted_courses,
                    'tables_data': all_tables,
                    'errors': errors,
                    'metadata': {
                        'processing_type': 'batch_titulo_textract_tables',
                        'total_lines': total_lines,
                        'total_words': total_words,
                        'average_confidence': round(avg_confidence, 2),
                        'total_tables_found': len(all_tables),
                        'total_courses_extracted': len(formatted_courses),
                        'bucket': bucket_name
                    }
                }
                
                logger.info(f"Titulo OCR completed - Success: {response_data['success']}, "
                          f"Processed: {response_data['files_processed']}, "
                          f"Tables: {len(all_tables)}, Courses: {len(formatted_courses)}, "
                          f"Avg Confidence: {avg_confidence:.2f}%")
                
                # Determine response status
                if response_data['files_failed'] == 0:
                    return Response(response_data, status=status.HTTP_200_OK)
                elif response_data['files_successful'] > 0:
                    return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
                else:
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Unexpected error in Titulo OCR endpoint: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                
                error_response = {
                    'success': False,
                    'files_processed': 0,
                    'files_successful': 0,
                    'files_failed': len(serializer.validated_data.get('file_list', [])),
                    'error': f'Unexpected titulo processing error: {str(e)}',
                    'error_code': '500_Titulo_Unexpected_Error',
                    'combined_response': {
                        'Lines': [],
                        'Words': [],
                        'FullText': '',
                        'BatchMetadata': []
                    },
                    'degree_info': {},
                    'courses': [],
                    'tables_data': [],
                    'errors': [{
                        'error': str(e),
                        'error_code': '500_Titulo_Unexpected_Error',
                        'exception_type': type(e).__name__
                    }],
                    'metadata': {
                        'processing_type': 'batch_titulo_textract_tables',
                        'total_lines': 0,
                        'total_words': 0,
                        'bucket': bucket_name if 'bucket_name' in locals() else 'unknown'
                    }
                }
                return Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Titulo OCR serializer validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'files_processed': 0,
                'files_successful': 0,
                'files_failed': 0,
                'error': 'Invalid request data for titulo OCR processing',
                'error_code': '400_Titulo_Validation_Error',
                'validation_errors': serializer.errors,
                'combined_response': {
                    'Lines': [],
                    'Words': [],
                    'FullText': '',
                    'BatchMetadata': []
                },
                'degree_info': {},
                'courses': [],
                'tables_data': [],
                'errors': [],
                'metadata': {
                    'processing_type': 'batch_titulo_textract_tables',
                    'total_lines': 0,
                    'total_words': 0
                }
            }, status=status.HTTP_400_BAD_REQUEST)