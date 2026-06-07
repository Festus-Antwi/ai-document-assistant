from typing import Annotated
from pathlib import Path
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi import status
from fastapi.responses import RedirectResponse


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
        return RedirectResponse(url="/?message=unsupported_file",status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        stored_filename = f"{uuid.uuid4()}{extension}"
        file_path = UPLOAD_DIR / stored_filename

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        new_document = models.Document(stored_filename = stored_filename, original_filename=file.filename)
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        return RedirectResponse(
            url=f"/?message=upload_success&filename={file.filename}",
            status_code=status.HTTP_303_SEE_OTHER
            )
    except Exception as e:
        print ("UPLOAD ERROR:", e)
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        return RedirectResponse(
            url=f"/?message=upload_failed",
            status_code=status.HTTP_303_SEE_OTHER
            )

# Get Documents
@router.get("/", include_in_schema=False, name="home")
@router.get("/documents", include_in_schema=False, name="documents")
def get_documents(request:Request, db:Annotated[Session, Depends(get_db)], message: str | None = None, filename: str | None = None):
    result = db.execute(select(models.Document))
    documents = result.scalars().all()

    alert = None
    if message == "upload_success":
        alert = f"{filename} uploaded successfully!"
    elif message == "unsupported_file":
        alert = "Unsupported file type. Please upload PDF, DOCX or TXT files."
    elif message == "upload_failed":
        alert = "Failed to upload document."

    return templates.TemplateResponse(
        request,
        "home.html",
        {"documents": documents, "title": "Documents", "message":message, "alert":alert},
    )

# Get A Document
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


#DELETE
###############################################
@router.post("/documents/{document_id}/delete", name="web_delete_document")
def delete_document(document_id:int, db:Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)
    if document:
        if not document.file_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file is missing")
        
        Path(document.filepath).unlink(missing_ok=True)
        db.delete(document)
        db.commit()
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.post("/documents/{document_id}/analysis/delete", name="web_delete_analysis")
def delete_document_analysis(document_id: int, db: Annotated[Session, Depends(get_db)]):
    document = db.get(models.Document,document_id)

    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not document.analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    db.delete(document.analysis)
    db.commit()
    return RedirectResponse(
            url=f"/documents/{document_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )



@router.post("/documents/sync_documents", name='web_sync_documents')
def sync_documents(request:Request,db:Annotated[Session, Depends(get_db)]):
    results = db.execute(select(models.Document))
    documents = results.scalars().all()
    for document in documents:
        if not document.file_exists:
            db.delete(document)
    db.commit()
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )

