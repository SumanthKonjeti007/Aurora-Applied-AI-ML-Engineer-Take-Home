"""
Extract entities from all 3,349 messages
This will take ~20-30 minutes
"""
import json
from src.entity_extraction import EntityExtractor
import random


def main():
    print("="*60)
    print("FULL ENTITY EXTRACTION - ALL 3,349 MESSAGES")
    print("="*60)

    # Load all messages
    print("\n📂 Loading messages...")
    with open('data/raw_messages.json') as f:
        messages = json.load(f)

    print(f"✅ Loaded {len(messages)} messages")

    # Initialize extractor
    extractor = EntityExtractor()

    # Confirm before starting
    print("\n⚠️  This will take approximately 20-30 minutes")
    print("   - Makes ~3,349 API calls to Groq")
    print("   - Processes ~2-3 messages per second")
    print("   - Extracts structured knowledge triples")
    print("\nStarting extraction...")

    # Extract from all messages
    # Batch size 1 with 0.1s delay = ~10 requests/sec = safe for rate limits
    triples = extractor.extract_from_messages_batch(
        messages,
        batch_size=1,
        delay=0.1
    )

    # Save results
    print("\n💾 Saving results...")
    extractor.save_triples(triples, "data/triples.json")

    # Show statistics
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE!")
    print("="*60)

    extractor.print_statistics(triples)

    # Show sample triples for validation
    print("\n" + "="*60)
    print("SAMPLE TRIPLES (for quality validation)")
    print("="*60)

    # Group by relationship type
    from collections import defaultdict
    by_relationship = defaultdict(list)
    for triple in triples:
        by_relationship[triple.get('relationship')].append(triple)

    # Show 3 samples for each relationship type
    for rel_type in sorted(by_relationship.keys()):
        samples = by_relationship[rel_type][:3]
        print(f"\n{rel_type} ({len(by_relationship[rel_type])} total):")
        for sample in samples:
            print(f"  • ({sample.get('subject')}, {sample.get('object')})")

    # Show random samples for manual validation
    print("\n" + "="*60)
    print("RANDOM SAMPLES FOR VALIDATION")
    print("="*60)
    print("\nReview these to check extraction quality:\n")

    random_samples = random.sample(triples, min(20, len(triples)))
    for i, triple in enumerate(random_samples, 1):
        print(f"{i}. Subject: {triple.get('subject')}")
        print(f"   Relationship: {triple.get('relationship')}")
        print(f"   Object: {triple.get('object')}")
        if triple.get('metadata'):
            print(f"   Metadata: {triple.get('metadata')}")
        print()

    # Save statistics
    stats = extractor.get_statistics(triples)
    with open('data/extraction_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    print("✅ Statistics saved to data/extraction_stats.json")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("\n1. Review the samples above for quality")
    print("2. Check data/triples.json for complete results")
    print("3. If quality is good → Proceed to build knowledge graph")
    print("4. If quality needs improvement → Adjust prompts and re-run")


if __name__ == "__main__":
    main()
