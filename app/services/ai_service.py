import json
from google import genai
from app.core.config import GEMINI_API_KEY

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

    return json.loads(text)