"""
Test query: What are Hans's preferences?
Tests preference detection across all retrieval methods
"""
import sys
sys.path.append('src')

from hybrid_retriever import HybridRetriever

print("="*80)
print("TEST QUERY: What are Hans's preferences?")
print("="*80)

# Initialize retriever
print("\n🔧 Loading retriever...")
retriever = HybridRetriever()
print("✅ Ready\n")

query = "What are Hans's preferences?"

# Test 1: Graph search (should find PREFERS/FAVORITE relationships)
print("="*80)
print("1. GRAPH SEARCH (Knowledge Graph)")
print("="*80)
print(f"Query: \"{query}\"\n")

graph_results = retriever._graph_search(query, top_k=10, verbose=True)

print(f"\n📊 Graph found {len(graph_results)} results:")
for i, msg in enumerate(graph_results[:5], 1):
    user = msg.get('user_name', 'Unknown')
    text = msg['message'][:100]
    print(f"\n{i}. [{user}]")
    print(f"   {text}...")

# Test 2: Check Hans's preference relationships directly
print("\n" + "="*80)
print("2. DIRECT GRAPH QUERY (Hans's preference relationships)")
print("="*80)

kg = retriever.knowledge_graph
hans_all = kg.get_user_relationships("Hans Müller")
hans_prefs = kg.get_user_relationships("Hans Müller", "PREFERS")
hans_favs = kg.get_user_relationships("Hans Müller", "FAVORITE")

print(f"\nHans Müller's relationships:")
print(f"  Total: {len(hans_all)}")
print(f"  PREFERS: {len(hans_prefs)}")
print(f"  FAVORITE: {len(hans_favs)}")

if hans_prefs:
    print(f"\n📋 PREFERS relationships:")
    for rel in hans_prefs[:10]:
        print(f"  • {rel['object']}")

if hans_favs:
    print(f"\n📋 FAVORITE relationships:")
    for rel in hans_favs[:10]:
        print(f"  • {rel['object']}")

# Test 3: BM25 search
print("\n" + "="*80)
print("3. BM25 KEYWORD SEARCH")
print("="*80)
print(f"Query: \"{query}\"\n")

bm25_results = retriever.bm25_search.search(query, top_k=10)

print(f"📊 BM25 found {len(bm25_results)} results:")
for i, (msg, score) in enumerate(bm25_results[:5], 1):
    user = msg.get('user_name', 'Unknown')
    text = msg['message'][:100]
    is_hans = 'Hans' in user or 'Müller' in user
    marker = "✅" if is_hans else "❌"
    print(f"\n{marker} {i}. [{user}] (score: {score:.4f})")
    print(f"   {text}...")

hans_in_bm25 = sum(1 for msg, _ in bm25_results if 'Hans' in msg.get('user_name', '') or 'Müller' in msg.get('user_name', ''))
print(f"\n📊 Hans messages in BM25 top-10: {hans_in_bm25}/10")

# Test 4: Semantic search
print("\n" + "="*80)
print("4. SEMANTIC SEARCH (Embeddings)")
print("="*80)
print(f"Query: \"{query}\"\n")

semantic_results = retriever.embedding_index.search(query, top_k=10)

print(f"📊 Semantic found {len(semantic_results)} results:")
for i, (msg, score) in enumerate(semantic_results[:5], 1):
    user = msg.get('user_name', 'Unknown')
    text = msg['message'][:100]
    is_hans = 'Hans' in user or 'Müller' in user
    marker = "✅" if is_hans else "❌"
    print(f"\n{marker} {i}. [{user}] (similarity: {score:.4f})")
    print(f"   {text}...")

hans_in_semantic = sum(1 for msg, _ in semantic_results if 'Hans' in msg.get('user_name', '') or 'Müller' in msg.get('user_name', ''))
print(f"\n📊 Hans messages in semantic top-10: {hans_in_semantic}/10")

# Test 5: Hybrid search (RRF fusion)
print("\n" + "="*80)
print("5. HYBRID SEARCH (RRF Fusion)")
print("="*80)
print(f"Query: \"{query}\"\n")

hybrid_results = retriever.search(query, top_k=10, verbose=True)

print(f"\n📊 Hybrid fusion top-10 results:")
for i, (msg, score) in enumerate(hybrid_results, 1):
    user = msg.get('user_name', 'Unknown')
    text = msg['message'][:100]
    is_hans = 'Hans' in user or 'Müller' in user
    marker = "✅" if is_hans else "❌"
    print(f"\n{marker} {i}. [{user}] (RRF score: {score:.4f})")
    print(f"   {text}...")

hans_in_hybrid = sum(1 for msg, _ in hybrid_results if 'Hans' in msg.get('user_name', '') or 'Müller' in msg.get('user_name', ''))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n📊 Hans messages in top-10:")
print(f"  Graph:    {len(graph_results)} / 10 (filtered for Hans only)")
print(f"  BM25:     {hans_in_bm25} / 10")
print(f"  Semantic: {hans_in_semantic} / 10")
print(f"  Hybrid:   {hans_in_hybrid} / 10")

print(f"\n📊 Hans's preference data:")
print(f"  PREFERS relationships: {len(hans_prefs)}")
print(f"  FAVORITE relationships: {len(hans_favs)}")

if hans_in_hybrid >= 7:
    print("\n✅ EXCELLENT: Hybrid retrieval strongly focuses on Hans")
elif hans_in_hybrid >= 5:
    print("\n✅ GOOD: Hybrid retrieval mostly focuses on Hans")
elif hans_in_hybrid >= 3:
    print("\n⚠️  FAIR: Some Hans results, but mixed with other users")
else:
    print("\n❌ POOR: Hybrid retrieval not focusing on Hans")

print("\n" + "="*80)
print("✅ Test complete")
print("="*80)
