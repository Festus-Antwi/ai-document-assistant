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