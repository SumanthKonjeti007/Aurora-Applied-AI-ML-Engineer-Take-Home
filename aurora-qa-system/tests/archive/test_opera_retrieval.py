"""
Debug Query 7: Opera/symphony/ballet tickets with travel dates
"""
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from src.bm25_search import BM25Search
from src.qdrant_search import QdrantSearch

query = "Who asked for opera/symphony/ballet tickets and also mentioned travel dates near those events?"

print("="*120)
print("QUERY 7 RETRIEVAL ANALYSIS")
print("="*120)
print(f"Query: {query}\n")

# Ground truth users
ground_truth = ['Fatima El-Tahir', 'Layla Kawaguchi', 'Hans Müller']

# BM25 Search
print("\n" + "="*120)
print("BM25 RANKINGS")
print("="*120)

bm25 = BM25Search()
bm25.load("data/bm25")
bm25_results = bm25.search(query, top_k=50, user_id=None)

bm25_ranks = {user: [] for user in ground_truth}
for i, (msg, score) in enumerate(bm25_results, 1):
    user = msg.get('user_name', 'Unknown')
    if user in ground_truth:
        message = msg.get('message', '')[:80]
        bm25_ranks[user].append((i, score, message))
        if i <= 20:  # Print top 20 only
            print(f"#{i:<4} {score:<10.4f} {user:<25} {message}...")

print("\nBM25 Summary:")
for user in ground_truth:
    if bm25_ranks[user]:
        ranks = ", ".join([f"#{rank}" for rank, _, _ in bm25_ranks[user][:3]])
        print(f"  {user}: {ranks}")
    else:
        print(f"  {user}: NOT FOUND in top 50")

# Qdrant Search
print("\n" + "="*120)
print("QDRANT RANKINGS")
print("="*120)

qdrant = QdrantSearch()
qdrant_results = qdrant.search(query, top_k=50, user_id=None, date_range=None)

qdrant_ranks = {user: [] for user in ground_truth}
for i, result in enumerate(qdrant_results, 1):
    user = result.get('user_name', 'Unknown')
    if user in ground_truth:
        score = result.get('score', 0.0)
        message = result.get('message', '')[:80]
        qdrant_ranks[user].append((i, score, message))
        if i <= 20:  # Print top 20 only
            print(f"#{i:<4} {score:<10.4f} {user:<25} {message}...")

print("\nQdrant Summary:")
for user in ground_truth:
    if qdrant_ranks[user]:
        ranks = ", ".join([f"#{rank}" for rank, _, _ in qdrant_ranks[user][:3]])
        print(f"  {user}: {ranks}")
    else:
        print(f"  {user}: NOT FOUND in top 50")

# Analysis
print("\n" + "="*120)
print("RRF FUSION IMPACT ANALYSIS")
print("="*120)

for user in ground_truth:
    print(f"\n{user}:")

    if bm25_ranks[user]:
        best_bm25 = bm25_ranks[user][0]
        print(f"  Best BM25: #{best_bm25[0]} (score: {best_bm25[1]:.4f})")
        print(f"    Message: {best_bm25[2]}...")
    else:
        print(f"  BM25: NOT FOUND")

    if qdrant_ranks[user]:
        best_qdrant = qdrant_ranks[user][0]
        print(f"  Best Qdrant: #{best_qdrant[0]} (score: {best_qdrant[1]:.4f})")
        print(f"    Message: {best_qdrant[2]}...")
    else:
        print(f"  Qdrant: NOT FOUND")

    # RRF score estimate (simplified)
    if bm25_ranks[user] and qdrant_ranks[user]:
        bm25_rank = bm25_ranks[user][0][0]
        qdrant_rank = qdrant_ranks[user][0][0]
        rrf_score = (1/(60+qdrant_rank) + 1/(60+bm25_rank)) / 2
        print(f"  Estimated RRF score: {rrf_score:.6f}")
        print(f"    (Likely position: {int(1/rrf_score) if rrf_score > 0 else 'unknown'})")
