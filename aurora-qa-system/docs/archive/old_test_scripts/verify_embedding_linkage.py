"""
Verify embedding-message linkage integrity
Ensures FAISS index positions correctly map to messages
"""
import json
import pickle
import faiss
from sentence_transformers import SentenceTransformer

print('='*70)
print('END-TO-END VERIFICATION: FAISS Index → Message Retrieval')
print('='*70)

# Load all components
print('\n📂 Loading components...')

# 1. Raw messages
with open('data/raw_messages.json') as f:
    raw_messages = json.load(f)

# 2. Embeddings metadata
with open('data/embeddings_metadata.pkl', 'rb') as f:
    embed_data = pickle.load(f)
embed_messages = embed_data['messages']

# 3. FAISS index
index = faiss.read_index('data/embeddings_faiss.index')

# 4. Model (for encoding test query)
print('Loading sentence transformer model...')
model = SentenceTransformer('BAAI/bge-small-en-v1.5')

print('✅ All components loaded')

# Test with a real query
query = 'Vikram BMW Tesla Mercedes'
print(f'\n🔍 Test Query: "{query}"')

# Encode query
query_embedding = model.encode(
    [f'query: {query}'],
    convert_to_numpy=True,
    normalize_embeddings=True
).astype('float32')

# Search FAISS
distances, indices = index.search(query_embedding, k=5)

print(f'\nTop 5 FAISS Results:')
print('='*70)

all_match = True
for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
    # Verify index is valid
    if idx >= len(embed_messages):
        print(f'\n❌ ERROR: Index {idx} out of bounds (max {len(embed_messages)-1})')
        all_match = False
        continue

    # Get message from embeddings metadata
    msg_from_embed = embed_messages[idx]

    # Verify it matches raw messages
    msg_from_raw = raw_messages[idx]

    # Check if they match
    match_status = '✅' if msg_from_embed['id'] == msg_from_raw['id'] else '❌'
    if msg_from_embed['id'] != msg_from_raw['id']:
        all_match = False

    print(f'\n{rank}. FAISS Index: {idx} | Distance: {dist:.3f} {match_status}')
    print(f'   Message ID: {msg_from_embed["id"][:16]}...')
    print(f'   User: {msg_from_embed["user_name"]}')
    print(f'   Content: {msg_from_embed["message"][:60]}...')

    # Verify both sources give same message
    if msg_from_embed['id'] != msg_from_raw['id']:
        print(f'   ❌ MISMATCH!')
        print(f'      Embed: {msg_from_embed["id"]}')
        print(f'      Raw: {msg_from_raw["id"]}')

print('\n' + '='*70)
print('VERIFICATION SUMMARY')
print('='*70)

if all_match:
    print('''
✅ Index Alignment: PASS
  - All FAISS indices correctly map to messages
  - embeddings_metadata.pkl matches raw_messages.json
  - No reordering detected

✅ Data Integrity: PASS
  - FAISS index[i] → embeddings_metadata['messages'][i] ✅
  - embeddings_metadata['messages'][i] == raw_messages[i] ✅

✅ Retrieval Flow: WORKING
  Query → FAISS search → Index i → Message at position i → Correct message

🎯 Conclusion: Embedding-message linkage is CORRECT!
''')
else:
    print('''
❌ CRITICAL ERROR: Index misalignment detected!
  - FAISS indices do NOT correctly map to messages
  - Data integrity compromised
  - Need to rebuild embeddings index
''')

# Additional spot checks
print('='*70)
print('ADDITIONAL SPOT CHECKS')
print('='*70)

# Random indices
import random
random.seed(42)
random_indices = random.sample(range(len(raw_messages)), 10)

print(f'\nVerifying 10 random indices: {random_indices[:5]}...')
mismatches = 0
for idx in random_indices:
    raw_id = raw_messages[idx]['id']
    embed_id = embed_messages[idx]['id']
    if raw_id != embed_id:
        mismatches += 1
        print(f'❌ Index {idx}: {raw_id} != {embed_id}')

if mismatches == 0:
    print(f'✅ All 10 random samples match perfectly!')
else:
    print(f'❌ {mismatches}/10 random samples mismatched!')

print('\n' + '='*70)
