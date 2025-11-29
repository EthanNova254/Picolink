"""
PDF Generation service - UPGRADED for modern HTML/CSS
Using WeasyPrint 62.3 with full CSS3 support
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import img2pdf
from PyPDF2 import PdfMerger
from app.config import settings
from app.utils import generate_filename

class PDFService:
    """Local PDF generation service with modern CSS support"""
    
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
        """Create PDF from plain text"""
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        page = self.page_sizes.get(page_size, self.default_page_size)
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=page,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        styles = self._get_styles(style)
        
        if title:
            story.append(Paragraph(title, styles['title']))
            story.append(Spacer(1, 0.3 * inch))
        
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para, styles['body']))
                story.append(Spacer(1, 0.2 * inch))
        
        doc.build(story)
        return output_file
    
    def create_from_html(
        self,
        html: str,
        page_size: str = "A4",
        css: Optional[str] = None
    ) -> Path:
        """
        Create PDF from HTML - WeasyPrint 62.3 with FULL CSS3 support
        Supports: flexbox, gradients, transforms, modern CSS!
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        try:
            # Prepare CSS list
            stylesheets = []
            if css:
                stylesheets.append(CSS(string=css))
            
            # Create PDF with WeasyPrint 62.3 (modern API)
            html_doc = HTML(string=html)
            html_doc.write_pdf(
                target=str(output_file),
                stylesheets=stylesheets
            )
            
            # Check if PDF was created successfully
            if output_file.exists() and output_file.stat().st_size > 100:
                return output_file
            else:
                raise Exception("PDF generation produced empty file")
                
        except Exception as e:
            print(f"⚠️ WeasyPrint error: {str(e)}")
            # Fallback to ReportLab extraction
            return self._create_pdf_from_html_fallback(html, page_size, output_file)
    
    def _create_pdf_from_html_fallback(self, html: str, page_size: str, output_file: Path) -> Path:
        """
        FALLBACK: Extract content from HTML and style with ReportLab
        Only used if WeasyPrint fails
        """
        soup = BeautifulSoup(html, 'html.parser')
        
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
        
        story.append(Spacer(1, 40*mm))
        
        title = soup.find('title') or soup.find(class_='title') or soup.find('h1')
        if title:
            story.append(Paragraph(title.get_text().strip(), title_style))
        
        age_range = soup.find(class_='age-range')
        if age_range:
            story.append(Paragraph(age_range.get_text().strip(), subtitle_style))
        
        content = soup.find(class_='content') or soup.find(class_='theme-message')
        if content:
            paragraphs = content.find_all('p') if content.find_all('p') else [content]
            for p in paragraphs:
                text = p.get_text().strip()
                if text:
                    story.append(Paragraph(text, content_style))
                    story.append(Spacer(1, 5*mm))
        
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
