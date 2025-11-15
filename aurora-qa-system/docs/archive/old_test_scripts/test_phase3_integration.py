"""
Test Phase 3: Name Resolver Integration with Hybrid Retriever

Tests that partial name queries correctly resolve to full names
"""
import sys
sys.path.insert(0, 'src')

from hybrid_retriever import HybridRetriever


def test_name_resolution_in_retrieval():
    """Test that name resolver works in hybrid retriever"""
    print("="*80)
    print("PHASE 3 INTEGRATION TEST: Name Resolver in Hybrid Retriever")
    print("="*80)

    # Initialize
    print("\nInitializing hybrid retriever...")
    retriever = HybridRetriever()

    # Test queries with partial names
    test_queries = [
        {
            "query": "What are Sophia's preferences?",
            "expected_user": "Sophia Al-Farsi",
            "description": "First name only with possessive"
        },
        {
            "query": "What does Hans prefer?",
            "expected_user": "Hans Müller",
            "description": "First name only"
        },
        {
            "query": "Al-Farsi's favorite restaurants",
            "expected_user": "Sophia Al-Farsi",
            "description": "Last name (hyphenated) with possessive"
        },
        {
            "query": "Show me Vikram's cars",
            "expected_user": "Vikram Desai",
            "description": "First name with possessive"
        },
        {
            "query": "What does Müller own?",
            "expected_user": "Hans Müller",
            "description": "Last name only"
        },
        {
            "query": "Desai's travel plans",
            "expected_user": "Vikram Desai",
            "description": "Last name with possessive"
        }
    ]

    print("\n" + "="*80)
    print("TESTING NAME RESOLUTION IN QUERIES")
    print("="*80)

    passed = 0
    failed = 0

    for test_case in test_queries:
        query = test_case["query"]
        expected_user = test_case["expected_user"]
        description = test_case["description"]

        print(f"\n{'='*80}")
        print(f"Query: \"{query}\"")
        print(f"Expected user: {expected_user}")
        print(f"Description: {description}")

        # Search with verbose to see user detection
        results = retriever.search(query, top_k=5, verbose=True)

        # Check if results contain messages from the expected user
        found_users = set()
        for msg, score in results:
            found_users.add(msg['user_name'])

        print(f"\nUsers in results: {found_users}")

        if expected_user in found_users:
            print(f"✅ PASS: Found messages from {expected_user}")
            passed += 1
        else:
            print(f"❌ FAIL: Expected {expected_user} but found {found_users}")
            failed += 1

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Passed: {passed}/{passed + failed}")
    print(f"❌ Failed: {failed}/{passed + failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("   ✅ Partial name resolution working")
        print("   ✅ Possessive handling working")
        print("   ✅ Hyphenated names working")
        print("   ✅ Integration with retriever successful")
        print("\n✅ PHASE 3 COMPLETE!")
    else:
        print(f"\n⚠️  {failed} test(s) failed - needs investigation")

    print("="*80)

    return passed, failed


if __name__ == "__main__":
    test_name_resolution_in_retrieval()
