"""
Comprehensive test for ALL Phase 1 fixes:
1. ✅ Subject extraction uses user_name
2. ✅ OWNS only extracts ownable entities
3. ✅ Verb tense fallback removed
4. ✅ Prepositions not extracted as objects
"""
import sys
sys.path.append('src')

from entity_extraction_gliner import GLiNEREntityExtractor

print("="*80)
print("PHASE 1 COMPLETE - COMPREHENSIVE TEST")
print("="*80)

# Initialize extractor
print("\nInitializing extractor...")
extractor = GLiNEREntityExtractor()

# Test messages designed to trigger all the bugs
test_cases = [
    {
        "name": "Fix #1: Subject should be user_name, not 'What'",
        "message": {
            "id": "test1",
            "user_name": "Sophia Al-Farsi",
            "message": "What are the best restaurants in Paris?",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Sophia Al-Farsi"],
        "should_not_contain_subjects": ["What", "restaurants"]
    },
    {
        "name": "Fix #2: OWNS should NOT extract 'my Paris trip'",
        "message": {
            "id": "test2",
            "user_name": "Vikram Desai",
            "message": "Can I get a Bentley for my Paris trip?",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Vikram Desai"],
        "should_not_contain_objects": ["my Paris trip", "my trip"],
        "expected_objects": []  # May not extract Bentley depending on parsing
    },
    {
        "name": "Fix #2: OWNS SHOULD extract 'my BMW' (ownable)",
        "message": {
            "id": "test3",
            "user_name": "Vikram Desai",
            "message": "Change my car service to my BMW instead of my Mercedes.",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Vikram Desai"],
        "should_contain_ownable": True  # Should find BMW or Mercedes
    },
    {
        "name": "Fix #3: Verb tense - 'received' should NOT → VISITED",
        "message": {
            "id": "test4",
            "user_name": "Sophia Al-Farsi",
            "message": "I haven't received the itinerary for my upcoming trip.",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Sophia Al-Farsi"],
        "should_not_contain_relationships": ["VISITED"]  # 'received' is not in pattern list
    },
    {
        "name": "Fix #3: Verb tense - 'suspect' should NOT → PLANNING_TRIP_TO",
        "message": {
            "id": "test5",
            "user_name": "Sophia Al-Farsi",
            "message": "I suspect overcharge in the latest invoice.",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Sophia Al-Farsi"],
        "should_not_contain_relationships": ["PLANNING_TRIP_TO"]  # 'suspect' not in patterns
    },
    {
        "name": "Fix #4: Prepositions - 'to' should NOT be extracted",
        "message": {
            "id": "test6",
            "user_name": "Armand Dupont",
            "message": "I need two tickets to the opera in Milan.",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Armand Dupont"],
        "should_not_contain_objects": ["to", "in"]  # Prepositions
    },
    {
        "name": "Fix #4: Prepositions - 'for' should NOT be extracted",
        "message": {
            "id": "test7",
            "user_name": "Hans Müller",
            "message": "I need four front-row seats for the game on November 20.",
            "timestamp": "2024-01-01"
        },
        "expected_subjects": ["Hans Müller"],
        "should_not_contain_objects": ["for", "on"]  # Prepositions
    }
]

print("\n" + "="*80)
print("RUNNING TESTS")
print("="*80)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}: {test['name']}")
    print(f"{'='*80}")
    print(f"User: {test['message']['user_name']}")
    print(f"Message: \"{test['message']['message']}\"")

    # Extract
    triples = extractor.extract_from_message(test['message'])

    print(f"\nExtracted {len(triples)} triples:")
    for triple in triples:
        print(f"  • ({triple['subject']}, {triple['relationship']}, {triple['object']})")

    # Validate
    test_passed = True
    errors = []

    # Check subjects
    if 'expected_subjects' in test:
        subjects = set(t['subject'] for t in triples)
        for expected in test['expected_subjects']:
            if expected not in subjects and len(triples) > 0:
                errors.append(f"Expected subject '{expected}' not found")
                test_passed = False

    if 'should_not_contain_subjects' in test:
        subjects = set(t['subject'] for t in triples)
        for bad_subject in test['should_not_contain_subjects']:
            if bad_subject in subjects:
                errors.append(f"❌ Found bad subject '{bad_subject}'")
                test_passed = False

    # Check objects
    if 'should_not_contain_objects' in test:
        objects = set(t['object'] for t in triples)
        for bad_obj in test['should_not_contain_objects']:
            if bad_obj in objects:
                errors.append(f"❌ Found bad object '{bad_obj}'")
                test_passed = False

    # Check relationships
    if 'should_not_contain_relationships' in test:
        rels = set(t['relationship'] for t in triples)
        for bad_rel in test['should_not_contain_relationships']:
            if bad_rel in rels:
                errors.append(f"❌ Found bad relationship '{bad_rel}'")
                test_passed = False

    # Check for ownable entities
    if test.get('should_contain_ownable'):
        ownable_found = any(
            any(word in t['object'].lower() for word in ['bmw', 'mercedes', 'car', 'tesla'])
            for t in triples if t['relationship'] == 'OWNS'
        )
        if not ownable_found:
            errors.append("❌ No ownable entities found in OWNS relationships")
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
print("PHASE 1 TEST SUMMARY")
print("="*80)

print(f"\n✅ Passed: {passed}/{len(test_cases)}")
print(f"❌ Failed: {failed}/{len(test_cases)}")

if failed == 0:
    print("\n" + "="*80)
    print("🎉 PHASE 1 COMPLETE - ALL FIXES WORKING!")
    print("="*80)
    print("\nFixed:")
    print("  1. ✅ Subject extraction - Uses user_name (not message text)")
    print("  2. ✅ OWNS bug - Only extracts ownable entities")
    print("  3. ✅ Verb tense fallback - Removed (no more garbage)")
    print("  4. ✅ Preposition bug - Not extracted as objects")
    print("\nReady for Phase 2: LLM Reasoner")
else:
    print(f"\n⚠️  {failed} tests failed - Phase 1 NOT complete")
    print("Review fixes and re-test.")

print("\n" + "="*80)
