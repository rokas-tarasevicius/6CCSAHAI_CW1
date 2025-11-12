"""FastAPI backend server for Adaptive Learning Platform."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.routes import questions, performance, videos, course

app = FastAPI(
    title="Adaptive Learning Platform API",
    description="Backend API for AI-powered adaptive learning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(course.router, prefix="/api/course", tags=["course"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(performance.router, prefix="/api/performance", tags=["performance"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Adaptive Learning Platform API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


