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

# Calculate backend root
BACKEND_ROOT = Path(__file__).parent.parent.parent

from backend.course_service.services.document.parser import parse_files
from llama_cloud_services import LlamaParse

router = APIRouter()

# Import quiz generation services
from backend.quiz_service.services.question.generator import QuestionGenerator
from backend.shared.services.llm.mistral_client import MistralClient
from backend.course_service.models.course import CourseStructure, Topic, Subtopic, Concept
from backend.quiz_service.models.question import DifficultyLevel
from backend.shared.services.llm.pdf_summary import PDF_SUMMARY_SYSTEM_INSTRUCTION

# Lock for JSON file operations to prevent race conditions
_json_file_lock = asyncio.Lock()


async def generate_quiz_for_file(file_name:str, content:str, summary:str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """Generate a quiz for a specific file content.
    
    Args:
        file_name (str): Name of the file
        content (str): The text content of the file.
        summary (str): A summary of the contents of the file.
        num_questions (int): The number of questions to generate.
        
    Returns:
        List of generated questions
    """
    try:
        # Initialize question generator
        mistral_client = MistralClient()
        generator = QuestionGenerator(mistral_client)
        
        # Create a concept from the file content
        topic_name = file_name.replace('.pdf', '').replace('_', ' ').title()
        
        # Use first 5000 chars for concept creation to avoid token limits
        content_preview = content[:5000] if len(content) > 5000 else content
        
        concept = Concept(
            name=topic_name, # TODO: Need to generate concept name
            description=f"Key concepts from {file_name}",
            keywords=[]
        )

        difficulties = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]

        from backend.quiz_service.models.question import MultipleChoiceQuestion
        print(f"Start generating questions")
        questions:List[MultipleChoiceQuestion] = generator.generate_questions(
            topic=topic_name, # Need to generate topic name
            subtopic="Main Content", # TODO: Need to generate subtopic
            concept=concept,
            difficulty=difficulties[0],
            content_context=content_preview,
            num_answers=4
        )

        formatted_questions:List[Dict[str, Any]] = []
        for question in questions:
            
            # Convert to dict format for JSON storage
            question_dict = {
                "question_text": question.question_text,
                "answers": [
                    {
                        "text": answer.text,
                        "is_correct": answer.is_correct,
                        "explanation": answer.explanation
                    }
                    for answer in question.answers
                ],
                "topic": question.topic,
                "subtopic": question.subtopic,
                "concepts": question.concepts,
                "difficulty": question.difficulty.value,
                "explanation": question.explanation
            }
            
            formatted_questions.append(question_dict)
            
        return formatted_questions
        
    except Exception as e:
        print(f"Error generating quiz for {file_name}: {str(e)}")
        # Return empty quiz if generation fails
        return []
    
