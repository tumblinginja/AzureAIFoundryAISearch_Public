#list packages to install: azure-search-documents, azure-identity, python-dotenv

import os
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
     SearchField,
     SearchFieldDataType,
     SearchIndex,
     SearchIndexerDataContainer,
     SearchIndexerDataSourceConnection,
     SearchIndexer,
     IndexingParameters
 )

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AZURE_SEARCH_SERVICE=os.getenv("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_KEY=os.getenv("AZURE_SEARCH_KEY")
AZURE_OPENAI_ACCOUNT=os.getenv("AZURE_OPENAI_ACCOUNT")
AZURE_STORAGE_CONNECTION=os.getenv("AZURE_STORAGE_CONNECTION")

# Create a credential object with the admin key
from azure.core.credentials import AzureKeyCredential
credential = AzureKeyCredential(AZURE_SEARCH_KEY)

prefix = "frankies-bakery-full-text-code-demo"
index_name = f"{prefix}-idx"
data_source_name = f"{prefix}-ds"
indexer_name = f"{prefix}-idxr"


index_description = "Index for Frankie's Bakery Product catalog."
indexer_description="Indexer for Frankie's Bakery Product Catalog"

##################### CREATE SEARCH INDEX ########################################################################

 # Create a search index  
index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  

fields = [
    SearchField(name="product_id", type=SearchFieldDataType.String, key=True, filterable=True, sortable=True),
    SearchField(name="name", type=SearchFieldDataType.String, searchable=True, sortable=True, filterable=True, analyzer_name="standard.lucene"),
    SearchField(name="description", type=SearchFieldDataType.String, facetable=False, sortable=False, filterable=False, searchable=True, analyzer_name="standard.lucene"),
    SearchField(name="category", type=SearchFieldDataType.String, searchable=True, filterable=True, sortable=True, facetable=True, analyzer_name="standard.lucene"),
    SearchField(name="price", type=SearchFieldDataType.Double, filterable=True, sortable=True, facetable=True),
    SearchField(name="availability", type=SearchFieldDataType.String, searchable=True, filterable=True, sortable=True, facetable=True, analyzer_name="standard.lucene"),
    SearchField(name="ingredients", type=SearchFieldDataType.String, facetable=False, filterable=False, sortable=False, searchable=True, analyzer_name="standard.lucene"),
    SearchField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True, facetable=True),
    SearchField(name="release_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
    SearchField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
    SearchField(name="image_url", type=SearchFieldDataType.String),
]

 # Create the search index
index = SearchIndex(name=index_name, fields=fields, description=index_description)  
# index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, description=index_description)  
result = index_client.create_or_update_index(index)  
print(f"{result.name} created or updated")


##################### CREATE DATA SOURCE ########################################################################

# Create a data source 
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)
container = SearchIndexerDataContainer(name="ContainName")
data_source_connection = SearchIndexerDataSourceConnection(
    name=data_source_name,
    type="azureblob",
    connection_string=AZURE_STORAGE_CONNECTION,
    container=container
)
data_source = indexer_client.create_or_update_data_source_connection(data_source_connection)

print(f"Data source '{data_source.name}' created or updated")



##################### CREATE SEARCH INDEXER ########################################################################

# Create an indexer  
indexer_parameters = IndexingParameters(configuration={"parsingMode": "json", "dataToExtract": "contentAndMetadata"})

indexer = SearchIndexer(  
    name=indexer_name,  
    description=indexer_description,  
    target_index_name=index_name,  
    data_source_name=data_source_name,
    parameters=indexer_parameters
)  


# Create and run the indexer  
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
indexer_result = indexer_client.create_or_update_indexer(indexer)  

print(f'{indexer_name} is created and running. Give the indexer a few minutes before running a query.')  