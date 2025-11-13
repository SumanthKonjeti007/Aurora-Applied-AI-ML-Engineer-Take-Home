"""
Extract entities from all 3,349 messages using GLiNER + spaCy
Industry-standard approach: Local, fast, zero API costs
Estimated time: ~20 minutes
"""
import json
import random
from src.entity_extraction_gliner import GLiNEREntityExtractor


def main():
    print("="*60)
    print("FULL ENTITY EXTRACTION - ALL 3,349 MESSAGES")
    print("Using GLiNER + spaCy (Local, 0 API Costs)")
    print("="*60)

    # Load all messages
    print("\n📂 Loading messages...")
    with open('data/raw_messages.json') as f:
        messages = json.load(f)

    print(f"✅ Loaded {len(messages)} messages")

    # Initialize extractor
    extractor = GLiNEREntityExtractor()

    # Extract from all messages
    print("\n⚡ Starting extraction...")
    print("   - Local processing (no rate limits)")
    print("   - GLiNER for entity recognition")
    print("   - spaCy for relationship extraction")
    print("   - Estimated time: ~20 minutes\n")

    triples = extractor.extract_from_messages_batch(messages)

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
    print("3. Build knowledge graph with networkx")
    print("4. Generate embeddings for semantic search")
    print("5. Build BM25 index for keyword search")


if __name__ == "__main__":
    main()
