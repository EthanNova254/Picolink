"""
PDF Generation service - Create PDFs from text, HTML, markdown, and images
Using xhtml2pdf with better HTML/CSS support
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from xhtml2pdf import pisa
import img2pdf
from PyPDF2 import PdfMerger
from app.config import settings
from app.utils import generate_filename

class PDFService:
    """Local PDF generation service"""
    
    def __init__(self):
        self.page_sizes = {
            "A4": A4,
            "letter": letter,
            "legal": legal
        }
        self.default_page_size = A4
        self.margin = settings.PDF_MARGIN
    
    def create_from_text(
        self,
        text: str,
        style: str = "default",
        page_size: str = "A4",
        title: Optional[str] = None
    ) -> Path:
        """
        Create PDF from plain text
        Styles: default, formal, casual, code
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Setup document
        page = self.page_sizes.get(page_size, self.default_page_size)
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=page,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build content
        story = []
        styles = self._get_styles(style)
        
        # Add title if provided
        if title:
            story.append(Paragraph(title, styles['title']))
            story.append(Spacer(1, 0.3 * inch))
        
        # Add paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para, styles['body']))
                story.append(Spacer(1, 0.2 * inch))
        
        # Build PDF
        doc.build(story)
        
        return output_file
    
    def create_from_html(
        self,
        html: str,
        page_size: str = "A4",
        css: Optional[str] = None
    ) -> Path:
        """Create PDF from HTML using xhtml2pdf with full CSS support"""
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Clean and prepare HTML
        html = self._prepare_html_for_pdf(html, page_size, css)
        
        # Generate PDF with better encoding handling
        with open(output_file, "wb") as pdf_file:
            # Convert HTML to PDF
            pisa_status = pisa.CreatePDF(
                src=html,
                dest=pdf_file,
                encoding='utf-8'
            )
        
        if pisa_status.err:
            # Fallback: try with simpler HTML if complex styling fails
            try:
                simple_html = self._simplify_html(html)
                with open(output_file, "wb") as pdf_file:
                    pisa.CreatePDF(
                        src=simple_html,
                        dest=pdf_file,
                        encoding='utf-8'
                    )
            except Exception as e:
                raise Exception(f"PDF generation failed: {str(e)}")
        
        return output_file
    
    def _prepare_html_for_pdf(self, html: str, page_size: str, custom_css: Optional[str]) -> str:
        """Prepare HTML with proper structure and CSS for PDF generation"""
        
        # Default CSS that works well with xhtml2pdf
        default_css = """
        <style type="text/css">
            @page {
                size: %s;
                margin: 1cm;
            }
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: Arial, Helvetica, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
            }
            h1, h2, h3, h4, h5, h6 {
                margin: 10px 0;
                color: #000;
            }
            h1 { font-size: 20pt; }
            h2 { font-size: 16pt; }
            h3 { font-size: 14pt; }
            p {
                margin: 10px 0;
                text-align: left;
            }
            .page-container, .content-box, .edges, .corner-accents {
                /* xhtml2pdf has limited support for complex positioning */
                position: relative;
                display: block;
            }
            .title {
                font-size: 24pt;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
                color: #2c3e50;
            }
            .content {
                font-size: 14pt;
                text-align: center;
                margin: 15px 0;
                color: #34495e;
            }
            /* Simplify gradients - xhtml2pdf doesn't support complex CSS */
            .page-container {
                padding: 20px;
                background-color: #ffffff;
            }
        </style>
        """ % page_size
        
        # Check if HTML already has proper structure
        if not html.strip().startswith('<!DOCTYPE') and not html.strip().startswith('<html'):
            # Wrap in proper HTML structure
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                {default_css}
                {f'<style type="text/css">{custom_css}</style>' if custom_css else ''}
            </head>
            <body>
                {html}
            </body>
            </html>
            """
        else:
            # Insert default CSS into existing HTML
            if '<head>' in html:
                html = html.replace('<head>', f'<head>{default_css}' + (f'<style type="text/css">{custom_css}</style>' if custom_css else ''))
            elif '<html>' in html:
                html = html.replace('<html>', f'<html><head>{default_css}' + (f'<style type="text/css">{custom_css}</style>' if custom_css else '') + '</head>', 1)
        
        return html
    
    def _simplify_html(self, html: str) -> str:
        """Simplify HTML by removing complex CSS that xhtml2pdf can't handle"""
        # Remove complex CSS properties that xhtml2pdf doesn't support
        unsupported = [
            r'linear-gradient\([^)]+\)',
            r'radial-gradient\([^)]+\)',
            r'box-shadow:[^;]+;',
            r'border-radius:[^;]+;',
            r'transform:[^;]+;',
            r'display:\s*flex[^;]*;',
            r'justify-content:[^;]+;',
            r'align-items:[^;]+;',
            r'flex-direction:[^;]+;',
        ]
        
        for pattern in unsupported:
            html = re.sub(pattern, '', html, flags=re.IGNORECASE)
        
        return html
    
    def create_from_markdown(
        self,
        md_text: str,
        page_size: str = "A4",
        style: str = "default"
    ) -> Path:
        """Convert markdown to PDF"""
        # Convert markdown to HTML
        html = markdown.markdown(
            md_text,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )
        
        # Wrap in basic HTML structure
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return self.create_from_html(full_html, page_size)
    
    def create_from_images(
        self,
        image_paths: List[Path],
        page_size: str = "A4",
        fit_to_page: bool = True
    ) -> Path:
        """Create PDF from multiple images"""
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        if fit_to_page:
            # Use img2pdf for better quality
            with open(output_file, "wb") as f:
                f.write(img2pdf.convert([str(p) for p in image_paths]))
        else:
            # Use ReportLab for more control
            page = self.page_sizes.get(page_size, self.default_page_size)
            doc = SimpleDocTemplate(str(output_file), pagesize=page)
            
            story = []
            for img_path in image_paths:
                img = RLImage(str(img_path))
                
                # Scale to fit page
                img_width, img_height = img.imageWidth, img.imageHeight
                page_width, page_height = page
                
                scale = min(
                    (page_width - 2 * self.margin) / img_width,
                    (page_height - 2 * self.margin) / img_height
                )
                
                img.drawWidth = img_width * scale
                img.drawHeight = img_height * scale
                
                story.append(img)
                story.append(PageBreak())
            
            doc.build(story)
        
        return output_file
    
    def merge_pdfs(self, pdf_paths: List[Path]) -> Path:
        """Merge multiple PDFs into one"""
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        merger = PdfMerger()
        for pdf_path in pdf_paths:
            merger.append(str(pdf_path))
        
        merger.write(str(output_file))
        merger.close()
        
        return output_file
    
    def _get_styles(self, style_name: str) -> Dict:
        """Get paragraph styles based on preset"""
        base_styles = getSampleStyleSheet()
        
        if style_name == "formal":
            return {
                'title': ParagraphStyle(
                    'CustomTitle',
                    parent=base_styles['Title'],
                    fontSize=18,
                    alignment=TA_CENTER,
                    spaceAfter=12
                ),
                'body': ParagraphStyle(
                    'CustomBody',
                    parent=base_styles['BodyText'],
                    fontSize=11,
                    alignment=TA_JUSTIFY,
                    fontName='Times-Roman'
                )
            }
        elif style_name == "casual":
            return {
                'title': ParagraphStyle(
                    'CustomTitle',
                    parent=base_styles['Title'],
                    fontSize=16,
                    alignment=TA_LEFT
                ),
                'body': ParagraphStyle(
                    'CustomBody',
                    parent=base_styles['BodyText'],
                    fontSize=10,
                    alignment=TA_LEFT
                )
            }
        elif style_name == "code":
            return {
                'title': base_styles['Title'],
                'body': ParagraphStyle(
                    'Code',
                    parent=base_styles['Code'],
                    fontSize=9,
                    fontName='Courier'
                )
            }
        else:  # default
            return {
                'title': base_styles['Title'],
                'body': base_styles['BodyText']
            }

# Singleton instance
pdf_service = PDFService()
