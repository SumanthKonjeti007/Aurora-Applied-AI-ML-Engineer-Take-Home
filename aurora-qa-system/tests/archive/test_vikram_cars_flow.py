"""
Custom test to show full detailed flow for: "How many cars does Vikram Desai have?"
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Set Mistral API key
os.environ['MISTRAL_API_KEY'] = 'tCQvPLqFgob8FOyqBcLye3duFWR3Qa2m'

from src.hybrid_retriever import HybridRetriever
from src.query_processor import QueryProcessor
from src.answer_generator import AnswerGenerator
from src.result_composer import ResultComposer
from collections import Counter
import re

# The query we want to test
query = "How many cars does Vikram Desai have?"

print("\n" + "="*100)
print("DETAILED FLOW ANALYSIS")
print("="*100)
print(f"\nQUERY: {query}")
print("="*100)

# Initialize components
print("\n🔧 Initializing components...")
retriever = HybridRetriever()
processor = QueryProcessor(name_resolver=retriever.name_resolver)
generator = AnswerGenerator()
composer = ResultComposer()

# STEP 1: QUERY PROCESSING & ROUTING
print("\n" + "="*100)
print("STEP 1: QUERY PROCESSING & ROUTING")
print("="*100)

query_plans = processor.process(query, verbose=True)

print(f"\n📊 Query Plan Summary:")
print(f"   Route: {query_plans[0].get('route', 'LOOKUP')}")
print(f"   Number of sub-queries: {len(query_plans)}")

for i, plan in enumerate(query_plans, 1):
    print(f"\n   Sub-Query {i}:")
    print(f"      Query: \"{plan['query']}\"")
    print(f"      Type: {plan['type']}")
    print(f"      Weights: semantic={plan['weights']['semantic']}, bm25={plan['weights']['bm25']}, graph={plan['weights']['graph']}")

route = query_plans[0].get('route', 'LOOKUP')

if route == "ANALYTICS":
    print("\n⚠️  ANALYTICS route detected - using graph aggregation pipeline")
    print("\nProceeding with ANALYTICS pipeline...")

    # Import and use GraphAnalytics
    from src.graph_analytics import GraphAnalytics

    analytics = GraphAnalytics(
        knowledge_graph=retriever.knowledge_graph,
        api_key=os.environ.get('MISTRAL_API_KEY')
    )

    print(f"\n{'='*100}")
    print("ANALYTICS PIPELINE")
    print(f"{'='*100}")

    result = analytics.analyze(query, verbose=True)

    print(f"\n{'='*100}")
    print("FINAL ANSWER")
    print(f"{'='*100}")
    print(f"\n{result['answer']}")

    print(f"\n{'='*100}")
    print("ANALYTICS DATA")
    print(f"{'='*100}")
    if result.get('aggregated_data'):
        import json
        print(json.dumps(result['aggregated_data'], indent=2))

    print("\n" + "="*100)
    print("TEST COMPLETE (ANALYTICS ROUTE)")
    print("="*100)
    exit(0)

# STEP 2: RETRIEVAL FOR EACH SUB-QUERY
print("\n" + "="*100)
print("STEP 2: HYBRID RETRIEVAL (PER SUB-QUERY)")
print("="*100)

all_results = []

for plan_idx, plan in enumerate(query_plans, 1):
    sub_query = plan['query']
    weights = plan['weights']

    print(f"\n{'-'*100}")
    print(f"Processing Sub-Query {plan_idx}/{len(query_plans)}: \"{sub_query}\"")
    print(f"{'-'*100}")

    # Detect user for this sub-query
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
        print(f"\n👤 Detected User: {users_detected[0]}")
        print(f"   User ID: {user_id}")
    else:
        print(f"\n👤 No specific user detected")

    # Check for temporal filtering
    date_range = retriever.temporal_analyzer.extract_date_range(sub_query)
    if date_range:
        print(f"📅 Date Range: {date_range[0]} to {date_range[1]}")
    else:
        print(f"📅 No temporal filtering")

    # 2A: QDRANT SEMANTIC SEARCH
    print(f"\n   2A. QDRANT SEMANTIC SEARCH")
    print(f"   {'-'*50}")

    semantic_results_raw = retriever.qdrant_search.search(
        sub_query,
        top_k=20,
        user_id=user_id,
        date_range=date_range
    )

    print(f"   ✓ Retrieved {len(semantic_results_raw)} results from Qdrant")

    if semantic_results_raw:
        print(f"\n   Top 5 Qdrant Results:")
        for i, r in enumerate(semantic_results_raw[:5], 1):
            print(f"      {i}. Score: {r['score']:.4f} | {r['user_name']} | {r['message'][:80]}...")

    # 2B: BM25 KEYWORD SEARCH
    print(f"\n   2B. BM25 KEYWORD SEARCH")
    print(f"   {'-'*50}")

    bm25_results = retriever.bm25_search.search(sub_query, top_k=20, user_id=user_id)

    if date_range:
        bm25_results = retriever._filter_by_date_range(bm25_results, date_range)

    print(f"   ✓ Retrieved {len(bm25_results)} results from BM25")

    if bm25_results:
        print(f"\n   Top 5 BM25 Results:")
        for i, (msg, score) in enumerate(bm25_results[:5], 1):
            print(f"      {i}. Score: {score:.4f} | {msg['user_name']} | {msg['message'][:80]}...")

    # 2C: KNOWLEDGE GRAPH SEARCH
    print(f"\n   2C. KNOWLEDGE GRAPH SEARCH")
    print(f"   {'-'*50}")

    graph_results = retriever._graph_search(sub_query, top_k=10, verbose=False)

    if date_range:
        graph_results = retriever._filter_by_date_range(graph_results, date_range)

    print(f"   ✓ Retrieved {len(graph_results)} results from Knowledge Graph")

    if graph_results:
        print(f"\n   Top 5 Graph Results:")
        for i, msg in enumerate(graph_results[:5], 1):
            print(f"      {i}. {msg['user_name']} | {msg['message'][:80]}...")

    # RECIPROCAL RANK FUSION (RRF)
    print(f"\n   2D. RECIPROCAL RANK FUSION (RRF)")
    print(f"   {'-'*50}")

    semantic_results = [(r, r['score']) for r in semantic_results_raw]

    fused_results = retriever._reciprocal_rank_fusion(
        semantic_results,
        bm25_results,
        graph_results,
        k=60,
        weights=weights
    )

    print(f"   ✓ RRF produced {len(fused_results)} unique results")
    print(f"   ✓ Taking top 20 for this sub-query")

    # Show top fused results
    print(f"\n   Top 10 Fused Results (after RRF):")
    for i, (msg, score) in enumerate(fused_results[:10], 1):
        print(f"      {i}. Score: {score:.6f} | {msg['user_name']} | {msg['message'][:80]}...")

    all_results.append(fused_results[:20])

# STEP 3: RESULT COMPOSITION
print(f"\n{'='*100}")
print("STEP 3: RESULT COMPOSITION")
print(f"{'='*100}")

print(f"\nComposing results from {len(all_results)} sub-queries:")
for i, results in enumerate(all_results, 1):
    print(f"   Sub-query {i}: {len(results)} results")

composed_results = composer.compose(
    all_results,
    strategy="auto",
    max_results=20,
    verbose=True
)

print(f"\n✅ Final Composed Results: {len(composed_results)} messages")

# Show user distribution
users = [msg['user_name'] for msg, score in composed_results]
user_dist = Counter(users)
print(f"\n📊 User Distribution in Results:")
for user, count in user_dist.most_common():
    print(f"   {user}: {count} messages")

print(f"\nTop 20 Composed Messages (sent to LLM):")
for i, (msg, score) in enumerate(composed_results[:20], 1):
    print(f"\n   {i}. Score: {score:.6f}")
    print(f"      User: {msg['user_name']}")
    print(f"      Date: {msg.get('timestamp', 'N/A')}")
    print(f"      Message: {msg['message'][:100]}...")

# STEP 4: LLM ANSWER GENERATION
print(f"\n{'='*100}")
print("STEP 4: LLM ANSWER GENERATION")
print(f"{'='*100}")

print(f"\nSending {len(composed_results)} context messages to Mistral LLM...")

answer_result = generator.generate_with_sources(
    query=query,
    composed_results=composed_results,
    verbose=True
)

# FINAL RESULT
print(f"\n{'='*100}")
print("FINAL ANSWER")
print(f"{'='*100}")
print(f"\n{answer_result['answer']}")

print(f"\n{'='*100}")
print("METADATA")
print(f"{'='*100}")
print(f"Model: {answer_result['model']}")
print(f"Tokens Used: {answer_result['tokens']}")
print(f"Number of Sources: {len(answer_result['sources'])}")

print(f"\n{'='*100}")
print("SOURCE MESSAGES")
print(f"{'='*100}")
for i, source in enumerate(answer_result['sources'][:10], 1):
    print(f"\n{i}. {source['user']} (score: {source['score']:.6f})")
    print(f"   {source['message']}")

print("\n" + "="*100)
print("TEST COMPLETE")
print("="*100)
