"""Course material API routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import json
import os
import tempfile
import asyncio
from pathlib import Path

# Calculate project root once
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.document.parser import parse_files
from llama_cloud_services import LlamaParse

router = APIRouter()


class ParsedFileMetadata(BaseModel):
    """Metadata for a parsed file."""
    file_name: str
    file_type: str
    content_length: int
    language: str
    extraction_timestamp: str
    timezone: str


class ParsedFileData(BaseModel):
    """Data structure for a parsed file."""
    metadata: ParsedFileMetadata
    content: str


class ParsedDataResponse(BaseModel):
    """Response model for parsed data."""
    files: Dict[str, ParsedFileData]


class UploadResponse(BaseModel):
    """PDF upload response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/", response_model=ParsedDataResponse)
async def get_course():
    """Get parsed course material from PDF files."""
    try:
        # Get absolute path to parsed data file
        parsed_data_file = PROJECT_ROOT / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # Convert the parsed data to the response model
        files = {}
        for file_path, file_data in parsed_data.items():
            files[file_path] = ParsedFileData(
                metadata=ParsedFileMetadata(**file_data["metadata"]),
                content=file_data["content"]
            )
        
        return ParsedDataResponse(files=files)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load parsed data: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and parse a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    if not LLAMA_CLOUD_API_KEY:
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY environment variable not set")

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name

    try:
        # Initialize parser (reduce workers for single file)
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            num_workers=1,  # Use 1 worker for single file uploads
            verbose=True,
            language="en"
        )

        # Parse the file with timeout (5 minutes max)
        try:
            result = await asyncio.wait_for(
                parse_files([tmp_path], parser),
                timeout=300.0  # 5 minutes timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="PDF parsing timed out. The file may be too large or complex. Please try a smaller file."
            )

        # Extract the parsed data
        parsed_data = result.get(tmp_path)

        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse PDF - no data returned")

        # Load existing parsed_data.json, update it, and save
        parsed_data_file = PROJECT_ROOT / "data" / "parsed_data.json"
        existing_data = {}
        if parsed_data_file.exists():
            with open(parsed_data_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

        # Add the new parsed file (use relative path as key)
        file_key = f"data/raw/{file.filename}"
        existing_data[file_key] = parsed_data

        # Save updated parsed_data.json
        with open(parsed_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)

        return UploadResponse(
            success=True,
            message=f"Successfully parsed {file.filename}",
            data=parsed_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


