from pathlib import Path
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException
from fastapi import status, Depends
from typing import Annotated
from app.services.ai_service import (
    call_gemini_with_retry,
    summarize, 
    answer_question, 
    extract_key_information, 
    extract_key_information_pdf,
    analyse,
    analyse_pdf
    )
from app.services.text_extraction_service import extract_document_text, clean_document_text

from app.schemas import(
    SummaryResponse, 
    ExtractionResponse, 
    QuestionRequest, 
    QuestionResponse, 
    AnalysisResponse,
    GeminiAnalysis
) 
from app.database import get_db
from sqlalchemy.orm import Session
from app import models

router = APIRouter()


@router.post("/summarize/{document_id}", response_model=SummaryResponse, status_code=status.HTTP_200_OK)
async def summarize_document(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") 
    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    raw_text = extract_document_text(document.filepath)
    cleaned_text = clean_document_text(raw_text)
    try:
        result = call_gemini_with_retry(lambda:summarize(cleaned_text))
    except Exception as e:
        print("SUMMARY ERROR:", repr(e))
        raise
        # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")

    existing_summary =  document.summary
    if existing_summary: #Update Summary text
        existing_summary.summary_text = result
        existing_summary.generated_at = datetime.now(UTC)
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
    try:
        result = call_gemini_with_retry(lambda:answer_question(cleaned_text, question_request))
    except Exception as e:
        print("ANSWERING ERROR:", repr(e))
        raise
        # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")
    
    new_question = models.Question(document_id=document.id, question=question_request.question, answer=result)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


@router.post("/extract/{document_id}", response_model=ExtractionResponse, status_code=status.HTTP_200_OK)
async def extract_document(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    extension = Path(document.filepath).suffix.lower()
    if extension == ".pdf":
        try:
            result = call_gemini_with_retry(lambda:extract_key_information_pdf(document.filepath))
        except Exception as e:
            # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")
            print("EXTRACTION ERROR:", repr(e))
            raise
    else:
        raw_text = extract_document_text(document.filepath)
        cleaned_text = clean_document_text(raw_text)
        try:
            result = call_gemini_with_retry(lambda:extract_key_information(cleaned_text))
        except Exception as e:
            # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")
            print("EXTRACTION ERROR:", repr(e))
            raise

    existing_extraction = document.extraction
    if existing_extraction:
        existing_extraction.extracted_json = result
        existing_extraction.generated_at = datetime.now(UTC)
        db.commit()
        db.refresh(existing_extraction)
        return existing_extraction
    
    new_extraction = models.Extraction(document_id=document.id, extracted_json = result)
    db.add(new_extraction)
    db.commit()
    db.refresh(new_extraction)
    return new_extraction


@router.post("/analyse/{document_id}", response_model=AnalysisResponse, status_code=status.HTTP_200_OK)
async def analyse_document(document_id:int,  db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file missing")
    
    extension = Path(document.filepath).suffix.lower()
    if extension == ".pdf":
        try:
            result = call_gemini_with_retry(lambda:analyse_pdf(document.filepath))
        except Exception as e:
            print("ANALYSIS ERROR:", repr(e))
            raise
            # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")
    else:
        raw_text = extract_document_text(document.filepath)
        cleaned_text = clean_document_text(raw_text)
        try:
            result = call_gemini_with_retry(lambda:analyse(cleaned_text))
        except Exception as e:
            print("ANALYSIS ERROR:", repr(e))
            # raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gemini Currently Unavailable")
            raise
    validated = GeminiAnalysis.model_validate(result)

    existing_analysis =  document.analysis
    if existing_analysis: #Update Analysis
        existing_analysis.document_type = validated.document_type
        existing_analysis.summary = validated.summary
        existing_analysis.extracted_json =validated.key_information
        existing_analysis.faq_json=validated.faq
        existing_analysis.generated_at = datetime.now(UTC)
        db.commit()
        db.refresh(existing_analysis)
        return existing_analysis
    
    new_analysis = models.DocumentAnalysis(
        document_id=document.id,
        document_type=validated.document_type,
        summary=validated.summary,
        extracted_json=validated.key_information,
        faq_json=validated.faq
    )

    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)
    return new_analysis