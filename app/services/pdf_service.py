"""
PDF Generation Service - Professional Children's Book Template (COMPLETE)
Beautiful, designed PDFs from simple text input with full customization
"""
from pathlib import Path
from typing import List, Optional, Dict
import markdown
from reportlab.lib.pagesizes import A4, letter, legal
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from weasyprint import HTML
import img2pdf
from PyPDF2 import PdfMerger
from app.config import settings
from app.utils import generate_filename


class DecorativeBorder(Flowable):
    """Custom decorative border for children's book pages"""
    
    def __init__(self, width, height, border_color="#FFE4B5", bg_color="#FFFEF8"):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.border_color = HexColor(border_color)
        self.bg_color = HexColor(bg_color)
    
    def wrap(self, availWidth, availHeight):
        """Required method - returns size of flowable"""
        return (self.width, self.height)
    
    def draw(self):
        """Draw decorative frame"""
        canvas = self.canv
        
        # Background
        canvas.setFillColor(self.bg_color)
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Decorative border
        canvas.setStrokeColor(self.border_color)
        canvas.setLineWidth(3)
        canvas.roundRect(10, 10, self.width - 20, self.height - 20, 10)
        
        # Corner decorations (simple circles)
        canvas.setFillColor(self.border_color)
        for x, y in [(20, 20), (self.width - 20, 20), 
                     (20, self.height - 20), (self.width - 20, self.height - 20)]:
            canvas.circle(x, y, 8, fill=1, stroke=0)


