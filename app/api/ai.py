from pathlib import Path
import uuid
from fastapi import APIRouter, HTTPException
from fastapi import status, Depends
from typing import Annotated
from app.schemas import QuestionRequest
from app.services.ai_service import (
    call_gemini_with_retry,
    summarize_document, 
    answer_question, 
    extract_key_information, 
    extract_key_information_pdf
    )

from app.services.text_extraction_service import extract_document_text, clean_document_text

from app.schemas import SummaryResponse, ExtractionResponse, QuestionRequest, QuestionResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app import models

router = APIRouter()


@router.post("/summarize/{document_id}", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def summarize_text(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") 
    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    raw_text = extract_document_text(document.filepath)
    cleaned_text = clean_document_text(raw_text)

    # result = summarize_document(cleaned_text)
    result = call_gemini_with_retry(lambda:summarize_document(cleaned_text))

    existing_summary =  document.summary
    if existing_summary: #Update Summary text
        existing_summary.summary_text = result
        db.commit()
        db.refresh(existing_summary)
        return existing_summary
        
    new_summary = models.Summary(summary_text=result, document_id=document.id)
    db.add(new_summary)
    db.commit()
    db.refresh(new_summary)
    return new_summary  
       

@router.post("/ask/{document_id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def ask_document(document_id:int, question_request:QuestionRequest, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    raw_text = extract_document_text(document.filepath)
    cleaned_text = clean_document_text(raw_text)
    # result = answer_question(cleaned_text, question_request.question)
    result = call_gemini_with_retry(lambda:answer_question(cleaned_text))
    
    new_question = models.Question(document_id=document.id, question=question_request.question, answer=result)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


@router.post("/extract/{document_id}", response_model=ExtractionResponse, status_code=status.HTTP_200_OK)
async def extract_information(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    extension = Path(document.filepath).suffix.lower()
    if extension == ".pdf":
        # result = extract_key_information_pdf(document.filepath)
        result = call_gemini_with_retry(lambda:extract_key_information_pdf(document.filepath))
    else:
        raw_text = extract_document_text(document.filepath)
        cleaned_text = clean_document_text(raw_text)
        # result = extract_key_information(cleaned_text)
        result = call_gemini_with_retry(lambda:extract_key_information(cleaned_text))

    existing_extraction = document.extraction
    if existing_extraction:
        document.extraction.extracted_json = result
        db.commit()
        db.refresh(existing_extraction)
        return existing_extraction
    
    new_extraction = models.Extraction(document_id=document.id, extracted_json = result)
    db.add(new_extraction)
    db.commit()
    db.refresh(new_extraction)
    return new_extraction