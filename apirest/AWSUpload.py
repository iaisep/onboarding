# -*- coding: utf-8 -*-
import boto3
import os
import io
import uuid
from datetime import datetime
from PIL import Image
from decouple import config
import logging
import mimetypes

# Libraries for document conversion
try:
    import fitz  # PyMuPDF for PDF conversion
    PDF_CONVERSION_AVAILABLE = True
except ImportError:
    PDF_CONVERSION_AVAILABLE = False
    
try:
    from docx2pdf import convert  # For DOCX to PDF conversion
    import pythoncom  # Required for Windows COM operations
    DOCX_CONVERSION_AVAILABLE = True
except ImportError:
    DOCX_CONVERSION_AVAILABLE = False

# Configure logger for file upload operations
logger = logging.getLogger('apirest.upload')

class FileUploadS3:
    """
    Clase para manejar subida de archivos a S3 con conversión automática
    Soporta: PDF, DOCX/DOC, JPG, JPEG, PNG
    """
    
    def __init__(self):
        logger.info("Initializing FileUploadS3 class")
        try:
            # Initialize AWS credentials from environment
            self.aws_access_key_id = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY') 
            self.aws_session_token = config('AWS_SESSION_TOKEN', default=None)
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET')
            
            # Supported file types
            self.supported_image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            self.supported_document_types = ['.pdf', '.docx', '.doc']
            self.supported_types = self.supported_image_types + self.supported_document_types
            
            logger.info(f"FileUploadS3 Config loaded - Region: {self.region_name}, Bucket: {self.bucket_name}")
            logger.info(f"Supported types: {self.supported_types}")
            logger.info(f"PDF conversion available: {PDF_CONVERSION_AVAILABLE}")
            logger.info(f"DOCX conversion available: {DOCX_CONVERSION_AVAILABLE}")
            
        except Exception as e:
            logger.error(f"Error loading AWS configuration for FileUpload: {str(e)}")
            raise

    def _get_s3_client(self):
        """Get configured S3 client"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
                region_name=self.region_name
            )
            logger.debug("S3 client configured successfully")
            return s3_client
        except Exception as e:
            logger.error(f"Error configuring S3 client: {str(e)}")
            raise

    def _generate_unique_filename(self, original_filename, extension=None):
        """Generate unique filename with timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        if extension:
            filename = f"{timestamp}_{unique_id}_{os.path.splitext(original_filename)[0]}{extension}"
        else:
            filename = f"{timestamp}_{unique_id}_{original_filename}"
            
        logger.debug(f"Generated unique filename: {filename}")
        return filename

    def _detect_file_type(self, file_content, filename):
        """Detect file type from content and filename"""
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        logger.debug(f"File detection - Name: {filename}, Extension: {file_ext}, MIME: {mime_type}")
        
        # Validate supported types
        if file_ext not in self.supported_types:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported: {self.supported_types}")
        
        # Determine file category
        if file_ext in self.supported_image_types:
            return 'image', file_ext, mime_type
        elif file_ext in self.supported_document_types:
            return 'document', file_ext, mime_type
        else:
            raise ValueError(f"Unknown file category for: {file_ext}")

    def _convert_pdf_to_images(self, pdf_content, original_filename):
        """Convert PDF to high-quality JPG images"""
        if not PDF_CONVERSION_AVAILABLE:
            raise ImportError("PyMuPDF not available for PDF conversion. Install with: pip install PyMuPDF")
        
        logger.info(f"Starting PDF to image conversion for: {original_filename}")
        
        try:
            # Open PDF from memory
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            converted_images = []
            
            logger.info(f"PDF has {len(pdf_document)} pages")
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document.load_page(page_num)
                
                # Convert to high-quality image
                # Higher matrix values = better quality
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.pil_tobytes(format="JPEG", optimize=True)
                
                # Generate filename for this page
                page_filename = f"{os.path.splitext(original_filename)[0]}_page_{page_num + 1}.jpg"
                unique_filename = self._generate_unique_filename(page_filename)
                
                converted_images.append({
                    'filename': unique_filename,
                    'content': img_data,
                    'page_number': page_num + 1,
                    'size': len(img_data)
                })
                
                logger.debug(f"Converted page {page_num + 1} to {len(img_data)} bytes")
            
            pdf_document.close()
            logger.info(f"PDF conversion completed - {len(converted_images)} images generated")
            
            return converted_images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise

    def _convert_docx_to_images(self, docx_content, original_filename):
        """Convert DOCX to images via PDF intermediate"""
        if not DOCX_CONVERSION_AVAILABLE:
            raise ImportError("docx2pdf not available for DOCX conversion. Install with: pip install docx2pdf")
        
        logger.info(f"Starting DOCX to image conversion for: {original_filename}")
        
        try:
            # Initialize COM for Windows
            pythoncom.CoInitialize()
            
            # Create temporary files
            temp_docx = f"temp_{uuid.uuid4()}.docx"
            temp_pdf = f"temp_{uuid.uuid4()}.pdf"
            
            try:
                # Save DOCX content to temporary file
                with open(temp_docx, 'wb') as f:
                    f.write(docx_content)
                
                logger.debug(f"Saved DOCX to temp file: {temp_docx}")
                
                # Convert DOCX to PDF
                convert(temp_docx, temp_pdf)
                logger.debug(f"Converted DOCX to PDF: {temp_pdf}")
                
                # Read PDF content
                with open(temp_pdf, 'rb') as f:
                    pdf_content = f.read()
                
                # Convert PDF to images
                converted_images = self._convert_pdf_to_images(pdf_content, original_filename)
                
                return converted_images
                
            finally:
                # Clean up temporary files
                try:
                    if os.path.exists(temp_docx):
                        os.remove(temp_docx)
                        logger.debug(f"Cleaned up temp file: {temp_docx}")
                    if os.path.exists(temp_pdf):
                        os.remove(temp_pdf)
                        logger.debug(f"Cleaned up temp file: {temp_pdf}")
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up temp files: {cleanup_error}")
                
                # Uninitialize COM
                pythoncom.CoUninitialize()
                
        except Exception as e:
            logger.error(f"Error converting DOCX to images: {str(e)}")
            raise

    def _optimize_image(self, image_content, original_filename):
        """Optimize image for better performance while maintaining quality"""
        try:
            logger.debug(f"Optimizing image: {original_filename}")
            
            # Open image
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Get original dimensions
            original_size = image.size
            logger.debug(f"Original image size: {original_size}")
            
            # Resize if too large (max 2048px on longest side)
            max_dimension = 2048
            if max(original_size) > max_dimension:
                ratio = max_dimension / max(original_size)
                new_size = tuple(int(dim * ratio) for dim in original_size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to: {new_size}")
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            optimized_content = output.getvalue()
            
            logger.debug(f"Image optimization: {len(image_content)} -> {len(optimized_content)} bytes")
            
            return optimized_content
            
        except Exception as e:
            logger.warning(f"Error optimizing image, using original: {str(e)}")
            return image_content

    def upload_file(self, file_content, filename):
        """
        Main method to upload file to S3 with automatic conversion
        Returns detailed information about uploaded files
        """
        logger.info(f"Starting file upload process for: {filename}")
        
        try:
            # Detect file type
            file_category, file_ext, mime_type = self._detect_file_type(file_content, filename)
            logger.info(f"File detected as: {file_category} ({file_ext})")
            
            # Get S3 client
            s3_client = self._get_s3_client()
            
            upload_results = []
            
            if file_category == 'image':
                # Handle image files
                logger.info("Processing image file")
                
                # Optimize image
                optimized_content = self._optimize_image(file_content, filename)
                
                # Generate unique filename
                unique_filename = self._generate_unique_filename(filename, '.jpg')
                
                # Upload to S3
                s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=unique_filename,
                    Body=optimized_content,
                    ContentType='image/jpeg'
                )
                
                upload_results.append({
                    'original_filename': filename,
                    's3_filename': unique_filename,
                    'file_type': 'image',
                    'size': len(optimized_content),
                    'url': f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{unique_filename}"
                })
                
                logger.info(f"Image uploaded successfully: {unique_filename}")
            
            elif file_category == 'document':
                # Handle document files
                logger.info(f"Processing document file: {file_ext}")
                
                if file_ext == '.pdf':
                    # Convert PDF to images
                    converted_images = self._convert_pdf_to_images(file_content, filename)
                    
                elif file_ext in ['.docx', '.doc']:
                    # Convert DOCX to images
                    converted_images = self._convert_docx_to_images(file_content, filename)
                    
                else:
                    raise ValueError(f"Unsupported document type: {file_ext}")
                
                # Upload all converted images
                for image_info in converted_images:
                    s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=image_info['filename'],
                        Body=image_info['content'],
                        ContentType='image/jpeg'
                    )
                    
                    upload_results.append({
                        'original_filename': filename,
                        's3_filename': image_info['filename'],
                        'file_type': 'converted_image',
                        'page_number': image_info['page_number'],
                        'size': image_info['size'],
                        'url': f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{image_info['filename']}"
                    })
                    
                    logger.info(f"Converted image uploaded: {image_info['filename']}")
            
            logger.info(f"Upload process completed - {len(upload_results)} files uploaded")
            
            return {
                'success': True,
                'error': None,
                'error_code': None,
                'uploaded_files': upload_results,
                'metadata': {
                    'original_filename': filename,
                    'original_file_type': file_category,
                    'original_extension': file_ext,
                    'original_mime_type': mime_type,
                    'total_files_uploaded': len(upload_results),
                    'bucket': self.bucket_name,
                    'region': self.region_name,
                    'upload_timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error uploading file {filename}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            
            return {
                'success': False,
                'error': f'Error uploading file: {str(e)}',
                'error_code': '500_Upload_Error',
                'uploaded_files': [],
                'metadata': {
                    'original_filename': filename,
                    'error_details': {
                        'exception_type': type(e).__name__,
                        'exception_message': str(e)
                    }
                }
            }

    def get_upload_info(self):
        """Get information about upload capabilities"""
        return {
            'service_type': 'File Upload to S3 with Conversion',
            'version': '1.0',
            'aws_region': self.region_name,
            'aws_bucket': self.bucket_name,
            'supported_image_types': self.supported_image_types,
            'supported_document_types': self.supported_document_types,
            'conversion_capabilities': {
                'pdf_to_image': PDF_CONVERSION_AVAILABLE,
                'docx_to_image': DOCX_CONVERSION_AVAILABLE
            },
            'features': [
                'Automatic file type detection',
                'Document to image conversion',
                'Image optimization',
                'Unique filename generation',
                'High-quality PDF conversion',
                'DOCX/DOC support via PDF intermediate'
            ]
        }
