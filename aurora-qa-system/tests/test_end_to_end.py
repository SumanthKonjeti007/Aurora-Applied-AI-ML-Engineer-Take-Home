"""
End-to-End Test: Both LOOKUP and ANALYTICS Pipelines
Verify complete system integration with routing
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qa_system import QASystem

print("=" * 80)
print("END-TO-END SYSTEM TEST - LOOKUP + ANALYTICS")
print("=" * 80)

# Initialize system
print("\nInitializing system...")
system = QASystem()

# Test queries: mix of LOOKUP and ANALYTICS
test_queries = [
    # LOOKUP queries (should use RAG pipeline)
    {
        "query": "Which clients have plans for January 2025?",
        "expected_route": "LOOKUP",
        "description": "Temporal query (Blocker #1 fix)"
    },
    {
        "query": "What is Layla's phone number?",
        "expected_route": "LOOKUP",
        "description": "Simple fact lookup"
    },

    # ANALYTICS queries (should use Graph pipeline)
    {
        "query": "Which clients requested reservations at the same restaurants?",
        "expected_route": "ANALYTICS",
        "description": "SAME pattern - requires aggregation"
    },
    {
        "query": "Who has the most restaurant bookings?",
        "expected_route": "ANALYTICS",
        "description": "MOST pattern - requires ranking"
    },
]

print("\n" + "=" * 80)
print("RUNNING END-TO-END TESTS")
print("=" * 80)

results_summary = []

for i, test in enumerate(test_queries, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}/{len(test_queries)}: {test['description']}")
    print(f"{'='*80}")
    print(f"Query: {test['query']}")
    print(f"Expected Route: {test['expected_route']}")
    print("-" * 80)

    # Run query
    result = system.answer(test['query'], verbose=False)

    # Check routing
    actual_route = result.get('route', 'UNKNOWN')
    route_correct = (actual_route == test['expected_route'])

    # Display results
    print(f"\n✓ Route: {actual_route} {'✅' if route_correct else '❌ WRONG'}")
    print(f"✓ Answer: {result['answer'][:150]}...")

    if actual_route == 'ANALYTICS':
        data = result.get('analytics_data', {})
        print(f"✓ Entities Found: {len(data)}")
        if data:
            print(f"✓ Top Entity: {list(data.items())[0] if data else 'None'}")
    else:
        print(f"✓ Sources Retrieved: {len(result.get('sources', []))}")

    # Summary
    results_summary.append({
        'query': test['query'],
        'expected': test['expected_route'],
        'actual': actual_route,
        'correct': route_correct
    })

    print("=" * 80)

# Overall summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

correct = sum(1 for r in results_summary if r['correct'])
total = len(results_summary)

print(f"\nRouting Accuracy: {correct}/{total} ({100*correct/total:.0f}%)")
print(f"\nResults:")
for r in results_summary:
    status = "✅" if r['correct'] else "❌"
    print(f"  {status} {r['query'][:50]}... → {r['actual']}")

if correct == total:
    print("\n✅ ALL TESTS PASSED - System working correctly!")
else:
    print(f"\n❌ {total - correct} tests failed - Check routing logic")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
