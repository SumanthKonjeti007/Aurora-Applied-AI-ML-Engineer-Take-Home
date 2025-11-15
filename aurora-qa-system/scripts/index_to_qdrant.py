"""
Index Messages to Qdrant Cloud

Indexes all messages with temporal metadata to Qdrant.

Features:
- Uses existing embeddings from FAISS
- Adds temporal metadata (normalized_dates)
- Adds user metadata (user_id, user_name)
- Supports filtering by date and user

Usage:
    python scripts/index_to_qdrant.py
"""
import json
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Qdrant Cloud credentials
QDRANT_URL = "https://64ffc9ea-bc97-48f6-97d9-7d00e5e3481d.europe-west3-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZpU1k_gFE_V37W19f5akrhArDSer0798azjq0ldnETo"
COLLECTION_NAME = "aurora_messages"


def create_collection(client: QdrantClient):
    """Create Qdrant collection with vector config"""
    print(f"\n🏗️  Creating collection '{COLLECTION_NAME}'...")

    # Delete if exists (fresh start)
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"   Deleted existing collection")
    except Exception:
        pass

    # Create new collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,  # bge-small-en-v1.5 dimension
            distance=Distance.COSINE  # Same as FAISS
        )
    )
    print(f"   ✅ Collection created!")


def load_embeddings():
    """Load existing embeddings from FAISS index"""
    print(f"\n📂 Loading embeddings...")
    import faiss

    # Load FAISS index
    index = faiss.read_index("data/embeddings_faiss.index")

    # Extract vectors
    vectors = np.zeros((index.ntotal, 384), dtype=np.float32)
    for i in range(index.ntotal):
        vectors[i] = index.reconstruct(i)

    print(f"   ✅ Loaded {len(vectors)} vectors (dim={vectors.shape[1]})")
    return vectors


def index_messages(client: QdrantClient, messages, embeddings):
    """
    Index messages to Qdrant with metadata

    Payload structure:
    {
        "message": "...",
        "user_id": "uuid",
        "user_name": "Name",
        "timestamp": "ISO",
        "normalized_dates": ["2025-12-03", ...]  # NEW: For temporal filtering
    }
    """
    print(f"\n📥 Indexing {len(messages)} messages to Qdrant...")

    # Prepare points (batched)
    points = []
    for i, msg in enumerate(messages):
        point = PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={
                "message": msg['message'],
                "user_id": msg['user_id'],
                "user_name": msg['user_name'],
                "timestamp": msg['timestamp'],
                "normalized_dates": msg.get('normalized_dates', [])  # Temporal metadata
            }
        )
        points.append(point)

    # Upload in batches (smaller for stability)
    batch_size = 50
    import time

    for i in tqdm(range(0, len(points), batch_size), desc="Uploading"):
        batch = points[i:i + batch_size]

        # Retry logic
        retries = 3
        for attempt in range(retries):
            try:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch,
                    wait=True
                )
                break  # Success
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    print(f"\n⚠️  Failed batch {i//batch_size}: {e}")
                    raise

    print(f"   ✅ Indexed {len(messages)} messages!")


def verify_index(client: QdrantClient):
    """Verify indexing and show stats"""
    print(f"\n📊 Verifying index...")

    # Get collection info
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    print(f"   Total vectors: {collection_info.points_count}")
    print(f"   Vector dimension: {collection_info.config.params.vectors.size}")
    print(f"   Distance metric: {collection_info.config.params.vectors.distance}")

    # Test search
    print(f"\n🔍 Testing search...")
    test_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=[0.0] * 384,  # Dummy vector
        limit=3
    )
    print(f"   ✅ Search works! Retrieved {len(test_results)} results")

    # Show sample with dates
    print(f"\n📋 Sample messages with dates:")
    scroll_results = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True,
        with_vectors=False
    )

    samples = [
        r for r in scroll_results[0]
        if r.payload.get('normalized_dates')
    ][:3]

    for sample in samples:
        print(f"\n   Message: {sample.payload['message'][:60]}...")
        print(f"   User: {sample.payload['user_name']}")
        print(f"   Dates: {sample.payload['normalized_dates']}")


def main():
    print("="*80)
    print("QDRANT INDEXING - Aurora QA System")
    print("="*80)

    # Connect to Qdrant Cloud
    print(f"\n🌐 Connecting to Qdrant Cloud...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"   ✅ Connected!")

    # Create collection
    create_collection(client)

    # Load data
    print(f"\n📂 Loading messages...")
    with open("data/messages_with_dates.json", 'r') as f:
        messages = json.load(f)
    print(f"   ✅ Loaded {len(messages)} messages")

    # Load embeddings
    embeddings = load_embeddings()

    # Index
    index_messages(client, messages, embeddings)

    # Verify
    verify_index(client)

    print(f"\n{'='*80}")
    print(f"✅ INDEXING COMPLETE!")
    print(f"{'='*80}")
    print(f"\nQdrant collection '{COLLECTION_NAME}' is ready!")
    print(f"- {len(messages)} messages indexed")
    print(f"- Temporal filtering enabled")
    print(f"- User filtering enabled")


if __name__ == "__main__":
    main()
