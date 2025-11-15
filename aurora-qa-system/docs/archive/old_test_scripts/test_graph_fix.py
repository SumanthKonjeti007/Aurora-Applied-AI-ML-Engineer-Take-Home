"""
Test to verify the graph filtering fix
This should demonstrate that "Hans front-row seats" only returns Hans's messages
"""
import sys
sys.path.append('src')

from hybrid_retriever import HybridRetriever

print("="*70)
print("TESTING GRAPH FILTERING FIX")
print("="*70)

# Initialize retriever (loads automatically)
print("\n📂 Loading retriever...")
retriever = HybridRetriever()
print("✅ Loaded")

# Test query
query = "Hans Müller front-row seats"
print(f"\n🔍 Query: \"{query}\"")
print("\n" + "-"*70)

# Get ONLY graph results to see the fix
print("\n📊 Graph search results (should ONLY show Hans):")
print("-"*70)

graph_results = retriever._graph_search(query, top_k=10, verbose=True)

print(f"\n✅ Found {len(graph_results)} messages from graph search")
print("\nResults:")
for i, msg in enumerate(graph_results, 1):
    user = msg.get('user_name', 'Unknown')
    text = msg['message'][:80]

    # Highlight if NOT Hans
    if 'Hans' not in user and 'Müller' not in user:
        print(f"\n❌ {i}. [{user}] - WRONG USER!")
        print(f"    {text}...")
    else:
        print(f"\n✅ {i}. [{user}]")
        print(f"    {text}...")

# Check if all results are Hans
hans_count = sum(1 for msg in graph_results
                 if 'Hans' in msg.get('user_name', '') or 'Müller' in msg.get('user_name', ''))

print("\n" + "="*70)
print("RESULT:")
print("="*70)
if hans_count == len(graph_results):
    print(f"✅ SUCCESS: All {len(graph_results)} results are from Hans Müller")
    print("   Graph filtering is working correctly!")
else:
    print(f"❌ FAIL: Only {hans_count}/{len(graph_results)} results are from Hans")
    print("   Other users' messages leaked through")

print("\n" + "="*70)

# Additional test: Check Hans's seat relationships
print("\n📊 Hans Müller's seat-related relationships:")
print("-"*70)

kg = retriever.knowledge_graph
hans_rels = kg.get_user_relationships("Hans Müller")
seat_rels = [r for r in hans_rels if 'seat' in r['object'].lower() or 'seat' in r['relationship'].lower()]

print(f"Total Hans relationships: {len(hans_rels)}")
print(f"Seat-related relationships: {len(seat_rels)}")

print("\nSeat relationships:")
for rel in seat_rels:
    print(f"  • {rel['relationship']} - {rel['object']}")

print("\n" + "="*70)
print("✅ Test complete")
print("="*70)
