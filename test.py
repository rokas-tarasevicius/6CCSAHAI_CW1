import os
import asyncio
import json
from llama_cloud_services import LlamaParse
from typing import List, Dict

async def parse_files(file_paths:List[str], parser:LlamaParse):
    results = await parser.aparse(file_paths)
    res = {}
    for r, file_path in zip(results, file_paths):
        text = ""
        for doc in r.get_text_documents(split_by_page=False):
            text = text + doc.text + "\n\n"
        res[file_path] = text
    return res
            
if __name__ == "__main__":

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", None)
    assert LLAMA_CLOUD_API_KEY is not None, "Please provide an environmental variable for 'LLAMA_CLOUD_API_KEY'"

    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        num_workers=4,
        verbose=True,
        language="en"
    )
    file_names:List[str] = [
        "LLMs.pdf",
        "Transformers.pdf"
    ]
    res = asyncio.run(
        parse_files(
            file_paths=file_names,
            parser=parser
        )
    )
    
    print(json.dumps(res, indent=4))
    with open(f"parsed_data.json", "w") as f:
        json.dump(res, f, indent=4)