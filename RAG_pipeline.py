from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY      = os.getenv("AZURE_SEARCH_KEY")
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY      = os.getenv("AZURE_OPENAI_KEY")
INDEX_NAME      = "Index"
TOP_K           = 3

search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
openai_client = AzureOpenAI(azure_endpoint=OPENAI_ENDPOINT, api_key=OPENAI_KEY, api_version="2024-02-01")

def get_embedding(text: str) -> list:
    response = openai_client.embeddings.create(
        input = text,
        model = "text-embedding-ada-002"
    )
    return response.data[0].embedding

def retrieve(query: str) -> list:
    """Hybrid search — semantic + vector combined."""
    embedding      = get_embedding(query)
    vector_query   = VectorizedQuery(
        vector        = embedding,
        k_nearest_neighbors = TOP_K,
        fields        = "embedding"
    )
    results = search_client.search(
        search_text  = query,           # keyword search
        vector_queries = [vector_query], # vector search
        query_type   = "semantic",
        semantic_configuration_name = "default",
        top          = TOP_K
    )
    return [r["chunk_text"] for r in results]

def generate(query: str, chunks: list) -> str:
    """Send retrieved chunks + query to LLM."""
    context  = "\n\n".join(chunks)
    response = openai_client.chat.completions.create(
        model    = "gpt-4",
        messages = [
            {"role": "system",  "content": "Answer questions using only the provided context."},
            {"role": "user",    "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    return response.choices[0].message.content

def rag(query: str) -> str:
    chunks = retrieve(query)
    return generate(query, chunks)


if __name__ == "__main__":
    query  = "What is the PDF about?"
    answer = rag(query)
    print(f"Q: {query}")
    print(f"A: {answer}")