#!/usr/bin/env python3
"""
Force vehicle query through LOOKUP pipeline
"""
import os

from src.qa_system import QASystem

query = "What types of vehicles have members requested?"

print("="*80)
print(f"QUERY: {query}")
print("="*80)

system = QASystem()

# Override routing - force LOOKUP
print("\n🔀 FORCING LOOKUP PIPELINE (bypassing ANALYTICS routing)\n")

# Manually call the LOOKUP pipeline
query_plans = system.processor.process(query, verbose=False)

# Override route
query_plans[0]['route'] = 'LOOKUP'
query_plans[0]['type'] = 'AGGREGATION'
query_plans[0]['weights'] = {'semantic': 1.5, 'bm25': 1.0, 'graph': 0.9}

# Retrieve
all_results = []
for plan in query_plans:
    results = system.retriever.search(
        query=plan['query'],
        top_k=20,
        weights=plan['weights'],
        query_type=plan['type'],
        verbose=False
    )
    all_results.append(results)

# Compose
composed_results = system.composer.compose(
    all_results,
    strategy="auto",
    max_results=20,
    verbose=False
)

print(f"📊 Retrieved {len(composed_results)} messages\n")

# Show user distribution
user_dist = {}
for msg, score in composed_results:
    user = msg.get('user_name', 'Unknown')
    user_dist[user] = user_dist.get(user, 0) + 1

print(f"👥 User Distribution:")
for user, count in sorted(user_dist.items(), key=lambda x: -x[1]):
    print(f"   {user}: {count} messages")

# Generate answer with LLM
print(f"\n💬 GENERATING LLM ANSWER...\n")
answer_result = system.generator.generate_with_sources(
    query=query,
    composed_results=composed_results,
    verbose=False
)

print("="*80)
print("FINAL ANSWER (LOOKUP PIPELINE):")
print("="*80)
print(answer_result['answer'])
print(f"\nTokens: {answer_result.get('tokens', 'N/A')}")
