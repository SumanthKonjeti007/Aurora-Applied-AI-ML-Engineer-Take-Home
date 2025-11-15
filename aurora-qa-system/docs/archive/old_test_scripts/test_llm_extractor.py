"""
Test LLM Semantic Extractor on complex messages
"""
import sys
sys.path.append('src')
import os

print("="*80)
print("LLM SEMANTIC EXTRACTOR TEST")
print("="*80)

# Check for API key
if not os.getenv('GROQ_API_KEY'):
    print("\n⚠️  GROQ_API_KEY not found in environment")
    print("\nTo test the LLM extractor:")
    print("  1. Get free API key at: https://console.groq.com/keys")
    print("  2. Set it: export GROQ_API_KEY='your-key-here'")
    print("  3. Run this test again")
    print("\nSkipping LLM test for now...")
    sys.exit(0)

from llm_extractor import LLMSemanticExtractor

# Test messages (complex ones that the rule-based filter couldn't handle)
test_messages = [
    {
        "name": "Semantic division test",
        "message": {
            "id": "test1",
            "user_name": "Vikram Desai",
            "message": "Can I get a Bentley for my Paris trip?",
            "timestamp": "2024-01-01"
        },
        "expected_triples": [
            ("Vikram Desai", "WANTS_TO_RENT", "Bentley"),
            ("Vikram Desai", "PLANNING_TRIP_TO", "Paris")
        ]
    },
    {
        "name": "Question with location",
        "message": {
            "id": "test2",
            "user_name": "Sophia Al-Farsi",
            "message": "What are the best restaurants in Paris?",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Sophia Al-Farsi"],
        "expected_contains": ["Paris", "restaurant"]
    },
    {
        "name": "Preference statement",
        "message": {
            "id": "test3",
            "user_name": "Hans Müller",
            "message": "I prefer Italian cuisine when dining in New York.",
            "timestamp": "2024-01-01"
        },
        "expected_triples": [
            ("Hans Müller", "PREFERS", "Italian cuisine"),
        ]
    },
    {
        "name": "Multiple ownership (semantic division)",
        "message": {
            "id": "test4",
            "user_name": "Vikram Desai",
            "message": "Change my car service to the BMW instead of the Mercedes.",
            "timestamp": "2024-01-01"
        },
        "expected_contains": ["BMW", "Mercedes"]
    }
]

print("\nInitializing LLM extractor...")
try:
    extractor = LLMSemanticExtractor()
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("RUNNING TESTS")
print("="*80)

passed = 0
failed = 0

for i, test in enumerate(test_messages, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {test['name']}")
    print(f"{'='*80}")
    print(f"User: {test['message']['user_name']}")
    print(f"Message: \"{test['message']['message']}\"")

    # Extract
    triples = extractor.extract_triples_llm(test['message'])

    print(f"\nExtracted {len(triples)} triples:")
    for triple in triples:
        confidence = triple.get('metadata', {}).get('confidence', 'unknown')
        print(f"  • ({triple['subject']}, {triple['relationship']}, {triple['object']})")
        print(f"    [confidence: {confidence}]")

    # Validate
    test_passed = True
    errors = []

    # Check expected triples
    if 'expected_triples' in test:
        for exp_subj, exp_rel, exp_obj in test['expected_triples']:
            found = any(
                t['subject'] == exp_subj and
                t['relationship'] == exp_rel and
                exp_obj.lower() in t['object'].lower()
                for t in triples
            )
            if not found:
                errors.append(f"❌ Expected triple not found: ({exp_subj}, {exp_rel}, {exp_obj})")
                test_passed = False

    # Check expected subjects
    if 'expected_subjects' in test:
        subjects = set(t['subject'] for t in triples)
        for exp_subj in test['expected_subjects']:
            if exp_subj not in subjects and len(triples) > 0:
                errors.append(f"❌ Expected subject '{exp_subj}' not found")
                test_passed = False

    # Check expected content
    if 'expected_contains' in test:
        all_objects = " ".join(t['object'].lower() for t in triples)
        for keyword in test['expected_contains']:
            if keyword.lower() not in all_objects:
                errors.append(f"❌ Expected keyword '{keyword}' not found in objects")
                test_passed = False

    # Print result
    if test_passed:
        print(f"\n✅ PASS")
        passed += 1
    else:
        print(f"\n❌ FAIL")
        for error in errors:
            print(f"   {error}")
        failed += 1

# Summary
print("\n" + "="*80)
print("LLM EXTRACTOR TEST SUMMARY")
print("="*80)

print(f"\n✅ Passed: {passed}/{len(test_messages)}")
print(f"❌ Failed: {failed}/{len(test_messages)}")

if failed == 0:
    print("\n" + "="*80)
    print("🎉 LLM EXTRACTOR WORKING!")
    print("="*80)
    print("\nCapabilities:")
    print("  ✅ Semantic division (Bentley + Paris = 2 triples)")
    print("  ✅ Proper subject assignment (always user_name)")
    print("  ✅ Complex message understanding")
    print("  ✅ Question handling")
else:
    print(f"\n⚠️  {failed} tests failed - Review LLM prompt")

print("\n" + "="*80)
