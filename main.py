from fastapi import FastAPI
from app.api.documents import router as document_router

app = FastAPI(
    title="Enterprise AI Assistant"
)

app.include_router(document_router, prefix="/documents", tags=["Documents"])


@app.get("/")
def root():
    return {
        "message": "Enterprise AI Assistant"
    }