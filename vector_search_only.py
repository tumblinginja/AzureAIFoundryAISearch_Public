import os
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
     SearchField,
     SearchFieldDataType,
     VectorSearch,
     HnswAlgorithmConfiguration,
     VectorSearchProfile,
     AzureOpenAIVectorizer,
     AzureOpenAIVectorizerParameters,
     SearchIndex,
     SearchIndexerDataContainer,
     SearchIndexerDataSourceConnection,
     MergeSkill,
     InputFieldMappingEntry,
     OutputFieldMappingEntry,
     AzureOpenAIEmbeddingSkill,
     SearchIndexerSkillset,
     CognitiveServicesAccountKey,
     SearchIndexer,
     IndexingParameters,
     FieldMapping
 )



from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

AZURE_SEARCH_SERVICE=os.getenv("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_KEY=os.getenv("AZURE_SEARCH_KEY")
AI_FOUNDRY_AI_SERVICES_URL=os.getenv("AI_FOUNDRY_AI_SERVICES_URL")
AI_FOUNDRY_KEY=os.getenv("AI_FOUNDRY_KEY")
AZURE_STORAGE_CONNECTION=os.getenv("AZURE_STORAGE_CONNECTION")

# AZURE_AI_MULTISERVICE_KEY=os.getenv("AZURE_AI_MULTISERVICE_KEY")
FOUNDRY_EMBEDDING_DEPLOYMENT_NAME=os.getenv("FOUNDRY_EMBEDDING_DEPLOYMENT_NAME")
FOUNDRY_EMBEDDING_MODEL_NAME=os.getenv("FOUNDRY_EMBEDDING_MODEL_NAME")

cognitive_services_account = CognitiveServicesAccountKey(key=AI_FOUNDRY_KEY)
# cognitive_services_account = CognitiveServicesAccountKey(key=AZURE_AI_MULTISERVICE_KEY)

# Create a credential object with the admin key
from azure.core.credentials import AzureKeyCredential
credential = AzureKeyCredential(AZURE_SEARCH_KEY)

prefix = "frankies-bakery-demo-with-vectors"
index_name = f"{prefix}-idx"
data_source_name = f"{prefix}-ds"
skillset_name = f"{prefix}-ss"
indexer_name = f"{prefix}-idxr"

embedding_model_deployment_name = FOUNDRY_EMBEDDING_DEPLOYMENT_NAME
embedding_model_name = FOUNDRY_EMBEDDING_MODEL_NAME
HnswAlgorithmConfiguration_name = "myHnsw"
my_vector_search_profile_name = "myHnswProfile"
my_vectorizer_name = "myOpenAI"


index_description = "Index"
search_indexer_skillset_description = "This is the skill set to vectorize data"
indexer_description="Indexer"

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
    SearchField(name="merged_text", type=SearchFieldDataType.String, searchable=True, analyzer_name="standard.lucene"),
    SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1024, vector_search_profile_name=my_vector_search_profile_name)
]



 # Configure the vector search configuration  
vector_search = VectorSearch(  
     profiles=[  
         VectorSearchProfile(  
             name=my_vector_search_profile_name,  
             algorithm_configuration_name=HnswAlgorithmConfiguration_name,  
             vectorizer_name=my_vectorizer_name,  
         )
     ],
      algorithms=[  
         HnswAlgorithmConfiguration(name=HnswAlgorithmConfiguration_name),
     ],
     vectorizers=[  
         AzureOpenAIVectorizer(  
             vectorizer_name=my_vectorizer_name,  
             kind="azureOpenAI",  
             parameters=AzureOpenAIVectorizerParameters(  
                 resource_url=AI_FOUNDRY_AI_SERVICES_URL,  
                 deployment_name=embedding_model_deployment_name,
                 model_name=embedding_model_name
             ),
         ),  
     ], 
 )  

 # Create the search index
# index = SearchIndex(name=index_name, fields=fields, description=index_description)  
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, description=index_description)  
result = index_client.create_or_update_index(index)  
print(f"{result.name} created or updated")


##################### CREATE DATA SOURCE ########################################################################

# Create a data source 
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)
container = SearchIndexerDataContainer(name="Indexer")
data_source_connection = SearchIndexerDataSourceConnection(
    name=data_source_name,
    type="azureblob",
    connection_string=AZURE_STORAGE_CONNECTION,
    container=container
)
data_source = indexer_client.create_or_update_data_source_connection(data_source_connection)

print(f"Data source '{data_source.name}' created or updated")


##################### CREATE SKILLSET ########################################################################

# Create a skillset  

#SKILL 1 Merge Skill
merge_skill = MergeSkill(
    name="mergeText",
    description="Merge things for embedding",
    context="/document",
    inputs=[
        InputFieldMappingEntry(name="text", source="/document/description"),
        InputFieldMappingEntry(name="itemsToInsert", source="/document/tags"),
    ],
    outputs=[
        OutputFieldMappingEntry(name="mergedText", target_name="combined_text")
    ],
)

#SKILL 2 Embedding Skill
embedding_skill = AzureOpenAIEmbeddingSkill(  
    description="Skill to generate embeddings via Azure OpenAI",  
    context="/document",  
    resource_url=AI_FOUNDRY_AI_SERVICES_URL,  
    deployment_name=embedding_model_deployment_name,  
    model_name=embedding_model_name,
    dimensions=1024,
    inputs=[  
        InputFieldMappingEntry(name="text", source="/document/combined_text"),  
    ],  
    outputs=[  
        OutputFieldMappingEntry(name="embedding", target_name="embedding")  
    ],  
)


skills = [merge_skill, embedding_skill]


skillset = SearchIndexerSkillset(  
    name=skillset_name,  
    description=search_indexer_skillset_description,  
    skills=skills,
    cognitive_services_account=cognitive_services_account
)


  
client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
client.create_or_update_skillset(skillset)  
print(f"{skillset.name} created")  




##################### CREATE SEARCH INDEXER ########################################################################

# Create an indexer  
indexer_parameters = IndexingParameters(configuration={"parsingMode": "json", "dataToExtract": "contentAndMetadata"})

# Output field mapping: skill output embedding -> index content_vector
output_field_mappings = [
    FieldMapping( source_field_name="/document/embedding", target_field_name="content_vector"),
    FieldMapping( source_field_name="/document/combined_text", target_field_name="merged_text")
]

  
indexer = SearchIndexer(  
    name=indexer_name,  
    description=indexer_description,  
    skillset_name=skillset_name,  
    target_index_name=index_name,  
    data_source_name=data_source_name,
    output_field_mappings=output_field_mappings,
    parameters=indexer_parameters
)  

# Create and run the indexer  
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
indexer_result = indexer_client.create_or_update_indexer(indexer)  

print(f'{indexer_name} is created and running. Give the indexer a few minutes before running a query.')  