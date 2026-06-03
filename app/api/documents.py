from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from app.services.pdf_service import extract_pdf_text, clean_pdf_text

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "message": "File uploaded successfully",
        "filename": file.filename
    }


@router.get("/extract/{filename}")
def extract_document_text(filename: str):

    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        return {
            "error": "File not found"
        }

    raw_text = extract_pdf_text(file_path)
    clean_text = clean_pdf_text(raw_text)

    return {
        "filename": filename,
        "text": clean_text
    }


