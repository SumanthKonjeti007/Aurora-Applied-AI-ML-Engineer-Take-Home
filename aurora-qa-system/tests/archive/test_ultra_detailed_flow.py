"""
Ultra-detailed flow test - Shows every step including sub-query handling

Usage: python test_ultra_detailed_flow.py "Your query here"
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.hybrid_retriever import HybridRetriever
from src.query_processor import QueryProcessor
from src.answer_generator import AnswerGenerator
from src.result_composer import ResultComposer
import sys

# Get query from command line argument
if len(sys.argv) < 2:
    print("Usage: python test_ultra_detailed_flow.py \"Your query here\"")
    sys.exit(1)

query = sys.argv[1]

# Initialize components
print("\n" + "="*100)
print("ULTRA-DETAILED FLOW TEST - STEP BY STEP ANALYSIS")
print("="*100)

print("\nInitializing components...")
retriever = HybridRetriever()
processor = QueryProcessor(name_resolver=retriever.name_resolver)
generator = AnswerGenerator()
composer = ResultComposer()

print(f"\n{'='*100}")
print(f"QUERY: {query}")
print(f"{'='*100}\n")

# STEP 1: ROUTING & DECOMPOSITION
print("\n" + "="*100)
print("STEP 1: QUERY PROCESSING & ROUTING")
print("="*100)

query_plans = processor.process(query, verbose=False)
route = query_plans[0].get('route', 'LOOKUP')

print(f"\n🔀 ROUTER DECISION: {route}")
print(f"   Number of Sub-Queries: {len(query_plans)}")

if len(query_plans) > 1:
    print(f"\n📋 QUERY DECOMPOSITION:")
    for i, plan in enumerate(query_plans, 1):
        print(f"   {i}. \"{plan['query']}\"")
        print(f"      Type: {plan['type']}")
        print(f"      Weights: sem={plan['weights']['semantic']}, bm25={plan['weights']['bm25']}, graph={plan['weights']['graph']}")

if route == "ANALYTICS":
    print("\n⚠️  This query uses ANALYTICS pipeline - skipping detailed retrieval analysis")
    exit(0)

# STEP 2: RETRIEVAL FOR EACH SUB-QUERY
print("\n" + "="*100)
print("STEP 2: RETRIEVAL FROM INDIVIDUAL SOURCES (PER SUB-QUERY)")
print("="*100)

all_results = []

for plan_idx, plan in enumerate(query_plans, 1):
    sub_query = plan['query']
    weights = plan['weights']

    print(f"\n{'*'*100}")
    print(f"SUB-QUERY {plan_idx}/{len(query_plans)}: \"{sub_query}\"")
    print(f"{'*'*100}")

    # Detect user and temporal for this sub-query
    import re
    query_normalized = re.sub(r"'s\b", "", sub_query.lower())
    query_normalized = re.sub(r'[^\w\s]', ' ', query_normalized)
    users_detected = []
    for word in query_normalized.split():
        resolved_name = retriever.name_resolver.resolve(word, fuzzy_threshold=0.85)
        if resolved_name and resolved_name not in users_detected:
            users_detected.append(resolved_name)

    user_id = None
    if users_detected:
        user_id = retriever.name_resolver.get_user_id(users_detected[0])
        print(f"\n👤 User: {users_detected[0]} (ID: {user_id[:8]}...)")
    else:
        print(f"\n👤 No specific user detected")

    date_range = retriever.temporal_analyzer.extract_date_range(sub_query)
    if date_range:
        print(f"📅 Date range: {date_range[0]} to {date_range[1]}")
    else:
        print(f"📅 No temporal filtering")

    # 2A: QDRANT
    print(f"\n{'-'*100}")
    print(f"2A. QDRANT SEMANTIC SEARCH")
    print(f"{'-'*100}")

    semantic_results_raw = retriever.qdrant_search.search(
        sub_query,
        top_k=20,
        user_id=user_id,
        date_range=date_range
    )

    print(f"\n✅ Retrieved {len(semantic_results_raw)} results from Qdrant")

    if semantic_results_raw:
        print(f"\nTop 3 Qdrant results:")
        for i, r in enumerate(semantic_results_raw[:3], 1):
            print(f"  {i}. Score: {r['score']:.4f} | {r['user_name']} | {r['message'][:60]}...")

    # 2B: BM25
    print(f"\n{'-'*100}")
    print(f"2B. BM25 KEYWORD SEARCH")
    print(f"{'-'*100}")

    bm25_results = retriever.bm25_search.search(sub_query, top_k=20, user_id=user_id)

    if date_range:
        bm25_results = retriever._filter_by_date_range(bm25_results, date_range)

    print(f"\n✅ Retrieved {len(bm25_results)} results from BM25")

    if bm25_results:
        print(f"\nTop 3 BM25 results:")
        for i, (msg, score) in enumerate(bm25_results[:3], 1):
            print(f"  {i}. Score: {score:.4f} | {msg['user_name']} | {msg['message'][:60]}...")

    # 2C: GRAPH
    print(f"\n{'-'*100}")
    print(f"2C. KNOWLEDGE GRAPH SEARCH")
    print(f"{'-'*100}")

    graph_results = retriever._graph_search(sub_query, top_k=10, verbose=False)

    if date_range:
        graph_results = retriever._filter_by_date_range(graph_results, date_range)

    print(f"\n✅ Retrieved {len(graph_results)} results from Knowledge Graph")

    # RRF FUSION FOR THIS SUB-QUERY
    print(f"\n{'-'*100}")
    print(f"RRF FUSION (Sub-Query {plan_idx})")
    print(f"{'-'*100}")

    semantic_results = [(r, r['score']) for r in semantic_results_raw]

    fused_results = retriever._reciprocal_rank_fusion(
        semantic_results,
        bm25_results,
        graph_results,
        k=60,
        weights=weights
    )

    print(f"✅ RRF produced {len(fused_results)} unique results for this sub-query")

    # Take top 20 for this sub-query (increased from 10)
    all_results.append(fused_results[:20])

# STEP 3: RESULT COMPOSITION
print(f"\n{'='*100}")
print("STEP 3: RESULT COMPOSITION (COMBINING SUB-QUERIES)")
print(f"{'='*100}")

print(f"\nInput to Composer:")
for i, results in enumerate(all_results, 1):
    print(f"  Sub-query {i}: {len(results)} results")

composed_results = composer.compose(
    all_results,
    strategy="auto",
    max_results=20,
    verbose=True
)

print(f"\n✅ Composed Results: {len(composed_results)} messages")

# Show user distribution
from collections import Counter
users = [msg['user_name'] for msg, score in composed_results]
user_dist = Counter(users)
print(f"\nUser Distribution: {dict(user_dist)}")

print(f"\nTop 20 Composed Results:")
for i, (msg, score) in enumerate(composed_results[:20], 1):
    print(f"\n  {i}. Score: {score:.6f}")
    print(f"     User: {msg['user_name']}")
    print(f"     Message: {msg['message'][:70]}...")

# STEP 4: LLM GENERATION
print(f"\n{'='*100}")
print("STEP 4: LLM ANSWER GENERATION")
print(f"{'='*100}")

print(f"\nSending {len(composed_results)} messages to LLM...")

answer_result = generator.generate_with_sources(
    query=query,
    composed_results=composed_results,
    verbose=True
)

print(f"\n{'='*100}")
print("FINAL ANSWER")
print(f"{'='*100}")
print(f"\n{answer_result['answer']}")
print(f"\nModel: {answer_result['model']}")
print(f"Tokens: {answer_result['tokens']}")
