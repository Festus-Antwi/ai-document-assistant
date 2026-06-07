from typing import Annotated
from pathlib import Path
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Response
from fastapi import status
from fastapi.responses import RedirectResponse

from app.schemas import DocumentResponse, SummaryResponse, ExtractionResponse, QuestionResponse, AnalysisResponse

from app.database import get_db
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base

Base.metadata.create_all(bind=engine)

router = APIRouter()
router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

#Upload Document
@router.post("/upload", include_in_schema=False, name="upload_file")
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
    return RedirectResponse(url=f"/documents/",status_code=303)

@router.get("/", include_in_schema=False, name="home")
@router.get("/documents", include_in_schema=False, name="documents")
def get_documents(request:Request, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Document))
    documents = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"documents": documents, "title": "Documents"},
    )


@router.get("/documents/{document_id}", include_in_schema=False, name="document_page")
def get_document(request:Request, document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if document:
        title = document.original_filename[:50]
        return templates.TemplateResponse(
            request,
            "document.html",
            {"document":document, "title":title}
            
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

