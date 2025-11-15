"""
Test specific user query
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_query(query):
    """Test a single query"""
    print("="*80)
    print(f"QUERY: {query}")
    print("="*80)

    # Initialize
    print("\nInitializing hybrid retriever...")
    retriever = HybridRetriever()

    # Search
    print(f"\n🔍 Searching...")
    results = retriever.search(query, top_k=10, verbose=True)

    # Show detailed results
    print(f"\n{'='*80}")
    print(f"TOP {len(results)} RESULTS")
    print(f"{'='*80}")

    for i, (msg, score) in enumerate(results, 1):
        print(f"\n{i}. [RRF Score: {score:.4f}]")
        print(f"   User: {msg['user_name']}")
        print(f"   Message: {msg['message']}")
        print(f"   ID: {msg['id']}")
        print(f"   Timestamp: {msg.get('timestamp', 'N/A')}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "What did Sophia reserve?"

    test_query(query)
