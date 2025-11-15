"""Verify March 25th query still works with conditional diversity"""
from src.hybrid_retriever import HybridRetriever

retriever = HybridRetriever()

print("="*80)
print("TEST: March 25th Query (AGGREGATION)")
print("="*80)

results = retriever.search(
    "Who had plans on March 25th, 2025?",
    top_k=10,
    query_type="AGGREGATION",  # Temporal aggregation query
    verbose=False
)

user_dist = {}
for msg, score in results:
    user = msg.get('user_name', 'Unknown')
    user_dist[user] = user_dist.get(user, 0) + 1

print(f"✓ Retrieved: {len(results)} messages")
print(f"✓ User distribution: {user_dist}")

# Check if Thiago is included (was missing before diversity fix)
if 'Thiago Monteiro' in user_dist:
    print(f"✅ PASS: Thiago Monteiro included (was missing before fix)")
else:
    print(f"❌ FAIL: Thiago Monteiro still missing")

# Check if Armand is included
if 'Armand Dupont' in user_dist:
    print(f"✅ PASS: Armand Dupont included")
else:
    print(f"❌ FAIL: Armand Dupont missing")

# Check diversity
max_count = max(user_dist.values()) if user_dist else 0
if max_count <= 2:
    print(f"✅ PASS: Diversity enforced (max {max_count} per user)")
else:
    print(f"⚠️  WARNING: Some user has {max_count} messages (expected max 2)")

print("="*80)
