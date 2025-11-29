"""
PDF Generation service - SIMPLIFIED for reliability
Less fancy, more stable HTML to PDF conversion
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from bs4 import BeautifulSoup
import img2pdf
from PyPDF2 import PdfMerger
from app.config import settings
from app.utils import generate_filename

class PDFService:
    """Local PDF generation service - focused on reliability"""
    
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
        Create PDF from HTML - SIMPLIFIED APPROACH
        Extracts content and applies clean, reliable styling
        More predictable results than trying to render complex CSS
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'meta', 'link', 'svg']):
            element.decompose()
        
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
            topMargin=30*mm,
            bottomMargin=30*mm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Define clean styles
        title_style = ParagraphStyle(
            'PageTitle',
            parent=styles['Title'],
            fontSize=32,
            textColor=HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=15*mm,
            spaceBefore=10*mm,
            fontName='Helvetica-Bold',
            leading=38
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=10*mm,
            fontName='Helvetica-Bold',
            leading=30
        )
        
        subheading_style = ParagraphStyle(
            'Subheading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#7b5e57'),
            alignment=TA_CENTER,
            spaceAfter=8*mm,
            fontName='Helvetica',
            leading=24
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=14,
            textColor=HexColor('#34495e'),
            alignment=TA_CENTER,
            spaceAfter=5*mm,
            fontName='Helvetica',
            leading=20
        )
        
        # Add spacing at top
        story.append(Spacer(1, 30*mm))
        
        # Extract and add content in order
        
        # 1. Check for <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            text = title_tag.string.strip()
            if text:
                story.append(Paragraph(text, title_style))
        
        # 2. Check for .title class
        title_div = soup.find(class_='title')
        if title_div:
            text = title_div.get_text().strip()
            if text and (not title_tag or text != title_tag.string):
                story.append(Paragraph(text, heading_style))
        
        # 3. Check for h1
        h1 = soup.find('h1')
        if h1 and not title_div:
            text = h1.get_text().strip()
            if text:
                story.append(Paragraph(text, heading_style))
        
        # 4. Check for age-range or subtitle
        age_div = soup.find(class_='age-range') or soup.find(class_='subtitle')
        if age_div:
            text = age_div.get_text().strip()
            if text:
                story.append(Paragraph(text, subheading_style))
        
        # 5. Check for h2
        h2 = soup.find('h2')
        if h2 and not age_div:
            text = h2.get_text().strip()
            if text:
                story.append(Paragraph(text, subheading_style))
        
        # 6. Main content
        content_areas = [
            soup.find(class_='content'),
            soup.find(class_='theme-message'),
            soup.find(class_='message'),
            soup.find('main'),
            soup.find(class_='body')
        ]
        
        content_found = False
        for content_div in content_areas:
            if content_div:
                # Get all paragraphs
                paragraphs = content_div.find_all('p')
                if paragraphs:
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if text:
                            story.append(Paragraph(text, body_style))
                            content_found = True
                else:
                    # No <p> tags, get all text
                    text = content_div.get_text().strip()
                    if text:
                        story.append(Paragraph(text, body_style))
                        content_found = True
                break
        
        # 7. If no structured content found, get all remaining paragraphs
        if not content_found:
            all_ps = soup.find_all('p')
            for p in all_ps:
                text = p.get_text().strip()
                if text:
                    story.append(Paragraph(text, body_style))
        
        # 8. If still no content, get all text as last resort
        if len(story) <= 1:  # Only spacer
            all_text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            for line in lines:
                if len(line) > 3:  # Ignore very short lines
                    story.append(Paragraph(line, body_style))
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as e:
            # If build fails, try with even simpler content
            story = [
                Spacer(1, 50*mm),
                Paragraph("Document Generated", title_style),
                Spacer(1, 10*mm),
                Paragraph("Content extraction failed. Please check your HTML.", body_style)
            ]
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
