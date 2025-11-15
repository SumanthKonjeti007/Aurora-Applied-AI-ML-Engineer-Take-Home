"""
Test script to debug Louvre query retrieval failure
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.bm25_search import BM25Search

# Initialize BM25
print("Loading BM25 index...")
bm25 = BM25Search()
bm25.load("data/bm25")
print(f"Total messages: {len(bm25.messages)}\n")

# Search for Louvre
query = "Which clients requested a private tour of the Louvre?"
results = bm25.search(query, top_k=50, user_id=None)

print(f"Top 50 BM25 results for query: '{query}'\n")
print(f"Rank   Score      User                      Message")
print("="*120)

missing_users = ['Vikram Desai', 'Hans Müller', "Lily O'Sullivan"]
found_ranks = {user: [] for user in missing_users}

for i, (msg, score) in enumerate(results, 1):
    user = msg.get('user_name', 'Unknown')
    message = msg.get('message', '')[:70]

    # Track missing users
    if user in missing_users:
        found_ranks[user].append((i, score))
        print(f"{i:<6} {score:<10.4f} {user:<25} {message}...")

print("\n" + "="*120)
print("SUMMARY OF MISSING USERS:")
print("="*120)
for user in missing_users:
    if found_ranks[user]:
        ranks = ", ".join([f"#{rank} (score: {score:.2f})" for rank, score in found_ranks[user]])
        print(f"{user}: Found at ranks {ranks}")
    else:
        print(f"{user}: NOT FOUND in top 50")
