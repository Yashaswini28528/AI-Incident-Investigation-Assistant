
import ollama
import chromadb

# 1. Connect to the local ChromaDB database
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 2. Access our existing collection
collection = client.get_or_create_collection(
    name="incident_knowledge"
)

# 3. Prepare our knowledge document
text = """
A database connection timeout occurs when an application
cannot establish a connection to the database within
the configured time limit.
"""

# 4. Generate the document embedding
response = ollama.embed(
    model="nomic-embed-text",
    input=text
)

embedding = response["embeddings"][0]

# 5. Store the document
collection.upsert(
    ids=["database_timeout_001"],
    documents=[text],
    embeddings=[embedding],
    metadatas=[{"topic": "database_timeout"}]
)

print("Document stored successfully!")

# 6. Create a search query
query = "The application is unable to connect to its database."

# 7. Convert the query into an embedding
query_response = ollama.embed(
    model="nomic-embed-text",
    input=query
)

query_embedding = query_response["embeddings"][0]

# 8. Search ChromaDB for similar documents
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=1
)

# 9. Display the retrieved document
print("\n===== RETRIEVED KNOWLEDGE =====")

print(results["documents"][0][0])

print("\nDistance:", results["distances"][0][0])
