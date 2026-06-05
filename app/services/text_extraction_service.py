from pathlib import Path
from docx import Document
import fitz
from pathlib import Path
from PyPDF2 import PdfReader
import re

def extract_pdf_text(file_path: Path) -> str:
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())

    return "\n".join(pages)


def clean_document_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def extract_docx_text(file_path: Path) -> str:
    doc = Document(file_path)

    return "\n".join(
        para.text
        for para in doc.paragraphs
        if para.text.strip()
    )


def extract_txt_text(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
    

def extract_document_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    elif extension == ".docx":
        return extract_docx_text(file_path)

    elif extension == ".txt":
        return extract_txt_text(file_path)
    
    raise ValueError(
        f"Unsupported file type: {extension}"
    )