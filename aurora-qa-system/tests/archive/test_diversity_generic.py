"""Test diversity filter works generically for different query types"""
from src.hybrid_retriever import HybridRetriever

# Initialize
retriever = HybridRetriever()

# Different query types to test diversity
test_queries = [
    ("AGGREGATION", "Which clients requested a private tour of the Louvre?"),
    ("USER-SPECIFIC", "What are Fatima El-Tahir's plans for next month?"),
    ("PREFERENCE", "Which clients prefer Italian cuisine?"),
    ("TEMPORAL", "Who had plans on March 25th, 2025?"),
    ("MULTI-CONSTRAINT", "Who asked for opera tickets and mentioned travel dates?"),
    ("LOCATION", "Which clients have visited Paris?"),
    ("COMPLAINT", "Who filed complaints about billing?"),
]

print("="*80)
print("DIVERSITY FILTER - GENERIC TEST")
print("="*80)
print("\nTesting diversity filter across different query types...")
print("Expected: Max 2 messages per user in all cases\n")

for query_type, query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query Type: {query_type}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    # Search with verbose to see diversity in action
    results = retriever.search(query, top_k=10, verbose=False)
    
    # Analyze user distribution
    user_dist = {}
    for msg, score in results:
        user = msg.get('user_name', 'Unknown')
        user_dist[user] = user_dist.get(user, 0) + 1
    
    # Check diversity
    max_count = max(user_dist.values()) if user_dist else 0
    total_messages = len(results)
    unique_users = len(user_dist)
    
    print(f"✓ Retrieved: {total_messages} messages")
    print(f"✓ Unique users: {unique_users}")
    print(f"✓ User distribution: {user_dist}")
    
    if max_count > 2:
        print(f"❌ DIVERSITY VIOLATION: One user has {max_count} messages (max should be 2)")
        print(f"   GENERIC FIX FAILED!")
    else:
        print(f"✅ Diversity: PASS (max {max_count} per user, within limit of 2)")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print("If all queries show '✅ Diversity: PASS', the fix is GENERIC.")
print("If any show '❌ DIVERSITY VIOLATION', the fix is QUERY-SPECIFIC (bad).")
print(f"{'='*80}")
