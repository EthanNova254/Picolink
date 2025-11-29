"""
PDF generation router - Create PDFs from various sources
JSON body, A4 default for all PDFs
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import base64
import requests
from pathlib import Path
from app.services.pdf_service import pdf_service
from app.utils import save_upload_file, cleanup_file, IMAGE_TYPES, PDF_TYPES, generate_filename
from app.config import settings

router = APIRouter(prefix="/pdf", tags=["PDF Generation"])

class TextToPDFRequest(BaseModel):
    text: str
    title: Optional[str] = None
    style: str = "default"
    page_size: str = "A4"  # Default A4

class HTMLToPDFRequest(BaseModel):
    html: str
    page_size: str = "A4"  # Default A4
    css: Optional[str] = None

class MarkdownToPDFRequest(BaseModel):
    markdown: str
    page_size: str = "A4"  # Default A4
    style: str = "default"

class MergePDFsFromURLRequest(BaseModel):
    urls: List[HttpUrl]

class MergePDFsFromBase64Request(BaseModel):
    pdfs: List[str]

@router.post("/from-text")
async def create_pdf_from_text(request: TextToPDFRequest):
    """Create PDF from plain text (A4 default)"""
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
            headers={
                "Content-Disposition": f"inline; filename=document_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-html")
async def create_pdf_from_html(request: HTMLToPDFRequest):
    """Create PDF from HTML (A4 default, reliable extraction)"""
    try:
        pdf_path = pdf_service.create_from_html(
            request.html,
            page_size=request.page_size,
            css=request.css
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=document_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-markdown")
async def create_pdf_from_markdown(request: MarkdownToPDFRequest):
    """Create PDF from Markdown (A4 default)"""
    try:
        pdf_path = pdf_service.create_from_markdown(
            request.markdown,
            page_size=request.page_size,
            style=request.style
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=document_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-images")
async def create_pdf_from_images(
    files: List[UploadFile] = File(...),
    page_size: str = Form("A4"),  # Default A4
    fit_to_page: bool = Form(True)
):
    """Create PDF from multiple images (A4 default)"""
    if len(files) > 100:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 100 images per request"
        )
    
    saved_paths = []
    
    try:
        for file in files:
            file_path, mime = await save_upload_file(file, IMAGE_TYPES)
            saved_paths.append(file_path)
        
        pdf_path = pdf_service.create_from_images(
            saved_paths,
            page_size=page_size,
            fit_to_page=fit_to_page
        )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=images_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        for path in saved_paths:
            cleanup_file(path)

@router.post("/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    """Merge multiple PDFs"""
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Max 50 PDFs per request"
        )
    
    saved_paths = []
    
    try:
        for file in files:
            file_path, mime = await save_upload_file(file, PDF_TYPES)
            saved_paths.append(file_path)
        
        pdf_path = pdf_service.merge_pdfs(saved_paths)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=merged_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        for path in saved_paths:
            cleanup_file(path)

@router.post("/merge-from-urls")
async def merge_pdfs_from_urls(request: MergePDFsFromURLRequest):
    """Merge PDFs from URLs"""
    if len(request.urls) > 50:
        raise HTTPException(
            status_code=400,
            detail="Too many URLs. Max 50 PDFs per request"
        )
    
    saved_paths = []
    
    try:
        for url in request.urls:
            try:
                response = requests.get(str(url), timeout=30)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '')
                if 'pdf' not in content_type.lower():
                    raise HTTPException(
                        status_code=400,
                        detail=f"URL {url} does not return a PDF"
                    )
                
                temp_path = settings.UPLOAD_DIR / generate_filename("pdf")
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                saved_paths.append(temp_path)
            except requests.RequestException as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download from {url}: {str(e)}"
                )
        
        pdf_path = pdf_service.merge_pdfs(saved_paths)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=merged_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        for path in saved_paths:
            cleanup_file(path)

@router.post("/merge-from-base64")
async def merge_pdfs_from_base64(request: MergePDFsFromBase64Request):
    """Merge PDFs from base64-encoded strings"""
    if len(request.pdfs) > 50:
        raise HTTPException(
            status_code=400,
            detail="Too many PDFs. Max 50 per request"
        )
    
    saved_paths = []
    
    try:
        for idx, pdf_b64 in enumerate(request.pdfs):
            try:
                pdf_bytes = base64.b64decode(pdf_b64)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid base64 at index {idx}"
                )
            
            if not pdf_bytes.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Data at index {idx} is not a PDF"
                )
            
            temp_path = settings.UPLOAD_DIR / generate_filename("pdf")
            with open(temp_path, 'wb') as f:
                f.write(pdf_bytes)
            
            saved_paths.append(temp_path)
        
        pdf_path = pdf_service.merge_pdfs(saved_paths)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=merged_{pdf_path.name}",
                "Content-Type": "application/pdf"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        for path in saved_paths:
            cleanup_file(path)
