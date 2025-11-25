"""
PDF generation router - Create PDFs from various sources
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
from app.services.pdf_service import pdf_service
from app.utils import save_upload_file, cleanup_file, IMAGE_TYPES, PDF_TYPES

router = APIRouter(prefix="/pdf", tags=["PDF Generation"])

class TextToPDFRequest(BaseModel):
    text: str
    title: Optional[str] = None
    style: str = "default"
    page_size: str = "A4"

class HTMLToPDFRequest(BaseModel):
    html: str
    page_size: str = "A4"
    css: Optional[str] = None

class MarkdownToPDFRequest(BaseModel):
    markdown: str
    page_size: str = "A4"
    style: str = "default"

@router.post("/from-text")
async def create_pdf_from_text(request: TextToPDFRequest):
    """
    Create PDF from plain text
    
    **Parameters:**
    - text: Plain text content
    - title: Optional title for the document
    - style: default, formal, casual, code
    - page_size: A4, letter, legal
    
    **Styles:**
    - default: Standard formatting
    - formal: Times Roman, justified, centered title
    - casual: Sans-serif, left-aligned
    - code: Monospace font for code/logs
    
    **Use cases:**
    - Convert notes to PDF
    - Export logs
    - Create simple documents
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/pdf/from-text",
      "body": {
        "text": "Your document content here...",
        "title": "My Document",
        "style": "formal",
        "page_size": "A4"
      }
    }
    ```
    
    **Response:**
    Returns the PDF file directly (application/pdf)
    """
    try:
        pdf_path = pdf_service.create_from_text(
            request.text,
            style=request.style,
            page_size=request.page_size,
            title=request.title
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"document_{pdf_path.name}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-html")
async def create_pdf_from_html(request: HTMLToPDFRequest):
    """
    Create PDF from HTML
    
    **Parameters:**
    - html: HTML content (full document or fragment)
    - page_size: A4, letter, legal
    - css: Optional custom CSS
    
    **Use cases:**
    - Convert web pages to PDF
    - Generate reports from HTML templates
    - Create styled documents
    
    **HTML tips:**
    - Include inline styles for best results
    - Use web-safe fonts
    - Images must be absolute URLs or base64
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/pdf/from-html",
      "body": {
        "html": "<h1>Title</h1><p>Content</p>",
        "page_size": "A4",
        "css": "h1 { color: blue; }"
      }
    }
    ```
    """
    try:
        pdf_path = pdf_service.create_from_html(
            request.html,
            page_size=request.page_size,
            css=request.css
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"document_{pdf_path.name}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-markdown")
async def create_pdf_from_markdown(request: MarkdownToPDFRequest):
    """
    Create PDF from Markdown
    
    **Parameters:**
    - markdown: Markdown content
    - page_size: A4, letter, legal
    - style: default, formal, casual
    
    **Supported markdown:**
    - Headers (#, ##, ###)
    - Lists (-, *, 1.)
    - Bold (**text**)
    - Italic (*text*)
    - Code blocks (```)
    - Tables
    - Links
    
    **Use cases:**
    - Convert README files
    - Export documentation
    - Create formatted reports
    
    **n8n example:**
    ```json
    {
      "method": "POST",
      "url": "https://your-service.koyeb.app/pdf/from-markdown",
      "body": {
        "markdown": "# Title\n\nContent here...",
        "page_size": "A4"
      }
    }
    ```
    """
    try:
        pdf_path = pdf_service.create_from_markdown(
            request.markdown,
            page_size=request.page_size,
            style=request.style
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"document_{pdf_path.name}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-images")
async def create_pdf_from_images(
    files: List[UploadFile] = File(...),
    page_size: str = Form("A4"),
    fit_to_page: bool = Form(True)
):
    """
    Create PDF from multiple images
    
    **Parameters:**
    - files: List of image files (JPG, PNG, WEBP, HEIF)
    - page_size: A4, letter, legal
    - fit_to_page: Scale images to fit page
    
    **Use cases:**
    - Convert scanned documents
    - Create photo albums
    - Combine multiple images
    
    **Ordering:**
    Images are added in the order uploaded
    
    **n8n example:**
    - Use HTTP Request node
    - Method: POST
    - Body: Form-Data
    - Add multiple file fields with name "files"
    - Add field "page_size" = "A4"
    - Add field "fit_to_page" = "true"
    
    **Limits:**
    - Max 100 images per request
    - Each image max 100MB
    """
    if len(files) > 100:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 100 images per request"
        )
    
    saved_paths = []
    
    try:
        # Save all uploaded images
        for file in files:
            file_path, mime = await save_upload_file(file, IMAGE_TYPES)
            saved_paths.append(file_path)
        
        # Create PDF
        pdf_path = pdf_service.create_from_images(
            saved_paths,
            page_size=page_size,
            fit_to_page=fit_to_page
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"images_{pdf_path.name}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup uploaded images
        for path in saved_paths:
            cleanup_file(path)

@router.post("/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    """
    Merge multiple PDFs into one
    
    **Parameters:**
    - files: List of PDF files to merge
    
    **Use cases:**
    - Combine multiple documents
    - Merge reports
    - Consolidate files
    
    **Ordering:**
    PDFs are merged in upload order
    
    **Limits:**
    - Max 50 PDFs per request
    
    **n8n example:**
    - Upload multiple PDF files with name "files"
    - Response is the merged PDF
    """
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 50 PDFs per request"
        )
    
    saved_paths = []
    
    try:
        # Save all uploaded PDFs
        for file in files:
            file_path, mime = await save_upload_file(file, PDF_TYPES)
            saved_paths.append(file_path)
        
        # Merge PDFs
        pdf_path = pdf_service.merge_pdfs(saved_paths)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"merged_{pdf_path.name}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup uploaded PDFs
        for path in saved_paths:
            cleanup_file(path)
