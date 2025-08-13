from __future__ import unicode_literals
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from apirest.serializers import llegaSerializer2, llegafaceSerializer2, FileUploadSerializer, TextractAnalysisSerializer
from django.http import HttpResponse
from .codeorm import consult2
from .AWSocr import consult45
from .AWSocrRaw import consult45Raw
from .AWScompare import consult46
from .AWSUpload import FileUploadS3
from .AWSTextract import TextractIDAnalyzer
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