# -*- coding: utf-8 -*-
"""
AWS Textract Birth Certificate Analysis Module
Specialized module for extracting text from Mexican birth certificates (Actas de Nacimiento)
Uses Textract's detect_document_text with optimized image preprocessing for OCR quality
"""

import boto3
import json
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
from decouple import config
import logging
import io
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger('apirest.textract_birth_certificate')


class TextractBirthCertificateAnalyzer:
    """
    Class specialized for extracting text from Mexican birth certificates
    Uses AWS Textract's detect_document_text with optimized image preprocessing
    """
    
    def __init__(self):
        """Initialize AWS Textract and S3 clients with credentials from environment variables"""
        try:
            # Get credentials from environment variables
            self.aws_access_key = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info("Initializing TextractBirthCertificateAnalyzer")
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
            
            logger.info("AWS Textract and S3 clients initialized successfully for birth certificate processing")
            
        except Exception as e:
            logger.error(f"Failed to initialize TextractBirthCertificateAnalyzer: {str(e)}")
            raise
    
    def _preprocess_image_for_ocr(self, image_bytes, filename):
        """
        Preprocess image to optimize OCR quality for birth certificates
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename for logging
            
        Returns:
            bytes: Preprocessed image bytes optimized for OCR
        """
        logger.info(f"Starting image preprocessing for birth certificate: {filename}")
        
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            original_mode = image.mode
            logger.debug(f"Original image: {original_size}, mode: {original_mode}")
            
            # Convert to RGB if necessary (Textract works best with RGB)
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.debug(f"Converted image mode from {original_mode} to RGB")
            
            # Step 1: Enhance contrast for better text visibility
            contrast_enhancer = ImageEnhance.Contrast(image)
            image = contrast_enhancer.enhance(1.3)  # Increase contrast by 30%
            logger.debug("Applied contrast enhancement (1.3x)")
            
            # Step 2: Enhance sharpness for clearer text edges
            sharpness_enhancer = ImageEnhance.Sharpness(image)
            image = sharpness_enhancer.enhance(1.5)  # Increase sharpness by 50%
            logger.debug("Applied sharpness enhancement (1.5x)")
            
            # Step 3: Slight brightness adjustment for washed-out documents
            brightness_enhancer = ImageEnhance.Brightness(image)
            image = brightness_enhancer.enhance(1.05)  # Slight brightness increase
            logger.debug("Applied brightness enhancement (1.05x)")
            
            # Step 4: Apply unsharp mask for text edge enhancement
            image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=100, threshold=2))
            logger.debug("Applied UnsharpMask filter")
            
            # Step 5: Ensure minimum resolution for OCR (Textract works best with high resolution)
            min_dimension = 1500  # Minimum pixels for smallest dimension
            width, height = image.size
            
            if width < min_dimension or height < min_dimension:
                # Scale up while maintaining aspect ratio
                scale_factor = max(min_dimension / width, min_dimension / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"Scaled up image from {(width, height)} to {(new_width, new_height)}")
            
            # Step 6: Ensure maximum size for Textract (5MB limit for synchronous operations)
            max_size_bytes = 4.5 * 1024 * 1024  # 4.5MB to leave margin
            
            # Save to bytes and check size
            output_buffer = io.BytesIO()
            quality = 95
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            
            # Reduce quality if necessary to meet size limit
            while output_buffer.tell() > max_size_bytes and quality > 60:
                output_buffer = io.BytesIO()
                quality -= 5
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                logger.debug(f"Reduced JPEG quality to {quality}%, size: {output_buffer.tell() / (1024*1024):.2f}MB")
            
            # If still too large, reduce dimensions
            if output_buffer.tell() > max_size_bytes:
                current_width, current_height = image.size
                scale = 0.9
                while output_buffer.tell() > max_size_bytes and scale > 0.5:
                    new_width = int(current_width * scale)
                    new_height = int(current_height * scale)
                    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Apply sharpening after resize
                    resized_image = resized_image.filter(
                        ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=2)
                    )
                    
                    output_buffer = io.BytesIO()
                    resized_image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                    scale -= 0.05
                    logger.debug(f"Reduced dimensions to {(new_width, new_height)}, size: {output_buffer.tell() / (1024*1024):.2f}MB")
            
            final_size = output_buffer.tell()
            output_buffer.seek(0)
            
            logger.info(f"Image preprocessing completed for {filename}: "
                       f"Original {original_size} -> Final size {final_size / (1024*1024):.2f}MB")
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error preprocessing image {filename}: {str(e)}")
            # Return original bytes if preprocessing fails
            return image_bytes
    
    def analyze_birth_certificate(self, document_name, bucket_name=None, preprocess=True):
        """
        Extract text from birth certificate using Textract's detect_document_text
        with optional image preprocessing for better OCR quality
        
        Args:
            document_name (str): Name of the document file in S3
            bucket_name (str, optional): S3 bucket name, defaults to config value
            preprocess (bool): Whether to apply image preprocessing (default: True)
            
        Returns:
            dict: Processed results with extracted text
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
            
        logger.info(f"Starting Textract birth certificate analysis for: {document_name}")
        logger.debug(f"Using bucket: {bucket_name}, preprocess: {preprocess}")
        
        try:
            # Download image from S3
            logger.debug(f"Downloading image from S3: {bucket_name}/{document_name}")
            response = self.s3_client.get_object(Bucket=bucket_name, Key=document_name)
            image_bytes = response['Body'].read()
            original_size = len(image_bytes)
            logger.debug(f"Downloaded image size: {original_size / (1024*1024):.2f}MB")
            
            # Preprocess image if enabled
            if preprocess:
                image_bytes = self._preprocess_image_for_ocr(image_bytes, document_name)
                processed_size = len(image_bytes)
                logger.debug(f"Preprocessed image size: {processed_size / (1024*1024):.2f}MB")
            
            # Call Textract detect_document_text with bytes
            logger.debug("Calling Textract detect_document_text API with preprocessed image")
            textract_response = self.textract_client.detect_document_text(
                Document={
                    'Bytes': image_bytes
                }
            )
            
            logger.info("Textract detect_document_text completed successfully")
            logger.debug(f"Response contains {len(textract_response.get('Blocks', []))} blocks")
            
            # Process the response
            processed_result = self._process_birth_certificate_response(
                textract_response, 
                document_name,
                preprocess
            )
            
            logger.info(f"Birth certificate analysis completed - "
                       f"Found {processed_result.get('total_lines', 0)} lines, "
                       f"{processed_result.get('total_words', 0)} words")
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Error in analyze_birth_certificate: {str(e)}")
            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'TEXTRACT_BIRTH_CERTIFICATE_ERROR',
                'document_name': document_name,
                'bucket_name': bucket_name,
                'text_blocks': [],
                'lines': [],
                'words': [],
                'full_text': '',
                'raw_response': None
            }
            return error_result
    
    def _process_birth_certificate_response(self, response, document_name, preprocessed=True):
        """
        Process the raw Textract detect_document_text response
        
        Args:
            response (dict): Raw response from Textract detect_document_text
            document_name (str): Name of the processed document
            preprocessed (bool): Whether image was preprocessed
            
        Returns:
            dict: Processed and structured response
        """
        logger.debug("Processing Textract birth certificate response")
        
        try:
            text_blocks = []
            lines = []
            words = []
            full_text_parts = []
            
            # Calculate average confidence
            confidences = []
            
            # Process each block
            for block in response.get('Blocks', []):
                block_type = block.get('BlockType', '')
                text = block.get('Text', '')
                confidence = block.get('Confidence', 0)
                
                block_info = {
                    'block_type': block_type,
                    'text': text,
                    'confidence': confidence,
                    'id': block.get('Id', ''),
                    'geometry': block.get('Geometry', {})
                }
                
                text_blocks.append(block_info)
                
                if block_type == 'LINE':
                    lines.append({
                        'text': text,
                        'confidence': confidence,
                        'geometry': block.get('Geometry', {})
                    })
                    full_text_parts.append(text)
                    if confidence > 0:
                        confidences.append(confidence)
                        
                elif block_type == 'WORD':
                    words.append({
                        'text': text,
                        'confidence': confidence
                    })
            
            # Join all text
            full_text = '\n'.join(full_text_parts)
            
            # Calculate statistics
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            low_confidence_count = sum(1 for c in confidences if c < 80)
            
            processed_result = {
                'success': True,
                'document_name': document_name,
                'document_type': 'birth_certificate',
                'processing_method': 'textract_detect_document_text',
                'preprocessed': preprocessed,
                'document_metadata': response.get('DocumentMetadata', {}),
                'text_blocks': text_blocks,
                'lines': lines,
                'words': words,
                'full_text': full_text,
                'statistics': {
                    'total_blocks': len(text_blocks),
                    'total_lines': len(lines),
                    'total_words': len(words),
                    'average_confidence': round(avg_confidence, 2),
                    'low_confidence_lines': low_confidence_count,
                    'high_quality': avg_confidence >= 90 and low_confidence_count < 5
                },
                'total_blocks': len(text_blocks),
                'total_lines': len(lines),
                'total_words': len(words),
                'raw_response': response
            }
            
            logger.info(f"Birth certificate processing completed - Avg confidence: {avg_confidence:.2f}%")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing birth certificate response: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing response: {str(e)}',
                'error_code': 'BIRTH_CERTIFICATE_RESPONSE_PROCESSING_ERROR',
                'document_name': document_name,
                'text_blocks': [],
                'full_text': '',
                'raw_response': response
            }
    
    def analyze_birth_certificate_batch(self, file_list, bucket_name=None, preprocess=True):
        """
        Process multiple birth certificate files and combine results
        Useful for multi-page birth certificates or batches
        
        Args:
            file_list (list): List of filenames to process
            bucket_name (str, optional): S3 bucket name
            preprocess (bool): Whether to apply image preprocessing
            
        Returns:
            dict: Combined batch results
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
            
        logger.info(f"Starting batch birth certificate processing for {len(file_list)} files")
        
        batch_results = {
            'success': True,
            'files_processed': len(file_list),
            'files_successful': 0,
            'files_failed': 0,
            'combined_response': {
                'TextBlocks': [],
                'Lines': [],
                'Words': [],
                'FullText': '',
                'BatchMetadata': []
            },
            'individual_results': [],
            'errors': [],
            'metadata': {
                'batch_id': datetime.now().isoformat(),
                'processing_type': 'batch_birth_certificate_textract',
                'total_lines': 0,
                'total_words': 0,
                'bucket': bucket_name,
                'preprocessed': preprocess,
                'processed_files': []
            }
        }
        
        full_text_parts = []
        all_confidences = []
        
        for index, filename in enumerate(file_list):
            logger.info(f"Processing birth certificate {index + 1}/{len(file_list)}: {filename}")
            
            try:
                # Process individual file
                single_result = self.analyze_birth_certificate(
                    filename, 
                    bucket_name, 
                    preprocess=preprocess
                )
                
                if single_result['success']:
                    # Add lines to combined result with page info
                    for line in single_result.get('lines', []):
                        line_with_source = line.copy()
                        line_with_source['source_file'] = filename
                        line_with_source['page_number'] = index + 1
                        batch_results['combined_response']['Lines'].append(line_with_source)
                        all_confidences.append(line.get('confidence', 0))
                    
                    # Add words to combined result
                    for word in single_result.get('words', []):
                        word_with_source = word.copy()
                        word_with_source['source_file'] = filename
                        word_with_source['page_number'] = index + 1
                        batch_results['combined_response']['Words'].append(word_with_source)
                    
                    # Add to full text
                    if single_result.get('full_text'):
                        full_text_parts.append(f"--- Página {index + 1}: {filename} ---")
                        full_text_parts.append(single_result['full_text'])
                    
                    batch_results['combined_response']['BatchMetadata'].append({
                        'filename': filename,
                        'page_number': index + 1,
                        'lines_count': len(single_result.get('lines', [])),
                        'words_count': len(single_result.get('words', [])),
                        'average_confidence': single_result.get('statistics', {}).get('average_confidence', 0),
                        'success': True
                    })
                    
                    batch_results['files_successful'] += 1
                    batch_results['metadata']['processed_files'].append({
                        'filename': filename,
                        'page_number': index + 1,
                        'status': 'success',
                        'lines': len(single_result.get('lines', [])),
                        'words': len(single_result.get('words', []))
                    })
                    
                    logger.info(f"Successfully processed {filename}: "
                               f"{len(single_result.get('lines', []))} lines")
                    
                else:
                    batch_results['files_failed'] += 1
                    error_info = {
                        'filename': filename,
                        'page_number': index + 1,
                        'error': single_result.get('error', 'Unknown error'),
                        'error_code': single_result.get('error_code', 'UNKNOWN')
                    }
                    batch_results['errors'].append(error_info)
                    batch_results['metadata']['processed_files'].append({
                        'filename': filename,
                        'page_number': index + 1,
                        'status': 'failed',
                        'error': single_result.get('error')
                    })
                    
                    logger.error(f"Failed to process {filename}: {single_result.get('error')}")
                
                # Store individual result
                batch_results['individual_results'].append({
                    'filename': filename,
                    'page_number': index + 1,
                    'result': single_result
                })
                
            except Exception as e:
                batch_results['files_failed'] += 1
                error_info = {
                    'filename': filename,
                    'page_number': index + 1,
                    'error': str(e),
                    'error_code': '500_Processing_Error'
                }
                batch_results['errors'].append(error_info)
                batch_results['metadata']['processed_files'].append({
                    'filename': filename,
                    'page_number': index + 1,
                    'status': 'exception',
                    'error': str(e)
                })
                
                logger.error(f"Exception processing {filename}: {str(e)}")
        
        # Combine full text
        batch_results['combined_response']['FullText'] = '\n\n'.join(full_text_parts)
        
        # Update metadata
        batch_results['metadata']['total_lines'] = len(batch_results['combined_response']['Lines'])
        batch_results['metadata']['total_words'] = len(batch_results['combined_response']['Words'])
        batch_results['metadata']['average_confidence'] = (
            round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else 0
        )
        batch_results['success'] = batch_results['files_failed'] == 0
        
        logger.info(f"Batch birth certificate processing completed: "
                   f"{batch_results['files_successful']} successful, "
                   f"{batch_results['files_failed']} failed, "
                   f"Average confidence: {batch_results['metadata']['average_confidence']}%")
        
        return batch_results
    
    def get_processing_info(self):
        """
        Returns information about the current processor configuration
        """
        return {
            'processor_type': 'Birth Certificate Textract Analyzer',
            'version': '1.0',
            'aws_region': self.region_name,
            'aws_bucket': self.bucket_name,
            'service': 'AWS Textract',
            'api_method': 'detect_document_text',
            'features': [
                'Image preprocessing for OCR optimization',
                'Contrast enhancement',
                'Sharpness enhancement',
                'Automatic size optimization',
                'Batch processing support',
                'Confidence statistics'
            ],
            'description': 'Specialized processor for Mexican birth certificates using AWS Textract with image preprocessing'
        }
