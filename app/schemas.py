from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stored_filename: str
    original_filename: str
    uploaded_at: datetime

class FAQItem(BaseModel):
    question: str
    answer: str

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    document_id:int
    document_type:str
    summary:str
    extracted_json: dict
    faq_json:list[FAQItem]
    generated_at:datetime

class GeminiAnalysis(BaseModel):
    document_type: str
    summary: str
    key_information: dict
    faq: list

class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    summary_text: str
    generated_at: datetime


class QuestionRequest(BaseModel):
    question:str


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    question: str
    answer: str
    created_at: datetime


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    extracted_json: dict
    generated_at: datetime
