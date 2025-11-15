"""
Test query: "What dining reservations has Lily O'Sullivan requested for her trip?"

This script tests each retrieval method individually and then shows RRF fusion results.
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_query_breakdown():
    """Test query and show detailed breakdown of each retrieval method"""
    query = "What dining reservations has Lily O'Sullivan requested for her trip?"

    print("="*80)
    print(f"QUERY: {query}")
    print("="*80)

    # Initialize retriever
    print("\nInitializing Hybrid Retriever...")
    retriever = HybridRetriever()
    print("\n" + "="*80)

    # 1. SEMANTIC SEARCH
    print("\n[1] SEMANTIC SEARCH (Top 10)")
    print("-"*80)
    semantic_results = retriever.embedding_index.search(query, top_k=10)
    print(f"Retrieved {len(semantic_results)} results\n")

    for i, (msg, score) in enumerate(semantic_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:80]
        print(f"{i:2}. Score:{score:.4f} | {user} | {message}...")

    # 2. BM25 KEYWORD SEARCH
    print("\n[2] BM25 KEYWORD SEARCH (Top 10)")
    print("-"*80)
    bm25_results = retriever.bm25_search.search(query, top_k=10)
    print(f"Retrieved {len(bm25_results)} results\n")

    for i, (msg, score) in enumerate(bm25_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:80]
        print(f"{i:2}. Score:{score:.4f} | {user} | {message}...")

    # 3. KNOWLEDGE GRAPH SEARCH
    print("\n[3] KNOWLEDGE GRAPH SEARCH (Top 10)")
    print("-"*80)
    graph_results = retriever._graph_search(query, top_k=10, verbose=True)
    print(f"\nRetrieved {len(graph_results)} results\n")

    for i, msg in enumerate(graph_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:80]
        print(f"{i:2}. {user} | {message}...")

    # 4. RRF FUSION WITH STATIC WEIGHTS
    print("\n[4] RRF FUSION - STATIC WEIGHTS")
    print("-"*80)
    static_weights = {'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}
    fused_static = retriever._reciprocal_rank_fusion(
        semantic_results, bm25_results, graph_results,
        k=60, weights=static_weights
    )
    print(f"Weights: semantic={static_weights['semantic']}, bm25={static_weights['bm25']}, graph={static_weights['graph']}")
    print(f"\nTop 10 after RRF:\n")

    for i, (msg, rrf_score) in enumerate(fused_static[:10], 1):
        msg_id = msg['id']

        # Find ranks in each method
        s_rank = next((j for j, (m, _) in enumerate(semantic_results, 1) if m['id'] == msg_id), None)
        b_rank = next((j for j, (m, _) in enumerate(bm25_results, 1) if m['id'] == msg_id), None)
        g_rank = next((j for j, m in enumerate(graph_results, 1) if m['id'] == msg_id), None)

        sources = []
        if s_rank: sources.append(f"Sem#{s_rank}")
        if b_rank: sources.append(f"BM25#{b_rank}")
        if g_rank: sources.append(f"Graph#{g_rank}")

        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:65]
        source_str = " + ".join(sources) if sources else "None"
        print(f"{i:2}. RRF:{rrf_score:.4f} [{source_str:25}] | {user} | {message}...")

    # 5. DETAILED CONTEXT FOR TOP 5
    print("\n[5] TOP 5 RESULTS - FULL CONTEXT")
    print("="*80)
    for i, (msg, score) in enumerate(fused_static[:5], 1):
        print(f"\n[{i}] User: {msg['user_name']}")
        print(f"    Message: {msg['message']}")
        print(f"    RRF Score: {score:.4f}")
        print(f"    Message ID: {msg['id']}")

    # 6. ANALYSIS
    print("\n[6] RETRIEVAL ANALYSIS")
    print("="*80)

    # Check overlap between methods
    sem_ids = set(msg['id'] for msg, _ in semantic_results[:10])
    bm25_ids = set(msg['id'] for msg, _ in bm25_results[:10])
    graph_ids = set(msg['id'] for msg in graph_results[:10])

    print(f"\nTop-10 Overlap:")
    print(f"  Semantic ∩ BM25:   {len(sem_ids & bm25_ids)} messages")
    print(f"  Semantic ∩ Graph:  {len(sem_ids & graph_ids)} messages")
    print(f"  BM25 ∩ Graph:      {len(bm25_ids & graph_ids)} messages")
    print(f"  All three:         {len(sem_ids & bm25_ids & graph_ids)} messages")

    # Check which method contributed most to top-5
    top5_sources = {'semantic': 0, 'bm25': 0, 'graph': 0}
    for msg, _ in fused_static[:5]:
        msg_id = msg['id']
        if msg_id in sem_ids:
            top5_sources['semantic'] += 1
        if msg_id in bm25_ids:
            top5_sources['bm25'] += 1
        if msg_id in graph_ids:
            top5_sources['graph'] += 1

    print(f"\nTop-5 Source Contributions:")
    print(f"  Semantic: {top5_sources['semantic']}/5 messages")
    print(f"  BM25:     {top5_sources['bm25']}/5 messages")
    print(f"  Graph:    {top5_sources['graph']}/5 messages")

    # Check if top results are actually from Lily O'Sullivan
    lily_count = sum(1 for msg, _ in fused_static[:5] if "lily" in msg['user_name'].lower())
    print(f"\nEntity Filtering:")
    print(f"  Top-5 from Lily O'Sullivan: {lily_count}/5 messages")

    print("\n" + "="*80)


if __name__ == "__main__":
    test_query_breakdown()
