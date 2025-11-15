"""Test Louvre query with verbose output"""
from src.hybrid_retriever import HybridRetriever

# Initialize retriever
retriever = HybridRetriever()

# Test query
query = "Which clients requested a private tour of the Louvre?"

print("\n" + "="*80)
print(f"QUERY: {query}")
print("="*80)

# Search with verbose mode
print("\n" + "="*80)
print("RETRIEVAL WITH VERBOSE MODE:")
print("="*80)

results = retriever.search(query, top_k=10, verbose=True)

print("\n" + "="*80)
print("TOP 10 RESULTS AFTER DIVERSITY:")
print("="*80)

for i, (msg, score) in enumerate(results, 1):
    user = msg['user_name']
    message_snippet = msg['message'][:100]
    louvre_marker = "✅ LOUVRE" if 'louvre' in msg['message'].lower() else "❌ NO LOUVRE"
    print(f"{i}. [{score:.6f}] {user:20s} {louvre_marker}")
    print(f"   {message_snippet}...")
    print()

# Show first 30 from RRF (before diversity)
print("\n" + "="*80)
print("ANALYZING RRF SCORES (BEFORE DIVERSITY) - Top 30:")
print("="*80)

# Get all results without diversity
all_results = retriever.search(query, top_k=50, verbose=False)

print(f"\nTotal unique messages from RRF: {len(all_results)}")
print("\nTop 30 positions (before diversity):")

# Show top 30
user_counts = {}
for i, (msg, score) in enumerate(all_results[:30], 1):
    user = msg['user_name']
    user_counts[user] = user_counts.get(user, 0) + 1
    louvre_marker = "✅ LOUVRE" if 'louvre' in msg['message'].lower() else "❌"
    print(f"{i:2d}. [{score:.6f}] {user:20s} {louvre_marker}")

print(f"\nUser counts in top 30: {user_counts}")

# Find Vikram and Hans
print("\n" + "="*80)
print("SEARCHING FOR VIKRAM AND HANS IN ALL RESULTS:")
print("="*80)

vikram_positions = []
hans_positions = []

for i, (msg, score) in enumerate(all_results, 1):
    user = msg['user_name']
    if 'Vikram' in user:
        vikram_positions.append((i, score, msg['message'][:80]))
    elif 'Hans' in user or 'Müller' in user:
        hans_positions.append((i, score, msg['message'][:80]))

if vikram_positions:
    print(f"\n✅ Vikram Desai found at positions:")
    for pos, score, msg in vikram_positions[:5]:
        louvre_marker = "✅ LOUVRE" if 'louvre' in msg.lower() else "❌"
        print(f"  Position {pos}: [{score:.6f}] {louvre_marker} {msg}...")
else:
    print("\n❌ Vikram Desai NOT in RRF results")

if hans_positions:
    print(f"\n✅ Hans Müller found at positions:")
    for pos, score, msg in hans_positions[:5]:
        louvre_marker = "✅ LOUVRE" if 'louvre' in msg.lower() else "❌"
        print(f"  Position {pos}: [{score:.6f}] {louvre_marker} {msg}...")
else:
    print("\n❌ Hans Müller NOT in RRF results")

