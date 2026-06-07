import json
import time
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from app.core.config import GEMINI_API_KEY
import random

import random
import time

from google.genai.errors import ClientError, ServerError


def call_gemini_with_retry(fn, max_retries=5):
    for i in range(max_retries):
        try:
            return fn()

        except ClientError as e:
            if "429" in str(e):
                wait = min(60, 2 ** i) + random.uniform(0, 1)

                print(f"Rate limit hit. Waiting {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise

        except ServerError as e:
            if "503" in str(e):
                wait = min(60, 2 ** i) + random.uniform(0, 1)

                print(
                    f"Gemini overloaded. "
                    f"Waiting {wait:.1f}s..."
                )

                time.sleep(wait)
            else:
                raise

    raise Exception("Max retries exceeded")


client = genai.Client(
    api_key=GEMINI_API_KEY
)

def summarize(text: str):

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
    

def analyse(document_text:str):
    prompt = f"""
    Analyze this document and return ONLY valid JSON.

    Do not use markdown.
    Do not use ```json.
    Do not include explanations.
    Do not include text before or after the JSON.

    Return exactly this structure:

    {{
        "document_type": "",
        "summary": "",
        "key_information": {{}},
        "faq": []
    }}

    Requirements:

    1. document_type
    - Identify the document type.
    - Examples:
        insurance_policy
        claims_document
        internal_procedures
        contract
        invoice
        receipt
        other

    2. summary
    - Provide a concise summary of the document.
    - Maximum 200 words.

    3. key_information
    - Extract the most important fields for the document.
    - Use meaningful field names.
    - Include dates, identifiers, amounts, parties, policy numbers, invoice numbers, 
      and other important details when available.

    4. faq
    - Generate 5-10 useful question and answer pairs.
    - Questions should be questions a user might ask about the document.
    - Answers must be based only on information found in the document.

    Example:

    {{
        "document_type": "insurance_policy",
        "summary": "This insurance policy provides vehicle coverage...",

        "key_information": {{
            "policy_number": "ABC123",
            "insured_name": "John Doe",
            "effective_date": "2026-01-01"
        }},

        "faq": [
            {{
                "question": "What is the policy number?",
                "answer": "ABC123"
            }},
            {{
                "question": "Who is insured?",
                "answer": "John Doe"
            }}
        ]
    }}
    DOCUMENT:{document_text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
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


def analyse_pdf(pdf_path):
    prompt = """
    Analyze this document and return ONLY valid JSON.

    Do not use markdown.
    Do not use ```json.
    Do not include explanations.
    Do not include text before or after the JSON.

    Return exactly this structure:

    {
        "document_type": "",
        "summary": "",
        "key_information": {},
        "faq": []
    }

    Requirements:

    1. document_type
    - Identify the document type.
    - Examples:
        insurance_policy
        claims_document
        internal_procedures
        contract
        invoice
        receipt
        other

    2. summary
    - Provide a concise summary of the document.
    - Maximum 200 words.

    3. key_information
    - Extract the most important fields for the document.
    - Use meaningful field names.
    - Include dates, identifiers, amounts, parties, policy numbers, invoice numbers, 
      and other important details when available.

    4. faq
    - Generate 5-10 useful question and answer pairs.
    - Questions should be questions a user might ask about the document.
    - Answers must be based only on information found in the document.

    Example:

    {
        "document_type": "insurance_policy",
        "summary": "This insurance policy provides vehicle coverage...",

        "key_information": {
            "policy_number": "ABC123",
            "insured_name": "John Doe",
            "effective_date": "2026-01-01"
        },

        "faq": [
            {
                "question": "What is the policy number?",
                "answer": "ABC123"
            },
            {
                "question": "Who is insured?",
                "answer": "John Doe"
            }
        ]
    }

    Return ONLY valid JSON.
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