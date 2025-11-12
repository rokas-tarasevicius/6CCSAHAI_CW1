import os
from llama_cloud_services import LlamaParse

if __name__ == "__main__":

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", None)
    assert LLAMA_CLOUD_API_KEY is not None, "Please provide an environmental variable for 'LLAMA_CLOUD_API_KEY'"

    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        num_workers=4,
        verbose=True,
        language="en"
    )

    result = parser.parse("LLMs.pdf")
    text_documents = result.get_text_documents(split_by_page=False)
    print(type(text_documents))
    print(f"Text: {text_documents}")