"""Test conditional diversity: AGGREGATION vs ENTITY_SPECIFIC"""
from src.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()

print("="*80)
print("CONDITIONAL DIVERSITY TEST")
print("="*80)

# Test 1: ENTITY_SPECIFIC (should allow many messages from Fatima)
print("\n" + "="*80)
print("TEST 1: ENTITY_SPECIFIC Query")
print("="*80)
print("Query: 'What are Fatima El-Tahir's plans for next month?'")
print("Expected: High concentration of Fatima messages (up to 10)")
print("-"*80)

results = retriever.search(
    "What are Fatima El-Tahir's plans for next month?",
    top_k=10,
    query_type="ENTITY_SPECIFIC_BROAD",  # User-specific query
    verbose=False
)

user_dist = {}
for msg, score in results:
    user = msg.get('user_name', 'Unknown')
    user_dist[user] = user_dist.get(user, 0) + 1

print(f"✓ Retrieved: {len(results)} messages")
print(f"✓ User distribution: {user_dist}")

fatima_count = user_dist.get('Fatima El-Tahir', 0)
if fatima_count >= 7:
    print(f"✅ PASS: Fatima has {fatima_count} messages (sufficient for complete answer)")
else:
    print(f"❌ FAIL: Fatima has only {fatima_count} messages (need >= 7 for complete answer)")

# Test 2: AGGREGATION (should limit to 2 per user for diversity)
print("\n" + "="*80)
print("TEST 2: AGGREGATION Query")
print("="*80)
print("Query: 'Which clients requested a private tour of the Louvre?'")
print("Expected: Diverse users, max 2 messages each")
print("-"*80)

results = retriever.search(
    "Which clients requested a private tour of the Louvre?",
    top_k=10,
    query_type="AGGREGATION",  # Aggregation query
    verbose=False
)

user_dist = {}
for msg, score in results:
    user = msg.get('user_name', 'Unknown')
    user_dist[user] = user_dist.get(user, 0) + 1

print(f"✓ Retrieved: {len(results)} messages")
print(f"✓ User distribution: {user_dist}")

max_count = max(user_dist.values()) if user_dist else 0
unique_users = len(user_dist)

if max_count <= 2 and unique_users >= 7:
    print(f"✅ PASS: Diversity enforced (max {max_count} per user, {unique_users} unique users)")
else:
    print(f"❌ FAIL: Diversity violation (max {max_count} per user, {unique_users} unique users)")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("Conditional diversity allows:")
print("  - ENTITY_SPECIFIC queries: High user concentration (max 10) for complete context")
print("  - AGGREGATION queries: User diversity (max 2) for broad coverage")
print("="*80)
