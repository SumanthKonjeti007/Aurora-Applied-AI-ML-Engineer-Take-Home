"""
Test query: "Compare the dining preferences of Thiago Monteiro and Hans Müller"

This is a COMPARISON query with TWO ENTITIES.
Tests whether the system retrieves information for BOTH entities or just one.
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_query_breakdown():
    """Test query and show detailed breakdown of each retrieval method"""
    query = "Compare the dining preferences of Thiago Monteiro and Hans Müller"

    print("="*80)
    print(f"QUERY: {query}")
    print("="*80)
    print("QUERY TYPE: COMPARISON (Multi-Entity)")
    print("ENTITIES: Thiago Monteiro, Hans Müller")
    print("ATTRIBUTE: dining preferences")
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

    # 6. MULTI-ENTITY ANALYSIS
    print("\n[6] MULTI-ENTITY COVERAGE ANALYSIS")
    print("="*80)

    # Count how many results are from each entity
    def count_entity_coverage(results, name1, name2):
        """Count messages from each entity"""
        count1 = sum(1 for msg, _ in results if name1.lower() in msg['user_name'].lower())
        count2 = sum(1 for msg, _ in results if name2.lower() in msg['user_name'].lower())
        other = len(results) - count1 - count2
        return count1, count2, other

    sem_thiago, sem_hans, sem_other = count_entity_coverage(semantic_results[:10], "Thiago", "Hans")
    bm25_thiago, bm25_hans, bm25_other = count_entity_coverage(bm25_results[:10], "Thiago", "Hans")

    # Graph results format is different (no tuples)
    graph_thiago = sum(1 for msg in graph_results[:10] if "thiago" in msg['user_name'].lower())
    graph_hans = sum(1 for msg in graph_results[:10] if "hans" in msg['user_name'].lower())
    graph_other = len(graph_results[:10]) - graph_thiago - graph_hans

    fused_thiago, fused_hans, fused_other = count_entity_coverage(fused_static[:10], "Thiago", "Hans")

    print("\nTop-10 Entity Distribution:")
    print(f"{'Method':<15} {'Thiago':<10} {'Hans':<10} {'Other':<10} {'Coverage'}")
    print("-"*80)
    print(f"{'Semantic':<15} {sem_thiago:<10} {sem_hans:<10} {sem_other:<10} {'✅ Both' if sem_thiago > 0 and sem_hans > 0 else '❌ Partial'}")
    print(f"{'BM25':<15} {bm25_thiago:<10} {bm25_hans:<10} {bm25_other:<10} {'✅ Both' if bm25_thiago > 0 and bm25_hans > 0 else '❌ Partial'}")
    print(f"{'Graph':<15} {graph_thiago:<10} {graph_hans:<10} {graph_other:<10} {'✅ Both' if graph_thiago > 0 and graph_hans > 0 else '❌ Partial'}")
    print(f"{'RRF Fusion':<15} {fused_thiago:<10} {fused_hans:<10} {fused_other:<10} {'✅ Both' if fused_thiago > 0 and fused_hans > 0 else '❌ Partial'}")

    print("\nTop-5 Entity Distribution:")
    fused5_thiago, fused5_hans, fused5_other = count_entity_coverage(fused_static[:5], "Thiago", "Hans")
    print(f"  Thiago Monteiro: {fused5_thiago}/5 messages")
    print(f"  Hans Müller:     {fused5_hans}/5 messages")
    print(f"  Other users:     {fused5_other}/5 messages")

    if fused5_thiago > 0 and fused5_hans > 0:
        print(f"\n  ✅ COMPARISON POSSIBLE - Both entities represented")
    elif fused5_thiago > 0 or fused5_hans > 0:
        print(f"\n  ⚠️ PARTIAL COMPARISON - Only one entity represented")
    else:
        print(f"\n  ❌ COMPARISON FAILED - Neither entity represented")

    # 7. RETRIEVAL ANALYSIS
    print("\n[7] RETRIEVAL ANALYSIS")
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

    print("\n" + "="*80)


if __name__ == "__main__":
    test_query_breakdown()
