"""
PDF Generation service - Create PDFs from text, HTML, markdown, and images
SMART FALLBACK: Tries to preserve HTML+CSS, falls back to extraction if needed
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from xhtml2pdf import pisa
from bs4 import BeautifulSoup
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
        """
        Create PDF from HTML - SMART FALLBACK APPROACH
        1. First: Try to render HTML+CSS with xhtml2pdf (preserves your styling)
        2. Fallback: If that fails, extract content and style with ReportLab
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Prepare HTML with proper structure
        prepared_html = self._prepare_html_for_pdf(html, page_size, css)
        
        # ATTEMPT 1: Try xhtml2pdf (preserves your HTML+CSS)
        try:
            with open(output_file, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    src=prepared_html,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            # Check if PDF was created successfully and has content
            if output_file.exists() and output_file.stat().st_size > 1000:
                # PDF created successfully with content
                print(f"✅ PDF created with xhtml2pdf (preserved HTML+CSS)")
                return output_file
            else:
                # PDF too small or failed
                print(f"⚠️ xhtml2pdf produced small/empty PDF, trying fallback...")
                raise Exception("PDF too small")
                
        except Exception as e:
            print(f"⚠️ xhtml2pdf failed: {str(e)}, using fallback renderer...")
            
            # ATTEMPT 2: Fallback to ReportLab extraction (clean styling)
            return self._create_pdf_from_html_fallback(html, page_size, output_file)
    
    def _prepare_html_for_pdf(self, html: str, page_size: str, custom_css: Optional[str]) -> str:
        """Prepare HTML with proper structure for xhtml2pdf"""
        
        # Simplified CSS that xhtml2pdf can handle better
        safe_css = """
        <style type="text/css">
            @page {
                size: %s;
                margin: 2cm;
            }
            body {
                font-family: Arial, Helvetica, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
                text-align: center;
                margin: 10px 0;
            }
            h1 { font-size: 24pt; }
            h2 { font-size: 18pt; }
            h3 { font-size: 14pt; }
            p {
                margin: 10px 0;
                text-align: center;
                color: #34495e;
            }
            .title {
                font-size: 28pt;
                font-weight: bold;
                text-align: center;
                color: #2c3e50;
                margin: 20px 0;
            }
            .age-range {
                font-size: 14pt;
                text-align: center;
                color: #7b5e57;
                margin: 10px 0;
            }
            .theme-message, .content {
                font-size: 14pt;
                text-align: center;
                color: #34495e;
                margin: 15px 0;
                line-height: 1.6;
            }
            .page-container {
                padding: 20px;
                background-color: #fff;
            }
        </style>
        """ % page_size
        
        # Check if HTML has proper structure
        if not html.strip().startswith('<!DOCTYPE') and not html.strip().startswith('<html'):
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                {safe_css}
                {f'<style type="text/css">{custom_css}</style>' if custom_css else ''}
            </head>
            <body>
                {html}
            </body>
            </html>
            """
        else:
            # Insert safe CSS
            if '<head>' in html:
                html = html.replace('<head>', f'<head>{safe_css}' + (f'<style type="text/css">{custom_css}</style>' if custom_css else ''))
            elif '<html>' in html:
                html = html.replace('<html>', f'<html><head>{safe_css}' + (f'<style type="text/css">{custom_css}</style>' if custom_css else '') + '</head>', 1)
        
        return html
    
    def _create_pdf_from_html_fallback(self, html: str, page_size: str, output_file: Path) -> Path:
        """
        FALLBACK: Extract content from HTML and style with ReportLab
        Only used if xhtml2pdf fails
        """
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Setup document
        if page_size == "A4":
            page = (210*mm, 297*mm)
        elif page_size == "letter":
            page = letter
        else:
            page = legal
        
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=page,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=12*mm,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=HexColor('#34495e'),
            alignment=TA_CENTER,
            spaceAfter=10*mm,
            fontName='Helvetica'
        )
        
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor('#34495e'),
            alignment=TA_CENTER,
            leading=21,
            fontName='Helvetica'
        )
        
        # Extract and build content
        story.append(Spacer(1, 40*mm))
        
        # Title
        title = soup.find('title') or soup.find(class_='title') or soup.find('h1')
        if title:
            story.append(Paragraph(title.get_text().strip(), title_style))
        
        # Age range / subtitle
        age_range = soup.find(class_='age-range')
        if age_range:
            story.append(Paragraph(age_range.get_text().strip(), subtitle_style))
        
        # Main content
        content = soup.find(class_='content') or soup.find(class_='theme-message')
        if content:
            paragraphs = content.find_all('p') if content.find_all('p') else [content]
            for p in paragraphs:
                text = p.get_text().strip()
                if text:
                    story.append(Paragraph(text, content_style))
                    story.append(Spacer(1, 5*mm))
        
        # Build PDF
        doc.build(story)
        
        return output_file
    
    def create_from_markdown(
        self,
        md_text: str,
        page_size: str = "A4",
        style: str = "default"
    ) -> Path:
        """Convert markdown to PDF"""
        html = markdown.markdown(
            md_text,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )
        
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
            with open(output_file, "wb") as f:
                f.write(img2pdf.convert([str(p) for p in image_paths]))
        else:
            page = self.page_sizes.get(page_size, self.default_page_size)
            doc = SimpleDocTemplate(str(output_file), pagesize=page)
            
            story = []
            for img_path in image_paths:
                img = RLImage(str(img_path))
                
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
        else:
            return {
                'title': base_styles['Title'],
                'body': base_styles['BodyText']
            }

# Singleton instance
pdf_service = PDFService()
