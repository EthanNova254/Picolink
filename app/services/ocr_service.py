"""
Tesseract OCR service - Local image and PDF text extraction
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import pillow_heif
from app.config import settings

# Register HEIF support
pillow_heif.register_heif_opener()

class OCRService:
    """Local OCR service using Tesseract"""
    
    def __init__(self):
        self.default_lang = settings.TESSERACT_LANG
        self.dpi = settings.OCR_DPI
    
    def extract_text_from_image(
        self,
        image_path: Path,
        lang: Optional[str] = None,
        output_format: str = "text"
    ) -> Dict:
        """
        Extract text from image
        Formats: text, hocr, json
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            lang = lang or self.default_lang
            
            # Extract based on format
            if output_format == "hocr":
                result = pytesseract.image_to_pdf_or_hocr(
                    image,
                    lang=lang,
                    extension='hocr'
                )
                text = result.decode('utf-8')
            elif output_format == "json":
                data = pytesseract.image_to_data(
                    image,
                    lang=lang,
                    output_type=pytesseract.Output.DICT
                )
                text = json.dumps(data, indent=2)
            else:  # text
                text = pytesseract.image_to_string(image, lang=lang)
            
            # Get confidence if available
            try:
                confidence = pytesseract.image_to_data(
                    image,
                    lang=lang,
                    output_type=pytesseract.Output.DICT
                )
                avg_confidence = sum(
                    int(c) for c in confidence['conf'] if int(c) > 0
                ) / len([c for c in confidence['conf'] if int(c) > 0])
            except:
                avg_confidence = None
            
            return {
                "success": True,
                "text": text,
                "format": output_format,
                "language": lang,
                "confidence": avg_confidence,
                "char_count": len(text) if output_format == "text" else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def extract_text_from_pdf(
        self,
        pdf_path: Path,
        lang: Optional[str] = None,
        pages: Optional[List[int]] = None,
        output_format: str = "text"
    ) -> Dict:
        """
        Extract text from PDF pages
        pages: List of page numbers (1-indexed) or None for all
        """
        try:
            lang = lang or self.default_lang
            
            # Convert PDF to images
            if pages:
                images = convert_from_path(
                    pdf_path,
                    dpi=self.dpi,
                    first_page=min(pages),
                    last_page=max(pages)
                )
            else:
                images = convert_from_path(pdf_path, dpi=self.dpi)
            
            # Limit pages to prevent resource exhaustion
            if len(images) > settings.MAX_PDF_PAGES:
                return {
                    "success": False,
                    "error": f"PDF too large. Max {settings.MAX_PDF_PAGES} pages allowed"
                }
            
            results = []
            
            for page_num, image in enumerate(images, start=1):
                if pages and page_num not in pages:
                    continue
                
                # Extract text
                if output_format == "text":
                    text = pytesseract.image_to_string(image, lang=lang)
                elif output_format == "hocr":
                    text = pytesseract.image_to_pdf_or_hocr(
                        image,
                        lang=lang,
                        extension='hocr'
                    ).decode('utf-8')
                else:  # json
                    data = pytesseract.image_to_data(
                        image,
                        lang=lang,
                        output_type=pytesseract.Output.DICT
                    )
                    text = json.dumps(data, indent=2)
                
                results.append({
                    "page": page_num,
                    "text": text,
                    "char_count": len(text) if output_format == "text" else None
                })
            
            # Combine all text if format is text
            if output_format == "text":
                combined_text = "\n\n--- Page Break ---\n\n".join(
                    r["text"] for r in results
                )
            else:
                combined_text = None
            
            return {
                "success": True,
                "format": output_format,
                "language": lang,
                "total_pages": len(images),
                "processed_pages": len(results),
                "combined_text": combined_text,
                "pages": results if output_format != "text" else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_languages(self) -> List[str]:
        """Get list of installed Tesseract languages"""
        try:
            langs = pytesseract.get_languages()
            return sorted(langs)
        except:
            return [self.default_lang]

# Singleton instance
ocr_service = OCRService()
