"""
AWS Textract ID Analysis Module
Extracts text from identity documents using Amazon Textract's analyze_id feature
"""

import boto3
import json
import pandas as pd
from decouple import config
import logging

# Configure logger
logger = logging.getLogger('apirest.aws')

class TextractIDAnalyzer:
    """
    Class to extract text from identity documents using AWS Textract's analyze_id
    Optimized for ID cards, passports, driver's licenses and other identity documents
    """
    
    def __init__(self):
        """Initialize AWS Textract client with credentials from environment variables"""
        try:
            # Get credentials from environment variables
            self.aws_access_key = config('AWS_ACCESS_KEY_ID')
            self.aws_secret_key = config('AWS_SECRET_ACCESS_KEY') 
            self.region_name = config('AWS_DEFAULT_REGION', default='us-east-1')
            self.bucket_name = config('AWS_S3_BUCKET', default='onboarding-uisep')
            
            logger.info("Initializing TextractIDAnalyzer")
            logger.debug(f"Region: {self.region_name}, Bucket: {self.bucket_name}")
            
            # Initialize Textract client
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region_name
            )
            
            logger.info("AWS Textract client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TextractIDAnalyzer: {str(e)}")
            raise
    
    def analyze_id_document(self, document_name, bucket_name=None):
        """
        Extract text from identity document using Textract's analyze_id
        
        Args:
            document_name (str): Name of the document file in S3
            bucket_name (str, optional): S3 bucket name, defaults to config value
            
        Returns:
            dict: Processed results with extracted information
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
            
        logger.info(f"Starting Textract ID analysis for document: {document_name}")
        logger.debug(f"Using bucket: {bucket_name}")
        
        try:
            # Call Textract analyze_id
            logger.debug("Calling Textract analyze_id API")
            response = self.textract_client.analyze_id(
                DocumentPages=[
                    {
                        'S3Object': {
                            'Bucket': bucket_name,
                            'Name': document_name
                        }
                    }
                ]
            )
            
            logger.info("Textract analyze_id completed successfully")
            logger.debug(f"Response contains {len(response.get('IdentityDocuments', []))} identity documents")
            
            # Process the response
            processed_result = self._process_analyze_id_response(response, document_name)
            
            logger.info(f"ID analysis completed - Found {len(processed_result.get('extracted_fields', []))} fields")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error in analyze_id_document: {str(e)}")
            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'TEXTRACT_ANALYZE_ID_ERROR',
                'document_name': document_name,
                'bucket_name': bucket_name,
                'extracted_fields': [],
                'raw_response': None
            }
            return error_result
    
    def _process_analyze_id_response(self, response, document_name):
        """
        Process the raw Textract analyze_id response into structured data
        
        Args:
            response (dict): Raw response from Textract analyze_id
            document_name (str): Name of the processed document
            
        Returns:
            dict: Processed and structured response
        """
        logger.debug("Processing Textract analyze_id response")
        
        try:
            processed_data = {
                'success': True,
                'document_name': document_name,
                'document_metadata': response.get('DocumentMetadata', {}),
                'extracted_fields': [],
                'identity_documents': [],
                'raw_response': response
            }
            
            # Process each identity document found
            for doc_index, identity_doc in enumerate(response.get('IdentityDocuments', [])):
                logger.debug(f"Processing identity document {doc_index + 1}")
                
                doc_info = {
                    'document_index': doc_index + 1,
                    'identity_document_fields': [],
                    'blocks': identity_doc.get('Blocks', [])
                }
                
                # Extract identity document fields
                for field in identity_doc.get('IdentityDocumentFields', []):
                    field_type = field.get('Type', {})
                    field_value = field.get('ValueDetection', {})
                    
                    extracted_field = {
                        'field_type': field_type.get('Text', ''),
                        'field_confidence': field_type.get('Confidence', 0),
                        'field_value': field_value.get('Text', ''),
                        'value_confidence': field_value.get('Confidence', 0),
                        'normalized_value': field_value.get('NormalizedValue', {})
                    }
                    
                    doc_info['identity_document_fields'].append(extracted_field)
                    processed_data['extracted_fields'].append(extracted_field)
                    
                    logger.debug(f"Extracted field: {extracted_field['field_type']} = {extracted_field['field_value']}")
                
                processed_data['identity_documents'].append(doc_info)
            
            # Create pandas DataFrame for consistency with other modules
            if processed_data['extracted_fields']:
                df_data = []
                for field in processed_data['extracted_fields']:
                    df_data.append({
                        'document_name': document_name,
                        'field_type': field['field_type'],
                        'field_value': field['field_value'],
                        'field_confidence': field['field_confidence'],
                        'value_confidence': field['value_confidence'],
                        'normalized_value': json.dumps(field['normalized_value']) if field['normalized_value'] else ''
                    })
                
                self.extracted_data = pd.DataFrame(df_data)
                logger.debug(f"Created DataFrame with {len(self.extracted_data)} rows")
            else:
                self.extracted_data = pd.DataFrame()
                logger.warning("No fields extracted, created empty DataFrame")
            
            logger.info("Successfully processed Textract analyze_id response")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing analyze_id response: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing response: {str(e)}',
                'error_code': 'RESPONSE_PROCESSING_ERROR',
                'document_name': document_name,
                'extracted_fields': [],
                'raw_response': response
            }
    
    def analyze_general_document(self, document_name, bucket_name=None):
        """
        Extract text from general documents using Textract's detect_document_text
        For non-ID documents like PDFs, forms, etc.
        
        Args:
            document_name (str): Name of the document file in S3
            bucket_name (str, optional): S3 bucket name, defaults to config value
            
        Returns:
            dict: Processed results with extracted text
        """
        if bucket_name is None:
            bucket_name = self.bucket_name
            
        logger.info(f"Starting Textract general document analysis for: {document_name}")
        logger.debug(f"Using bucket: {bucket_name}")
        
        try:
            # Call Textract detect_document_text
            logger.debug("Calling Textract detect_document_text API")
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': document_name
                    }
                }
            )
            
            logger.info("Textract detect_document_text completed successfully")
            logger.debug(f"Response contains {len(response.get('Blocks', []))} blocks")
            
            # Process the response
            processed_result = self._process_general_document_response(response, document_name)
            
            logger.info(f"General document analysis completed - Found {len(processed_result.get('text_blocks', []))} text blocks")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error in analyze_general_document: {str(e)}")
            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'TEXTRACT_GENERAL_DOCUMENT_ERROR',
                'document_name': document_name,
                'bucket_name': bucket_name,
                'text_blocks': [],
                'full_text': '',
                'raw_response': None
            }
            return error_result
    
    def _process_general_document_response(self, response, document_name):
        """
        Process the raw Textract detect_document_text response
        
        Args:
            response (dict): Raw response from Textract detect_document_text
            document_name (str): Name of the processed document
            
        Returns:
            dict: Processed and structured response
        """
        logger.debug("Processing Textract general document response")
        
        try:
            text_blocks = []
            lines = []
            words = []
            full_text_parts = []
            
            # Process each block
            for block in response.get('Blocks', []):
                block_type = block.get('BlockType', '')
                text = block.get('Text', '')
                confidence = block.get('Confidence', 0)
                
                block_info = {
                    'block_type': block_type,
                    'text': text,
                    'confidence': confidence,
                    'geometry': block.get('Geometry', {})
                }
                
                text_blocks.append(block_info)
                
                if block_type == 'LINE':
                    lines.append(text)
                    full_text_parts.append(text)
                elif block_type == 'WORD':
                    words.append({
                        'text': text,
                        'confidence': confidence
                    })
            
            # Join all text
            full_text = '\n'.join(full_text_parts)
            
            processed_result = {
                'success': True,
                'document_name': document_name,
                'document_metadata': response.get('DocumentMetadata', {}),
                'text_blocks': text_blocks,
                'lines': lines,
                'words': words,
                'full_text': full_text,
                'total_blocks': len(text_blocks),
                'total_lines': len(lines),
                'total_words': len(words),
                'raw_response': response
            }
            
            # Create pandas DataFrame for consistency
            if text_blocks:
                df_data = []
                for i, block in enumerate(text_blocks):
                    if block['text']:  # Only include blocks with text
                        df_data.append({
                            'document_name': document_name,
                            'block_index': i,
                            'block_type': block['block_type'],
                            'text': block['text'],
                            'confidence': block['confidence']
                        })
                
                self.extracted_data = pd.DataFrame(df_data)
                logger.debug(f"Created general document DataFrame with {len(self.extracted_data)} rows")
            else:
                self.extracted_data = pd.DataFrame()
                logger.warning("No text blocks found, created empty DataFrame")
            
            logger.info("Successfully processed Textract general document response")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing general document response: {str(e)}")
            return {
                'success': False,
                'error': f'Error processing response: {str(e)}',
                'error_code': 'GENERAL_RESPONSE_PROCESSING_ERROR',
                'document_name': document_name,
                'text_blocks': [],
                'full_text': '',
                'raw_response': response
            }
