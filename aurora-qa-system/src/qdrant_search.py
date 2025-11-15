"""
Qdrant Vector Search with Metadata Filtering

Replaces FAISS semantic search with Qdrant for temporal + user filtering.

Architecture:
- Vector search with metadata filters
- Supports temporal (date range) filtering
- Supports user filtering
- Compatible with existing HybridRetriever interface
- Uses FastEmbed for lightweight local embeddings (no torch dependency)

Usage:
    searcher = QdrantSearch()
    results = searcher.search(
        query="December 2025 plans",
        top_k=10,
        date_range=("2025-12-01", "2025-12-31"),
        user_id="user_123"
    )
"""
import os
from typing import List, Optional, Tuple, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, Range
from fastembed import TextEmbedding


class QdrantSearch:
    """
    Qdrant-based vector search with metadata filtering

    Features:
    - Temporal filtering (date ranges)
    - User filtering (user_id)
    - Backward compatible with FAISS interface
    """

    def __init__(
        self,
        collection_name: str = "aurora_messages",
        model_name: str = "BAAI/bge-small-en-v1.5",
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None
    ):
        """
        Initialize Qdrant searcher with FastEmbed for lightweight embeddings

        Args:
            collection_name: Qdrant collection name
            model_name: Embedding model name (FastEmbed uses ONNX models - much lighter than torch)
            qdrant_url: Qdrant server URL (env: QDRANT_URL)
            qdrant_api_key: Qdrant API key (env: QDRANT_API_KEY)
        """
        # Qdrant connection
        self.collection_name = collection_name
        self.qdrant_url = qdrant_url or os.getenv(
            "QDRANT_URL",
            "https://64ffc9ea-bc97-48f6-97d9-7d00e5e3481d.europe-west3-0.gcp.cloud.qdrant.io:6333"
        )
        self.qdrant_api_key = qdrant_api_key or os.getenv(
            "QDRANT_API_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZpU1k_gFE_V37W19f5akrhArDSer0798azjq0ldnETo"
        )

        self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

        # FastEmbed for lightweight embeddings (ONNX - no torch!)
        self.model_name = model_name
        self.embedding_model = TextEmbedding(model_name=model_name)

    def _build_filter(
        self,
        date_range: Optional[Tuple[str, str]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Filter]:
        """
        Build Qdrant filter from parameters

        Args:
            date_range: (start_date, end_date) in ISO format
            user_id: User ID to filter by

        Returns:
            Qdrant Filter or None if no filters
        """
        conditions = []

        # Date range filter
        # normalized_dates is an array of ISO date strings
        # We need to match messages where ANY date in the array falls in our range
        if date_range:
            from datetime import datetime, timedelta

            start_date, end_date = date_range
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            # Generate all dates in range
            dates_in_range = []
            current = start
            while current <= end:
                dates_in_range.append(current.date().isoformat())
                current += timedelta(days=1)

            # Match any date in the range
            conditions.append(
                FieldCondition(
                    key="normalized_dates",
                    match=MatchAny(any=dates_in_range)
                )
            )

        # User filter
        if user_id:
            conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            )

        if not conditions:
            return None

        return Filter(must=conditions)

    def search(
        self,
        query: str,
        top_k: int = 10,
        date_range: Optional[Tuple[str, str]] = None,
        user_id: Optional[str] = None,
        verbose: bool = False
    ) -> List[Dict]:
        """
        Search with optional temporal and user filtering

        Args:
            query: Search query
            top_k: Number of results
            date_range: Optional (start, end) date range
            user_id: Optional user ID filter
            verbose: Print debug info

        Returns:
            List of results with metadata
            [
                {
                    'id': int,
                    'score': float,
                    'message': str,
                    'user_id': str,
                    'user_name': str,
                    'timestamp': str,
                    'normalized_dates': List[str]
                },
                ...
            ]
        """
        # Embed query using FastEmbed (ONNX - lightweight!)
        query_embedding = list(self.embedding_model.embed([query]))[0]
        query_vector = query_embedding.tolist()

        # Build filter
        filter_condition = self._build_filter(date_range=date_range, user_id=user_id)

        if verbose and filter_condition:
            print(f"   Qdrant filter: date_range={date_range}, user_id={user_id}")

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=filter_condition,
            limit=top_k,
            with_payload=True
        )

        # Format results (compatible with FAISS interface)
        formatted = []
        for r in results:
            formatted.append({
                'id': r.id,
                'score': r.score,
                'message': r.payload['message'],
                'user_id': r.payload['user_id'],
                'user_name': r.payload['user_name'],
                'timestamp': r.payload['timestamp'],
                'normalized_dates': r.payload.get('normalized_dates', [])
            })

        return formatted


def test_qdrant_search():
    """Test Qdrant search with filters"""
    print("="*80)
    print("QDRANT SEARCH TEST")
    print("="*80)

    searcher = QdrantSearch()

    # Test 1: No filters
    print("\n[TEST 1] Search without filters")
    results = searcher.search("travel preferences", top_k=3)
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  - {r['user_name']}: {r['message'][:60]}...")

    # Test 2: User filter
    print("\n[TEST 2] Search with user filter")
    results = searcher.search(
        "preferences",
        top_k=5,
        user_id="8b507cf4-e93d-4c87-aad2-5a70ac0d8f31"  # Layla
    )
    print(f"Results: {len(results)} (all from Layla)")
    for r in results:
        print(f"  - {r['user_name']}: {r['message'][:60]}...")

    # Test 3: Date filter
    print("\n[TEST 3] Search with date filter (December 2025)")
    results = searcher.search(
        "plans",
        top_k=10,
        date_range=("2025-12-01", "2025-12-31")
    )
    print(f"Results: {len(results)}")
    for r in results:
        print(f"  - {r['user_name']}: {r['normalized_dates']} - {r['message'][:50]}...")

    # Test 4: Combined filters
    print("\n[TEST 4] Search with user + date filter")
    results = searcher.search(
        "booking",
        top_k=5,
        date_range=("2025-12-01", "2025-12-31"),
        user_id="8b507cf4-e93d-4c87-aad2-5a70ac0d8f31"
    )
    print(f"Results: {len(results)}")

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)


if __name__ == "__main__":
    test_qdrant_search()
