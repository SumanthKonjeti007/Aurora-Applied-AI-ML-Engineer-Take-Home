"""
Test Phase 1 fix: Subject extraction now uses user_name
"""
import sys
sys.path.append('src')

from entity_extraction_gliner import GLiNEREntityExtractor
import json

print("="*80)
print("PHASE 1 FIX TEST - Subject Extraction")
print("="*80)

# Load a few test messages
with open('data/raw_messages.json') as f:
    messages = json.load(f)

# Initialize extractor
print("\nInitializing extractor...")
extractor = GLiNEREntityExtractor()

# Test on problematic messages
test_messages = [
    {
        "id": "test1",
        "user_name": "Sophia Al-Farsi",
        "message": "What are the best restaurants in Paris?",
        "timestamp": "2024-01-01"
    },
    {
        "id": "test2",
        "user_name": "Vikram Desai",
        "message": "Can I get a Bentley for my Paris trip?",
        "timestamp": "2024-01-01"
    },
    {
        "id": "test3",
        "user_name": "Hans Müller",
        "message": "I prefer Italian cuisine when dining in New York.",
        "timestamp": "2024-01-01"
    },
    {
        "id": "test4",
        "user_name": "Layla Kawaguchi",
        "message": "Please remember I prefer aisle seats during my flights.",
        "timestamp": "2024-01-01"
    }
]

print("\n" + "="*80)
print("TEST RESULTS")
print("="*80)

for msg in test_messages:
    print(f"\n{'='*80}")
    print(f"User: {msg['user_name']}")
    print(f"Message: \"{msg['message']}\"")
    print(f"{'='*80}")

    # Extract triples
    triples = extractor.extract_from_message(msg)

    print(f"\nExtracted {len(triples)} triples:")

    for i, triple in enumerate(triples, 1):
        subject = triple['subject']
        rel = triple['relationship']
        obj = triple['object']

        # Check if subject is correct
        is_correct = subject == msg['user_name']
        marker = "✅" if is_correct else "❌"

        print(f"{marker} {i}. ({subject}, {rel}, {obj})")

        if not is_correct:
            print(f"      ERROR: Subject should be '{msg['user_name']}', not '{subject}'")

# Test on real messages
print("\n" + "="*80)
print("REAL MESSAGE TEST (First 10 messages)")
print("="*80)

real_messages = messages[:10]
all_triples = []

for msg in real_messages:
    triples = extractor.extract_from_message(msg)
    all_triples.extend(triples)

# Check subjects
unique_subjects = set(t['subject'] for t in all_triples)
message_users = set(m['user_name'] for m in real_messages)

print(f"\nMessages processed: {len(real_messages)}")
print(f"Unique users in messages: {len(message_users)}")
print(f"Unique subjects in triples: {len(unique_subjects)}")

print(f"\nSubjects extracted:")
for subject in sorted(unique_subjects):
    count = sum(1 for t in all_triples if t['subject'] == subject)
    is_valid = subject in message_users
    marker = "✅" if is_valid else "❌"
    print(f"  {marker} {subject:30s} ({count} triples)")

# Validation
invalid_subjects = unique_subjects - message_users

print("\n" + "="*80)
print("VALIDATION RESULT")
print("="*80)

if not invalid_subjects:
    print("\n✅ SUCCESS: All subjects are valid user names!")
    print("   • No random words as subjects")
    print("   • No split names")
    print("   • Subject extraction is working correctly")
else:
    print(f"\n❌ FAILED: Found {len(invalid_subjects)} invalid subjects:")
    for subj in invalid_subjects:
        print(f"   • {subj}")

print("\n" + "="*80)
