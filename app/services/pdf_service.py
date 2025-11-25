"""
PDF Generation service - Create PDFs from text, HTML, markdown, and images
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from weasyprint import HTML, CSS
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
        """Create PDF from HTML using WeasyPrint"""
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Base CSS for consistent rendering
        base_css = """
        @page {
            size: %s;
            margin: 1cm;
        }
        body {
            font-family: 'DejaVu Sans', sans-serif;
            font-size: 11pt;
            line-height: 1.5;
        }
        h1 { font-size: 20pt; margin-top: 0; }
        h2 { font-size: 16pt; }
        h3 { font-size: 14pt; }
        code { 
            background: #f4f4f4; 
            padding: 2px 4px;
            font-family: monospace;
        }
        pre {
            background: #f4f4f4;
            padding: 10px;
            overflow-x: auto;
        }
        """ % page_size
        
        css_list = [CSS(string=base_css)]
        if css:
            css_list.append(CSS(string=css))
        
        # Generate PDF
        HTML(string=html).write_pdf(str(output_file), stylesheets=css_list)
        
        return output_file
    
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
