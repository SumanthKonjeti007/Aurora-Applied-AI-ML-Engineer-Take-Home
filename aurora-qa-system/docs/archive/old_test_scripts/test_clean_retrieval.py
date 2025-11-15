"""
Test hybrid retrieval with the new, clean knowledge graph
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_retrieval():
    """Test queries with new clean graph"""
    print("="*80)
    print("TESTING HYBRID RETRIEVAL WITH CLEAN GRAPH")
    print("="*80)

    # Initialize
    print("\nInitializing hybrid retriever...")
    retriever = HybridRetriever()

    # Test queries from assignment
    test_queries = [
        {
            "query": "How many cars does Vikram Desai have?",
            "expected": "Should find Vikram's car ownership from OWNS relationships"
        },
        {
            "query": "What are Hans's preferences?",
            "expected": "Should find Hans Müller's PREFERS relationships"
        },
        {
            "query": "Show me all bookings for Sophia",
            "expected": "Should find Sophia Al-Farsi's RENTED/BOOKED relationships"
        },
        {
            "query": "Which cities has Vikram visited?",
            "expected": "Should find Vikram's VISITED relationships"
        }
    ]

    print("\n" + "="*80)
    print("TEST QUERIES")
    print("="*80)

    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        expected = test["expected"]

        print(f"\n{'='*80}")
        print(f"Query {i}: \"{query}\"")
        print(f"Expected: {expected}")
        print(f"{'='*80}")

        # Search
        results = retriever.search(query, top_k=5, verbose=True)

        # Show results
        print(f"\n📊 Top {len(results)} results:")
        for j, (msg, score) in enumerate(results, 1):
            print(f"\n{j}. [Score: {score:.4f}] {msg['user_name']}")
            print(f"   {msg['message'][:150]}...")

    print("\n" + "="*80)
    print("✅ Retrieval test complete!")
    print("="*80)


if __name__ == "__main__":
    test_retrieval()
