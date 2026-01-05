"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload, status, results
from app.config import settings

app = FastAPI(
    title="Meeting Video Processing API",
    description="API for processing meeting videos with transcription, summarization, and slide extraction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(status.router)
app.include_router(results.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Meeting Video Processing API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}



