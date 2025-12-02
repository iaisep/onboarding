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

# Platform detection for Linux/Docker compatibility
import platform
RUNNING_ON_WINDOWS = platform.system() == 'Windows'

# Alternative DOCX handling for Linux
if not RUNNING_ON_WINDOWS:
    try:
        from docx import Document  # python-docx for basic DOCX reading
        DOCX_READING_AVAILABLE = True
    except ImportError:
        DOCX_READING_AVAILABLE = False
else:
    DOCX_READING_AVAILABLE = False

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

    def _compress_image_to_max_size(self, img, max_size_bytes=4.5 * 1024 * 1024, min_quality=70):
        """
        Compress image to ensure it doesn't exceed max_size_bytes (default 4.5MB).
        Optimized for OCR: prioritizes text readability over file size.
        Uses adaptive quality reduction and smart resizing.
        
        For documents with small text (like birth certificates), we:
        1. First try reducing JPEG quality (down to min_quality=70)
        2. Then resize while maintaining aspect ratio
        3. Apply sharpening to preserve text edges
        """
        from PIL import Image, ImageEnhance, ImageFilter
        import io
        
        # Start with high quality
        quality = 95
        current_img = img.copy()
        original_width = current_img.width
        original_height = current_img.height
        
        logger.debug(f"Starting compression - Original size: {original_width}x{original_height}")
        
        # Phase 1: Try quality reduction only (preserves resolution for OCR)
        while quality >= min_quality:
            output = io.BytesIO()
            current_img.save(output, format='JPEG', quality=quality, optimize=True, dpi=(300, 300))
            img_data = output.getvalue()
            
            if len(img_data) <= max_size_bytes:
                logger.debug(f"Image compressed to {len(img_data) / 1024 / 1024:.2f}MB at quality={quality} (no resize needed)")
                return img_data, quality
            
            # Reduce quality in smaller steps to find optimal point
            quality -= 5
            logger.debug(f"Image too large ({len(img_data) / 1024 / 1024:.2f}MB), reducing quality to {quality}")
        
        # Phase 2: Smart resize - reduce dimensions while keeping text readable
        # For OCR, minimum recommended is ~150 DPI, so we limit resize to 70% minimum
        logger.info("Quality reduction insufficient, applying smart resize for OCR optimization")
        
        # Reset quality to 80 for resized images (good balance for text)
        resize_quality = 80
        scale_factor = 0.95  # Start with minimal reduction
        min_scale = 0.70  # Don't go below 70% to maintain OCR readability
        
        while scale_factor >= min_scale:
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Use LANCZOS for best quality downscaling
            resized_img = current_img.resize((new_width, new_height), Image.LANCZOS)
            
            # Apply slight sharpening to compensate for resize blur (helps OCR)
            enhancer = ImageEnhance.Sharpness(resized_img)
            sharpened_img = enhancer.enhance(1.3)  # Moderate sharpening
            
            output = io.BytesIO()
            sharpened_img.save(output, format='JPEG', quality=resize_quality, optimize=True, dpi=(300, 300))
            img_data = output.getvalue()
            
            if len(img_data) <= max_size_bytes:
                logger.debug(f"Image resized to {new_width}x{new_height} ({scale_factor*100:.0f}%) and compressed to {len(img_data) / 1024 / 1024:.2f}MB")
                return img_data, resize_quality
            
            scale_factor -= 0.05
            logger.debug(f"Image still too large ({len(img_data) / 1024 / 1024:.2f}MB), reducing scale to {scale_factor:.2f}")
        
        # Phase 3: Final fallback - more aggressive but still OCR-friendly
        logger.warning("Applying final compression strategy for large document")
        
        # Calculate the scale needed to approximate target size
        # Estimate: if current is X MB at 70% scale, target scale = sqrt(4.5/X) * 0.7
        current_size_mb = len(img_data) / 1024 / 1024
        estimated_scale = min_scale * (max_size_bytes / 1024 / 1024 / current_size_mb) ** 0.5
        estimated_scale = max(0.5, min(estimated_scale, min_scale))  # Keep between 50-70%
        
        final_width = int(original_width * estimated_scale)
        final_height = int(original_height * estimated_scale)
        
        final_img = current_img.resize((final_width, final_height), Image.LANCZOS)
        
        # Apply unsharp mask for better text edge definition
        final_img = final_img.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=2))
        
        output = io.BytesIO()
        final_img.save(output, format='JPEG', quality=min_quality, optimize=True, dpi=(300, 300))
        img_data = output.getvalue()
        
        logger.info(f"Final image: {final_width}x{final_height} ({estimated_scale*100:.0f}%), {len(img_data) / 1024 / 1024:.2f}MB at quality={min_quality}")
        return img_data, min_quality

    def _convert_pdf_to_images(self, pdf_content, original_filename):
        """Convert PDF to high-quality JPG images optimized for OCR with max 4.5MB size limit"""
        if not PDF_CONVERSION_AVAILABLE:
            raise ImportError("PyMuPDF not available for PDF conversion. Install with: pip install PyMuPDF")
        
        # Maximum image size in bytes (4.5MB)
        MAX_IMAGE_SIZE = 4.5 * 1024 * 1024
        
        logger.info(f"Starting PDF to image conversion for: {original_filename} (max size: {MAX_IMAGE_SIZE / 1024 / 1024}MB)")
        
        try:
            # Open PDF from memory
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            converted_images = []
            
            logger.info(f"PDF has {len(pdf_document)} pages")
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document.load_page(page_num)
                
                # Convert to high-quality image for better OCR
                # Matrix(3.0, 3.0) = 3x zoom = ~300 DPI (optimal for OCR)
                # Higher DPI = better text recognition
                mat = fitz.Matrix(3.0, 3.0)  # 300 DPI - optimal balance
                
                # Get pixmap with high quality settings
                # alpha=False removes transparency for smaller file size
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image for additional optimization
                from PIL import Image
                import io
                
                # Create PIL Image from pixmap
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Apply sharpening for better OCR (optional but recommended)
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.2)  # Slight sharpening (1.0 = original)
                
                # Compress image to ensure it doesn't exceed 4.5MB
                img_data, final_quality = self._compress_image_to_max_size(img, MAX_IMAGE_SIZE)
                
                # Generate filename for this page
                page_filename = f"{os.path.splitext(original_filename)[0]}_page_{page_num + 1}.jpg"
                unique_filename = self._generate_unique_filename(page_filename)
                
                converted_images.append({
                    'filename': unique_filename,
                    'content': img_data,
                    'page_number': page_num + 1,
                    'size': len(img_data)
                })
                
                logger.debug(f"Converted page {page_num + 1} to {len(img_data) / 1024 / 1024:.2f}MB at quality={final_quality}")
            
            pdf_document.close()
            logger.info(f"PDF conversion completed - {len(converted_images)} images generated (max 4.5MB each)")
            
            return converted_images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise

    def _convert_docx_to_images(self, docx_content, original_filename):
        """Convert DOCX to images via PDF intermediate"""
        if not RUNNING_ON_WINDOWS:
            # On Linux/Docker, DOCX conversion is not supported due to Windows COM dependency
            logger.error("DOCX conversion not supported on Linux/Docker platforms")
            raise ValueError(
                "DOCX conversion requires Windows platform with Microsoft Office or LibreOffice. "
                "On Linux/Docker, please convert DOCX to PDF manually before uploading, "
                "or upload the DOCX file directly for text extraction only."
            )
        
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

    def upload_file(self, file_content, filename, upload_original=True):
        """
        Main method to upload file to S3 with automatic conversion
        Returns detailed information about uploaded files
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            upload_original: If True, also uploads the original file (PDF/image) to S3
        """
        logger.info(f"Starting file upload process for: {filename} (upload_original={upload_original})")
        
        try:
            # Detect file type
            file_category, file_ext, mime_type = self._detect_file_type(file_content, filename)
            logger.info(f"File detected as: {file_category} ({file_ext})")
            
            # Get S3 client
            s3_client = self._get_s3_client()
            
            upload_results = []
            original_file_info = None
            
            # Upload original file first if requested
            if upload_original:
                original_unique_filename = self._generate_unique_filename(filename)
                content_type = mime_type or 'application/octet-stream'
                
                s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=original_unique_filename,
                    Body=file_content,
                    ContentType=content_type
                )
                
                original_file_info = {
                    'original_filename': filename,
                    's3_filename': original_unique_filename,
                    'file_type': 'original',
                    'size': len(file_content),
                    'content_type': content_type,
                    'url': f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{original_unique_filename}"
                }
                
                upload_results.append(original_file_info)
                logger.info(f"Original file uploaded successfully: {original_unique_filename}")
            
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
                    # Convert DOCX to images (Windows only)
                    if RUNNING_ON_WINDOWS:
                        converted_images = self._convert_docx_to_images(file_content, filename)
                    else:
                        # On Linux, DOCX conversion is not supported
                        error_msg = (
                            "DOCX conversion is not supported on Linux platforms. "
                            "This feature requires Microsoft Office COM interface which is Windows-only. "
                            "Please convert your DOCX files to PDF format before uploading."
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    
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