async def generate_pdf_summary_for_file(file_name:str, prompt_data:Dict[str, Any]) -> str:
    """Generate a summary for a specific PDF file content.
    
    Args:
        file_name: Name of the file
        content: File content
    Returns:
        Generated summary string
    """
    try:
        mistral_client = MistralClient()
        
        # # Use first 3000 chars to avoid token limits
        # content_preview = prompt_data["raw_text"][:3000] if len(prompt_data["raw_text"]) > 3000 else prompt_data["raw_text"]

        response = mistral_client.generate(
            prompt=json.dumps(prompt_data, indent=4),
            system_message=PDF_SUMMARY_SYSTEM_INSTRUCTION
        )
        print(f"Generated summary for {file_name}: {response.strip()}")
        
        return response.strip()
    except Exception as e:
        print(f"Error generating summary for {file_name}: {str(e)}")
        return "No summary available."

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
    summary: Optional[str] = None  # AI-generated summary
    quiz: Optional[List[Dict[str, Any]]] = None  # Quiz questions for this file


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
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        # Convert the parsed data to the response model
        files = {}
        for file_path, file_data in parsed_data.items():
            files[file_path] = ParsedFileData(
                metadata=ParsedFileMetadata(**file_data["metadata"]),
                content=file_data["content"],
                summary=file_data.get("summary"),  # Include summary if present
                quiz=file_data.get("quiz")  # Include quiz data if present
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
    if len(file_content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    if not LLAMA_CLOUD_API_KEY:
        raise HTTPException(status_code=500, detail="LLAMA_CLOUD_API_KEY environment variable not set")

    # Check if file has already been processed (already exists in parsed_data.json)
    parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
    file_key = f"data/raw/{file.filename}"
    
    async with _json_file_lock:
        if parsed_data_file.exists():
            # Use asyncio.to_thread to make file I/O non-blocking
            def read_json_file():
                with open(parsed_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            existing_data = await asyncio.to_thread(read_json_file)
            
            if file_key in existing_data:
                raise HTTPException(
                    status_code=409, 
                    detail=f"This file has already been uploaded and processed. Please use a different filename or delete the existing file first."
                )
    
    # Save file temporarily
    original_file_name = file.filename # For saving later on
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name

    try:
        # Initialize parser (reduce workers for single file)
        print(LLAMA_CLOUD_API_KEY)
        print("path", tmp_path)
        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            num_workers=1,  # Use 1 worker for single file uploads
            verbose=True,
            language="en"
        )

        # Parse the file with timeout (5 minutes max)
        try:
            print(f"Started parsing")
            file_names:List[str] = [tmp_path]
            result = await asyncio.wait_for(
                parse_files(file_names, parser),
                timeout=300.0 # 5 minutes timeout
            )
            print(f"Result: {result}")
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="PDF parsing timed out. The file may be too large or complex. Please try a smaller file."
            )

        # Extract the parsed data
        parsed_data = result.get(tmp_path)

        if not parsed_data:
            raise HTTPException(status_code=500, detail="Failed to parse PDF - no data returned")
        
        # Modify the file name back to original for saving (and display)
        parsed_data["metadata"]["file_name"] = original_file_name
        file_contents = parsed_data["content"]

        # Generate summary first (quiz generation requires summary parameter)
        print(f"Generating summary for {original_file_name}...")
        pdf_summary_prompt_data = {
            "file_name": original_file_name,
            "raw_text": file_contents,
            "topic": "", # TODO: Need to somehow generate a topic
            "subtopic": "" # TODO: Need to somehow generate a subtopic
        }
        
        pdf_summary = await generate_pdf_summary_for_file(
            file_name=original_file_name,
            prompt_data=pdf_summary_prompt_data,
        )
        
        # Add summary to parsed data
        parsed_data["summary"] = pdf_summary
        
        # Generate quiz after summary (quiz generation requires summary)
        print(f"Generating quiz for {original_file_name}...")
        num_questions = 5  # Default number of questions
        quiz_questions = await generate_quiz_for_file(
            file_name=original_file_name,
            content=file_contents,
            summary=pdf_summary,
            num_questions=num_questions
        )
        
        # Add quiz to parsed data
        parsed_data["quiz"] = quiz_questions
        print(f"Generated {len(quiz_questions)} quiz questions and summary for {original_file_name}")

        # Use lock to safely write to JSON file (prevents race conditions with parallel uploads)
        async with _json_file_lock:
            # Load existing parsed_data.json
            parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
            
            def read_json_file():
                if parsed_data_file.exists():
                    with open(parsed_data_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return {}
            
            def write_json_file(data):
                with open(parsed_data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            
            # Load existing data (non-blocking)
            existing_data = await asyncio.to_thread(read_json_file)

            # Add the new parsed file (use relative path as key)
            file_key = f"data/raw/{file.filename}"
            existing_data[file_key] = parsed_data

            # Save updated parsed_data.json (non-blocking)
            await asyncio.to_thread(write_json_file, existing_data)

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


@router.post("/generate-quiz/{file_key:path}", response_model=UploadResponse)
async def generate_quiz_for_existing_file(file_key: str, num_questions: int = 5):
    """Generate or regenerate a quiz for an existing parsed file.
    
    Args:
        file_key: Key of the file in parsed_data.json
        num_questions: Number of questions to generate (default: 5)
    """
    try:
        # Load existing parsed_data.json
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if file_key not in existing_data:
            raise HTTPException(status_code=404, detail=f"File {file_key} not found in parsed data")
        
        file_data = existing_data[file_key]
        file_name = file_data["metadata"]["file_name"]
        content = file_data["content"]
        summary = file_data["summary"] 
        
        # Generate new quiz
        print(f"Regenerating quiz for {file_name}...")
        quiz_questions = await generate_quiz_for_file(
            file_name=file_name,
            content=content,
            summary=summary,
            num_questions=num_questions
        )
        
        # Update the quiz in the file data
        existing_data[file_key]["quiz"] = quiz_questions
        
        # Save updated parsed_data.json
        with open(parsed_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        
        print(f"Successfully regenerated {len(quiz_questions)} quiz questions for {file_name}")
        
        return UploadResponse(
            success=True,
            message=f"Successfully generated {len(quiz_questions)} quiz questions for {file_name}",
            data={"quiz": quiz_questions}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.delete("/{file_key:path}", response_model=UploadResponse)
async def delete_course(file_key: str):
    """Delete a course file from parsed_data.json.
    
    Args:
        file_key: Key of the file in parsed_data.json (e.g., "data/raw/filename.pdf")
    """
    try:
        # Load existing parsed_data.json
        parsed_data_file = BACKEND_ROOT / "course_service" / "data" / "parsed_data.json"
        
        if not parsed_data_file.exists():
            raise HTTPException(status_code=404, detail="Parsed data file not found")
        
        with open(parsed_data_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        if file_key not in existing_data:
            raise HTTPException(status_code=404, detail=f"File {file_key} not found in parsed data")
        
        # Get file name for response message
        file_name = existing_data[file_key]["metadata"]["file_name"]
        
        # Remove the file from the data
        del existing_data[file_key]
        
        # Save updated parsed_data.json
        with open(parsed_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        
        print(f"Successfully deleted {file_name} from parsed data")
        
        return UploadResponse(
            success=True,
            message=f"Successfully deleted {file_name}",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")


