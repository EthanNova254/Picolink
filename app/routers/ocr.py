"""
OCR router - Text extraction from images and PDFs
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from app.services.ocr_service import ocr_service
from app.utils import save_upload_file, cleanup_file, IMAGE_TYPES, PDF_TYPES

router = APIRouter(prefix="/ocr", tags=["OCR"])

@router.post("/image")
async def ocr_image(
    file: UploadFile = File(...),
    language: Optional[str] = Form("eng"),
    output_format: str = Form("text")
):
    """
    Extract text from image
    
    **Supported formats:** JPG, PNG, WEBP, HEIF, HEIC
    
    **Languages:** eng, fra, deu, spa, ara, chi_sim, etc.
    
    **Output formats:**
    - text: Plain text
    - hocr: HTML with position data
    - json: Detailed word-level data
    
    **Use cases:**
    - Scan receipts
    - Extract text from screenshots
    - Digitize documents
    
    **n8n example:**
    - Use HTTP Request node
    - Set Method: POST
    - URL: https://your-service.koyeb.app/ocr/image
    - Body: Form-Data
    - Add file field: "file"
    - Add text field: "language" = "eng"
    - Add text field: "output_format" = "text"
    
    **cURL example:**
    ```bash
    curl -X POST https://your-service.koyeb.app/ocr/image \
      -F "file=@image.jpg" \
      -F "language=eng" \
      -F "output_format=text"
    ```
    """
    if output_format not in ["text", "hocr", "json"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid output_format. Use: text, hocr, or json"
        )
    
    # Save uploaded file
    file_path, mime = await save_upload_file(file, IMAGE_TYPES)
    
    try:
        # Extract text
        result = ocr_service.extract_text_from_image(
            file_path,
            lang=language,
            output_format=output_format
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    finally:
        # Cleanup
        cleanup_file(file_path)

@router.post("/pdf")
async def ocr_pdf(
    file: UploadFile = File(...),
    language: Optional[str] = Form("eng"),
    pages: Optional[str] = Form(None),
    output_format: str = Form("text")
):
    """
    Extract text from PDF pages
    
    **Parameters:**
    - file: PDF file
    - language: Tesseract language code
    - pages: Comma-separated page numbers (e.g., "1,3,5") or leave empty for all
    - output_format: text, hocr, or json
    
    **Use cases:**
    - OCR scanned documents
    - Extract text from image-based PDFs
    - Process forms
    
    **Limitations:**
    - Max 500 pages per request
    - Processing time: ~2-5 seconds per page
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/ocr/pdf",
      "body": {
        "file": "@document.pdf",
        "language": "eng",
        "pages": "1,2,3",
        "output_format": "text"
      }
    }
    ```
    
    **Response format:**
    ```json
    {
      "success": true,
      "format": "text",
      "language": "eng",
      "total_pages": 10,
      "processed_pages": 3,
      "combined_text": "Full extracted text here..."
    }
    ```
    """
    if output_format not in ["text", "hocr", "json"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid output_format. Use: text, hocr, or json"
        )
    
    # Parse page numbers
    page_list = None
    if pages:
        try:
            page_list = [int(p.strip()) for p in pages.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid pages format. Use comma-separated numbers: 1,2,3"
            )
    
    # Save uploaded file
    file_path, mime = await save_upload_file(file, PDF_TYPES)
    
    try:
        # Extract text
        result = ocr_service.extract_text_from_pdf(
            file_path,
            lang=language,
            pages=page_list,
            output_format=output_format
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    finally:
        # Cleanup
        cleanup_file(file_path)

@router.get("/languages")
async def get_languages():
    """
    Get list of available OCR languages
    
    **Returns:** List of installed Tesseract language codes
    
    **Common languages:**
    - eng: English
    - fra: French
    - deu: German
    - spa: Spanish
    - ara: Arabic
    - chi_sim: Chinese Simplified
    """
    return {
        "languages": ocr_service.get_available_languages()
    }
