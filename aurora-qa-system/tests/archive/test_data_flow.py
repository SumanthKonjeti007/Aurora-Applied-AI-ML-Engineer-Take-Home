"""
Efficient data flow test - shows key decisions without verbose output

Usage: python test_data_flow.py "Your query here"
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qa_system import QASystem
import sys

# Get query from command line argument
if len(sys.argv) < 2:
    print("Usage: python test_data_flow.py \"Your query here\"")
    sys.exit(1)

query = sys.argv[1]

print("="*80)
print(f"QUERY: {query}")
print("="*80)

# Initialize and run
system = QASystem()
result = system.answer(query, verbose=False)

# Extract key info
route = result['route']
query_plans = result.get('query_plans', [{}])
query_type = query_plans[0].get('type', 'UNKNOWN') if query_plans else 'UNKNOWN'
sources = result.get('sources', [])

print(f"\n📍 DATA FLOW:")
print(f"   Router: {route}")
print(f"   Type: {query_type}")

if route == 'ANALYTICS':
    print(f"   Pipeline: Graph Analytics")
    analytics_data = result.get('analytics_data', {})
    print(f"   Aggregated Entities: {len(analytics_data)}")
else:
    print(f"   Pipeline: RAG (Qdrant + BM25 + Graph + RRF)")
    print(f"   Retrieved: {len(sources)} messages")

    if sources:
        # Show user distribution
        from collections import Counter
        if isinstance(sources[0], tuple):
            users = [s[0].get('user', s[0].get('user_name', 'Unknown')) for s in sources]
        else:
            users = [s.get('user', s.get('user_name', 'Unknown')) for s in sources]
        user_dist = Counter(users)
        print(f"   User Distribution: {dict(user_dist)}")

print(f"\n💬 ANSWER:")
print(f"   {result['answer']}")

print(f"\n📊 TOKENS:")
if 'tokens' in result:
    print(f"   Total: {result['tokens'].get('total', 'N/A')}")
