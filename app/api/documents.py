from typing import Annotated
from pathlib import Path
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.services.pdf_service import extract_pdf_text, clean_pdf_text
from fastapi import status

from app.schemas import DocumentResponse

from app.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

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


@router.get("/", response_model=list[DocumentResponse], status_code=status.HTTP_200_OK)
def get_documents(db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document))
    documents = result.scalars().all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document).where(models.Document.id == document_id))
    document = result.scalars().first()
    if document:
        return document
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/extract/{document_id}", status_code=status.HTTP_200_OK)
def extract_document_text(document_id:int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document).where(models.Document.id == document_id))
    document = result.scalars().first()
    if document:
        if not document.file_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
        
        raw_text = extract_pdf_text(document.filepath)
        clean_text = clean_pdf_text(raw_text)

        return {
            "filename": document.original_filename,
            "text": clean_text
        }
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.delete("/delete/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
def delete_document(document_id:int, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document).where(models.Document.id == document_id))
    document = result.scalars().first()
    if document:
        if not document.file_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
        
        Path(document.filepath).unlink(missing_ok=True)
        db.delete(document)
        db.commit()
        return document
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.post("/sync-documents")
def sync_documents(db:Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Document))
    documents = results.scalars().all()
    for document in documents:
        if not document.file_exists:
            db.delete(document)
    db.commit()

