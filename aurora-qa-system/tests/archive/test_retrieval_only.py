#!/usr/bin/env python3
"""
Test retrieval without LLM generation (to avoid rate limits)
Shows what data is retrieved before generating an answer
"""

import sys
from src.hybrid_retriever import HybridRetriever
from src.query_processor import QueryProcessor
from src.knowledge_graph import KnowledgeGraph

def test_retrieval(query):
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    # Initialize components
    print("\n🔧 Initializing components...")

    retriever = HybridRetriever(
        embedding_path="data/embeddings",
        bm25_path="data/bm25",
        graph_path="data/knowledge_graph.pkl"
    )

    processor = QueryProcessor(name_resolver=retriever.name_resolver)

    # Process query
    print(f"\n📋 Processing query...")
    query_plans = processor.process(query)

    for i, plan in enumerate(query_plans, 1):
        print(f"\n--- Sub-query {i}/{len(query_plans)} ---")
        print(f"Query: {plan['query']}")
        print(f"Route: {plan['route']}")
        print(f"Type: {plan['type']}")
        print(f"Weights: {plan['weights']}")

        if plan['route'] == 'ANALYTICS':
            print("⚠️ ANALYTICS query - would use Graph Analytics pipeline")
            continue

        # Retrieve
        print(f"\n🔍 Retrieving results...")
        results = retriever.search(
            query=plan['query'],
            top_k=10,
            weights=plan['weights'],
            query_type=plan['type'],
            verbose=False
        )

        print(f"\n📊 Retrieved {len(results)} results:")

        # Show user distribution
        user_dist = {}
        for msg, score in results:
            user = msg.get('user_name', msg.get('user', 'Unknown'))
            user_dist[user] = user_dist.get(user, 0) + 1

        print(f"\n👥 User Distribution:")
        for user, count in sorted(user_dist.items(), key=lambda x: -x[1]):
            print(f"   {user}: {count} messages")

        # Show top messages
        print(f"\n📝 All {len(results)} messages:")
        for idx, (msg, score) in enumerate(results, 1):
            user = msg.get('user_name', msg.get('user', 'Unknown'))
            text = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
            dates = msg.get('normalized_dates', [])
            date_str = f" [Date: {dates[0]}]" if dates else ""
            print(f"\n   {idx}. [{user}] (score: {score:.4f}){date_str}")
            print(f"      {text}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Who requested a hot-air balloon ride and when?"

    test_retrieval(query)