class PDFService:
    """PDF generation service with professional children's book template"""
    
    # Available fonts for children's books (readable, friendly)
    AVAILABLE_FONTS = {
        "default": "Helvetica",
        "friendly": "Helvetica",
        "classic": "Times-Roman",
        "modern": "Courier",
        "playful": "Courier-Bold"
    }
    
    def __init__(self):
        self.page_sizes = {
            "A4": A4,
            "letter": letter,
            "legal": legal
        }
        self.default_page_size = A4
        self.margin = settings.PDF_MARGIN
    
    def create_childrens_book(
        self,
        text: str,
        title: Optional[str] = None,
        font_family: str = "default",
        theme_color: str = "#2c3e50",
        page_size: str = "A4",
        add_border: bool = False,
        border_color: str = "#FFE4B5",
        background_color: str = "#FFFEF8"
    ) -> Path:
        """
        Create beautiful children's book PDF from text
        
        Args:
            text: Main content
            title: Optional title (omit for no title section)
            font_family: default, friendly, classic, modern, playful
            theme_color: Hex color for title and accents
            page_size: A4 (default), letter, legal
            add_border: Add decorative border around content
            border_color: Color of decorative border
            background_color: Background color for bordered pages
        
        Returns:
            Path to generated PDF file
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        # Get page size
        page = self.page_sizes.get(page_size, self.default_page_size)
        page_width, page_height = page
        
        # Setup document
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=page,
            rightMargin=25*mm,
            leftMargin=25*mm,
            topMargin=30*mm,
            bottomMargin=30*mm
        )
        
        # Get font (with safe bold handling)
        font_name = self.AVAILABLE_FONTS.get(font_family, "Helvetica")
        title_font = self._get_bold_font(font_name)
        
        # Create custom styles
        title_style = ParagraphStyle(
            'BookTitle',
            fontName=title_font,
            fontSize=32,
            textColor=HexColor(theme_color),
            alignment=TA_CENTER,
            spaceAfter=20*mm,
            spaceBefore=10*mm,
            leading=40,
            leftIndent=0,
            rightIndent=0
        )
        
        body_style = ParagraphStyle(
            'BookBody',
            fontName=font_name,
            fontSize=16,
            textColor=HexColor('#34495e'),
            alignment=TA_CENTER,
            spaceAfter=8*mm,
            leading=24,
            leftIndent=0,
            rightIndent=0,
            wordWrap='CJK'
        )
        
        # Build content
        story = []
        
        # Add decorative border if requested
        if add_border:
            border_width = page_width - 50*mm
            border_height = page_height - 60*mm
            story.append(DecorativeBorder(border_width, border_height, border_color, background_color))
            story.append(Spacer(1, -border_height))  # Overlay content on border
        
        # Add top spacing
        story.append(Spacer(1, 35*mm if not add_border else 40*mm))
        
        # Add title if provided
        if title and title.strip():
            story.append(Paragraph(title.strip(), title_style))
        
        # Add body text with smart alignment
        paragraphs = self._split_paragraphs(text)
        
        for para_text in paragraphs:
            if para_text:
                # Smart alignment based on text length
                style = self._get_paragraph_style(para_text, body_style)
                story.append(Paragraph(para_text, style))
                story.append(Spacer(1, 5*mm))
        
        # Build PDF
        doc.build(story)
        return output_file
    
    def create_from_text(
        self,
        text: str,
        style: str = "default",
        page_size: str = "A4",
        title: Optional[str] = None,
        font_family: str = "default",
        theme_color: str = "#2c3e50"
    ) -> Path:
        """
        Legacy method - redirects to create_childrens_book
        Kept for backward compatibility
        """
        return self.create_childrens_book(
            text=text,
            title=title,
            font_family=font_family,
            theme_color=theme_color,
            page_size=page_size,
            add_border=False
        )
    
    def _get_bold_font(self, font_name: str) -> str:
        """Safely get bold version of font"""
        base_font = font_name.split('-')[0]
        
        # Known fonts with bold variants
        if base_font in ['Helvetica', 'Times', 'Courier']:
            return f"{base_font}-Bold"
        elif 'Bold' not in font_name:
            return f"{font_name}-Bold" if f"{font_name}-Bold" in ['Helvetica-Bold', 'Times-Bold', 'Courier-Bold'] else font_name
        
        return font_name
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs intelligently"""
        # Try double newline first
        if '\n\n' in text:
            paragraphs = text.split('\n\n')
        else:
            paragraphs = text.split('\n')
        
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _get_paragraph_style(self, text: str, base_style: ParagraphStyle) -> ParagraphStyle:
        """Get appropriate style based on text length"""
        text_length = len(text)
        
        if text_length > 150:
            # Long text - justified
            return ParagraphStyle(
                'LongText',
                parent=base_style,
                alignment=TA_JUSTIFY
            )
        elif text_length > 80:
            # Medium text - left aligned
            return ParagraphStyle(
                'MediumText',
                parent=base_style,
                alignment=TA_LEFT
            )
        else:
            # Short text - centered
            return base_style
    
    def create_from_html(
        self,
        html: str,
        page_size: str = "A4",
        css: Optional[str] = None
    ) -> Path:
        """
        Create PDF from HTML using WeasyPrint
        For custom HTML designs when you need full control
        """
        output_file = settings.OUTPUT_DIR / generate_filename("pdf")
        
        try:
            # Ensure HTML has proper structure
            if not html.strip().startswith('<!DOCTYPE') and not html.strip().startswith('<html'):
                html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    {f'<style>{css}</style>' if css else ''}
</head>
<body>
{html}
</body>
</html>"""
            elif css and '<head>' in html:
                html = html.replace('</head>', f'<style>{css}</style></head>')
            
            # Generate PDF with WeasyPrint
            HTML(string=html).write_pdf(str(output_file))
            
            if not output_file.exists() or output_file.stat().st_size < 100:
                raise Exception("PDF generation failed")
            
            return output_file
            
        except Exception as e:
            raise Exception(f"WeasyPrint PDF generation failed: {str(e)}")
    
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
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: {page_size}; margin: 1cm; }}
        body {{ font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; }}
        h1 {{ font-size: 20pt; margin-top: 0; }}
        h2 {{ font-size: 16pt; }}
        h3 {{ font-size: 14pt; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        pre {{ background: #f4f4f4; padding: 10px; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
        
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


# Singleton instance
pdf_service = PDFService()
