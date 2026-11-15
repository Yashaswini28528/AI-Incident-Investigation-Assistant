
import ollama
import chromadb
from pathlib import Path

# 1. Connect to the local ChromaDB database
client = chromadb.PersistentClient(
    path="./chroma_db"
)

# 2. Access our existing collection
collection = client.get_or_create_collection(
    name="incident_knowledge"
)


# 3. Read all Markdown knowledge documents
knowledge_folder = Path("knowledge_base")

knowledge_files = list(knowledge_folder.glob("*.md"))

if not knowledge_files:
    raise FileNotFoundError("No Markdown documents found!")

# 4. Generate embeddings and store documents
for file_path in knowledge_files:

    # Read the document content
    text = file_path.read_text(encoding="utf-8")

    # Generate its embedding
    response = ollama.embed(
        model="nomic-embed-text",
        input=text
    )

    embedding = response["embeddings"][0]

    # Store or update the document in ChromaDB
    collection.upsert(
        ids=[f"{file_path.stem}_001"],
        documents=[text],
        embeddings=[embedding],
        metadatas=[{"topic": file_path.stem}]
    )

    print(f"Indexed successfully: {file_path.name}")


# 6. Create a search query
query = "The user's authentication token has expired and login is failing."
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
