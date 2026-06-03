from fastapi import FastAPI
from app.api.documents import router as document_router
from app.api.ai import router as ai_router
app = FastAPI(
    title="Enterprise AI Assistant"
)

app.include_router(document_router, prefix="/documents", tags=["Documents"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

@app.get("/")
def root():
    return {
        "message": "Enterprise AI Assistant"
    }