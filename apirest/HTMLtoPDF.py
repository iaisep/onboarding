# -*- coding: utf-8 -*-
"""
HTML to PDF Conversion Module
Converts HTML content to PDF files using WeasyPrint
"""

import logging
import io
import base64
from datetime import datetime

# Configure logger
logger = logging.getLogger('apirest.html_to_pdf')

# Try to import weasyprint, fallback to xhtml2pdf if not available
try:
    from weasyprint import HTML, CSS
    PDF_ENGINE = 'weasyprint'
    logger.info("Using WeasyPrint for PDF generation")
except ImportError:
    try:
        from xhtml2pdf import pisa
        PDF_ENGINE = 'xhtml2pdf'
        logger.info("Using xhtml2pdf for PDF generation")
    except ImportError:
        PDF_ENGINE = None
        logger.error("No PDF engine available. Install weasyprint or xhtml2pdf")


class HTMLToPDFConverter:
    """
    Class for converting HTML content to PDF
    Supports both WeasyPrint and xhtml2pdf engines
    """
    
    def __init__(self):
        """Initialize the HTML to PDF converter"""
        self.engine = PDF_ENGINE
        if not self.engine:
            raise ImportError("No PDF engine available. Install weasyprint or xhtml2pdf")
        logger.info(f"HTMLToPDFConverter initialized with engine: {self.engine}")
    
    def convert_html_to_pdf(self, html_content, css_content=None, base_url=None):
        """
        Convert HTML content to PDF
        
        Args:
            html_content: HTML string to convert
            css_content: Optional CSS string for styling
            base_url: Base URL for resolving relative URLs in HTML
            
        Returns:
            dict: Result with PDF bytes (base64 encoded) or error
        """
        logger.info(f"Starting HTML to PDF conversion with {self.engine}")
        logger.debug(f"HTML content length: {len(html_content)} chars")
        
        if not html_content:
            return {
                'success': False,
                'error': 'HTML content is required',
                'error_code': '400_Missing_HTML'
            }
        
        try:
            if self.engine == 'weasyprint':
                pdf_bytes = self._convert_with_weasyprint(html_content, css_content, base_url)
            else:
                pdf_bytes = self._convert_with_xhtml2pdf(html_content, css_content)
            
            # Encode PDF to base64 for JSON response
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            logger.info(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")
            
            return {
                'success': True,
                'pdf_base64': pdf_base64,
                'pdf_size_bytes': len(pdf_bytes),
                'engine_used': self.engine,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {str(e)}")
            return {
                'success': False,
                'error': f'PDF conversion failed: {str(e)}',
                'error_code': '500_Conversion_Error'
            }
    
    def convert_html_to_pdf_bytes(self, html_content, css_content=None, base_url=None):
        """
        Convert HTML content to PDF and return raw bytes
        Useful for direct file download response
        
        Args:
            html_content: HTML string to convert
            css_content: Optional CSS string for styling
            base_url: Base URL for resolving relative URLs
            
        Returns:
            bytes: PDF file bytes or None on error
        """
        logger.info(f"Starting HTML to PDF conversion (bytes) with {self.engine}")
        
        if not html_content:
            raise ValueError("HTML content is required")
        
        try:
            if self.engine == 'weasyprint':
                return self._convert_with_weasyprint(html_content, css_content, base_url)
            else:
                return self._convert_with_xhtml2pdf(html_content, css_content)
        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {str(e)}")
            raise
    
    def _convert_with_weasyprint(self, html_content, css_content=None, base_url=None):
        """Convert using WeasyPrint engine"""
        from weasyprint import HTML, CSS
        
        # Create HTML document
        html_doc = HTML(string=html_content, base_url=base_url)
        
        # Apply CSS if provided
        stylesheets = []
        if css_content:
            stylesheets.append(CSS(string=css_content))
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        html_doc.write_pdf(pdf_buffer, stylesheets=stylesheets if stylesheets else None)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    
    def _convert_with_xhtml2pdf(self, html_content, css_content=None):
        """Convert using xhtml2pdf engine"""
        from xhtml2pdf import pisa
        
        # If CSS is provided, inject it into HTML
        if css_content:
            html_content = f"<style>{css_content}</style>{html_content}"
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
        
        if pisa_status.err:
            raise Exception(f"xhtml2pdf conversion error: {pisa_status.err}")
        
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
