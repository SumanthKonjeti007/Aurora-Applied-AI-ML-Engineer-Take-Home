"""
Test: What does current RAG pipeline return for "same restaurants" query?
This demonstrates why this query NEEDS the analytics pipeline
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qa_system import QASystem

query = "Which clients have requested reservations at the same restaurants?"

print("=" * 80)
print("TESTING CURRENT RAG PIPELINE (LOOKUP ROUTE)")
print("=" * 80)
print(f"\nQuery: {query}\n")

print("Initializing QA System...")
system = QASystem()

print("\nExecuting query through current RAG pipeline...\n")
print("-" * 80)

result = system.answer(query, verbose=False)

print(f"\nAnswer from RAG Pipeline:")
print(f"{result['answer']}")

print(f"\n\nSources Retrieved: {len(result['sources'])} messages")
print("\nRetrieved Messages:")
for i, source in enumerate(result['sources'][:5], 1):
    user = source['user_name']
    msg = source['message'][:80]
    print(f"  {i}. {user}: {msg}...")

print("\n" + "=" * 80)
print("COMPARISON WITH GROUND TRUTH")
print("=" * 80)

print("\nGround Truth (from graph analysis earlier):")
print("  ✓ Osteria Francescana: Hans Müller, Lily O'Sullivan, Sophia Al-Farsi (3 clients)")
print("  ✓ Le Bernardin: Lily O'Sullivan, Fatima El-Tahir (2 clients)")

print("\nDid RAG pipeline find this?")
# Check if answer mentions these restaurants
answer_lower = result['answer'].lower()
found_osteria = 'osteria' in answer_lower
found_bernardin = 'bernardin' in answer_lower

print(f"  - Found Osteria Francescana: {'✅' if found_osteria else '❌'}")
print(f"  - Found Le Bernardin: {'✅' if found_bernardin else '❌'}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if found_osteria and found_bernardin:
    print("\n✅ RAG pipeline found the answer (got lucky with top-10)")
else:
    print("\n❌ RAG pipeline FAILED to find complete answer")
    print("   Reason: Can only see top-10 messages, misses data")
    print("   Solution: Route to Graph Analytics pipeline instead")

print("\n" + "=" * 80)
