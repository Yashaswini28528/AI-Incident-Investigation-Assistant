
from embedding_config import embeddings
import math

# Two sentences to compare
sentence1 = "Database connection timeout"

sentence2 = "The application cannot connect to the database"

# Generate Gemini embeddings for both sentences
vectors = embeddings.embed_documents(
    [sentence1, sentence2]
)

# Extract both vectors
embedding1 = vectors[0]
embedding2 = vectors[1]

# Display dimensions
print("Sentence 1 dimensions:", len(embedding1))
print("Sentence 2 dimensions:", len(embedding2))

# Compare the vectors using cosine similarity
dot_product = sum(
    a * b for a, b in zip(embedding1, embedding2)
)

magnitude1 = math.sqrt(sum(a * a for a in embedding1))
magnitude2 = math.sqrt(sum(b * b for b in embedding2))

similarity = dot_product / (magnitude1 * magnitude2)

print("\nCosine Similarity:", similarity)
