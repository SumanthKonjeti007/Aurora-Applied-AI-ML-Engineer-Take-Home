"""
Rebuild triples.json using pure rule-based extraction (no LLM)

Fast, deterministic, local processing
Estimated time: 5-10 minutes for 3,349 messages
"""
import json
import sys
import os
from collections import defaultdict
import random

sys.path.insert(0, 'src')
from rule_based_extractor import RuleBasedExtractor
from knowledge_graph import KnowledgeGraph


def compare_old_vs_new(old_triples, new_triples):
    """Compare old and new extraction quality"""
    print("\n" + "="*80)
    print("OLD VS NEW COMPARISON")
    print("="*80)

    # Count unique subjects
    old_subjects = set(t.get('subject') for t in old_triples)
    new_subjects = set(t.get('subject') for t in new_triples)

    print(f"\n📊 Unique Subjects:")
    print(f"   Old: {len(old_subjects)} subjects")
    print(f"   New: {len(new_subjects)} subjects")
    print(f"   Improvement: {len(old_subjects) - len(new_subjects)} fewer subjects")

    # Show garbage subjects that were removed
    print(f"\n🗑️  Garbage Subjects Removed (sample):")
    garbage_subjects = old_subjects - new_subjects
    sample_garbage = sorted(garbage_subjects)[:20]
    for subj in sample_garbage:
        print(f"   ❌ {subj}")

    if len(garbage_subjects) > 20:
        print(f"   ... and {len(garbage_subjects) - 20} more")

    print(f"\n✅ Valid Subjects Retained:")
    valid_subjects = new_subjects & old_subjects
    for subj in sorted(valid_subjects)[:15]:
        print(f"   ✅ {subj}")

    # Count by relationship type
    old_by_rel = defaultdict(int)
    new_by_rel = defaultdict(int)

    for t in old_triples:
        old_by_rel[t.get('relationship')] += 1

    for t in new_triples:
        new_by_rel[t.get('relationship')] += 1

    print(f"\n📊 Triples by Relationship:")
    print(f"   {'Relationship':<25} {'Old':<10} {'New':<10} {'Change':<10}")
    print(f"   {'-'*60}")

    all_rels = sorted(set(list(old_by_rel.keys()) + list(new_by_rel.keys())))
    for rel in all_rels:
        old_count = old_by_rel.get(rel, 0)
        new_count = new_by_rel.get(rel, 0)
        change = new_count - old_count
        sign = "+" if change > 0 else ""
        print(f"   {rel:<25} {old_count:<10} {new_count:<10} {sign}{change}")


def main():
    print("="*80)
    print("REBUILD TRIPLES.JSON - PURE RULE-BASED (NO LLM)")
    print("="*80)

    # Load old triples for comparison
    print("\n📂 Loading old triples for comparison...")
    try:
        with open('data/triples.json') as f:
            old_triples = json.load(f)
        print(f"✅ Loaded {len(old_triples)} old triples")
    except:
        print("⚠️  No old triples found, skipping comparison")
        old_triples = []

    # Load all messages
    print("\n📂 Loading messages...")
    with open('data/raw_messages.json') as f:
        messages = json.load(f)

    print(f"✅ Loaded {len(messages)} messages")

    # Initialize rule-based extractor
    print("\n🔧 Initializing rule-based extractor...")
    extractor = RuleBasedExtractor()

    # Extract from all messages
    print("\n⚡ Starting extraction...")
    print("   - Pure rule-based (spaCy only)")
    print("   - No API calls, no rate limits")
    print("   - Deterministic output")
    print("   - Estimated time: 5-10 minutes\n")

    new_triples = extractor.extract_from_messages_batch(messages, show_progress=True)

    # Show statistics
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE!")
    print("="*80)

    extractor.print_statistics(new_triples)

    # Compare old vs new
    if old_triples:
        compare_old_vs_new(old_triples, new_triples)

    # Show sample triples
    print("\n" + "="*80)
    print("SAMPLE NEW TRIPLES (for quality validation)")
    print("="*80)

    # Group by relationship type
    by_relationship = defaultdict(list)
    for triple in new_triples:
        by_relationship[triple.get('relationship')].append(triple)

    # Show 3 samples for each relationship type
    for rel_type in sorted(by_relationship.keys()):
        samples = by_relationship[rel_type][:3]
        print(f"\n{rel_type} ({len(by_relationship[rel_type])} total):")
        for sample in samples:
            print(f"  • ({sample.get('subject')}, {sample.get('object')})")

    # Save new triples
    print("\n💾 Saving new triples...")

    # Backup old triples
    if os.path.exists('data/triples.json'):
        os.rename('data/triples.json', 'data/triples_old.json')
        print("   ✅ Backed up old triples to data/triples_old.json")

    extractor.save_triples(new_triples, 'data/triples.json')

    # Build new knowledge graph
    print("\n" + "="*80)
    print("BUILDING NEW KNOWLEDGE GRAPH")
    print("="*80)

    kg = KnowledgeGraph()
    kg.build_from_triples(new_triples)

    # Save new knowledge graph
    print("\n💾 Saving new knowledge graph...")

    # Backup old graph
    if os.path.exists('data/knowledge_graph.pkl'):
        os.rename('data/knowledge_graph.pkl', 'data/knowledge_graph_old.pkl')
        print("   ✅ Backed up old graph to data/knowledge_graph_old.pkl")

    kg.save('data/knowledge_graph.pkl')
    print("   ✅ Saved new graph to data/knowledge_graph.pkl")

    # Final summary
    print("\n" + "="*80)
    print("REBUILD COMPLETE!")
    print("="*80)

    print("\n📊 Summary:")
    print(f"   Old triples: {len(old_triples)}")
    print(f"   New triples: {len(new_triples)}")
    if old_triples:
        print(f"   Change: {len(new_triples) - len(old_triples):+d} ({((len(new_triples) - len(old_triples))/len(old_triples)*100):+.1f}%)")

    print("\n✅ Files updated:")
    print("   • data/triples.json (new triples)")
    print("   • data/triples_old.json (backup)")
    print("   • data/knowledge_graph.pkl (new graph)")
    print("   • data/knowledge_graph_old.pkl (backup)")

    print("\n🔄 Next steps:")
    print("   1. Embeddings and BM25 indexes already exist")
    print("   2. Test hybrid retrieval with new graph")
    print("   3. Validate answer quality on assignment examples")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
