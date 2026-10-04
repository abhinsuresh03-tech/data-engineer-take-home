import faiss
import numpy as np
import pickle

from sentence_transformers import SentenceTransformer
from db import get_connection


MODEL_NAME = "all-MiniLM-L6-v2"

INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "faiss_metadata.pkl"


def get_enrichment_data():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT ON (variant_code)
                    variant_code,
                    enrichment_description
                FROM variant_enrichment
                WHERE status = 'success'
                  AND enrichment_description IS NOT NULL
                ORDER BY variant_code, created_at DESC;
            """)

            return cursor.fetchall()

    finally:
        conn.close()


def build_faiss_index():

    rows = get_enrichment_data()

    print(f"Found {len(rows)} descriptions")

    variant_codes = [row[0] for row in rows]
    descriptions = [row[1] for row in rows]

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")

    embeddings = model.encode(
        descriptions,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    # Normalize so inner product behaves like cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    print(f"Embedding dimension: {dimension}")

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print(f"Vectors stored in FAISS: {index.ntotal}")

    faiss.write_index(index, INDEX_FILE)

    metadata = {
        "variant_codes": variant_codes,
        "descriptions": descriptions
    }

    with open(METADATA_FILE, "wb") as file:
        pickle.dump(metadata, file)

    print(f"Saved index to {INDEX_FILE}")
    print(f"Saved metadata to {METADATA_FILE}")

def search_similar(query, top_k=5):

    print(f"\nSearching for: {query}")

    # Load embedding model
    model = SentenceTransformer(MODEL_NAME)

    # Convert query into an embedding
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    # Normalize for cosine similarity
    faiss.normalize_L2(query_embedding)

    # Load FAISS index
    index = faiss.read_index(INDEX_FILE)

    # Load metadata
    with open(METADATA_FILE, "rb") as file:
        metadata = pickle.load(file)

    # Search
    scores, indices = index.search(
        query_embedding,
        top_k
    )

    print("\nTop matches:")

    for score, idx in zip(scores[0], indices[0]):

        variant_code = metadata["variant_codes"][idx]
        description = metadata["descriptions"][idx]

        print(
            f"\nVariant: {variant_code}"
            f"\nScore: {score:.4f}"
            f"\nDescription: {description}"
        )

if __name__ == "__main__":
    
    search_similar(
        "lightweight breathable clothing",
        top_k=5
    )