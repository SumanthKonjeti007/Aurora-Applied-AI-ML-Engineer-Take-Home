"""
Test single query with verbose output to see all phases
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qa_system import QASystem

# Initialize system
print("Initializing system...\n")
system = QASystem()

# Test query
query = "What are Fatima El-Tahir's plans for next month?"

print("\n" + "="*80)
print(f"TESTING QUERY: {query}")
print("="*80 + "\n")

# Run with verbose to see all phases
result = system.answer(query, verbose=True)

print("\n" + "="*80)
print("FINAL RESULT")
print("="*80)
print(f"Route: {result['route']}")
print(f"Answer: {result['answer']}")

if result['route'] == 'ANALYTICS':
    print(f"\nAggregated Data:")
    for entity, users in list(result['analytics_data'].items())[:5]:
        print(f"  - {entity}: {len(users)} clients - {users}")
