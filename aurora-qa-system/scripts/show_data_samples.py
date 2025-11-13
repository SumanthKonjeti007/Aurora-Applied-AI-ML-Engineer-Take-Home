"""
Display samples from all data artifacts
Shows format and structure of each saved data file
"""
import json
import pickle
import faiss

print("="*70)
print("DATA ARTIFACTS SAMPLES")
print("="*70)

# 1. Raw Messages
print("\n1️⃣ RAW MESSAGES (data/raw_messages.json)")
print("="*70)
with open('data/raw_messages.json') as f:
    messages = json.load(f)
print(f"Total: {len(messages)} messages")
print(f"Format: JSON array of message objects")
print(f"\nSchema:")
print("  - id: UUID string")
print("  - user_id: UUID string")
print("  - user_name: String")
print("  - timestamp: ISO datetime string")
print("  - message: String")
print(f"\nSample (first 2 messages):\n")
for i, msg in enumerate(messages[:2], 1):
    print(json.dumps(msg, indent=2))
    print()

# 2. Triples
print("="*70)
print("2️⃣ KNOWLEDGE TRIPLES (data/triples.json)")
print("="*70)
with open('data/triples.json') as f:
    triples = json.load(f)
print(f"Total: {len(triples)} triples")
print(f"Format: JSON array of triple objects")
print(f"\nSchema:")
print("  - subject: String (usually user_name)")
print("  - relationship: String (OWNS, VISITED, etc.)")
print("  - object: String (entity or phrase)")
print("  - message_id: UUID string (links to message)")
print("  - timestamp: ISO datetime string")
print("  - metadata: Dict (extraction details)")
print(f"\nSample (first 3 triples):\n")
for i, triple in enumerate(triples[:3], 1):
    print(json.dumps(triple, indent=2))
    print()

# 3. Knowledge Graph
print("="*70)
print("3️⃣ KNOWLEDGE GRAPH (data/knowledge_graph.pkl)")
print("="*70)
with open('data/knowledge_graph.pkl', 'rb') as f:
    kg_data = pickle.load(f)

print(f"Format: Pickle file (binary)")
print(f"Contents: networkx MultiDiGraph + lookup indices")
print(f"\nKeys in pickle: {list(kg_data.keys())}")

graph = kg_data['graph']
print(f"\nGraph statistics:")
print(f"  Nodes: {graph.number_of_nodes()}")
print(f"  Edges: {graph.number_of_edges()}")
print(f"  Type: {type(graph).__name__}")

print(f"\nSample nodes (first 5):")
for i, node in enumerate(list(graph.nodes())[:5], 1):
    print(f"  {i}. {repr(node)}")

print(f"\nSample edges with data (first 3):")
for i, (u, v, data) in enumerate(list(graph.edges(data=True))[:3], 1):
    rel = data.get('relationship', '?')
    msg_id = data.get('message_id', '?')[:8]
    print(f"  {i}. {repr(u)} --[{rel}]--> {repr(v)}")
    print(f"     message_id: {msg_id}...")
    print()

print(f"Indices available:")
print(f"  - user_index: {len(kg_data['user_index'])} users indexed")
print(f"  - relationship_index: {len(kg_data['relationship_index'])} relationship types")
print(f"  - entity_index: {len(kg_data['entity_index'])} entities indexed")

print(f"\nSample user_index (first 3 users):")
for i, user in enumerate(list(kg_data['user_index'].keys())[:3], 1):
    edge_count = len(kg_data['user_index'][user])
    print(f"  {i}. {repr(user)}: {edge_count} edges")

# 4. FAISS Index
print("\n" + "="*70)
print("4️⃣ EMBEDDINGS FAISS INDEX (data/embeddings_faiss.index)")
print("="*70)
index = faiss.read_index('data/embeddings_faiss.index')
print(f"Format: FAISS binary index file")
print(f"Index type: {type(index).__name__}")
print(f"\nIndex properties:")
print(f"  Dimension: {index.d}")
print(f"  Total vectors: {index.ntotal}")
print(f"  Is trained: {index.is_trained}")
print(f"  Metric: L2 (Euclidean distance)")
print(f"\nVector format:")
print(f"  - Type: float32 numpy arrays")
print(f"  - Normalized: Yes (L2 norm = 1)")
print(f"  - BGE prefixes: 'passage:' added during indexing")

# 5. Embeddings Metadata
print("\n" + "="*70)
print("5️⃣ EMBEDDINGS METADATA (data/embeddings_metadata.pkl)")
print("="*70)
with open('data/embeddings_metadata.pkl', 'rb') as f:
    embed_data = pickle.load(f)

print(f"Format: Pickle file (binary)")
print(f"Keys: {list(embed_data.keys())}")
print(f"\nMetadata:")
print(f"  Dimension: {embed_data['dimension']}")
print(f"  Model: {embed_data['model_name']}")
print(f"  Index size: {embed_data['index_size']} vectors")
print(f"  Strategy: {embed_data['strategy']}")
print(f"  Total messages: {len(embed_data['messages'])}")

print(f"\nMessage schema (same as raw_messages.json):")
print("  - id: UUID string")
print("  - user_id: UUID string")
print("  - user_name: String")
print("  - timestamp: ISO datetime string")
print("  - message: String")

print(f"\nSample message (first 1):")
msg = embed_data['messages'][0]
print(json.dumps(msg, indent=2))

# 6. BM25 Index
print("\n" + "="*70)
print("6️⃣ BM25 SEARCH INDEX (data/bm25.pkl)")
print("="*70)
with open('data/bm25.pkl', 'rb') as f:
    bm25_data = pickle.load(f)

print(f"Format: Pickle file (binary)")
print(f"Keys: {list(bm25_data.keys())}")
print(f"\nContents:")
print(f"  - bm25: BM25Okapi object")
print(f"  - messages: List of message dicts ({len(bm25_data['messages'])} total)")
print(f"  - tokenized_corpus: List of token lists ({len(bm25_data['tokenized_corpus'])} docs)")

print(f"\nSample tokenized document (first 1):")
print(f"  Original message: {bm25_data['messages'][0]['message'][:80]}...")
print(f"  Tokenized: {bm25_data['tokenized_corpus'][0][:15]}...")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
Data Pipeline:
1. raw_messages.json (3,349 messages)
   └──> 2. triples.json (3,247 knowledge triples)
        └──> 3. knowledge_graph.pkl (1,637 nodes, 2,572 edges)

   └──> 4. embeddings_faiss.index (3,349 vectors × 384 dim)
        + embeddings_metadata.pkl (messages + metadata)

   └──> 6. bm25.pkl (tokenized corpus + BM25 index)

All indices point back to messages via message_id or index position.
""")

print("="*70)
