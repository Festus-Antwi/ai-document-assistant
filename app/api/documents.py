from typing import Annotated
from pathlib import Path
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi import status

from app.schemas import DocumentResponse, SummaryResponse, ExtractionResponse, QuestionResponse, AnalysisResponse

from app.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

#Upload Document
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(db: Annotated[Session, Depends(get_db)], file: UploadFile = File(...)):
    extension = Path(file.filename).suffix
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported File Type")
    
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
    document = db.get(models.Document,document_id)
    if document:
        return document
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/{document_id}/extraction", response_model=ExtractionResponse)
def get_document_extraction(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if document:
        if not document.extraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document has no extraction")
        return document.extraction
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/{document_id}/summary", response_model=SummaryResponse)
def get_document_summary(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if document:
        if not document.extraction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document has no summary")
        return document.summary
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/{document_id}/analysis", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
def get_document_analysis(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if document:
        if not document.analysis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document has no analysis")
        return document.analysis
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


@router.get("/{document_id}/questions", response_model=list[QuestionResponse])
def get_document_questions(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if document:
        if not document.questions:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document has no questions")
        return document.questions
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


#DELETE ROUTES
####################################################
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if document:
        if not document.file_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
        
        Path(document.filepath).unlink(missing_ok=True)
        db.delete(document)
        db.commit()
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.delete("/{document_id}/summary", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_summary(document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not document.summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")

    db.delete(document.summary)
    db.commit()


@router.delete("/{document_id}/questions", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_questions(document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not document.questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questions not found")

    db.delete(document.questions)
    db.commit()


@router.delete("/questions/{question_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int,db: Annotated[Session, Depends(get_db)]):
    question = db.get(models.Question,question_id)

    if not question:
        raise HTTPException(status_code=404,detail="Question not found")

    db.delete(question)
    db.commit()


@router.delete("/{document_id}/extraction", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_extraction(document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not document.questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questions not found")

    db.delete(document.questions)
    db.commit()


@router.delete("/{document_id}/analysis", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_analysis(document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not document.analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    db.delete(document.analysis)
    db.commit()


@router.post("/sync-documents", status_code=status.HTTP_200_OK)
def sync_documents(db:Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Document))
    documents = results.scalars().all()
    for document in documents:
        if not document.file_exists:
            db.delete(document)
    db.commit()
    




# @router.get("/extract/{document_id}", status_code=status.HTTP_200_OK)
# def extract_text(document_id:int, db: Annotated[Session, Depends(get_db)]):
#     document = db.get(models.Document,document_id)
#     if document:
#         if not document.file_exists:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
        
#         raw_text = extract_document_text(document.filepath)
#         clean_text = clean_document_text(raw_text)

#         return {
#             "filename": document.original_filename,
#             "text": clean_text
#         }
    
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
