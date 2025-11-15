"""
Validate that user names are extracted correctly and not split
"""
import sys
sys.path.append('src')

import json
from knowledge_graph import KnowledgeGraph
from collections import Counter

print("="*80)
print("NAME EXTRACTION VALIDATION")
print("="*80)

# Load data
with open('data/raw_messages.json') as f:
    messages = json.load(f)

with open('data/triples.json') as f:
    triples = json.load(f)

kg = KnowledgeGraph()
kg.load("data/knowledge_graph.pkl")

# Get all unique user names from messages
message_users = set(m['user_name'] for m in messages)
print(f"\n📊 Users in raw messages: {len(message_users)}")

# Get all unique subjects from triples
triple_subjects = set(t['subject'] for t in triples)
print(f"📊 Unique subjects in triples: {len(triple_subjects)}")

# Get all users in graph
graph_users = set(kg.user_index.keys())
print(f"📊 Users in graph: {len(graph_users)}")

# Check for name splitting issues
print("\n" + "="*80)
print("1. NAME SPLITTING CHECK")
print("="*80)

print("\n🔍 Looking for split names (single-word subjects that should be full names):")
split_names = []
for subject in triple_subjects:
    # Check if it's a single word (might be split)
    if ' ' not in subject and '-' not in subject:
        # Check if it looks like a first/last name only
        if subject not in {'VIP', 'We', 'arrangements', 'accommodations', 'booking', 'room'}:
            split_names.append(subject)

if split_names:
    print(f"\n⚠️  Found {len(split_names)} potential split names:")
    for name in split_names[:20]:
        count = sum(1 for t in triples if t['subject'] == name)
        print(f"  • {name:30s} ({count} triples)")
else:
    print("✅ No split names detected - all subjects are full names or valid entities")

# Check for inconsistent name formats
print("\n" + "="*80)
print("2. NAME CONSISTENCY CHECK")
print("="*80)

# Compare message users vs triple subjects
missing_in_triples = message_users - triple_subjects
extra_in_triples = triple_subjects - message_users

if missing_in_triples:
    print(f"\n⚠️  {len(missing_in_triples)} users have NO triples extracted:")
    for user in list(missing_in_triples)[:10]:
        msg_count = sum(1 for m in messages if m['user_name'] == user)
        print(f"  • {user:30s} ({msg_count} messages)")

if extra_in_triples:
    print(f"\n⚠️  {len(extra_in_triples)} subjects in triples NOT in original users:")
    for subject in list(extra_in_triples)[:20]:
        count = sum(1 for t in triples if t['subject'] == subject)
        print(f"  • {subject:30s} ({count} triples)")

        # Check if it's a partial name
        for full_name in message_users:
            if subject in full_name or full_name in subject:
                print(f"      → Might be partial match for: {full_name}")
                break

# Sample full names to verify format
print("\n" + "="*80)
print("3. SAMPLE FULL NAMES")
print("="*80)

print("\nSample of correctly formatted names:")
sample_users = sorted(list(graph_users))[:20]
for user in sample_users:
    triple_count = len(kg.user_index[user])
    print(f"  ✅ {user:35s} ({triple_count} relationships)")

# Test partial name matching
print("\n" + "="*80)
print("4. PARTIAL NAME MATCHING TEST")
print("="*80)

test_cases = [
    ("Sophia", "Sophia Al-Farsi"),
    ("Al-Farsi", "Sophia Al-Farsi"),
    ("Hans", "Hans Müller"),
    ("Müller", "Hans Müller"),
    ("Vikram", "Vikram Desai"),
    ("Desai", "Vikram Desai"),
]

print("\n🔍 Testing if partial names can be resolved to full names:\n")

for partial, expected_full in test_cases:
    # Find matches
    matches = []
    for full_name in graph_users:
        name_lower = full_name.lower()
        partial_lower = partial.lower()

        # Check if partial appears in full name
        if partial_lower in name_lower:
            matches.append(full_name)

        # Check if partial matches any name part
        parts = name_lower.split()
        for part in parts:
            if part == partial_lower:
                if full_name not in matches:
                    matches.append(full_name)
                break

    if expected_full in matches:
        if len(matches) == 1:
            print(f"✅ '{partial}' → '{matches[0]}' (unique match)")
        else:
            print(f"⚠️  '{partial}' → {len(matches)} matches: {matches[:3]}")
    else:
        print(f"❌ '{partial}' → NOT found (expected '{expected_full}')")

# Check for ambiguous partial names
print("\n" + "="*80)
print("5. AMBIGUOUS NAME DETECTION")
print("="*80)

# Build partial name index
partial_index = {}
for full_name in graph_users:
    parts = full_name.split()
    for part in parts:
        if len(part) > 2:
            if part not in partial_index:
                partial_index[part] = []
            partial_index[part].append(full_name)

ambiguous = {part: names for part, names in partial_index.items() if len(names) > 1}

if ambiguous:
    print(f"\n⚠️  Found {len(ambiguous)} ambiguous name parts (shared by multiple users):")
    for part, names in list(ambiguous.items())[:10]:
        print(f"  • '{part}' → {len(names)} users: {names[:3]}")
else:
    print("\n✅ No ambiguous name parts - all partial names are unique")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if not split_names and not extra_in_triples:
    print("\n✅ EXCELLENT: Name extraction is working correctly")
    print("   • All names are full names (no splitting)")
    print("   • All subjects map to real users")
    print("   • Partial name matching is possible")
elif len(split_names) < 10 and len(extra_in_triples) < 20:
    print("\n⚠️  GOOD: Minor issues found")
    print(f"   • {len(split_names)} potential split names")
    print(f"   • {len(extra_in_triples)} subjects not in user list")
    print("   • Recommend: Add name resolver for better matching")
else:
    print("\n❌ POOR: Significant name extraction issues")
    print(f"   • {len(split_names)} split names detected")
    print(f"   • {len(extra_in_triples)} invalid subjects")
    print("   • MUST FIX: Implement proper name entity recognition")

print("\n" + "="*80)
