"""
Test dynamic weights for query-dependent reranking
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_query_with_analysis(query):
    """Test query and show detailed breakdown"""
    print("="*80)
    print(f"QUERY: {query}")
    print("="*80)

    retriever = HybridRetriever()

    # 1. Semantic Search
    print("\n[1] SEMANTIC SEARCH (Top 10)")
    print("-"*80)
    semantic_results = retriever.embedding_index.search(query, top_k=10)
    for i, (msg, score) in enumerate(semantic_results[:10], 1):
        user = msg['user_name'][:20].ljust(20)
        message = msg['message'][:70]
        print(f"{i}. Score:{score:.4f} | {user} | {message}...")

    # 2. BM25 Search
    print("\n[2] BM25 KEYWORD SEARCH (Top 10)")
    print("-"*80)
    bm25_results = retriever.bm25_search.search(query, top_k=10)
    for i, (msg, score) in enumerate(bm25_results[:10], 1):
        user = msg['user_name'][:20].ljust(20)
        message = msg['message'][:70]
        print(f"{i}. Score:{score:.4f} | {user} | {message}...")

    # 3. Graph Search
    print("\n[3] KNOWLEDGE GRAPH SEARCH (Top 10)")
    print("-"*80)
    graph_results = retriever._graph_search(query, top_k=10, verbose=True)
    print(f"Graph returned {len(graph_results)} results")
    for i, msg in enumerate(graph_results[:10], 1):
        user = msg['user_name'][:20].ljust(20)
        message = msg['message'][:70]
        print(f"{i}. {user} | {message}...")

    # 4. RRF Fusion with STATIC weights
    print("\n[4] RRF FUSION - STATIC WEIGHTS")
    print("-"*80)
    static_weights = {'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}
    fused_static = retriever._reciprocal_rank_fusion(
        semantic_results, bm25_results, graph_results,
        k=60, weights=static_weights
    )
    print(f"Weights: semantic=0.7, bm25=1.5, graph=0.8")
    print(f"\nTop 10 after RRF:")

    for i, (msg, rrf_score) in enumerate(fused_static[:10], 1):
        msg_id = msg['id']
        s_rank = next((j for j, (m, _) in enumerate(semantic_results, 1) if m['id'] == msg_id), None)
        b_rank = next((j for j, (m, _) in enumerate(bm25_results, 1) if m['id'] == msg_id), None)
        g_rank = next((j for j, m in enumerate(graph_results, 1) if m['id'] == msg_id), None)

        sources = []
        if s_rank: sources.append(f"S#{s_rank}")
        if b_rank: sources.append(f"B#{b_rank}")
        if g_rank: sources.append(f"G#{g_rank}")

        user = msg['user_name'][:20].ljust(20)
        message = msg['message'][:60]
        source_str = " + ".join(sources) if sources else "None"
        print(f"{i}. RRF:{rrf_score:.4f} [{source_str:20}] | {user} | {message}...")

    # 5. Query Classification & Dynamic Weights
    print("\n[5] QUERY CLASSIFICATION & DYNAMIC WEIGHTS")
    print("-"*80)

    query_type = classify_query(query)
    print(f"Query Type: {query_type['type']}")
    print(f"Reasoning: {query_type['reason']}")

    dynamic_weights = query_type['weights']
    print(f"\nDynamic Weights: semantic={dynamic_weights['semantic']}, bm25={dynamic_weights['bm25']}, graph={dynamic_weights['graph']}")

    fused_dynamic = retriever._reciprocal_rank_fusion(
        semantic_results, bm25_results, graph_results,
        k=60, weights=dynamic_weights
    )

    print(f"\nTop 10 after RRF with DYNAMIC weights:")
    for i, (msg, rrf_score) in enumerate(fused_dynamic[:10], 1):
        msg_id = msg['id']
        s_rank = next((j for j, (m, _) in enumerate(semantic_results, 1) if m['id'] == msg_id), None)
        b_rank = next((j for j, (m, _) in enumerate(bm25_results, 1) if m['id'] == msg_id), None)
        g_rank = next((j for j, m in enumerate(graph_results, 1) if m['id'] == msg_id), None)

        sources = []
        if s_rank: sources.append(f"S#{s_rank}")
        if b_rank: sources.append(f"B#{b_rank}")
        if g_rank: sources.append(f"G#{g_rank}")

        user = msg['user_name'][:20].ljust(20)
        message = msg['message'][:60]
        source_str = " + ".join(sources) if sources else "None"
        print(f"{i}. RRF:{rrf_score:.4f} [{source_str:20}] | {user} | {message}...")

    # 6. Context for LLM
    print("\n[6] CONTEXT FOR LLM (Top 5 with Dynamic Weights)")
    print("="*80)
    for i, (msg, score) in enumerate(fused_dynamic[:5], 1):
        print(f"\n[{i}] User: {msg['user_name']}")
        print(f"Message: {msg['message']}")
        print(f"RRF Score: {score:.4f}")

    # 7. Comparison
    print("\n[7] STATIC vs DYNAMIC COMPARISON")
    print("="*80)

    print("\nTop 5 Message IDs - STATIC weights:")
    for i, (msg, score) in enumerate(fused_static[:5], 1):
        print(f"  {i}. {msg['id']} (score: {score:.4f})")

    print("\nTop 5 Message IDs - DYNAMIC weights:")
    for i, (msg, score) in enumerate(fused_dynamic[:5], 1):
        print(f"  {i}. {msg['id']} (score: {score:.4f})")

    # Check if order changed
    static_ids = [msg['id'] for msg, _ in fused_static[:5]]
    dynamic_ids = [msg['id'] for msg, _ in fused_dynamic[:5]]

    if static_ids == dynamic_ids:
        print("\n⚠️ Rankings are IDENTICAL")
    else:
        print("\n✅ Rankings CHANGED with dynamic weights")
        print(f"   Differences: {len(set(static_ids) - set(dynamic_ids))} messages swapped")


def classify_query(query):
    """
    Classify query type and return appropriate weights

    Query Types:
    1. CONCEPTUAL/PREFERENCE - Vague, semantic queries about preferences
    2. ENTITY_SPECIFIC - Named user + specific entity/item
    3. AGGREGATION - "which members", "who has", cross-user queries
    4. MULTI_INTENT - Multiple aspects in one query
    """
    query_lower = query.lower()

    # Check for aggregation queries
    if any(phrase in query_lower for phrase in ['which members', 'who has', 'who requested', 'how many people', 'list all']):
        return {
            'type': 'AGGREGATION',
            'reason': 'Cross-user query requiring entity-based search',
            'weights': {'semantic': 1.5, 'bm25': 2.0, 'graph': 0.1}  # Graph fails on aggregation
        }

    # Check for multi-intent (AND/OR keywords)
    if any(phrase in query_lower for phrase in [' and ', ' or ', 'preferences and', 'plans and', 'both']):
        return {
            'type': 'MULTI_INTENT',
            'reason': 'Multiple aspects in query, need semantic understanding',
            'weights': {'semantic': 1.2, 'bm25': 1.5, 'graph': 0.3}  # Boost semantic, reduce graph
        }

    # Check for conceptual/preference queries
    conceptual_keywords = ['ideas', 'suggestions', 'recommendations', 'relaxing', 'luxury',
                          'best', 'favorite', 'prefer', 'like', 'enjoy', 'getaway', 'experience']
    if any(keyword in query_lower for keyword in conceptual_keywords):
        return {
            'type': 'CONCEPTUAL',
            'reason': 'Vague conceptual query requiring semantic understanding',
            'weights': {'semantic': 1.8, 'bm25': 1.0, 'graph': 0.5}  # Heavily boost semantic
        }

    # Check for entity-specific queries (user name present)
    # This is simplified - in practice, use name resolver
    names = ['sophia', 'thiago', 'vikram', 'hans', 'layla', 'amira', 'priya', 'emeka', 'elena', 'jin']
    if any(name in query_lower for name in names):
        return {
            'type': 'ENTITY_SPECIFIC',
            'reason': 'User name + entity query, BM25 excels at exact matching',
            'weights': {'semantic': 0.5, 'bm25': 2.0, 'graph': 1.0}  # Boost BM25 for name matching
        }

    # Default: Balanced
    return {
        'type': 'BALANCED',
        'reason': 'Standard query, using current static weights',
        'weights': {'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}
    }


if __name__ == "__main__":
    # Test query from user
    query = "Show me ideas for a relaxing getaway."
    test_query_with_analysis(query)
