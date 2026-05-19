from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from fastapi.openapi.utils import get_openapi
from app.models import User, Document, Bookmark
from app.routes import auth
from app.routes import auth, documents, bookmarks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VoiceReader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ 
        "http://localhost:3000",
        "https://voicereader-frontend.onrender.com"
        "https://voicereader-frontend.vercel.app",
        "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(bookmarks.router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="VoiceReader API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def read_root():
    return {"message": "VoiceReader API is running"}