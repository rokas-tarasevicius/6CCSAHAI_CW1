"""Course material API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import json
from pathlib import Path

# Calculate project root once
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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


