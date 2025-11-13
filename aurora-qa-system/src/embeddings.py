"""
Embedding Module
Generate and store vector embeddings for semantic search using FAISS

Architecture:
- PRIMARY vector: Message content only (pure semantics)
- METADATA: user_name, timestamp, entities (for filtering/boosting)
- Query-time boosting: Use metadata to rerank results
- USER FILTERING: Use user_index.json for fast user-specific search
"""
import json
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple, Optional, Set
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import faiss


class EmbeddingIndex:
    """Vector embedding index for semantic search using FAISS"""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """
        Initialize embedding model

        Args:
            model_name: Sentence transformer model name
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.messages = []  # Store full messages with metadata
        self.model_name = model_name
        self.user_index = {}  # user_id -> message_indices mapping
        print(f"✅ Model loaded (dimension: {self.dimension})")

    def build_index(self, messages: List[Dict], batch_size: int = 64):
        """
        Build FAISS index from messages

        Strategy: Embed ONLY message content (pure semantics)
        Metadata (user_name, timestamp, entities) stored separately for filtering
        Uses BGE "passage:" prefix for optimal retrieval performance

        Args:
            messages: List of message dicts with keys: id, user_name, message, timestamp
            batch_size: Batch size for encoding
        """
        print(f"\n📊 Building embedding index for {len(messages)} messages...")
        print(f"   Model: {self.model_name}")
        print(f"   Dimension: {self.dimension}")
        print(f"   Strategy: Message-only vectors (metadata separate)")
        print(f"   BGE Prefix: 'passage:' (for retrieval optimization)")
        print(f"   Batch size: {batch_size}\n")

        self.messages = messages

        # Extract message text with BGE "passage:" prefix
        # This tells the model these are documents to be retrieved
        texts = [f"passage: {msg['message']}" for msg in messages]

        # Generate embeddings with progress bar
        print("Encoding messages...")
        embeddings = []

        for i in tqdm(range(0, len(texts), batch_size), desc="Batches"):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalization
            )
            embeddings.append(batch_embeddings)

        # Concatenate all embeddings
        embeddings = np.vstack(embeddings).astype('float32')

        print(f"\n✅ Generated {len(embeddings)} embeddings")
        print(f"   Shape: {embeddings.shape}")

        # Build FAISS index (IndexFlatL2 for exact search)
        print("\n🔨 Building FAISS index (exact search)...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)

        print(f"✅ FAISS index built ({self.index.ntotal} vectors)")
        print(f"\nℹ️  Metadata stored separately for query-time boosting:")
        print(f"   - user_name (for user-specific queries)")
        print(f"   - timestamp (for temporal filtering)")
        print(f"   - message_id (for citation)")

    def search(
        self,
        query: str,
        top_k: int = 10,
        user_filter: Optional[str] = None,
        user_id: Optional[str] = None,
        boost_user: Optional[str] = None,
        boost_factor: float = 0.8
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar messages with optional metadata filtering/boosting

        Args:
            query: Search query
            top_k: Number of results to return
            user_filter: Only return messages from this user (strict filter by name)
            user_id: Only return messages from this user (strict filter by ID - faster)
            boost_user: Boost messages from this user (soft preference)
            boost_factor: Multiplicative boost (0.8 = 20% better score)

        Returns:
            List of (message, distance) tuples (lower distance = more similar)
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Encode query with BGE "query:" prefix
        # This tells the model this is a search query (not a document)
        query_embedding = self.model.encode(
            [f"query: {query}"],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype('float32')

        # Get valid message indices if user_id filtering is requested
        valid_indices = None
        if user_id and user_id in self.user_index:
            valid_indices = set(self.user_index[user_id]['message_indices'])

        # Search with larger k if we're filtering
        search_k = top_k * 5 if (user_filter or user_id) else top_k
        distances, indices = self.index.search(query_embedding, search_k)

        # Build results with metadata
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            msg = self.messages[idx]

            # Apply user_id filter (fast - uses pre-built index)
            if valid_indices is not None and idx not in valid_indices:
                continue

            # Apply user_filter by name (legacy - slower)
            if user_filter and msg['user_name'] != user_filter:
                continue

            # Apply user boost if specified
            if boost_user and msg['user_name'] == boost_user:
                dist = dist * boost_factor  # Lower distance = better match

            results.append((msg, float(dist)))

            # Stop when we have enough results
            if len(results) >= top_k:
                break

        return results

    def save(self, base_path: str = "data/embeddings"):
        """
        Save index and metadata to files

        Args:
            base_path: Base path (will create .index and .pkl files)
        """
        print(f"\n💾 Saving embedding index...")

        # Save FAISS index
        faiss_path = f"{base_path}_faiss.index"
        faiss.write_index(self.index, faiss_path)
        print(f"   ✓ FAISS index: {faiss_path}")

        # Save messages and metadata
        metadata_path = f"{base_path}_metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'messages': self.messages,
                'dimension': self.dimension,
                'model_name': self.model_name,
                'index_size': self.index.ntotal,
                'strategy': 'message_only'
            }, f)
        print(f"   ✓ Metadata: {metadata_path}")

        print(f"✅ Saved successfully")

    def load(self, base_path: str = "data/embeddings"):
        """
        Load index and metadata from files

        Args:
            base_path: Base path (will load .index and .pkl files)
        """
        print(f"\n📂 Loading embedding index...")

        # Load FAISS index
        faiss_path = f"{base_path}_faiss.index"
        self.index = faiss.read_index(faiss_path)
        print(f"   ✓ FAISS index: {faiss_path}")

        # Load messages and metadata
        metadata_path = f"{base_path}_metadata.pkl"
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.messages = data['messages']
            self.dimension = data['dimension']
            self.model_name = data.get('model_name', 'unknown')

        # Load user index if available
        user_index_path = "data/user_indexed/user_index.json"
        if os.path.exists(user_index_path):
            with open(user_index_path, 'r') as f:
                self.user_index = json.load(f)
            print(f"   ✓ User index: {len(self.user_index)} users")

        print(f"✅ Loaded {len(self.messages)} messages")
        print(f"   FAISS vectors: {self.index.ntotal}")
        print(f"   Model: {self.model_name}")
        print(f"   Strategy: {data.get('strategy', 'unknown')}")


def main():
    """Build embedding index with message-only strategy + BGE prefixes"""
    print("="*60)
    print("EMBEDDING INDEX BUILDER")
    print("Strategy: MESSAGE-ONLY (metadata separate)")
    print("BGE Prefixes: passage: / query:")
    print("="*60)

    # Load messages
    print("\n📂 Loading messages...")
    with open('data/raw_messages.json') as f:
        messages = json.load(f)
    print(f"✅ Loaded {len(messages)} messages")

    # Build index
    embedding_index = EmbeddingIndex()
    embedding_index.build_index(messages, batch_size=64)

    # Save index
    embedding_index.save("data/embeddings")

    # Demonstration of metadata boosting
    print("\n" + "="*60)
    print("DEMONSTRATION: Metadata Boosting")
    print("="*60)

    query = "trip to Tokyo"

    print(f"\nQuery: '{query}'")
    print("\n1. Pure semantic search (no boost):")
    results = embedding_index.search(query, top_k=3)
    for i, (msg, dist) in enumerate(results, 1):
        print(f"  {i}. [{dist:.3f}] {msg['user_name']}: {msg['message'][:60]}...")

    print("\n2. With user boost (Vikram):")
    results_boosted = embedding_index.search(query, top_k=3, boost_user="Vikram Desai", boost_factor=0.7)
    for i, (msg, dist) in enumerate(results_boosted, 1):
        print(f"  {i}. [{dist:.3f}] {msg['user_name']}: {msg['message'][:60]}...")

    print("\n3. With user filter (only Vikram):")
    results_filtered = embedding_index.search(query, top_k=3, user_filter="Vikram Desai")
    for i, (msg, dist) in enumerate(results_filtered, 1):
        print(f"  {i}. [{dist:.3f}] {msg['user_name']}: {msg['message'][:60]}...")

    print("\n" + "="*60)
    print("✅ Embedding index ready!")
    print("="*60)
    print("\nKey Features:")
    print("  ✓ Pure semantic vectors (message content only)")
    print("  ✓ Metadata stored separately (user, timestamp, id)")
    print("  ✓ Query-time boosting (user preference)")
    print("  ✓ Query-time filtering (user-specific search)")
    print("\nNext step: Run comprehensive test suite")
    print("  → python tests/test_embeddings.py")


if __name__ == "__main__":
    main()
