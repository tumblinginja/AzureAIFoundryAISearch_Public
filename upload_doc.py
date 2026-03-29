from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")
CONTAINER_NAME         = "documents"
LOCAL_DOCS_PATH        = "data/raw/pdfs/"

blob_service  = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container     = blob_service.get_container_client(CONTAINER_NAME)

# Create container if it doesn't exist
if not container.exists():
    container.create_container()

# Upload all files in local folder
for filename in os.listdir(LOCAL_DOCS_PATH):
    filepath   = os.path.join(LOCAL_DOCS_PATH, filename)
    blob_client = container.get_blob_client(filename)

    with open(filepath, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    print(f"Uploaded: {filename}")