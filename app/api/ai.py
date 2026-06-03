from pathlib import Path
from fastapi import APIRouter
from app.schemas.question import QuestionRequest
from app.services.ai_service import summarize_document, answer_question, extract_key_information
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


@router.post("/ask/{filename}")
def ask_document(filename:str, question_request:QuestionRequest):
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
       return {
            "error":"File not found"
       }
    
    raw_text = extract_pdf_text(file_path)
    cleaned_text = clean_pdf_text(raw_text)
    answer = answer_question(cleaned_text, question_request.question)
    
    return {
        "filename":filename,
        "question":question_request.question,
        "answer":answer
    }


@router.post("/extract/{filename}")
def extract_information(filename:str):
    filepath = UPLOAD_DIR/filename
    if not filepath.exists():
        return{
            "error":"File not found"
        }
    
    raw_text = extract_pdf_text(filepath)
    cleaned_text = clean_pdf_text(raw_text)

    key_information = extract_key_information(cleaned_text)

    return key_information