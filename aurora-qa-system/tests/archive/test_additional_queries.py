"""
Additional Test Queries - Verify System Robustness
Test edge cases and various query patterns
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qa_system import QASystem

print("=" * 80)
print("ADDITIONAL ROBUSTNESS TESTS")
print("=" * 80)

# Initialize system
print("\nInitializing system...")
system = QASystem()

# Additional test queries
test_queries = [
    # ANALYTICS queries
    ("What are the most popular destinations?", "ANALYTICS"),
    ("Which clients visited the same hotels?", "ANALYTICS"),
    ("Find clients with similar spa preferences", "ANALYTICS"),

    # LOOKUP queries
    ("Which clients visited Paris?", "LOOKUP"),
    ("Compare Layla and Lily's preferences", "LOOKUP"),
    ("Which clients have billing issues?", "LOOKUP"),
    ("Which clients have plans for December 2025?", "LOOKUP"),

    # Edge cases
    ("Does anyone prefer aisle seats?", "LOOKUP"),
    ("Show me everyone who visited Paris", "LOOKUP"),
]

print("\n" + "=" * 80)
print("RUNNING ADDITIONAL TESTS")
print("=" * 80)

results = []

for i, (query, expected_route) in enumerate(test_queries, 1):
    print(f"\n[{i}/{len(test_queries)}] {query}")
    print("-" * 80)

    try:
        result = system.answer(query, verbose=False)
        actual_route = result.get('route', 'UNKNOWN')
        correct = (actual_route == expected_route)

        status = "✅" if correct else "❌"
        print(f"{status} Route: {actual_route} (expected {expected_route})")
        print(f"   Answer: {result['answer'][:80]}...")

        if actual_route == 'ANALYTICS':
            data = result.get('analytics_data', {})
            print(f"   Aggregated Entities: {len(data)}")

        results.append({
            'query': query,
            'expected': expected_route,
            'actual': actual_route,
            'correct': correct
        })

    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")
        results.append({
            'query': query,
            'expected': expected_route,
            'actual': 'ERROR',
            'correct': False
        })

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

correct = sum(1 for r in results if r['correct'])
total = len(results)

print(f"\nTotal Tests: {total}")
print(f"Passed: {correct}")
print(f"Failed: {total - correct}")
print(f"Accuracy: {100 * correct / total:.1f}%")

print("\nDetailed Results:")
for r in results:
    status = "✅" if r['correct'] else "❌"
    print(f"  {status} {r['query'][:45]:45s} → {r['actual']:10s} (expected {r['expected']})")

if correct == total:
    print("\n✅ ALL ADDITIONAL TESTS PASSED!")
else:
    print(f"\n⚠️  {total - correct} tests failed")

print("\n" + "=" * 80)
