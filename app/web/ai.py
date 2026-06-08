from pathlib import Path
from datetime import datetime, UTC
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi import status, Depends
from typing import Annotated

import httpx
from app.services.ai_service import (
    call_gemini_with_retry,
    answer_question, 
    analyse,
    analyse_pdf
    )
from app.services.text_extraction_service import extract_document_text, clean_document_text

from app.schemas import(
    GeminiAnalysis
) 
from app.database import get_db
from sqlalchemy.orm import Session
from app import models

router = APIRouter()


@router.post("/ask/{document_id}", name="ask_question")
async def ask_document(document_id:int, db:Annotated[Session, Depends(get_db)], question:str=Form(...)):
    document = db.get(models.Document,document_id)
    if not any(char.isalnum() for char in question):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Question Detected")
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not document.file_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
    
    raw_text = extract_document_text(document.filepath)
    cleaned_text = clean_document_text(raw_text)
    try:
       result = call_gemini_with_retry(lambda:answer_question(cleaned_text, question))

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to Gemini. Check your internet connection."
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Gemini currently unavailable."
        )
    
    new_question = models.Question(document_id=document.id, question=question, answer=result)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return RedirectResponse(url=f"/documents/{document_id}/#questions",status_code=303)


@router.post("/analyse/{document_id}", name="web_analyse_document")
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
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Gemini. Check your internet connection."
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Gemini currently unavailable."
            )
    else:
        raw_text = extract_document_text(document.filepath)
        cleaned_text = clean_document_text(raw_text)
        try:
            result = call_gemini_with_retry(lambda:analyse(cleaned_text))
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Gemini. Check your internet connection."
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Gemini currently unavailable."
            )
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

        return RedirectResponse(url=f"/documents/{document_id}",status_code=303)
    
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

    return RedirectResponse(url=f"/documents/{document_id}",status_code=303)