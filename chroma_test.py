
import chromadb
from pathlib import Path

from embedding_config import embeddings


# 1. Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

COLLECTION_NAME = "incident_knowledge"


# 2. Find existing collection
existing_collections = [
    item.name if hasattr(item, "name") else str(item)
    for item in client.list_collections()
]

# 3. Remove the old collection because it contains

#    We will recreate it using Gemini (3072 dimensions).
if COLLECTION_NAME in existing_collections:
    client.delete_collection(name=COLLECTION_NAME)

collection = client.create_collection(
    name=COLLECTION_NAME
)


# 4. Find knowledge documents
knowledge_folder = Path("knowledge_base")

knowledge_files = sorted(
    knowledge_folder.glob("*.md")
)

if not knowledge_files:
    raise FileNotFoundError(
        "No Markdown documents found in knowledge_base!"
    )


# 5. Generate Gemini embeddings and store documents
for file_path in knowledge_files:

    text = file_path.read_text(encoding="utf-8")

    document_embedding = embeddings.embed_documents(
        [text]
    )[0]

    collection.upsert(
        ids=[f"{file_path.stem}_001"],
        documents=[text],
        embeddings=[document_embedding],
        metadatas=[{"topic": file_path.stem}]
    )

    print(f"Indexed successfully: {file_path.name}")


# 6. Test retrieval using a Gemini query embedding
query = (
    "The user's authentication token has expired "
    "and login is failing."
)

query_embedding = embeddings.embed_query(query)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=1
)


# 7. Display retrieved knowledge
print("\n===== RETRIEVED KNOWLEDGE =====")

if results["documents"] and results["documents"][0]:

    print(results["documents"][0][0])

    print(
        "\nDistance:",
        results["distances"][0][0]
    )

else:
    print("No matching knowledge document found.")
