"""
Phase 4: Rebuild Knowledge Graph with Hybrid Extractor

Uses the fixed Filter + LLM Reasoner to re-extract all 3,349 messages
Expected improvements:
- 247 subjects → ~10 subjects (all valid users)
- 21% noise → 10% noise
- OWNS relationships semantically correct
- Can answer assignment questions correctly

Estimated time: 15-20 minutes (with LLM rate limiting)
"""
import json
import sys
import os
from collections import defaultdict
import random

sys.path.insert(0, 'src')
from hybrid_extractor import HybridExtractor
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


def main():
    print("="*80)
    print("PHASE 4: REBUILD KNOWLEDGE GRAPH WITH HYBRID EXTRACTOR")
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

    # Initialize hybrid extractor
    print("\n🔧 Initializing Hybrid Extractor...")
    extractor = HybridExtractor(use_llm=True)

    # Extract from all messages
    print("\n⚡ Starting hybrid extraction...")
    print("   - Triage: Simple → Filter, Complex → LLM")
    print("   - Filter: GLiNER + spaCy (fast, free)")
    print("   - LLM: Llama-3.1-8B via Groq (semantic understanding)")
    print("   - Rate limiting: 2.1s between LLM calls")
    print("   - Estimated time: 15-20 minutes\n")

    new_triples = extractor.extract_from_messages_batch(
        messages,
        show_progress=True,
        verbose=False
    )

    # Compare old vs new
    if old_triples:
        compare_old_vs_new(old_triples, new_triples)

    # Save new triples
    print("\n💾 Saving new triples...")

    # Backup old triples
    if os.path.exists('data/triples.json'):
        os.rename('data/triples.json', 'data/triples_old.json')
        print("   ✅ Backed up old triples to data/triples_old.json")

    with open('data/triples.json', 'w') as f:
        json.dump(new_triples, f, indent=2)
    print("   ✅ Saved new triples to data/triples.json")

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

    # Build new knowledge graph
    print("\n" + "="*80)
    print("BUILDING NEW KNOWLEDGE GRAPH")
    print("="*80)

    kg = KnowledgeGraph()

    print("\n📊 Adding triples to graph...")
    for triple in new_triples:
        kg.add_triple(
            subject=triple.get('subject'),
            relationship=triple.get('relationship'),
            obj=triple.get('object'),
            message_id=triple.get('message_id')
        )

    # Show graph statistics
    print("\n✅ Knowledge Graph built!")
    kg.print_statistics()

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
    print("PHASE 4 COMPLETE!")
    print("="*80)

    print("\n📊 Summary:")
    print(f"   Old triples: {len(old_triples)}")
    print(f"   New triples: {len(new_triples)}")
    print(f"   Change: {len(new_triples) - len(old_triples):+d} ({((len(new_triples) - len(old_triples))/len(old_triples)*100):+.1f}%)")

    print("\n✅ Files updated:")
    print("   • data/triples.json (new triples)")
    print("   • data/triples_old.json (backup)")
    print("   • data/knowledge_graph.pkl (new graph)")
    print("   • data/knowledge_graph_old.pkl (backup)")

    print("\n🔄 Next steps:")
    print("   1. Embeddings and BM25 indexes are already built from messages")
    print("   2. Test retrieval with assignment examples")
    print("   3. Validate improvements in answer quality")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
