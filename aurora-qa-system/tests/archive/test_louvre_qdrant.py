"""
Test Qdrant rankings for Louvre query
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.qdrant_search import QdrantSearch

# Initialize Qdrant
print("Connecting to Qdrant...")
qdrant = QdrantSearch()

# Search for Louvre
query = "Which clients requested a private tour of the Louvre?"
results = qdrant.search(query, top_k=50, user_id=None, date_range=None)

print(f"\nTop 50 Qdrant results for query: '{query}'\n")
print(f"Rank   Score      User                      Message")
print("="*120)

missing_users = ['Vikram Desai', 'Hans Müller', "Lily O'Sullivan"]
found_ranks = {user: [] for user in missing_users}

for i, result in enumerate(results, 1):
    user = result.get('user_name', 'Unknown')
    score = result.get('score', 0.0)
    message = result.get('message', '')[:70]

    # Track missing users
    if user in missing_users:
        found_ranks[user].append((i, score))
        print(f"{i:<6} {score:<10.4f} {user:<25} {message}...")

print("\n" + "="*120)
print("SUMMARY OF MISSING USERS IN QDRANT:")
print("="*120)
for user in missing_users:
    if found_ranks[user]:
        ranks = ", ".join([f"#{rank} (score: {score:.4f})" for rank, score in found_ranks[user]])
        print(f"{user}: Found at ranks {ranks}")
    else:
        print(f"{user}: NOT FOUND in top 50 Qdrant results")
