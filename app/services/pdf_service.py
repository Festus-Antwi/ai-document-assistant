from pathlib import Path
from PyPDF2 import PdfReader
import re

def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

def clean_pdf_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()