"""PDF/DOCX parsing service using LlamaParse."""
import os
import asyncio
import json
from llama_cloud_services import LlamaParse
from typing import List, Dict, Any
from datetime import datetime, timezone


async def parse_files(file_paths: List[str], parser: LlamaParse) -> Dict[str, Dict[str, Any]]:
    """
    Asynchronously parses one or more PDF/DOCX files into plain text and attaches some
    metadata.

    Args:
        file_paths (List[str]): A list of file paths to documents to parse. Each path should
                                point to a supported file type such as ".pdf" or ".docx"
        parser (LlamaParse): LlamaParse client instance with a valid API key.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping file paths to parsed content and metadata.
    """
    results = await parser.aparse(file_paths)
    res = {}
    for r, file_path in zip(results, file_paths):
        text = ""
        for doc in r.get_text_documents(split_by_page=False):
            text = text + doc.text + "\n\n"
        res[file_path] = {
            "metadata": {
                "file_name": os.path.basename(file_path),
                "file_type": file_path.split(".")[-1],
                "content_length": len(text),
                "language": "en",
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "timezone": "utc"
            },
            "content": text
        }
    return res


async def parse_pdf_file(file_path: str, api_key: str) -> Dict[str, Any]:
    """
    Parse a single PDF file using LlamaParse.
    
    Args:
        file_path: Path to the PDF file
        api_key: LlamaCloud API key
    
    Returns:
        Dict containing parsed content and metadata
    """
    parser = LlamaParse(
        api_key=api_key,
        num_workers=4,
        verbose=True,
        language="en"
    )
    result = await parse_files([file_path], parser)
    return result.get(file_path, {})


if __name__ == "__main__":
    """CLI entry point for batch parsing."""
    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", None)
    assert LLAMA_CLOUD_API_KEY is not None, "Please provide an environmental variable for 'LLAMA_CLOUD_API_KEY'"

    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        num_workers=4,
        verbose=True,
        language="en"
    )
    file_names: List[str] = [
        "data/raw/LLMs.pdf",
        "data/raw/Transformers.pdf"
    ]
    res = asyncio.run(
        parse_files(
            file_paths=file_names,
            parser=parser
        )
    )
    
    print(json.dumps(res, indent=4))
    with open("data/parsed_data.json", "w") as f:
        json.dump(res, f, indent=4)

