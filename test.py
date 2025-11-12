import os
import json
from llama_cloud_services import LlamaParse
from typing import List, Dict

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
    ]
    result = parser.parse(file_names)[0]
    text_documents = result.get_text_documents(split_by_page=False)
    print(type(text_documents), len(text_documents))
    
    res:Dict[str, str] = {}
    for file_name, doc in zip(file_names, text_documents):
        res[file_name] = doc.text
    
    print(json.dumps(res, indent=4))