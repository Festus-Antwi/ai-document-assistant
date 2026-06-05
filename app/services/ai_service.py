import json
import time
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from app.core.config import GEMINI_API_KEY
import random

def call_gemini_with_retry(fn, max_retries=5):
    for i in range(max_retries):
        try:
            return fn()
        except ClientError as e:
            code = getattr(e, "code", None)
            
            if code == 429:
                wait = min(60, 2 ** i) + random.uniform(0, 1)
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")

client = genai.Client(
    api_key=GEMINI_API_KEY
)

def summarize_document(text: str):

    prompt = f"""
    Summarize the following document.

    Document:
    {text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def answer_question(document_text:str, question:str):
    prompt = f"""
    You are an enterprise document assistant.

    Answer ONLY using information found in the document.

    If the answer cannot be found, say:

    "I could not find that information in the document."

    Document:
    {document_text}
    Question:
    {question}
    """

    response = client.models.generate_content(
        model= "gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def extract_key_information(document_text: str):

    prompt = f"""
    Analyze the document and return ONLY valid JSON.

    Do not wrap the JSON in markdown.
    Do not use ```json.
    Do not provide explanations.

    Format:

    {{
        "document_type": "",
        "key_information": {{}}
    }}

    The key_information object should contain fields relevant to the document type.

    DOCUMENT:

    {document_text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "document_type": "Unknown",
            "key_information": {},
            "raw_response": text
        }


def extract_key_information_pdf(pdf_path):
    prompt = f"""
        Analyze the document and return ONLY valid JSON.

        Do not wrap the JSON in markdown.
        Do not use ```json.
        Do not provide explanations.

        Format:

        {{
            "document_type": "",
            "key_information": {{}}
        }}

        The key_information object should contain fields relevant to the document type.

    """

    with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

    response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                ),
                prompt
            ]
        )
    text =  response.text
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "document_type": "Unknown",
            "key_information": {},
            "raw_response": text
        }
    