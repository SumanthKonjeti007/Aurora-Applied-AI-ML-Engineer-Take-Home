"""
BM25 Keyword Search Module
Exact keyword matching to complement semantic search

Architecture:
- Tokenize messages into terms
- Build BM25 index for TF-IDF based ranking
- Support user-specific filtering
- Include user_name in searchable text for user queries
- USER FILTERING: Use user_index.json for fast user-specific search
"""
import json
import pickle
import os
from typing import List, Dict, Tuple, Optional, Set
from rank_bm25 import BM25Okapi
import re


class BM25Search:
    """BM25 keyword search for exact term matching"""

    def __init__(self):
        """Initialize BM25 search"""
        self.bm25 = None
        self.messages = []
        self.tokenized_corpus = []
        self.user_index = {}  # user_id -> message_indices mapping

    def tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization: lowercase + split on non-alphanumeric

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def build_index(self, messages: List[Dict]):
        """
        Build BM25 index from messages

        Strategy: Index message + user_name together
        This allows queries like "Vikram cars" to match Vikram's messages

        Args:
            messages: List of message dicts with keys: id, user_name, message, timestamp
        """
        print(f"\n📊 Building BM25 index for {len(messages)} messages...")

        self.messages = messages

        # Tokenize messages (include user_name for user-specific queries)
        self.tokenized_corpus = []
        for msg in messages:
            # Combine user_name + message for indexing
            # This allows "Vikram BMW" to match messages from Vikram about BMW
            combined_text = f"{msg['user_name']} {msg['message']}"
            tokens = self.tokenize(combined_text)
            self.tokenized_corpus.append(tokens)

        # Build BM25 index
        print("   Building BM25Okapi index...")
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        print(f"✅ BM25 index built")
        print(f"   Corpus size: {len(self.tokenized_corpus)} documents")
        print(f"   Strategy: user_name + message (for user-specific queries)")

    def search(
        self,
        query: str,
        top_k: int = 10,
        user_filter: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Search for messages using BM25 keyword matching

        Args:
            query: Search query
            top_k: Number of results to return
            user_filter: Only return messages from this user (strict filter by name)
            user_id: Only return messages from this user (strict filter by ID - faster)

        Returns:
            List of (message, score) tuples (higher score = better match)
        """
        if self.bm25 is None:
            raise ValueError("Index not built. Call build_index() first.")

        # Tokenize query
        query_tokens = self.tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get valid message indices if user_id filtering is requested
        valid_indices = None
        if user_id and user_id in self.user_index:
            valid_indices = set(self.user_index[user_id]['message_indices'])

        # Get top-k indices (sorted by score descending)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        # Build results
        results = []
        for idx in top_indices:
            msg = self.messages[idx]
            score = scores[idx]

            # Apply user_id filter (fast - uses pre-built index)
            if valid_indices is not None and idx not in valid_indices:
                continue

            # Apply user_filter by name (legacy - slower)
            if user_filter and msg['user_name'] != user_filter:
                continue

            # Only return non-zero scores
            if score > 0:
                results.append((msg, float(score)))

            # Stop when we have enough results
            if len(results) >= top_k:
                break

        return results

    def save(self, base_path: str = "data/bm25"):
        """
        Save BM25 index and metadata to files

        Args:
            base_path: Base path (will create .pkl files)
        """
        print(f"\n💾 Saving BM25 index...")

        # Save everything in one pickle file
        data = {
            'bm25': self.bm25,
            'messages': self.messages,
            'tokenized_corpus': self.tokenized_corpus,
        }

        path = f"{base_path}.pkl"
        with open(path, 'wb') as f:
            pickle.dump(data, f)

        print(f"   ✓ Saved: {path}")
        print(f"✅ BM25 index saved successfully")

    def load(self, base_path: str = "data/bm25"):
        """
        Load BM25 index and metadata from files

        Args:
            base_path: Base path (will load .pkl file)
        """
        print(f"\n📂 Loading BM25 index...")

        path = f"{base_path}.pkl"
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.bm25 = data['bm25']
        self.messages = data['messages']
        self.tokenized_corpus = data['tokenized_corpus']

        # Load user index if available
        user_index_path = "data/user_indexed/user_index.json"
        if os.path.exists(user_index_path):
            with open(user_index_path, 'r') as f:
                self.user_index = json.load(f)
            print(f"   ✓ User index: {len(self.user_index)} users")

        print(f"✅ Loaded {len(self.messages)} messages")
        print(f"   Corpus size: {len(self.tokenized_corpus)} documents")


def main():
    """Build BM25 index and demonstrate keyword search"""
    print("="*60)
    print("BM25 KEYWORD SEARCH INDEX BUILDER")
    print("="*60)

    # Load messages
    print("\n📂 Loading messages...")
    with open('data/raw_messages.json') as f:
        messages = json.load(f)
    print(f"✅ Loaded {len(messages)} messages")

    # Build index
    bm25_search = BM25Search()
    bm25_search.build_index(messages)

    # Save index
    bm25_search.save("data/bm25")

    # Demonstration
    print("\n" + "="*60)
    print("DEMONSTRATION: BM25 Keyword Matching")
    print("="*60)

    # Test case 1: Vikram + cars (failed in semantic search)
    print("\n🔍 Test 1: 'How many cars does Vikram Desai have?'")
    print("   (This FAILED in semantic search - let's see BM25)")

    query = "How many cars does Vikram Desai have"
    results = bm25_search.search(query, top_k=5)

    print(f"\n   Top 5 BM25 Results:")
    for i, (msg, score) in enumerate(results, 1):
        excerpt = msg['message'][:80]
        print(f"   {i}. [score={score:.2f}] {msg['user_name']}: {excerpt}...")

    # Test case 2: With user filter
    print("\n🔍 Test 2: 'cars' (filtered to Vikram only)")
    results_filtered = bm25_search.search("cars", top_k=5, user_filter="Vikram Desai")

    print(f"\n   Top 5 BM25 Results (Vikram only):")
    for i, (msg, score) in enumerate(results_filtered, 1):
        excerpt = msg['message'][:80]
        print(f"   {i}. [score={score:.2f}] {msg['user_name']}: {excerpt}...")

    # Test case 3: London trip
    print("\n🔍 Test 3: 'Layla planning trip to London'")
    results = bm25_search.search("Layla planning trip to London", top_k=5)

    print(f"\n   Top 5 BM25 Results:")
    for i, (msg, score) in enumerate(results, 1):
        excerpt = msg['message'][:80]
        print(f"   {i}. [score={score:.2f}] {msg['user_name']}: {excerpt}...")

    print("\n" + "="*60)
    print("✅ BM25 index ready!")
    print("="*60)
    print("\nKey Features:")
    print("  ✓ Exact keyword matching (TF-IDF based)")
    print("  ✓ User names indexed (for user-specific queries)")
    print("  ✓ Complements semantic search")
    print("  ✓ Fast retrieval")
    print("\nNext step: Implement hybrid retrieval (semantic + BM25 + graph)")


if __name__ == "__main__":
    main()
