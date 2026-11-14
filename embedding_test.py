
import ollama

# Two sentences to compare
sentence1 = "Database connection timeout"

sentence2 = "The application cannot connect to the database"

# Generate embeddings for both sentences
response = ollama.embed(
    model="nomic-embed-text",
    input=[sentence1, sentence2]
)

# Extract both vectors
embedding1 = response["embeddings"][0]
embedding2 = response["embeddings"][1]

# Display dimensions
print("Sentence 1 dimensions:", len(embedding1))
print("Sentence 2 dimensions:", len(embedding2))

# Compare the vectors using cosine similarity
import math

dot_product = sum(
    a * b for a, b in zip(embedding1, embedding2)
)

magnitude1 = math.sqrt(sum(a * a for a in embedding1))
magnitude2 = math.sqrt(sum(b * b for b in embedding2))

similarity = dot_product / (magnitude1 * magnitude2)

print("\nCosine Similarity:", similarity)
