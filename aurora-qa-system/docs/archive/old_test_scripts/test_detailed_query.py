"""
Test query with detailed breakdown of each retrieval method
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_query_detailed(query):
    """Test query with full breakdown"""
    print("="*80)
    print(f"DETAILED QUERY ANALYSIS: {query}")
    print("="*80)

    # Initialize
    print("\n🔧 Initializing hybrid retriever...")
    retriever = HybridRetriever()

    # Get results from each method separately
    print(f"\n{'='*80}")
    print("RETRIEVAL METHOD 1: SEMANTIC SEARCH")
    print(f"{'='*80}")

    semantic_results = retriever.embedding_index.search(query, top_k=10)

    print(f"\nRetrieved {len(semantic_results)} results from semantic search:")
    for i, (msg, score) in enumerate(semantic_results, 1):
        print(f"\n{i}. [Semantic Score: {score:.4f}]")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message'][:120]}...")

    # BM25 Search
    print(f"\n{'='*80}")
    print("RETRIEVAL METHOD 2: BM25 KEYWORD SEARCH")
    print(f"{'='*80}")

    bm25_results = retriever.bm25_search.search(query, top_k=10)

    print(f"\nRetrieved {len(bm25_results)} results from BM25:")
    for i, (msg, score) in enumerate(bm25_results, 1):
        print(f"\n{i}. [BM25 Score: {score:.4f}]")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message'][:120]}...")

    # Graph Search
    print(f"\n{'='*80}")
    print("RETRIEVAL METHOD 3: KNOWLEDGE GRAPH SEARCH")
    print(f"{'='*80}")

    graph_results = retriever._graph_search(query, top_k=10, verbose=True)

    print(f"\nRetrieved {len(graph_results)} results from graph:")
    for i, msg in enumerate(graph_results, 1):
        print(f"\n{i}. [Graph Result]")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message'][:120]}...")

    # RRF Fusion
    print(f"\n{'='*80}")
    print("RRF FUSION")
    print(f"{'='*80}")

    # Perform fusion
    fused_results = retriever._reciprocal_rank_fusion(
        semantic_results,
        bm25_results,
        graph_results,
        k=60,
        weights={'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}
    )

    print(f"\n✅ Fused {len(fused_results)} unique messages")
    print(f"\nWeights used:")
    print(f"  - Semantic: 0.7")
    print(f"  - BM25: 1.5 (boosted for keyword matching)")
    print(f"  - Graph: 0.8")

    # Show top 10 after fusion
    print(f"\n{'='*80}")
    print("TOP 10 RESULTS AFTER RRF FUSION")
    print(f"{'='*80}")

    for i, (msg, rrf_score) in enumerate(fused_results[:10], 1):
        msg_id = msg['id']

        # Find ranks from each method
        semantic_rank = next((j for j, (m, _) in enumerate(semantic_results, 1) if m['id'] == msg_id), None)
        bm25_rank = next((j for j, (m, _) in enumerate(bm25_results, 1) if m['id'] == msg_id), None)
        graph_rank = next((j for j, m in enumerate(graph_results, 1) if m['id'] == msg_id), None)

        print(f"\n{i}. [RRF Score: {rrf_score:.4f}]")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message'][:120]}...")
        print(f"   Sources: ", end="")

        sources = []
        if semantic_rank:
            sources.append(f"Semantic(#{semantic_rank})")
        if bm25_rank:
            sources.append(f"BM25(#{bm25_rank})")
        if graph_rank:
            sources.append(f"Graph(#{graph_rank})")

        print(" + ".join(sources) if sources else "None")

    # Context for LLM
    print(f"\n{'='*80}")
    print("CONTEXT FOR LLM (Top 5 Results)")
    print(f"{'='*80}")

    print(f"\nThese messages would be passed to the LLM to generate the final answer:")
    print(f"\n---")

    for i, (msg, rrf_score) in enumerate(fused_results[:5], 1):
        print(f"\nMessage {i}:")
        print(f"User: {msg['user_name']}")
        print(f"Content: {msg['message']}")
        print(f"Timestamp: {msg.get('timestamp', 'N/A')}")
        print(f"Relevance Score: {rrf_score:.4f}")
        print(f"---")

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\nQuery: \"{query}\"")
    print(f"\nRetrieval Results:")
    print(f"  - Semantic: {len(semantic_results)} results")
    print(f"  - BM25: {len(bm25_results)} results")
    print(f"  - Graph: {len(graph_results)} results")
    print(f"  - Fused: {len(fused_results)} unique results")
    print(f"\n✅ Top 5 most relevant messages ready for LLM")


if __name__ == "__main__":
    query = "What bookings does Thiago Monteiro have?"
    test_query_detailed(query)
