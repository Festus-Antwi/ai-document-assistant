from fastapi import FastAPI
from app.api.documents import router as api_document_router
from app.api.ai import router as api_ai_router

from app.web.documents import router as web_document_router
from app.web.ai import router as web_ai_router

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise AI Document Assistant")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


app.include_router(api_document_router, prefix="/api/documents", tags=["Documents"])
app.include_router(api_ai_router, prefix="/api/ai", tags=["AI"])

app.include_router(web_document_router, prefix="/documents", tags=["Documents"], include_in_schema=False)
app.include_router(web_ai_router, prefix="/ai", tags=["AI"], include_in_schema=False)


@app.get("/")
def root():
    return {
        "message": "Enterprise AI Document Assistant"
    }





@app.exception_handler(StarletteHTTPException)
def general_http_exception_hander(request:Request, exception:StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail else "An error occured. Check your request and try again"
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail":message}, status_code=exception.status_code)
    
    return templates.TemplateResponse(
        request, 
        "error.html",
        {
            "message":message,
            "title":exception.status_code,
            "status_code":exception.status_code
        },
        status_code=exception.status_code
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request:Request, exception:RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail":exception.errors()}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message":"Invalid request. Please check your input and try again.",
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )
 