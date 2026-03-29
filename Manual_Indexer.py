from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import uuid
import PyPDF2
import io

load_dotenv()

BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")
SEARCH_ENDPOINT        = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY             = os.getenv("AZURE_SEARCH_KEY")
OPENAI_ENDPOINT        = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY             = os.getenv("AZURE_OPENAI_KEY")
CONTAINER_NAME         = "documents"
INDEX_NAME             = "index"
CHUNK_SIZE             = 500     # characters per chunk
CHUNK_OVERLAP          = 50      # overlap between chunks

# Clients
blob_service  = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
openai_client = AzureOpenAI(azure_endpoint=OPENAI_ENDPOINT, api_key=OPENAI_KEY, api_version="2024-02-01")

def extract_text(blob_content: bytes, filename: str) -> str:
    """Extract raw text from PDF or txt file."""
    if filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(blob_content))
        return " ".join(page.extract_text() for page in reader.pages)
    return blob_content.decode("utf-8")

def chunk_text(text: str) -> list:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def get_embedding(text: str) -> list:
    """Call Azure OpenAI to embed a chunk."""
    response = openai_client.embeddings.create(
        input = text,
        model = "text-embedding-ada-002"
    )
    return response.data[0].embedding

# Process each blob
container = blob_service.get_container_client(CONTAINER_NAME)
documents = []

for blob in container.list_blobs():
    print(f"Processing: {blob.name}")
    content   = container.get_blob_client(blob.name).download_blob().readall()
    text      = extract_text(content, blob.name)
    chunks    = chunk_text(text)

    for chunk in chunks:
        embedding = get_embedding(chunk)
        documents.append({
            "id"         : str(uuid.uuid4()),
            "chunk_text" : chunk,
            "source"     : blob.name,
            "embedding"  : embedding
        })

# Upload all documents to index in one batch
search_client.upload_documents(documents)
print(f"Indexed {len(documents)} chunks")