#!/usr/bin/env python3
"""
Test vehicle query with forced LOOKUP routing
"""
from src.hybrid_retriever import HybridRetriever
from src.query_processor import QueryProcessor

query = "What types of vehicles have members requested?"

print("=" * 80)
print(f"QUERY: {query}")
print("=" * 80)

# Initialize
retriever = HybridRetriever()
processor = QueryProcessor(name_resolver=retriever.name_resolver)

# Process query
query_plans = processor.process(query, verbose=False)

print(f"\n🔀 Router Decision: {query_plans[0]['route']}")
print(f"Query Type: {query_plans[0]['type']}")
print(f"Weights: {query_plans[0]['weights']}")

# Force it to use RAG retrieval (override ANALYTICS routing)
print(f"\n🔍 Forcing LOOKUP retrieval to see what RAG would find...\n")

# Retrieve with top_k=20
results = retriever.search(
    query=query,
    top_k=20,
    weights={'semantic': 1.5, 'bm25': 1.0, 'graph': 0.9},  # Use optimized weights
    query_type='AGGREGATION',
    verbose=False
)

print(f"📊 Retrieved {len(results)} results\n")

# Show user distribution
user_dist = {}
for msg, score in results:
    user = msg.get('user_name', msg.get('user', 'Unknown'))
    user_dist[user] = user_dist.get(user, 0) + 1

print(f"👥 User Distribution:")
for user, count in sorted(user_dist.items(), key=lambda x: -x[1]):
    print(f"   {user}: {count} messages")

# Show all messages
print(f"\n📝 All {len(results)} messages:\n")
for idx, (msg, score) in enumerate(results, 1):
    user = msg.get('user_name', msg.get('user', 'Unknown'))
    text = msg['message']
    dates = msg.get('normalized_dates', [])
    date_str = f" [Date: {dates[0]}]" if dates else ""

    # Check if message contains vehicle-related keywords
    vehicle_keywords = ['car', 'vehicle', 'limousine', 'limo', 'suv', 'sedan',
                        'van', 'bus', 'chauffeur', 'driver', 'transport', 'ride',
                        'jet', 'helicopter', 'yacht', 'boat']
    has_vehicle = any(keyword in text.lower() for keyword in vehicle_keywords)
    marker = "🚗" if has_vehicle else "  "

    print(f"{marker} {idx}. [{user}] (score: {score:.4f}){date_str}")
    print(f"     {text}")
    print()
