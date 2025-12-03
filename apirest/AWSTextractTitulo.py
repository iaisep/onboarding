# -*- coding: utf-8 -*-
"""
AWS Textract University Title/Degree Certificate Analysis Module
Specialized module for extracting text and tables from university degree certificates
and professional titles (Títulos de Licenciatura, Certificados Universitarios)
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
logger = logging.getLogger('apirest.textract_titulo')


class TextractUniversityTitleAnalyzer:
    """
    Class specialized for extracting text and tables from university degree certificates
    Uses AWS Textract's analyze_document with TABLES and FORMS features
    Optimized for professional titles, degree certificates with course codes and credits
    """
    
    def __init__(self):
        """Initialize AWS Textract and S3 clients with credentials from environment variables"""
        try:
            # Get credentials from environment variables
            self.aws_access_key = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY')
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info("Initializing TextractTituloAnalyzer")
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
            
            logger.info("AWS Textract and S3 clients initialized successfully for titulo processing")
            
        except Exception as e:
            logger.error(f"Failed to initialize TextractTituloAnalyzer: {str(e)}")
            raise
    
    def _enhance_for_document_ocr(self, image):
        """
        Apply enhancements specifically optimized for printed documents with tables
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            logger.debug("Converted image mode to RGB")
        
        # Auto-contrast to normalize lighting
        image = ImageOps.autocontrast(image, cutoff=0.5)
        logger.debug("Applied auto-contrast")
        
        # Increase contrast for better text visibility
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(1.4)
        logger.debug("Applied contrast enhancement (1.4x)")
        
        # Increase sharpness for clear text
        sharpness_enhancer = ImageEnhance.Sharpness(image)
        image = sharpness_enhancer.enhance(2.0)
        logger.debug("Applied sharpness enhancement (2.0x)")
        
        # Apply unsharp mask for crisp text
        image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))
        logger.debug("Applied UnsharpMask filter")
        
        return image
    
    def _ensure_optimal_resolution(self, image):
        """Ensure the image has optimal resolution for Textract table detection"""
        width, height = image.size
        
        # For documents with tables, we need good resolution
        min_long_side = 2500  # Higher for detailed tables
        max_long_side = 4500
        
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
        """Compress image to meet Textract size limit while preserving quality"""
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
        """Complete preprocessing pipeline for titulo/degree certificate images"""
        logger.info(f"Starting titulo image preprocessing: {filename}")
        
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
            logger.error(f"Error preprocessing titulo image: {str(e)}")
            raise
    
    def _extract_tables_from_blocks(self, blocks):
        """Extract table data from Textract blocks"""
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
    
    def _is_watermark_text(self, text):
        """
        Check if text is a watermark pattern that should be filtered out
        Common watermarks in Mexican educational documents
        """
        if not text:
            return False
            
        # Normalize text for comparison
        text_upper = text.upper().replace(' ', '').replace('\n', '')
        
        # Known watermark patterns (including partial fragments)
        watermark_patterns = [
            'SISTEMAEDUCATIVONACIONAL',
            'SISTEMAEDUCATIVO',
            'SISTEMAEDU',
            'SISTEMAEDI',
            'EDUCATIVONACIONAL',
            'EDUCATIVONACION',
            'EDUCATIVO',
            'ISTEMAEDUCATIVONACIONAL',
            'ISTEMAEDUCATIVO',
            'STEMAEDUCATIVONACIONAL',
            'TEMAEDUCATIVONACIONAL',
            'EMAEDUCATIVONACIONAL',
            'EMAEDUCATIVON',
            'EMAEDUCATIVOI',
            'EMAEDUCATIVO',
            'MAEDUCATIVONACIONAL',
            'MAEDUCATIVO',
            'AEDUCATIVONACIONAL',
            'AEDUCATIVO',
            'IVONACIONAL',
            'VONACIONAL',
            'ONACIONAL',
            'ONACIOSISTEMA',
        ]
        
        # If text is ONLY a watermark pattern (exact match or slight variation)
        for pattern in watermark_patterns:
            if text_upper == pattern:
                return True
            # Check if text starts with pattern and is mostly pattern
            if text_upper.startswith(pattern) and len(text_upper) < len(pattern) + 5:
                return True
        
        # Check if text contains watermark patterns
        for pattern in watermark_patterns:
            if len(pattern) >= 10 and pattern in text_upper:
                return True
        
        # Check if text is a fragment of the full watermark (at least 8 chars)
        full_watermark = 'SISTEMAEDUCATIVONACIONAL'
        if len(text_upper) >= 8 and len(text_upper) <= 30:
            if text_upper in full_watermark:
                return True
        
        # Check for repeated pattern fragments
        if len(text_upper) >= 10:
            # If text is mostly repetition of watermark fragments
            clean_text = text_upper
            for pattern in ['SISTEMAEDUCATIVONACIONAL', 'SISTEMAEDUCATIVO', 'EDUCATIVONACIONAL', 'EDUCATIVO', 'SISTEMA']:
                clean_text = clean_text.replace(pattern, '')
            if len(clean_text) < len(text_upper) * 0.3:  # More than 70% was watermark
                return True
        
        return False
    
    def _clean_watermark_from_text(self, text):
        """
        Remove watermark fragments from text that contains mixed content
        Returns cleaned text or None if text becomes empty/meaningless
        """
        if not text:
            return None
            
        original_text = text
        
        # Patterns to remove (order matters - longer patterns first)
        watermark_fragments = [
            'SISTEMAEDUCATIVONACIONAL',
            'SISTEMAEDUCATIVO',
            'EDUCATIVONACIONAL',
            'ISTEMAEDUCATIVO',
            'EMAEDUCATIVON',
            'EMAEDUCATIVO',
            'SISTEMAEDU',
            'SISTEMAEDI',
            'EDUCATIVO',
            'ONACIONAL',
            'SISTEMA',
            ' AL ',  # Common artifact
        ]
        
        text_clean = text
        for fragment in watermark_fragments:
            text_clean = re.sub(re.escape(fragment), '', text_clean, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and trim
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        
        # If text became too short or empty, return None
        if len(text_clean) < 3:
            return None
            
        # If we removed more than 50% of the text, it was mostly watermark
        if len(text_clean) < len(original_text) * 0.5:
            return None
            
        return text_clean

    def _filter_watermarks(self, items, text_key='text'):
        """
        Filter out watermark text from a list of items (lines or words)
        Also cleans mixed content where watermark appears with real text
        
        Args:
            items: List of dicts containing text data
            text_key: Key to access text in each item dict
            
        Returns:
            List of items with watermarks removed or cleaned
        """
        filtered = []
        for item in items:
            text = item.get(text_key, '')
            
            # First check if it's purely watermark
            if self._is_watermark_text(text):
                logger.debug(f"Filtered watermark text: {text[:50]}...")
                continue
            
            # Try to clean mixed content
            cleaned_text = self._clean_watermark_from_text(text)
            if cleaned_text is None:
                logger.debug(f"Filtered after cleaning: {text[:50]}...")
                continue
            
            # Update text if it was cleaned
            if cleaned_text != text:
                item = item.copy()  # Don't modify original
                item[text_key] = cleaned_text
                logger.debug(f"Cleaned text: '{text[:30]}...' -> '{cleaned_text[:30]}...'")
            
            filtered.append(item)
        
        return filtered

    def _extract_courses_from_tables(self, tables):
        """
        Extract course/subject information from detected tables
        Handles formats like: CLAVE, NOMBRE, AÑO, CALIFICACIÓN, TIPO, CRÉDITOS, OBSERVACIONES
        """
        courses = []
        
        # Pattern for course codes (PSY101, MAT201, etc.)
        code_pattern = re.compile(r'^[A-Z]{2,4}\d{2,4}[A-Z]?$')
        # Pattern for grades/scores
        grade_pattern = re.compile(r'^\d{1,2}(\.\d{1,2})?$')
        # Pattern for credits
        credit_pattern = re.compile(r'^\d{1,2}(\.\d{1,2})?$')
        # Pattern for year/period (2015-1, 2016-2, etc.)
        year_pattern = re.compile(r'^\d{4}-\d$')
        
        for table in tables:
            for row_idx, row in enumerate(table.get('rows', [])):
                if len(row) >= 3:  # At least code, name, and one more column
                    row_texts = [cell.get('text', '') for cell in row]
                    
                    course_data = {
                        'clave': None,
                        'nombre_asignatura': None,
                        'periodo': None,
                        'calificacion': None,
                        'tipo_asignatura': None,
                        'creditos': None,
                        'observaciones': None,
                        'raw_row': row_texts
                    }
                    
                    # Try to identify each column
                    for i, text in enumerate(row_texts):
                        text_clean = text.strip().upper()
                        text_original = text.strip()
                        
                        # Skip header rows
                        if text_clean in ['CLAVE', 'NOMBRE', 'ASIGNATURA', 'CALIFICACIÓN', 
                                         'CRÉDITOS', 'TIPO', 'OBSERVACIONES', 'AÑO', 
                                         'NOMBRE DE LA ASIGNATURA', 'TIPO DE ASIGNATURA',
                                         'CALIFICACION NUMERICA']:
                            course_data = None
                            break
                        
                        # Check for course code
                        if code_pattern.match(text_clean) and not course_data.get('clave'):
                            course_data['clave'] = text_clean
                        # Check for year/period
                        elif year_pattern.match(text_clean):
                            course_data['periodo'] = text_clean
                        # Check for grade (usually single or double digit with decimals)
                        elif grade_pattern.match(text_original) and i > 1:
                            if not course_data.get('calificacion'):
                                course_data['calificacion'] = text_original
                            elif not course_data.get('creditos'):
                                course_data['creditos'] = text_original
                        # Check for subject type
                        elif text_clean in ['OBLIGATORIA', 'OPTATIVA', 'ELECTIVA', 'OBLIGATORIO', 'OPTATIVO']:
                            course_data['tipo_asignatura'] = text_clean
                        # Check for observations
                        elif text_clean in ['E.E.', 'E.E', 'EE', 'AC', 'NA', 'N/A']:
                            course_data['observaciones'] = text_clean
                        # Otherwise, likely the subject name
                        elif len(text_original) > 3 and not course_data.get('nombre_asignatura'):
                            course_data['nombre_asignatura'] = text_original
                    
                    if course_data and (course_data.get('clave') or course_data.get('nombre_asignatura')):
                        courses.append(course_data)
        
        return courses
    
    def _extract_student_info(self, lines):
        """Extract student and degree information from text lines"""
        info = {
            'nombre': None,
            'curp': None,
            'carrera': None,
            'clave_carrera': None,
            'clave_plan': None,
            'institucion': None,
            'campus': None,
            'folio': None,
            'fecha_expedicion': None,
            'promedio': None,
            'total_asignaturas': None,
            'total_creditos': None,
            'creditos_requeridos': None
        }
        
        full_text = ' '.join([line.get('text', '') for line in lines])
        
        # Look for CURP
        curp_match = re.search(r'CURP[:\s]+([A-Z]{4}\d{6}[A-Z]{6}\d{2})', full_text, re.IGNORECASE)
        if curp_match:
            info['curp'] = curp_match.group(1)
        
        # Look for name after "Hace constar que" or "constar que"
        name_match = re.search(r'(?:Hace\s+)?constar\s+que\s+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+con|\s+CURP)', full_text, re.IGNORECASE)
        if name_match:
            info['nombre'] = name_match.group(1).strip()
        
        # Look for career/degree
        career_match = re.search(r'(?:acredit[óo]|cursó)\s+(LICENCIATURA\s+EN\s+[A-ZÁÉÍÓÚÑ\s]+|INGENIERÍA\s+EN\s+[A-ZÁÉÍÓÚÑ\s]+|MAESTRÍA\s+EN\s+[A-ZÁÉÍÓÚÑ\s]+)', full_text, re.IGNORECASE)
        if career_match:
            info['carrera'] = career_match.group(1).strip()
        
        # Look for career code
        clave_carrera_match = re.search(r'clave\s+de\s+carrera[:\s]+(\d+)', full_text, re.IGNORECASE)
        if clave_carrera_match:
            info['clave_carrera'] = clave_carrera_match.group(1)
        
        # Look for plan code
        clave_plan_match = re.search(r'clave\s+del\s+plan[:\s]+(\d+)', full_text, re.IGNORECASE)
        if clave_plan_match:
            info['clave_plan'] = clave_plan_match.group(1)
        
        # Look for institution
        inst_match = re.search(r'(CENTRO\s+DE\s+ESTUDIOS\s+[A-ZÁÉÍÓÚÑ\s]+|UNIVERSIDAD\s+[A-ZÁÉÍÓÚÑ\s]+)', full_text, re.IGNORECASE)
        if inst_match:
            info['institucion'] = inst_match.group(1).strip()
        
        # Look for campus
        campus_match = re.search(r'Campus[:\s]+([A-ZÁÉÍÓÚÑ\s]+?)(?:\s+Hace|\s+con|\s+CURP|$)', full_text, re.IGNORECASE)
        if campus_match:
            info['campus'] = campus_match.group(1).strip()
        
        # Look for folio
        folio_match = re.search(r'Folio[:\s]+([a-zA-Z0-9\-]+)', full_text, re.IGNORECASE)
        if folio_match:
            info['folio'] = folio_match.group(1)
        
        # Look for average/promedio
        promedio_match = re.search(r'promedio\s+(?:de\s+)?(\d{1,2}\.\d{1,2})', full_text, re.IGNORECASE)
        if promedio_match:
            info['promedio'] = promedio_match.group(1)
        
        # Look for total subjects
        asig_match = re.search(r'(\d+)\s+asignaturas\s+de\s+un\s+total\s+de\s+(\d+)', full_text, re.IGNORECASE)
        if asig_match:
            info['total_asignaturas'] = asig_match.group(2)
        
        # Look for credits
        creditos_match = re.search(r'total\s+de\s+(\d+(?:\.\d+)?)\s+créditos\s+de\s+un\s+mínimo\s+de\s+(\d+(?:\.\d+)?)', full_text, re.IGNORECASE)
        if creditos_match:
            info['total_creditos'] = creditos_match.group(1)
            info['creditos_requeridos'] = creditos_match.group(2)
        
        # Look for expedition date
        date_match = re.search(r'(?:Fecha\s+de\s+expedición|expedición)[:\s]+(\d{1,2}\s+DE\s+[A-Z]+\s+DE\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})', full_text, re.IGNORECASE)
        if date_match:
            info['fecha_expedicion'] = date_match.group(1)
        
        return info
    
    def analyze_titulo(self, photo, bucket=None):
        """
        Analyze a university degree certificate using AWS Textract with table detection
        
        Args:
            photo: S3 key of the image file
            bucket: S3 bucket name (optional)
            
        Returns:
            dict: Complete analysis results with extracted text and tables
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting titulo analysis for: {photo} in bucket: {bucket}")
        
        if not photo or not isinstance(photo, str):
            return {
                'success': False,
                'error': f'Invalid photo parameter: {photo}',
                'error_code': '400_Invalid_Parameters'
            }
        
        temp_file = None
        
        try:
            # Download file from S3
            temp_file = f'temp_titulo_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.tmp'
            logger.debug(f"Downloading from S3: {bucket}/{photo}")
            
            self.s3_client.download_file(bucket, photo, temp_file)
            
            with open(temp_file, 'rb') as f:
                original_bytes = f.read()
            
            logger.info(f"Downloaded titulo image: {len(original_bytes) / (1024*1024):.2f}MB")
            
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
            logger.info("Calling AWS Textract analyze_document with TABLES feature for titulo")
            
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
                    
                elif block['BlockType'] == 'WORD':
                    word_data = {
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'geometry': block.get('Geometry', {})
                    }
                    words.append(word_data)
            
            # Filter out watermarks from lines and words
            original_lines_count = len(lines)
            original_words_count = len(words)
            
            lines = self._filter_watermarks(lines, 'text')
            words = self._filter_watermarks(words, 'text')
            
            logger.info(f"Watermark filtering: Lines {original_lines_count} -> {len(lines)}, "
                       f"Words {original_words_count} -> {len(words)}")
            
            # Build all_text from filtered lines
            all_text = [line.get('text', '') for line in lines]
            
            # Extract tables
            tables = self._extract_tables_from_blocks(blocks)
            logger.info(f"Extracted {len(tables)} tables from document")
            
            # Extract courses from tables
            courses = self._extract_courses_from_tables(tables)
            logger.info(f"Extracted {len(courses)} course entries")
            
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
                'document_type': 'titulo_licenciatura',
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
                'courses': courses,
                'student_info': student_info,
                'metadata': {
                    'photo': photo,
                    'bucket': bucket,
                    'processed_at': datetime.now().isoformat(),
                    'textract_blocks': len(blocks),
                    'tables_found': len(tables),
                    'courses_extracted': len(courses)
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
                'error': f'Error analyzing titulo: {str(e)}',
                'error_code': '500_Analysis_Error'
            }
    
    def analyze_batch(self, photos, bucket=None):
        """
        Analyze multiple degree certificate images
        
        Args:
            photos: List of S3 keys
            bucket: S3 bucket name
            
        Returns:
            dict: Results for all images
        """
        if bucket is None:
            bucket = self.bucket_name
            
        logger.info(f"Starting batch titulo analysis for {len(photos)} images")
        
        results = []
        success_count = 0
        error_count = 0
        all_courses = []
        
        for photo in photos:
            result = self.analyze_titulo(photo, bucket)
            results.append({
                'photo': photo,
                'result': result
            })
            
            if result.get('success'):
                success_count += 1
                # Collect courses from all pages
                all_courses.extend(result.get('courses', []))
            else:
                error_count += 1
        
        logger.info(f"Batch analysis complete: {success_count} successful, {error_count} errors")
        
        return {
            'success': error_count == 0,
            'total_processed': len(photos),
            'successful': success_count,
            'errors': error_count,
            'results': results,
            'combined_courses': all_courses,
            'total_courses_extracted': len(all_courses)
        }
