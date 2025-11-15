"""
Investigate Graph Search for Vikram + Cars

Questions:
1. What relationships exist for Vikram Desai in the knowledge graph?
2. Are there any car-related entities/relationships?
3. What messages does Vikram have about cars?
4. Why did graph search only return 1 result (Oscars tickets)?
"""
import sys
sys.path.insert(0, 'src')

from src.knowledge_graph import KnowledgeGraph
from src.embeddings import EmbeddingIndex
from src.hybrid_retriever import HybridRetriever


def investigate_vikram_cars():
    """Investigate Vikram's car-related data in graph"""

    print("="*100)
    print("GRAPH SEARCH INVESTIGATION: Vikram Desai + Cars")
    print("="*100)

    # Load knowledge graph
    print("\nLoading knowledge graph...")
    kg = KnowledgeGraph()
    kg.load("data/knowledge_graph.pkl")

    # Load embeddings for full message access
    embedding_index = EmbeddingIndex()
    embedding_index.load("data/embeddings")

    print(f"✅ Loaded {len(embedding_index.messages)} messages")
    print(f"✅ Knowledge graph has {len(kg.user_index)} users")

    # ========== STEP 1: All Vikram's relationships ==========
    print("\n" + "="*100)
    print("STEP 1: All Vikram Desai's Relationships in Knowledge Graph")
    print("="*100)

    vikram_rels = kg.get_user_relationships("Vikram Desai")

    print(f"\nTotal relationships for Vikram: {len(vikram_rels)}")

    # Group by relationship type
    rel_types = {}
    for rel in vikram_rels:
        rel_type = rel['relationship']
        if rel_type not in rel_types:
            rel_types[rel_type] = []
        rel_types[rel_type].append(rel)

    print(f"\nRelationship types breakdown:")
    for rel_type, rels in sorted(rel_types.items(), key=lambda x: -len(x[1])):
        print(f"  {rel_type}: {len(rels)} relationships")

    # ========== STEP 2: Search for car-related entities ==========
    print("\n" + "="*100)
    print("STEP 2: Car-Related Entities in Vikram's Relationships")
    print("="*100)

    # First, check the structure of relationships
    if vikram_rels:
        print(f"\nSample relationship structure:")
        print(f"Keys: {vikram_rels[0].keys()}")
        print(f"Sample: {vikram_rels[0]}")

    car_keywords = ['car', 'cars', 'vehicle', 'auto', 'bmw', 'mercedes', 'tesla',
                   'porsche', 'bentley', 'ferrari', 'lamborghini', 'audi']

    car_related_rels = []
    for rel in vikram_rels:
        # Check all values in the relationship for car keywords
        rel_str = str(rel).lower()
        if any(keyword in rel_str for keyword in car_keywords):
            car_related_rels.append(rel)

    print(f"\nFound {len(car_related_rels)} car-related relationships for Vikram")

    if car_related_rels:
        print("\nCar-related relationships:")
        for i, rel in enumerate(car_related_rels[:10], 1):
            print(f"\n{i}. Relationship: {rel}")

            # Get full message
            msg_id = rel.get('message_id')
            if msg_id:
                msg = next((m for m in embedding_index.messages if m['id'] == msg_id), None)
                if msg:
                    print(f"   Message: {msg['message'][:100]}...")
    else:
        print("❌ NO car-related entities found in Vikram's relationships!")

    # ========== STEP 3: Search messages directly for "car" ==========
    print("\n" + "="*100)
    print("STEP 3: Vikram's Messages Containing 'car' (Direct Search)")
    print("="*100)

    vikram_messages = [msg for msg in embedding_index.messages
                      if msg['user_name'] == "Vikram Desai"]

    print(f"\nTotal messages from Vikram: {len(vikram_messages)}")

    car_messages = [msg for msg in vikram_messages
                   if any(keyword in msg['message'].lower() for keyword in car_keywords)]

    print(f"Messages mentioning 'car' keywords: {len(car_messages)}")

    if car_messages:
        print("\nVikram's car-related messages:")
        for i, msg in enumerate(car_messages[:10], 1):
            print(f"\n{i}. {msg['message']}")
            print(f"   Message ID: {msg['id']}")
    else:
        print("❌ NO messages from Vikram mentioning cars!")

    # ========== STEP 4: Why did graph search return only 1 result? ==========
    print("\n" + "="*100)
    print("STEP 4: Why Graph Search Failed")
    print("="*100)

    # Simulate graph search
    retriever = HybridRetriever()
    query = "How many cars does Vikram Desai?"

    print(f"\nSimulating graph search for: \"{query}\"")
    graph_results = retriever._graph_search(query, top_k=20, verbose=True)

    print(f"\n\nGraph search returned: {len(graph_results)} results")
    print("\nAll results from graph:")
    for i, msg in enumerate(graph_results, 1):
        print(f"\n{i}. {msg['message'][:80]}...")
        print(f"   Message ID: {msg['id']}")

        # Check if this message mentions cars
        if any(keyword in msg['message'].lower() for keyword in car_keywords):
            print("   ⚠️ THIS MESSAGE MENTIONS CARS!")

    # ========== STEP 5: Check entity index for "car" ==========
    print("\n" + "="*100)
    print("STEP 5: Entity Index Lookup for 'car' Keywords")
    print("="*100)

    print("\nChecking entity_index for car-related terms:")
    for keyword in car_keywords:
        if keyword in kg.entity_index:
            users = kg.entity_index[keyword]
            print(f"\n  '{keyword}': {len(users)} users")
            if "Vikram Desai" in users:
                print(f"    ✅ Vikram Desai found!")
            else:
                print(f"    ❌ Vikram Desai NOT in this index")
                print(f"    Users: {users[:5]}")
        else:
            print(f"\n  '{keyword}': NOT in entity_index")

    print("\n" + "="*100)
    print("INVESTIGATION COMPLETE")
    print("="*100)


if __name__ == "__main__":
    investigate_vikram_cars()
