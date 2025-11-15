"""
Detailed Step-by-Step Execution Test

Shows complete pipeline execution for query:
"How many cars does Vikram Desai?"

Displays:
1. Query Processing (classification, weights)
2. Semantic Search results
3. BM25 Search results
4. Graph Search results
5. RRF Fusion with weights
6. Final context for LLM
7. LLM Answer
"""
import sys
sys.path.insert(0, 'src')

from src.qa_system import QASystem
from src.hybrid_retriever import HybridRetriever
from src.query_processor import QueryProcessor


def detailed_execution(query: str):
    """
    Execute query with detailed step-by-step display
    """
    print("="*100)
    print("DETAILED STEP-BY-STEP EXECUTION")
    print("="*100)
    print(f"\nQUERY: \"{query}\"")
    print("="*100)

    # Initialize components
    print("\n[Initializing system...]")
    retriever = HybridRetriever()
    processor = QueryProcessor(retriever.name_resolver)

    # ========== STEP 1: QUERY PROCESSING ==========
    print("\n" + "="*100)
    print("STEP 1: QUERY PROCESSING & OPTIMIZATION")
    print("="*100)

    query_plans = processor.process(query, verbose=False)

    for i, plan in enumerate(query_plans, 1):
        print(f"\n📋 Query Plan {i}:")
        print(f"   Original Query: \"{query}\"")
        if len(query_plans) > 1:
            print(f"   Optimized Sub-Query: \"{plan['query']}\"")
        print(f"   Query Type: {plan['type']}")
        print(f"   Classification Reason: {plan['reason']}")
        print(f"\n   🎯 Dynamic Weights Assigned:")
        print(f"      ├─ Semantic: {plan['weights']['semantic']}")
        print(f"      ├─ BM25:     {plan['weights']['bm25']}")
        print(f"      └─ Graph:    {plan['weights']['graph']}")

    # Process first plan (or only plan)
    plan = query_plans[0]
    search_query = plan['query']
    weights = plan['weights']

    # ========== STEP 2: SEMANTIC SEARCH ==========
    print("\n" + "="*100)
    print("STEP 2: SEMANTIC SEARCH (Vector Similarity)")
    print("="*100)

    semantic_results = retriever.embedding_index.search(search_query, top_k=10)

    print(f"\n🔍 Retrieved {len(semantic_results)} results from semantic search")
    print(f"   Model: BAAI/bge-small-en-v1.5")
    print(f"   Strategy: Dense vector similarity (cosine)")
    print(f"\nTop 10 Results:")

    for i, (msg, score) in enumerate(semantic_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:70]
        print(f"   {i:2}. Score: {score:.4f} | {user} | {message}...")

    # ========== STEP 3: BM25 KEYWORD SEARCH ==========
    print("\n" + "="*100)
    print("STEP 3: BM25 KEYWORD SEARCH (Lexical Matching)")
    print("="*100)

    bm25_results = retriever.bm25_search.search(search_query, top_k=10)

    print(f"\n🔍 Retrieved {len(bm25_results)} results from BM25 search")
    print(f"   Algorithm: BM25 (Best Matching 25)")
    print(f"   Strategy: TF-IDF weighted keyword matching")
    print(f"\nTop 10 Results:")

    for i, (msg, score) in enumerate(bm25_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:70]
        print(f"   {i:2}. Score: {score:.4f} | {user} | {message}...")

    # ========== STEP 4: KNOWLEDGE GRAPH SEARCH ==========
    print("\n" + "="*100)
    print("STEP 4: KNOWLEDGE GRAPH SEARCH (Entity Relationships)")
    print("="*100)

    graph_results = retriever._graph_search(search_query, top_k=10, verbose=True)

    print(f"\n🔍 Retrieved {len(graph_results)} results from graph search")
    print(f"   Strategy: Entity-based relationship traversal")
    print(f"\nTop {len(graph_results)} Results:")

    for i, msg in enumerate(graph_results[:10], 1):
        user = msg['user_name'][:25].ljust(25)
        message = msg['message'][:70]
        print(f"   {i:2}. {user} | {message}...")

    # ========== STEP 5: RRF FUSION ==========
    print("\n" + "="*100)
    print("STEP 5: RECIPROCAL RANK FUSION (RRF)")
    print("="*100)

    print(f"\n⚖️  Applying Dynamic Weights:")
    print(f"   ├─ Semantic: {weights['semantic']} (weight)")
    print(f"   ├─ BM25:     {weights['bm25']} (weight)")
    print(f"   └─ Graph:    {weights['graph']} (weight)")
    print(f"\n   Formula: RRF_score(doc) = Σ [weight_method × 1/(k + rank_method)]")
    print(f"   RRF constant k = 60")

    fused_results = retriever._reciprocal_rank_fusion(
        semantic_results,
        bm25_results,
        graph_results,
        k=60,
        weights=weights
    )

    print(f"\n🎯 Fused {len(fused_results)} unique messages")
    print(f"\nTop 10 After RRF Fusion:")
    print(f"\n{'Rank':<6} {'RRF Score':<12} {'Sources':<35} {'User':<25} {'Message'}")
    print("-"*100)

    for i, (msg, rrf_score) in enumerate(fused_results[:10], 1):
        msg_id = msg['id']

        # Find ranks in each method
        s_rank = next((j for j, (m, _) in enumerate(semantic_results, 1) if m['id'] == msg_id), None)
        b_rank = next((j for j, (m, _) in enumerate(bm25_results, 1) if m['id'] == msg_id), None)
        g_rank = next((j for j, m in enumerate(graph_results, 1) if m['id'] == msg_id), None)

        sources = []
        if s_rank: sources.append(f"Sem#{s_rank}")
        if b_rank: sources.append(f"BM25#{b_rank}")
        if g_rank: sources.append(f"Graph#{g_rank}")

        source_str = " + ".join(sources) if sources else "None"
        user = msg['user_name'][:23]
        message = msg['message'][:40]

        print(f"{i:<6} {rrf_score:<12.4f} {source_str:<35} {user:<25} {message}...")

    # ========== STEP 6: CONTEXT FOR LLM ==========
    print("\n" + "="*100)
    print("STEP 6: FINAL CONTEXT FOR LLM")
    print("="*100)

    from src.result_composer import ResultComposer
    composer = ResultComposer()

    top_results = fused_results[:5]
    context = composer.format_context_for_llm(top_results, include_scores=False)

    print(f"\n📄 Formatted Context (Top 5 messages):")
    print("-"*100)
    print(context)
    print("-"*100)
    print(f"\nContext Stats:")
    print(f"   ├─ Messages: {len(top_results)}")
    print(f"   ├─ Characters: {len(context)}")
    print(f"   └─ Users represented: {len(set(msg['user_name'] for msg, _ in top_results))}")

    # ========== STEP 7: LLM ANSWER GENERATION ==========
    print("\n" + "="*100)
    print("STEP 7: LLM ANSWER GENERATION (RAG)")
    print("="*100)

    from src.answer_generator import AnswerGenerator
    import os

    generator = AnswerGenerator()

    print(f"\n🤖 Calling LLM...")
    print(f"   Model: llama-3.3-70b-versatile (Groq)")
    print(f"   Temperature: 0.3")
    print(f"   Max tokens: 500")

    result = generator.generate(
        query=query,
        context=context,
        temperature=0.3,
        verbose=False
    )

    print(f"\n✅ Answer Generated")
    print(f"   ├─ Prompt tokens: {result['tokens']['prompt']}")
    print(f"   ├─ Completion tokens: {result['tokens']['completion']}")
    print(f"   └─ Total tokens: {result['tokens']['total']}")

    # ========== FINAL ANSWER ==========
    print("\n" + "="*100)
    print("FINAL ANSWER")
    print("="*100)
    print(f"\n{result['answer']}")

    print("\n" + "="*100)
    print("EXECUTION COMPLETE")
    print("="*100)


if __name__ == "__main__":
    query = "How many cars does Vikram Desai?"
    detailed_execution(query)
