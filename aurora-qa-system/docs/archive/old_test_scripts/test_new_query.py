"""
Test QueryProcessor with new query: "How many children does Layla Kawaguchi have?"
"""
import sys
sys.path.insert(0, 'src')

from src.query_processor import QueryProcessor
from src.name_resolver import NameResolver
from src.knowledge_graph import KnowledgeGraph


def test_new_query():
    """Test QueryProcessor on new query"""
    print("="*80)
    print("QUERY PROCESSOR - NEW QUERY TEST")
    print("="*80)

    # Initialize
    print("\nInitializing...")
    kg = KnowledgeGraph()
    kg.load("data/knowledge_graph.pkl")

    name_resolver = NameResolver()
    for user_name in kg.user_index.keys():
        name_resolver.add_user(user_name)

    processor = QueryProcessor(name_resolver)
    print(f"✅ Ready with {name_resolver.total_users} users indexed")

    # Test query
    query = "How many children does Layla Kawaguchi have?"

    print(f"\n{'='*80}")
    print(f"TESTING: {query}")
    print(f"{'='*80}")

    # Process query
    plans = processor.process(query, verbose=True)

    # Show results
    print(f"\n{'='*80}")
    print("RESULT ANALYSIS")
    print(f"{'='*80}")
    print(f"\nNumber of sub-queries: {len(plans)}")

    for i, plan in enumerate(plans, 1):
        print(f"\nPlan {i}:")
        print(f"  Query: '{plan['query']}'")
        print(f"  Type: {plan['type']}")
        print(f"  Weights:")
        print(f"    - Semantic: {plan['weights']['semantic']}")
        print(f"    - BM25:     {plan['weights']['bm25']}")
        print(f"    - Graph:    {plan['weights']['graph']}")
        print(f"  Reason: {plan['reason']}")

    # Expected behavior analysis
    print(f"\n{'='*80}")
    print("EXPECTED BEHAVIOR")
    print(f"{'='*80}")
    print("\nThis query should:")
    print("  1. ✅ Detect entity: Layla Kawaguchi")
    print("  2. ✅ No decomposition (single entity)")
    print("  3. ? Classification:")
    print("     - 'children' is a specific attribute")
    print("     - BUT 'children' is NOT in specific_attrs list")
    print("     - So it might classify as ENTITY_SPECIFIC_BROAD")
    print("\nOptimal weights for this query:")
    print("  - High BM25 (keyword matching for 'Layla' + 'children')")
    print("  - Medium-low semantic (specific factual query, not conceptual)")
    print("  - Medium graph (might have family relationships)")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    test_new_query()
