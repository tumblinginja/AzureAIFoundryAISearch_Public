from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceType,
    SearchIndexer,
    SearchIndexerSkillset,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    IndexingParameters,
    IndexingParametersConfiguration,
    BlobIndexerParsingMode,
    FieldMapping
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os

load_dotenv()

SEARCH_ENDPOINT   = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY        = os.getenv("AZURE_SEARCH_KEY")
BLOB_CONN_STRING  = os.getenv("AZURE_BLOB_CONNECTION_STRING")
OPENAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY        = os.getenv("AZURE_OPENAI_KEY")
CONTAINER_NAME    = "documents"
INDEX_NAME        = "index"
DATASOURCE_NAME   = "blob-datasource"
SKILLSET_NAME     = "skillset"
INDEXER_NAME      = "indexer"

client = SearchIndexerClient(
    endpoint   = SEARCH_ENDPOINT,
    credential = AzureKeyCredential(SEARCH_KEY)
)

# ── 1. DATA SOURCE ──────────────────────────────────────────────────────────
# Tells the indexer where to pull from (replaces your list_blobs loop)
data_source = SearchIndexerDataSourceConnection(
    name             = DATASOURCE_NAME,
    type             = SearchIndexerDataSourceType.AZURE_BLOB,
    connection_string= BLOB_CONN_STRING,
    container        = SearchIndexerDataContainer(name=CONTAINER_NAME)
)
client.create_or_update_data_source_connection(data_source)
print(f"Data source '{DATASOURCE_NAME}' created")

# ── 2. SKILLSET ─────────────────────────────────────────────────────────────
# Replaces your extract_text() + chunk_text() + get_embedding() functions

# Skill 1: split document text into overlapping chunks
split_skill = SplitSkill(
    name               = "split-skill",
    description        = "Chunk document text",
    text_split_mode    = "pages",           # splits on ~500 token pages
    maximum_page_length= 500,
    page_overlap_length= 50,
    context            = "/document",
    inputs             = [InputFieldMappingEntry(name="text", source="/document/content")],
    outputs            = [OutputFieldMappingEntry(name="textItems", target_name="pages")]
)

# Skill 2: embed each chunk via Azure OpenAI ada-002
embedding_skill = AzureOpenAIEmbeddingSkill(
    name              = "embedding-skill",
    description       = "Generate embeddings per chunk",
    resource_uri      = OPENAI_ENDPOINT,
    api_key           = OPENAI_KEY,
    deployment_id     = "text-embedding-ada-002",
    model_name        = "text-embedding-ada-002",
    dimensions        = 1536,
    context           = "/document/pages/*",    # runs once per chunk
    inputs            = [InputFieldMappingEntry(name="text", source="/document/pages/*")],
    outputs           = [OutputFieldMappingEntry(name="embedding", target_name="embedding")]
)

skillset = SearchIndexerSkillset(
    name        = SKILLSET_NAME,
    description = "Document enrichment pipeline",
    skills      = [split_skill, embedding_skill]
)
client.create_or_update_skillset(skillset)
print(f"Skillset '{SKILLSET_NAME}' created")

# ── 3. INDEXER ──────────────────────────────────────────────────────────────
# Wires data source → skillset → index, with scheduling + PDF cracking built in
indexer = SearchIndexer(
    name               = INDEXER_NAME,
    description        = "blob indexer",
    data_source_name   = DATASOURCE_NAME,
    skillset_name      = SKILLSET_NAME,
    target_index_name  = INDEX_NAME,
    parameters         = IndexingParameters(
        configuration  = IndexingParametersConfiguration(
            parsing_mode               = BlobIndexerParsingMode.DEFAULT,  # handles PDF cracking
            data_to_extract            = "contentAndMetadata"
        )
    ),
    # Map enriched skill outputs → index fields
    output_field_mappings = [
        FieldMapping(source_field_name="/document/pages/*/embedding", target_field_name="embedding"),
        FieldMapping(source_field_name="/document/pages/*",           target_field_name="chunk_text"),
    ],
    field_mappings = [
        FieldMapping(source_field_name="metadata_storage_name", target_field_name="source")
    ]
)
client.create_or_update_indexer(indexer)
print(f"Indexer '{INDEXER_NAME}' created")

# ── 4. RUN ──────────────────────────────────────────────────────────────────
client.run_indexer(INDEXER_NAME)
print(f"Indexer '{INDEXER_NAME}' triggered — check portal for status")