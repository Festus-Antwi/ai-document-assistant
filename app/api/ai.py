from pathlib import Path
from fastapi import APIRouter
from app.services.ai_service import summarize_document
from app.services.pdf_service import extract_pdf_text, clean_pdf_text

router = APIRouter()
UPLOAD_DIR = Path("uploads")


@router.post("/summarize/{filename}")
async def summarize_text(filename:str):
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
       return {
            "error":"File not found"
       }
    
    raw_text = extract_pdf_text(file_path)
    cleaned_text = clean_pdf_text(raw_text)
    summary = summarize_document(cleaned_text)
    
    return {
        "filename":filename,
        "summary":summary
    }
    
    