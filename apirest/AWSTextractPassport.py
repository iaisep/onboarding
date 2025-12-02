# -*- coding: utf-8 -*-
"""
AWS Textract Passport Analysis Module
Specialized module for extracting text from passports
Uses Textract's detect_document_text with optimized image preprocessing for passport OCR
Handles rotated images and MRZ (Machine Readable Zone) detection
"""

import boto3
import json
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from decouple import config
import logging
import io
import os
import re
from datetime import datetime

# Configure logger
logger = logging.getLogger('apirest.textract_passport')


class TextractPassportAnalyzer:
    """
    Class specialized for extracting text from passports
    Uses AWS Textract's detect_document_text with optimized image preprocessing
    Includes automatic rotation detection and MRZ zone optimization
    """
    
    def __init__(self):
        """Initialize AWS Textract and S3 clients with credentials from environment variables"""
        try:
            # Get credentials from environment variables
            self.aws_access_key = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info("Initializing TextractPassportAnalyzer")
            logger.debug(f"Region: {self.region_name}, Bucket: {self.bucket_name}")
            
            # Initialize Textract client
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region_name
            )
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region_name
            )
            
            logger.info("AWS Textract and S3 clients initialized successfully for passport processing")
            
        except Exception as e:
            logger.error(f"Failed to initialize TextractPassportAnalyzer: {str(e)}")
            raise
    
    def _detect_and_fix_rotation(self, image):
        """
        Detect if the image is rotated and correct it
        Passports should be horizontal with text readable left-to-right
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Correctly oriented image
        """
        width, height = image.size
        
        # If image is portrait (taller than wide), it's likely rotated 90 degrees
        if height > width * 1.2:
            logger.info(f"Image appears to be portrait ({width}x{height}), rotating 90° clockwise")
            image = image.rotate(-90, expand=True)
            logger.debug(f"New dimensions after rotation: {image.size}")
        
        return image
    
    def _enhance_for_passport_ocr(self, image):
        """
        Apply enhancements specifically optimized for passport text extraction
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Enhanced image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            logger.debug(f"Converted image mode to RGB")
        
        # Step 1: Auto-contrast to normalize lighting
        image = ImageOps.autocontrast(image, cutoff=1)
        logger.debug("Applied auto-contrast")
        
        # Step 2: Increase contrast for better text visibility (passports often have subtle text)
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.4)  # Stronger contrast for passport
        logger.debug("Applied contrast enhancement (1.4x)")
        
        # Step 3: Increase sharpness significantly for small text
        sharpness_enhancer = ImageEnhance.Sharpness(image)
        image = sharpness_enhancer.enhance(2.0)  # Strong sharpening for MRZ
        logger.debug("Applied sharpness enhancement (2.0x)")
        
        # Step 4: Slight brightness adjustment 
        brightness_enhancer = ImageEnhance.Brightness(image)
        image = brightness_enhancer.enhance(1.02)
        logger.debug("Applied brightness enhancement (1.02x)")
        
        # Step 5: Apply unsharp mask for crisp text edges
        image = image.filter(ImageFilter.UnsharpMask(radius=2.0, percent=150, threshold=2))
        logger.debug("Applied UnsharpMask filter for text edges")
        
        return image
    
    def _ensure_optimal_resolution(self, image):
        """
        Ensure the image has optimal resolution for Textract OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Image with optimal resolution
        """
        width, height = image.size
        
        # Passports need good resolution - minimum 2000px on the longer side
        min_long_side = 2000
        max_long_side = 4000  # Don't go too high to avoid memory issues
        
        long_side = max(width, height)
        short_side = min(width, height)
        
        if long_side < min_long_side:
            # Scale up
            scale_factor = min_long_side / long_side
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Scaled up from ({width}, {height}) to ({new_width}, {new_height})")
            
            # Re-apply sharpening after upscale
            image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=2))
            
        elif long_side > max_long_side:
            # Scale down slightly
            scale_factor = max_long_side / long_side
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Scaled down from ({width}, {height}) to ({new_width}, {new_height})")
        
        return image
    
    def _compress_to_size_limit(self, image, max_size_mb=4.5):
        """
        Compress image to meet Textract size limit while preserving quality
        
        Args:
            image: PIL Image object
            max_size_mb: Maximum size in megabytes
            
        Returns:
            bytes: Compressed image bytes
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        output_buffer = io.BytesIO()
        quality = 95
        image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        
        # Reduce quality if necessary
        while output_buffer.tell() > max_size_bytes and quality > 70:
            output_buffer = io.BytesIO()
            quality -= 5
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            logger.debug(f"Reduced quality to {quality}%, size: {output_buffer.tell() / (1024*1024):.2f}MB")
        
        # If still too large, reduce dimensions
        if output_buffer.tell() > max_size_bytes:
            width, height = image.size
            scale = 0.9
            while output_buffer.tell() > max_size_bytes and scale > 0.6:
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Re-sharpen after resize
                resized = resized.filter(ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=2))
                
                output_buffer = io.BytesIO()
                resized.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                scale -= 0.05
                logger.debug(f"Reduced dimensions by {int((1-scale)*100)}%, size: {output_buffer.tell() / (1024*1024):.2f}MB")
        
        output_buffer.seek(0)
        return output_buffer.getvalue()
    
    def _preprocess_image_for_passport(self, image_bytes, filename):
        """
        Complete preprocessing pipeline for passport images
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename for logging
            
        Returns:
            bytes: Preprocessed image bytes optimized for passport OCR
        """
        logger.info(f"Starting passport image preprocessing: {filename}")
        
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            logger.debug(f"Original image: {original_size}, mode: {image.mode}")
            
            # Step 1: Detect and fix rotation
            image = self._detect_and_fix_rotation(image)
            
            # Step 2: Apply passport-specific enhancements
            image = self._enhance_for_passport_ocr(image)
            
            # Step 3: Ensure optimal resolution
            image = self._ensure_optimal_resolution(image)
            
            # Step 4: Compress to size limit
            processed_bytes = self._compress_to_size_limit(image)
            
            final_size = len(processed_bytes) / (1024 * 1024)
            logger.info(f"Preprocessing complete. Final size: {final_size:.2f}MB")
            
            return processed_bytes
            
        except Exception as e:
            logger.error(f"Error preprocessing passport image: {str(e)}")
            raise
    
    def _parse_mrz_from_text(self, all_text):
        """
        Attempt to identify and parse MRZ (Machine Readable Zone) from extracted text
        
        Args:
            all_text: List of text lines extracted by Textract
            
        Returns:
            dict: Parsed MRZ data if found, None otherwise
        """
        mrz_pattern = re.compile(r'^[A-Z0-9<]{30,44}$')
        mrz_lines = []
        
        for text in all_text:
            # Clean the text
            cleaned = text.upper().replace(' ', '').replace('«', '<').replace('‹', '<')
            if mrz_pattern.match(cleaned) and len(cleaned) >= 30:
                mrz_lines.append(cleaned)
        
        if len(mrz_lines) >= 2:
            logger.info(f"Found potential MRZ zone with {len(mrz_lines)} lines")
            return {
                'mrz_detected': True,
                'mrz_lines': mrz_lines[-2:],  # Usually last 2 lines
                'mrz_raw': '\n'.join(mrz_lines[-2:])
            }
        
        return {'mrz_detected': False, 'mrz_lines': [], 'mrz_raw': None}
    
    def analyze_passport(self, photo, bucket=None):
        """
        Analyze a passport image using AWS Textract with preprocessing
        
        Args:
            photo: S3 key of the image file
            bucket: S3 bucket name (optional, uses default if not provided)
            
        Returns:
            dict: Complete analysis results with extracted text
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting passport analysis for: {photo} in bucket: {bucket}")
        
        # Validate parameters
        if not photo or not isinstance(photo, str):
            return {
                'success': False,
                'error': f'Invalid photo parameter: {photo}',
                'error_code': '400_Invalid_Parameters'
            }
        
        temp_file = None
        
        try:
            # Download file from S3
            temp_file = f'temp_passport_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.tmp'
            logger.debug(f"Downloading from S3: {bucket}/{photo}")
            
            self.s3_client.download_file(bucket, photo, temp_file)
            
            with open(temp_file, 'rb') as f:
                original_bytes = f.read()
            
            logger.info(f"Downloaded passport image: {len(original_bytes) / (1024*1024):.2f}MB")
            
        except Exception as e:
            logger.error(f"Error accessing S3: {str(e)}")
            return {
                'success': False,
                'error': f'Error accessing S3 file: {str(e)}',
                'error_code': '400_S3_Access_Error'
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        try:
            # Preprocess the image for passport OCR
            processed_bytes = self._preprocess_image_for_passport(original_bytes, photo)
            
            # Call Textract
            logger.info("Calling AWS Textract detect_document_text for passport")
            
            response = self.textract_client.detect_document_text(
                Document={'Bytes': processed_bytes}
            )
            
            logger.info(f"Textract response received with {len(response.get('Blocks', []))} blocks")
            
            # Extract text content
            lines = []
            words = []
            all_text = []
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    line_data = {
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    }
                    lines.append(line_data)
                    all_text.append(block.get('Text', ''))
                    
                elif block['BlockType'] == 'WORD':
                    word_data = {
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    }
                    words.append(word_data)
            
            # Try to detect MRZ zone
            mrz_info = self._parse_mrz_from_text(all_text)
            
            # Calculate average confidence
            confidences = [line['confidence'] for line in lines if line['confidence'] > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(f"Extracted {len(lines)} lines, {len(words)} words. Avg confidence: {avg_confidence:.2f}%")
            
            return {
                'success': True,
                'error': None,
                'error_code': None,
                'document_type': 'passport',
                'raw_response': response,
                'extracted_data': {
                    'lines': lines,
                    'words': words,
                    'full_text': '\n'.join(all_text),
                    'line_count': len(lines),
                    'word_count': len(words),
                    'average_confidence': round(avg_confidence, 2)
                },
                'mrz_analysis': mrz_info,
                'metadata': {
                    'photo': photo,
                    'bucket': bucket,
                    'processed_at': datetime.now().isoformat(),
                    'textract_blocks': len(response.get('Blocks', []))
                }
            }
            
        except self.textract_client.exceptions.InvalidParameterException as e:
            logger.error(f"Textract InvalidParameterException: {str(e)}")
            return {
                'success': False,
                'error': f'Invalid image format or size: {str(e)}',
                'error_code': '400_Invalid_Image'
            }
            
        except self.textract_client.exceptions.UnsupportedDocumentException as e:
            logger.error(f"Textract UnsupportedDocumentException: {str(e)}")
            return {
                'success': False,
                'error': f'Unsupported document type: {str(e)}',
                'error_code': '400_Unsupported_Document'
            }
            
        except Exception as e:
            logger.error(f"Error during Textract analysis: {str(e)}")
            return {
                'success': False,
                'error': f'Error analyzing passport: {str(e)}',
                'error_code': '500_Analysis_Error'
            }
    
    def batch_analyze(self, photos, bucket=None):
        """
        Analyze multiple passport images
        
        Args:
            photos: List of S3 keys
            bucket: S3 bucket name
            
        Returns:
            dict: Results for all images
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting batch passport analysis for {len(photos)} images")
        
        results = []
        success_count = 0
        error_count = 0
        
        for photo in photos:
            result = self.analyze_passport(photo, bucket)
            results.append({
                'photo': photo,
                'result': result
            })
            
            if result.get('success'):
                success_count += 1
            else:
                error_count += 1
        
        logger.info(f"Batch analysis complete: {success_count} successful, {error_count} errors")
        
        return {
            'success': error_count == 0,
            'total_processed': len(photos),
            'successful': success_count,
            'errors': error_count,
            'results': results
        }
