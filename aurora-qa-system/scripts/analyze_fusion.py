"""
Analyze why hybrid fusion doesn't prioritize Hans's PREFERS messages
even though graph returns 10/10 Hans messages
"""
import sys
sys.path.append('src')

from hybrid_retriever import HybridRetriever

print("="*80)
print("HYBRID FUSION ANALYSIS")
print("="*80)

# Initialize
retriever = HybridRetriever()

query = "What are Hans's preferences?"
print(f"\nQuery: \"{query}\"\n")

# Get individual results
print("="*80)
print("INDIVIDUAL METHOD RESULTS")
print("="*80)

semantic_results = retriever.embedding_index.search(query, top_k=20)
bm25_results = retriever.bm25_search.search(query, top_k=20)
graph_results = retriever._graph_search(query, top_k=10, verbose=False)

print(f"\n1. GRAPH (10 results, weight=0.8):")
for i, msg in enumerate(graph_results[:5], 1):
    user = msg.get('user_name', '')
    text = msg['message'][:60]
    print(f"   {i}. [{user}] {text}...")

print(f"\n2. BM25 (20 results, weight=1.5):")
hans_count = 0
for i, (msg, score) in enumerate(bm25_results[:5], 1):
    user = msg.get('user_name', '')
    is_hans = 'Hans' in user
    if is_hans:
        hans_count += 1
    text = msg['message'][:60]
    marker = "✅" if is_hans else "❌"
    print(f"   {marker} {i}. [{user}] (score: {score:.2f}) {text}...")
print(f"   Hans in BM25 top-20: {sum(1 for m, _ in bm25_results if 'Hans' in m.get('user_name', ''))}/20")

print(f"\n3. SEMANTIC (20 results, weight=0.7):")
for i, (msg, score) in enumerate(semantic_results[:5], 1):
    user = msg.get('user_name', '')
    is_hans = 'Hans' in user
    text = msg['message'][:60]
    marker = "✅" if is_hans else "❌"
    print(f"   {marker} {i}. [{user}] (sim: {score:.2f}) {text}...")
print(f"   Hans in semantic top-20: {sum(1 for m, _ in semantic_results if 'Hans' in m.get('user_name', ''))}/20")

# Get hybrid
print("\n" + "="*80)
print("HYBRID RRF FUSION")
print("="*80)

hybrid_results = retriever.search(query, top_k=15, verbose=False)

print(f"\nTop-15 hybrid results:")
hans_in_hybrid = 0
for i, (msg, score) in enumerate(hybrid_results, 1):
    user = msg.get('user_name', '')
    is_hans = 'Hans' in user
    if is_hans:
        hans_in_hybrid += 1
    text = msg['message'][:60]
    marker = "✅" if is_hans else "❌"

    # Check which methods included this message
    in_graph = any(msg['id'] == gm['id'] for gm in graph_results)
    in_bm25 = any(msg['id'] == bm[0]['id'] for bm in bm25_results)
    in_semantic = any(msg['id'] == sm[0]['id'] for sm in semantic_results)

    sources = []
    if in_graph:
        sources.append("G")
    if in_bm25:
        sources.append("B")
    if in_semantic:
        sources.append("S")

    sources_str = "+".join(sources)

    print(f"{marker} {i:2d}. [{user[:20]:20s}] (RRF: {score:.4f}) [{sources_str:5s}]")
    print(f"       {text}...")

print(f"\n📊 Hans messages in hybrid top-15: {hans_in_hybrid}/15")

# Check if graph messages made it in
print("\n" + "="*80)
print("WHERE DID GRAPH'S PREFERS MESSAGES GO?")
print("="*80)

print("\nChecking if Hans's 10 PREFERS messages appear in hybrid top-15:")
for i, graph_msg in enumerate(graph_results[:10], 1):
    graph_id = graph_msg['id']
    text = graph_msg['message'][:60]

    # Find in hybrid results
    hybrid_rank = None
    for j, (hybrid_msg, score) in enumerate(hybrid_results, 1):
        if hybrid_msg['id'] == graph_id:
            hybrid_rank = j
            break

    if hybrid_rank and hybrid_rank <= 15:
        print(f"  ✅ PREFERS #{i}: Ranked #{hybrid_rank} in hybrid")
    elif hybrid_rank:
        print(f"  ⚠️  PREFERS #{i}: Ranked #{hybrid_rank} (outside top-15)")
    else:
        print(f"  ❌ PREFERS #{i}: Not in hybrid results at all!")
    print(f"      {text}...")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
print("\nThe problem:")
print("  • Graph returns 10/10 Hans PREFERS messages (perfect!)")
print("  • But they don't appear in BM25 or semantic results")
print("  • RRF formula: score = Σ weight_i × 1/(k + rank_i)")
print("  • Graph-only messages get: 0.8 × 1/(60 + rank)")
print("  • BM25+Semantic messages get: 1.5 × 1/(60 + rank) + 0.7 × 1/(60 + rank)")
print("  • Result: Messages in multiple methods always win")
print("\nSolution:")
print("  • Boost graph weight when relationship type is detected, OR")
print("  • User-aware RRF that prioritizes detected user, OR")
print("  • LLM query enhancement to make all methods focus on Hans")
print("="*80)
