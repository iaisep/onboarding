# -*- coding: utf-8 -*-
"""
AWS Textract Certificate/Transcript Analysis Module
Specialized module for extracting text and tables from academic certificates and transcripts
Uses Textract's analyze_document with TABLES feature for structured data extraction
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
logger = logging.getLogger('apirest.textract_certificado')


class TextractCertificadoAnalyzer:
    """
    Class specialized for extracting text and tables from academic certificates
    Uses AWS Textract's analyze_document with TABLES and FORMS features
    Optimized for grade transcripts, certificates, and structured academic documents
    """
    
    def __init__(self):
        """Initialize AWS Textract and S3 clients with credentials from environment variables"""
        try:
            # Get credentials from environment variables
            self.aws_access_key = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info("Initializing TextractCertificadoAnalyzer")
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
            
            logger.info("AWS Textract and S3 clients initialized successfully for certificate processing")
            
        except Exception as e:
            logger.error(f"Failed to initialize TextractCertificadoAnalyzer: {str(e)}")
            raise
    
    def _enhance_for_document_ocr(self, image):
        """
        Apply enhancements specifically optimized for printed documents with tables
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Enhanced image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            logger.debug("Converted image mode to RGB")
        
        # Step 1: Auto-contrast to normalize lighting
        image = ImageOps.autocontrast(image, cutoff=0.5)
        logger.debug("Applied auto-contrast")
        
        # Step 2: Increase contrast for better text visibility
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.3)
        logger.debug("Applied contrast enhancement (1.3x)")
        
        # Step 3: Increase sharpness for clear text
        sharpness_enhancer = ImageEnhance.Sharpness(image)
        image = sharpness_enhancer.enhance(1.8)
        logger.debug("Applied sharpness enhancement (1.8x)")
        
        # Step 4: Slight brightness adjustment for white backgrounds
        brightness_enhancer = ImageEnhance.Brightness(image)
        image = brightness_enhancer.enhance(1.02)
        logger.debug("Applied brightness enhancement (1.02x)")
        
        # Step 5: Apply unsharp mask for crisp text
        image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
        logger.debug("Applied UnsharpMask filter")
        
        return image
    
    def _ensure_optimal_resolution(self, image):
        """
        Ensure the image has optimal resolution for Textract table detection
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL Image: Image with optimal resolution
        """
        width, height = image.size
        
        # For documents with tables, we need good resolution
        min_long_side = 2000
        max_long_side = 4000
        
        long_side = max(width, height)
        
        if long_side < min_long_side:
            scale_factor = min_long_side / long_side
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Scaled up from ({width}, {height}) to ({new_width}, {new_height})")
            
            # Re-apply sharpening after upscale
            image = image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=2))
            
        elif long_side > max_long_side:
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
        
        while output_buffer.tell() > max_size_bytes and quality > 70:
            output_buffer = io.BytesIO()
            quality -= 5
            image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            logger.debug(f"Reduced quality to {quality}%, size: {output_buffer.tell() / (1024*1024):.2f}MB")
        
        if output_buffer.tell() > max_size_bytes:
            width, height = image.size
            scale = 0.9
            while output_buffer.tell() > max_size_bytes and scale > 0.6:
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized = resized.filter(ImageFilter.UnsharpMask(radius=1.0, percent=100, threshold=2))
                
                output_buffer = io.BytesIO()
                resized.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                scale -= 0.05
                logger.debug(f"Reduced dimensions, size: {output_buffer.tell() / (1024*1024):.2f}MB")
        
        output_buffer.seek(0)
        return output_buffer.getvalue()
    
    def _preprocess_image(self, image_bytes, filename):
        """
        Complete preprocessing pipeline for certificate/transcript images
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename for logging
            
        Returns:
            bytes: Preprocessed image bytes
        """
        logger.info(f"Starting certificate image preprocessing: {filename}")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            logger.debug(f"Original image: {original_size}, mode: {image.mode}")
            
            # Apply enhancements
            image = self._enhance_for_document_ocr(image)
            
            # Ensure optimal resolution
            image = self._ensure_optimal_resolution(image)
            
            # Compress to size limit
            processed_bytes = self._compress_to_size_limit(image)
            
            final_size = len(processed_bytes) / (1024 * 1024)
            logger.info(f"Preprocessing complete. Final size: {final_size:.2f}MB")
            
            return processed_bytes
            
        except Exception as e:
            logger.error(f"Error preprocessing certificate image: {str(e)}")
            raise
    
    def _extract_tables_from_blocks(self, blocks):
        """
        Extract table data from Textract blocks
        
        Args:
            blocks: List of Textract blocks
            
        Returns:
            list: List of extracted tables with rows and cells
        """
        tables = []
        table_blocks = {}
        cell_blocks = {}
        word_blocks = {}
        
        # First pass: categorize blocks
        for block in blocks:
            block_id = block.get('Id', '')
            block_type = block.get('BlockType', '')
            
            if block_type == 'TABLE':
                table_blocks[block_id] = block
            elif block_type == 'CELL':
                cell_blocks[block_id] = block
            elif block_type == 'WORD':
                word_blocks[block_id] = block
        
        # Second pass: build tables
        for table_id, table_block in table_blocks.items():
            table_data = {
                'table_id': table_id,
                'rows': {},
                'confidence': table_block.get('Confidence', 0)
            }
            
            # Get cells in this table
            relationships = table_block.get('Relationships', [])
            for rel in relationships:
                if rel.get('Type') == 'CHILD':
                    for cell_id in rel.get('Ids', []):
                        if cell_id in cell_blocks:
                            cell = cell_blocks[cell_id]
                            row_idx = cell.get('RowIndex', 0)
                            col_idx = cell.get('ColumnIndex', 0)
                            
                            # Get cell text
                            cell_text = ''
                            cell_rels = cell.get('Relationships', [])
                            for cell_rel in cell_rels:
                                if cell_rel.get('Type') == 'CHILD':
                                    for word_id in cell_rel.get('Ids', []):
                                        if word_id in word_blocks:
                                            word_text = word_blocks[word_id].get('Text', '')
                                            cell_text += word_text + ' '
                            
                            cell_text = cell_text.strip()
                            
                            if row_idx not in table_data['rows']:
                                table_data['rows'][row_idx] = {}
                            
                            table_data['rows'][row_idx][col_idx] = {
                                'text': cell_text,
                                'confidence': cell.get('Confidence', 0),
                                'row_span': cell.get('RowSpan', 1),
                                'col_span': cell.get('ColumnSpan', 1)
                            }
            
            # Convert rows dict to list
            table_rows = []
            for row_idx in sorted(table_data['rows'].keys()):
                row_cells = []
                for col_idx in sorted(table_data['rows'][row_idx].keys()):
                    row_cells.append(table_data['rows'][row_idx][col_idx])
                table_rows.append(row_cells)
            
            table_data['rows'] = table_rows
            tables.append(table_data)
        
        return tables
    
    def _extract_grades_from_tables(self, tables):
        """
        Extract grade information from detected tables
        
        Args:
            tables: List of extracted tables
            
        Returns:
            list: List of grade entries (codigo, asignatura, calificacion)
        """
        grades = []
        
        for table in tables:
            for row in table.get('rows', []):
                if len(row) >= 2:
                    # Try to identify code, subject, and grade
                    row_texts = [cell.get('text', '') for cell in row]
                    
                    # Look for patterns like MTNP01, MTNP02, etc.
                    code_pattern = re.compile(r'^[A-Z]{2,5}\d{2,3}$')
                    grade_pattern = re.compile(r'^\d{1,2}(\.\d{1,2})?$')
                    
                    code = None
                    subject = None
                    grade = None
                    
                    for i, text in enumerate(row_texts):
                        text_clean = text.strip()
                        
                        if code_pattern.match(text_clean):
                            code = text_clean
                        elif grade_pattern.match(text_clean):
                            grade = text_clean
                        elif len(text_clean) > 5 and not code and not grade:
                            # Likely the subject name
                            if subject:
                                subject += ' ' + text_clean
                            else:
                                subject = text_clean
                    
                    if code or subject or grade:
                        grades.append({
                            'codigo': code,
                            'asignatura': subject,
                            'calificacion': grade,
                            'raw_row': row_texts
                        })
        
        return grades
    
    def _extract_student_info(self, lines):
        """
        Extract student information from text lines
        
        Args:
            lines: List of text lines
            
        Returns:
            dict: Student information
        """
        info = {
            'nombre': None,
            'matricula': None,
            'programa': None,
            'fecha_certificado': None
        }
        
        full_text = ' '.join([line.get('text', '') for line in lines])
        
        # Look for matricula pattern (AD followed by numbers)
        matricula_match = re.search(r'matrícula\s*([A-Z]{1,3}\d{4,6})', full_text, re.IGNORECASE)
        if matricula_match:
            info['matricula'] = matricula_match.group(1)
        
        # Look for name after "Que" and before "con número"
        name_match = re.search(r'Que\s+(.+?)\s+con\s+número', full_text, re.IGNORECASE)
        if name_match:
            info['nombre'] = name_match.group(1).strip()
        
        # Look for program (MÁSTER, MAESTRÍA, etc.)
        program_match = re.search(r'(M[ÁA]STER\s+EN\s+[A-ZÁÉÍÓÚÑ\s]+|MAESTR[ÍI]A\s+EN\s+[A-ZÁÉÍÓÚÑ\s]+)', full_text, re.IGNORECASE)
        if program_match:
            info['programa'] = program_match.group(1).strip()
        
        # Look for date
        date_match = re.search(r'(\d{1,2}\s+(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4})', full_text, re.IGNORECASE)
        if date_match:
            info['fecha_certificado'] = date_match.group(1)
        
        return info
    
    def analyze_certificado(self, photo, bucket=None):
        """
        Analyze a certificate/transcript image using AWS Textract with table detection
        
        Args:
            photo: S3 key of the image file
            bucket: S3 bucket name (optional)
            
        Returns:
            dict: Complete analysis results with extracted text and tables
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting certificate analysis for: {photo} in bucket: {bucket}")
        
        if not photo or not isinstance(photo, str):
            return {
                'success': False,
                'error': f'Invalid photo parameter: {photo}',
                'error_code': '400_Invalid_Parameters'
            }
        
        temp_file = None
        
        try:
            # Download file from S3
            temp_file = f'temp_cert_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.tmp'
            logger.debug(f"Downloading from S3: {bucket}/{photo}")
            
            self.s3_client.download_file(bucket, photo, temp_file)
            
            with open(temp_file, 'rb') as f:
                original_bytes = f.read()
            
            logger.info(f"Downloaded certificate image: {len(original_bytes) / (1024*1024):.2f}MB")
            
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
            # Preprocess the image
            processed_bytes = self._preprocess_image(original_bytes, photo)
            
            # Call Textract with TABLES and FORMS features
            logger.info("Calling AWS Textract analyze_document with TABLES feature")
            
            response = self.textract_client.analyze_document(
                Document={'Bytes': processed_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            blocks = response.get('Blocks', [])
            logger.info(f"Textract response received with {len(blocks)} blocks")
            
            # Extract text lines and words
            lines = []
            words = []
            all_text = []
            
            for block in blocks:
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
            
            # Extract tables
            tables = self._extract_tables_from_blocks(blocks)
            logger.info(f"Extracted {len(tables)} tables from document")
            
            # Extract grades from tables
            grades = self._extract_grades_from_tables(tables)
            logger.info(f"Extracted {len(grades)} grade entries")
            
            # Extract student info
            student_info = self._extract_student_info(lines)
            
            # Calculate average confidence
            confidences = [line['confidence'] for line in lines if line['confidence'] > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(f"Extracted {len(lines)} lines, {len(words)} words. Avg confidence: {avg_confidence:.2f}%")
            
            return {
                'success': True,
                'error': None,
                'error_code': None,
                'document_type': 'certificado_notas',
                'raw_response': response,
                'extracted_data': {
                    'lines': lines,
                    'words': words,
                    'full_text': '\n'.join(all_text),
                    'line_count': len(lines),
                    'word_count': len(words),
                    'average_confidence': round(avg_confidence, 2)
                },
                'tables': tables,
                'grades': grades,
                'student_info': student_info,
                'metadata': {
                    'photo': photo,
                    'bucket': bucket,
                    'processed_at': datetime.now().isoformat(),
                    'textract_blocks': len(blocks),
                    'tables_found': len(tables),
                    'grades_extracted': len(grades)
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
                'error': f'Error analyzing certificate: {str(e)}',
                'error_code': '500_Analysis_Error'
            }
    
    def batch_analyze(self, photos, bucket=None):
        """
        Analyze multiple certificate images
        
        Args:
            photos: List of S3 keys
            bucket: S3 bucket name
            
        Returns:
            dict: Results for all images
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting batch certificate analysis for {len(photos)} images")
        
        results = []
        success_count = 0
        error_count = 0
        all_grades = []
        
        for photo in photos:
            result = self.analyze_certificado(photo, bucket)
            results.append({
                'photo': photo,
                'result': result
            })
            
            if result.get('success'):
                success_count += 1
                # Collect grades from all pages
                all_grades.extend(result.get('grades', []))
            else:
                error_count += 1
        
        logger.info(f"Batch analysis complete: {success_count} successful, {error_count} errors")
        
        return {
            'success': error_count == 0,
            'total_processed': len(photos),
            'successful': success_count,
            'errors': error_count,
            'results': results,
            'combined_grades': all_grades,
            'total_grades_extracted': len(all_grades)
        }
