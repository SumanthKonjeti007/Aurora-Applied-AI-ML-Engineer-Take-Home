"""
Debug: Why does graph search return 0 results for Hans's preferences?
"""
import sys
sys.path.append('src')

from knowledge_graph import KnowledgeGraph
import json

print("="*80)
print("DEBUG: Hans's PREFERS relationships")
print("="*80)

# Load graph
kg = KnowledgeGraph()
kg.load("data/knowledge_graph.pkl")

# Load messages
with open('data/raw_messages.json') as f:
    messages = json.load(f)

# Get Hans's PREFERS relationships
hans_prefs = kg.get_user_relationships("Hans Müller", "PREFERS")

print(f"\nHans has {len(hans_prefs)} PREFERS relationships")
print("\nLet's check if those messages contain 'preferences' keyword:\n")

for i, rel in enumerate(hans_prefs, 1):
    msg_id = rel['message_id']
    obj = rel['object']

    # Find the message
    msg = next((m for m in messages if m['id'] == msg_id), None)

    if msg:
        text = msg['message']
        has_pref_word = 'prefer' in text.lower()

        print(f"{i}. Object: '{obj}'")
        print(f"   Message ID: {msg_id}")
        print(f"   Contains 'prefer': {has_pref_word}")
        print(f"   Text: {text[:150]}...")
        print()

print("="*80)
print("DIAGNOSIS:")
print("="*80)
print("\nThe graph search looks for messages containing the keyword 'preferences'.")
print("But Hans's messages say 'I prefer X' not 'my preferences are X'.")
print("\nCurrent logic:")
print("  1. Find Hans ✅")
print("  2. Get Hans's relationships ✅")
print("  3. Filter for messages with 'preferences' keyword ❌ (too restrictive)")
print("\nSuggestion:")
print("  When user + relationship type detected, return those messages")
print("  without requiring exact keyword match.")
print("="*80)
