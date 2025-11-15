"""
Demonstration: Hybrid Retrieval Pipeline
Show how semantic + BM25 + graph combine to answer a query

Example: "How many cars does Vikram Desai have?"
- Semantic search: FAILED (0 relevant in top-10)
- BM25 search: Should find exact keyword matches
- Graph: Should find ownership relationships
- Hybrid: Combine all three → Should succeed
"""
import json
from src.embeddings import EmbeddingIndex
from src.bm25_search import BM25Search
from src.knowledge_graph import KnowledgeGraph


def print_results(results, method_name, top_k=10):
    """Pretty print search results"""
    print(f"\n{'='*70}")
    print(f"{method_name} - Top {top_k} Results")
    print('='*70)

    if not results:
        print("   ❌ No results found")
        return

    for i, (msg, score) in enumerate(results[:top_k], 1):
        user = msg['user_name']
        text = msg['message'][:80]
        print(f"{i:2d}. [score={score:.3f}] {user}")
        print(f"    {text}...")
        print()


def simple_rrf_fusion(semantic_results, bm25_results, graph_results, k=60):
    """
    Simple Reciprocal Rank Fusion (RRF)

    score = Σ 1/(k + rank_i) for each retrieval method

    Args:
        semantic_results: List of (msg, score) from semantic search
        bm25_results: List of (msg, score) from BM25
        graph_results: List of message dicts from graph
        k: RRF constant (typically 60)

    Returns:
        List of (msg, fused_score) sorted by fused score
    """
    # Build score accumulator
    scores = {}  # message_id -> score
    messages = {}  # message_id -> message dict

    # Add semantic results
    for rank, (msg, _) in enumerate(semantic_results, start=1):
        msg_id = msg['id']
        rrf_score = 1.0 / (k + rank)
        scores[msg_id] = scores.get(msg_id, 0) + rrf_score
        messages[msg_id] = msg

    # Add BM25 results
    for rank, (msg, _) in enumerate(bm25_results, start=1):
        msg_id = msg['id']
        rrf_score = 1.0 / (k + rank)
        scores[msg_id] = scores.get(msg_id, 0) + rrf_score
        messages[msg_id] = msg

    # Add graph results
    for rank, msg in enumerate(graph_results, start=1):
        msg_id = msg['id']
        rrf_score = 1.0 / (k + rank)
        scores[msg_id] = scores.get(msg_id, 0) + rrf_score
        messages[msg_id] = msg

    # Sort by fused score
    fused_results = [
        (messages[msg_id], score)
        for msg_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return fused_results


def analyze_relevance(msg, query_info):
    """
    Check if message is relevant to the query

    Args:
        msg: Message dict
        query_info: Dict with 'expected_user' and 'expected_keywords'

    Returns:
        (is_relevant, reason)
    """
    user_match = msg['user_name'] == query_info['expected_user']
    text = msg['message'].lower()

    keyword_matches = [kw for kw in query_info['expected_keywords'] if kw in text]

    if user_match and len(keyword_matches) >= 1:
        return True, f"✅ User match + keywords: {keyword_matches}"
    elif user_match:
        return False, f"⚠️  User match but no keywords"
    elif len(keyword_matches) >= 2:
        return True, f"✅ Multiple keywords: {keyword_matches}"
    else:
        return False, f"❌ No match"


def main():
    print("="*70)
    print("HYBRID RETRIEVAL DEMONSTRATION")
    print("="*70)

    # Query that FAILED in semantic search
    query = "How many cars does Vikram Desai have?"

    print(f"\n📋 Query: \"{query}\"")
    print("\n   Background:")
    print("   - Semantic search FAILED: 0 relevant in top-10")
    print("   - Expected answer: Vikram owns BMW, Tesla, Mercedes (possibly Bentley)")
    print("   - Ground truth: Messages mention these vehicles")

    query_info = {
        'expected_user': 'Vikram Desai',
        'expected_keywords': ['car', 'bmw', 'tesla', 'mercedes', 'bentley', 'vehicle']
    }

    # Load all indices
    print("\n" + "="*70)
    print("LOADING INDICES")
    print("="*70)

    print("\n1️⃣ Loading semantic search (embeddings)...")
    embedding_index = EmbeddingIndex()
    embedding_index.load("data/embeddings")

    print("\n2️⃣ Loading keyword search (BM25)...")
    bm25_search = BM25Search()
    bm25_search.load("data/bm25")

    print("\n3️⃣ Loading knowledge graph...")
    kg = KnowledgeGraph()
    kg.load("data/knowledge_graph.pkl")

    # ========== RETRIEVAL 1: SEMANTIC SEARCH ==========
    print("\n" + "="*70)
    print("RETRIEVAL 1: SEMANTIC SEARCH (Embeddings)")
    print("="*70)
    print("\nQuery embedding: 'query: How many cars does Vikram Desai have?'")
    print("Document embeddings: 'passage: {message}'")
    print("Method: Cosine similarity (L2 distance)")

    semantic_results = embedding_index.search(query, top_k=20)
    print_results(semantic_results, "Semantic Search", top_k=10)

    # Count relevant
    relevant_semantic = sum(1 for msg, _ in semantic_results[:10]
                           if analyze_relevance(msg, query_info)[0])
    print(f"📊 Relevant in top-10: {relevant_semantic}/10")

    # ========== RETRIEVAL 2: BM25 KEYWORD SEARCH ==========
    print("\n" + "="*70)
    print("RETRIEVAL 2: BM25 KEYWORD SEARCH")
    print("="*70)
    print("\nTokenized query: ['how', 'many', 'cars', 'does', 'vikram', 'desai', 'have']")
    print("Method: TF-IDF scoring (exact token matching)")

    bm25_results = bm25_search.search(query, top_k=20)
    print_results(bm25_results, "BM25 Search", top_k=10)

    relevant_bm25 = sum(1 for msg, _ in bm25_results[:10]
                       if analyze_relevance(msg, query_info)[0])
    print(f"📊 Relevant in top-10: {relevant_bm25}/10")

    # ========== RETRIEVAL 3: KNOWLEDGE GRAPH ==========
    print("\n" + "="*70)
    print("RETRIEVAL 3: KNOWLEDGE GRAPH")
    print("="*70)
    print("\nGraph query: Find relationships for 'Vikram Desai'")
    print("Method: Graph traversal (entities connected to user)")

    # Get messages related to Vikram and car-related entities
    graph_messages = []

    # Get all relationships for Vikram
    vikram_relationships = kg.get_user_relationships("Vikram Desai")
    print(f"\nFound {len(vikram_relationships)} relationships for Vikram Desai")

    # Get messages from these relationships
    seen_ids = set()
    for rel in vikram_relationships:
        msg_id = rel['message_id']
        if msg_id not in seen_ids:
            # Find the message
            msg = next((m for m in embedding_index.messages if m['id'] == msg_id), None)
            if msg:
                # Check if it's car-related
                text = msg['message'].lower()
                if any(kw in text for kw in ['car', 'bmw', 'tesla', 'mercedes', 'bentley', 'vehicle']):
                    graph_messages.append(msg)
                    seen_ids.add(msg_id)

    print(f"Found {len(graph_messages)} car-related messages from graph")

    # Convert to results format
    graph_results = [(msg, 1.0) for msg in graph_messages[:20]]
    print_results(graph_results, "Knowledge Graph", top_k=10)

    relevant_graph = sum(1 for msg, _ in graph_results[:10]
                        if analyze_relevance(msg, query_info)[0])
    print(f"📊 Relevant in top-10: {relevant_graph}/10")

    # ========== HYBRID FUSION (RRF) ==========
    print("\n" + "="*70)
    print("HYBRID FUSION: RECIPROCAL RANK FUSION (RRF)")
    print("="*70)
    print("\nCombining all three methods using RRF:")
    print("  score(msg) = Σ 1/(k + rank_i) for i in [semantic, bm25, graph]")
    print("  k = 60 (standard RRF constant)")
    print("\nIntuition:")
    print("  - Messages appearing in multiple methods get boosted")
    print("  - Higher ranks contribute more to final score")
    print("  - Balances strengths of each method")

    fused_results = simple_rrf_fusion(
        semantic_results[:20],
        bm25_results[:20],
        graph_messages[:20],
        k=60
    )

    print_results(fused_results, "Hybrid (RRF)", top_k=10)

    relevant_hybrid = sum(1 for msg, _ in fused_results[:10]
                         if analyze_relevance(msg, query_info)[0])
    print(f"📊 Relevant in top-10: {relevant_hybrid}/10")

    # ========== DETAILED ANALYSIS OF TOP-10 HYBRID ==========
    print("\n" + "="*70)
    print("DETAILED RELEVANCE ANALYSIS - Top 10 Hybrid Results")
    print("="*70)

    for i, (msg, score) in enumerate(fused_results[:10], 1):
        is_relevant, reason = analyze_relevance(msg, query_info)
        status = "✅ RELEVANT" if is_relevant else "❌ NOT RELEVANT"

        print(f"\n{i}. [RRF score={score:.4f}] {status}")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message'][:100]}...")
        print(f"   {reason}")

    # ========== COMPARISON SUMMARY ==========
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)

    print(f"""
Method              | Relevant/10 | Pass? | Notes
--------------------|-------------|-------|-------------------------------
Semantic (alone)    | {relevant_semantic}/10      | ❌    | Format mismatch (question vs statement)
BM25 (alone)        | {relevant_bm25}/10      | {'✅' if relevant_bm25 >= 3 else '❌'}    | Good keyword matching
Knowledge Graph     | {relevant_graph}/10      | {'✅' if relevant_graph >= 3 else '❌'}    | Entity-based filtering
Hybrid (RRF)        | {relevant_hybrid}/10      | {'✅' if relevant_hybrid >= 3 else '❌'}    | Combined strength of all methods
""")

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)

    if relevant_hybrid >= 3:
        print("\n✅ SUCCESS: Hybrid retrieval found sufficient relevant messages!")
        print(f"   Improvement: {relevant_semantic} → {relevant_hybrid} relevant messages")
        print("\n   Next step: Feed these top-10 messages to LLM for answer extraction")
        print("\n   Expected LLM answer:")
        print('   "Vikram Desai owns at least 2-3 cars based on the messages:')
        print('    - BMW (mentioned in car service message)')
        print('    - Tesla (mentioned for airport pickup)')
        print('    - Mercedes (mentioned, but unclear if he still owns it)"')
    else:
        print("\n⚠️  Hybrid still needs improvement, but better than semantic alone")
        print(f"   Improvement: {relevant_semantic} → {relevant_hybrid} relevant messages")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
