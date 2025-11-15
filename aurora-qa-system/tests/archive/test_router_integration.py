"""
Test Router Integration with Query Processor
Verify routing works correctly in the actual system
"""
import os

from src.query_processor import QueryProcessor
from src.name_resolver import NameResolver
import json

# Initialize components
print("=" * 80)
print("ROUTER INTEGRATION TEST")
print("=" * 80)

print("\nInitializing components...")
name_resolver = NameResolver()
processor = QueryProcessor(name_resolver, use_llm=True)

# Test queries
test_queries = [
    ("Which clients have plans for January 2025?", "LOOKUP"),
    ("Which clients requested same restaurants?", "ANALYTICS"),
    ("What is Layla's phone number?", "LOOKUP"),
    ("Who has the most restaurant bookings?", "ANALYTICS"),
    ("Compare Layla and Lily's preferences", "LOOKUP"),
    ("What are the most popular destinations?", "ANALYTICS"),
]

print("\n" + "=" * 80)
print("ROUTING TESTS")
print("=" * 80)

all_correct = True

for query, expected_route in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)

    # Process query
    plans = processor.process(query, verbose=True)

    # Check routing
    actual_route = plans[0]['route']
    is_correct = (actual_route == expected_route)
    status = "✅" if is_correct else "❌"

    print(f"\n{status} Expected: {expected_route}, Got: {actual_route}")

    if not is_correct:
        all_correct = False

    print("=" * 80)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if all_correct:
    print("\n✅ ALL TESTS PASSED - Router integration working correctly!")
else:
    print("\n❌ SOME TESTS FAILED - Check routing logic")

print("\n" + "=" * 80)
