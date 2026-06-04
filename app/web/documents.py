from typing import Annotated
from pathlib import Path
import uuid

from fastapi import APIRouter, UploadFile, File, Depends
from app.services.pdf_service import extract_pdf_text, clean_pdf_text
from fastapi import status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.schemas import DocumentResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app import models
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

#Upload Document
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(db: Annotated[Session, Depends(get_db)], file: UploadFile = File(...)):
    extension = Path(file.filename).suffix
    stored_filename = f"{uuid.uuid4()}{extension}"

    file_path = UPLOAD_DIR / stored_filename

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    new_document = models.Document(stored_filename = stored_filename, original_filename=file.filename)
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return new_document



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


