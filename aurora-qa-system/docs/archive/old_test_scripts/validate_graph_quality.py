"""
Comprehensive Knowledge Graph Data Quality Validation

Checks:
1. Triple quality - Are subject-relationship-object meaningful?
2. Entity quality - Are objects real entities or noise words?
3. Relationship correctness - Do triples make semantic sense?
4. Coverage - Can we answer actual questions?
"""
import sys
sys.path.append('src')

import json
from knowledge_graph import KnowledgeGraph
from collections import Counter

print("="*80)
print("KNOWLEDGE GRAPH DATA QUALITY VALIDATION")
print("="*80)

# Load graph and messages
kg = KnowledgeGraph()
kg.load("data/knowledge_graph.pkl")

with open('data/triples.json') as f:
    triples = json.load(f)

with open('data/raw_messages.json') as f:
    messages = json.load(f)

print(f"\n📊 Graph Statistics:")
print(f"  Total triples: {len(triples)}")
print(f"  Graph nodes: {kg.graph.number_of_nodes()}")
print(f"  Graph edges: {kg.graph.number_of_edges()}")
print(f"  Users: {len(kg.user_index)}")

# Get relationship distribution
rel_counts = Counter(t['relationship'] for t in triples)
print(f"\n📊 Relationship Types:")
for rel, count in rel_counts.most_common():
    print(f"  {rel:25s}: {count:4d} triples")

# 1. SAMPLE TRIPLES FROM EACH RELATIONSHIP TYPE
print("\n" + "="*80)
print("1. SAMPLE TRIPLES (with original messages)")
print("="*80)

for rel_type in rel_counts.keys():
    print(f"\n{'='*80}")
    print(f"Relationship: {rel_type}")
    print(f"{'='*80}")

    rel_triples = [t for t in triples if t['relationship'] == rel_type][:5]

    for i, triple in enumerate(rel_triples, 1):
        subject = triple['subject']
        obj = triple['object']
        msg_id = triple['message_id']

        # Find original message
        msg = next((m for m in messages if m['id'] == msg_id), None)

        print(f"\n{i}. {subject} --[{rel_type}]--> {obj}")
        if msg:
            print(f"   Original message: \"{msg['message'][:120]}...\"")

        # Quality check
        issues = []
        if len(obj) <= 2:
            issues.append("⚠️ Object too short")
        if obj.lower() in {'it', 'to', 'for', 'in', 'on', 'at', 'the', 'a', 'an'}:
            issues.append("⚠️ Noise word detected")
        if msg and obj.lower() not in msg['message'].lower():
            issues.append("⚠️ Object not in original message")

        if issues:
            print(f"   Issues: {', '.join(issues)}")

# 2. ENTITY QUALITY ANALYSIS
print("\n" + "="*80)
print("2. ENTITY QUALITY ANALYSIS")
print("="*80)

# Get all entities (objects)
all_objects = [t['object'] for t in triples]
object_counts = Counter(all_objects)

print(f"\nTotal unique entities: {len(object_counts)}")
print(f"\n📋 Most common entities (top 30):")
for entity, count in object_counts.most_common(30):
    # Check if it's a noise word
    is_noise = entity.lower() in {'it', 'to', 'for', 'in', 'on', 'at', 'the', 'a', 'an', 'type', 'time'}
    marker = "⚠️" if is_noise else "✅"
    print(f"  {marker} {entity:30s}: {count:3d} occurrences")

# Count noise words
noise_words = {'it', 'to', 'for', 'in', 'on', 'at', 'of', 'during', 'with', 'from', 'the', 'a', 'an', 'type', 'time'}
noise_count = sum(1 for obj in all_objects if obj.lower() in noise_words)
print(f"\n⚠️  Noise entities: {noise_count}/{len(all_objects)} ({noise_count/len(all_objects)*100:.1f}%)")

# 3. RELATIONSHIP CORRECTNESS CHECK
print("\n" + "="*80)
print("3. RELATIONSHIP CORRECTNESS - Can we answer real questions?")
print("="*80)

test_cases = [
    {
        "question": "What does Vikram Desai own?",
        "user": "Vikram Desai",
        "relationship": "OWNS",
        "expected_entities": ["BMW", "Tesla", "Mercedes", "Bentley", "car"]
    },
    {
        "question": "What are Hans Müller's preferences?",
        "user": "Hans Müller",
        "relationship": "PREFERS",
        "expected_entities": ["Italian cuisine", "rooms", "cars", "classic"]
    },
    {
        "question": "Where has Layla London visited?",
        "user": "Layla London",
        "relationship": "VISITED",
        "expected_entities": ["Paris", "London", "Dubai", "city", "place"]
    },
    {
        "question": "Where is Amira Khan planning to travel?",
        "user": "Amira Khan",
        "relationship": "PLANNING_TRIP_TO",
        "expected_entities": ["Maldives", "Paris", "Tokyo", "destination"]
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['question']}")
    print(f"   User: {test['user']}")
    print(f"   Relationship: {test['relationship']}")

    # Query graph
    rels = kg.get_user_relationships(test['user'], test['relationship'])
    entities = [r['object'] for r in rels]

    print(f"   Found {len(entities)} entities: {entities[:10]}")

    # Check quality
    if len(entities) == 0:
        print(f"   ❌ NO DATA - Cannot answer question")
    else:
        # Count meaningful entities
        meaningful = [e for e in entities if e.lower() not in noise_words and len(e) > 2]
        noise = [e for e in entities if e.lower() in noise_words or len(e) <= 2]

        print(f"   ✅ Meaningful: {len(meaningful)} - {meaningful[:5]}")
        if noise:
            print(f"   ⚠️  Noise: {len(noise)} - {noise[:5]}")

        # Calculate quality score
        quality = len(meaningful) / len(entities) * 100 if entities else 0
        if quality >= 70:
            print(f"   ✅ Quality: {quality:.0f}% - GOOD")
        elif quality >= 50:
            print(f"   ⚠️  Quality: {quality:.0f}% - FAIR")
        else:
            print(f"   ❌ Quality: {quality:.0f}% - POOR")

# 4. DETAILED EXAMPLE - VIKRAM'S CARS
print("\n" + "="*80)
print("4. DETAILED EXAMPLE: Vikram Desai's cars")
print("="*80)

vikram_owns = kg.get_user_relationships("Vikram Desai", "OWNS")
print(f"\nVikram has {len(vikram_owns)} OWNS relationships")

print(f"\n{'Object':<30s} | Original Message")
print("-"*80)

for rel in vikram_owns[:15]:
    obj = rel['object']
    msg_id = rel['message_id']
    msg = next((m for m in messages if m['id'] == msg_id), None)

    if msg:
        text = msg['message'][:60]
        is_car_related = any(word in text.lower() for word in ['car', 'bmw', 'tesla', 'mercedes', 'bentley', 'vehicle'])
        marker = "🚗" if is_car_related else "  "
        print(f"{marker} {obj:<28s} | {text}...")

# Can we answer "How many cars does Vikram have?"
car_related_msgs = []
for rel in vikram_owns:
    msg = next((m for m in messages if m['id'] == rel['message_id']), None)
    if msg:
        text = msg['message'].lower()
        if any(word in text for word in ['car', 'bmw', 'tesla', 'mercedes', 'bentley', 'audi', 'porsche', 'jaguar']):
            car_related_msgs.append((rel['object'], msg['message'][:80]))

print(f"\n🚗 Car-related OWNS relationships: {len(car_related_msgs)}")
for obj, msg in car_related_msgs[:10]:
    print(f"   • {obj}: {msg}...")

if len(car_related_msgs) >= 3:
    print(f"\n✅ SUFFICIENT DATA to answer 'How many cars does Vikram have?'")
else:
    print(f"\n⚠️  LIMITED DATA - May not answer 'How many cars does Vikram have?' accurately")

# 5. OVERALL ASSESSMENT
print("\n" + "="*80)
print("5. OVERALL ASSESSMENT")
print("="*80)

total_triples = len(triples)
edges_in_graph = kg.graph.number_of_edges()
filtered_out = total_triples - edges_in_graph

print(f"\n📊 Data Pipeline:")
print(f"  Raw triples extracted: {total_triples}")
print(f"  Filtered out (noise):  {filtered_out} ({filtered_out/total_triples*100:.1f}%)")
print(f"  Final edges in graph:  {edges_in_graph}")

print(f"\n📊 Entity Quality:")
noise_pct = noise_count / len(all_objects) * 100
if noise_pct < 10:
    print(f"  ✅ EXCELLENT - {100-noise_pct:.0f}% clean entities")
elif noise_pct < 20:
    print(f"  ✅ GOOD - {100-noise_pct:.0f}% clean entities")
elif noise_pct < 30:
    print(f"  ⚠️  FAIR - {100-noise_pct:.0f}% clean entities")
else:
    print(f"  ❌ POOR - {100-noise_pct:.0f}% clean entities")

print(f"\n📊 Recommendation:")
if noise_pct < 15 and edges_in_graph > 2000:
    print("  ✅ Graph quality is GOOD - Proceed with weight tuning")
elif noise_pct < 25:
    print("  ⚠️  Graph quality is FAIR - Consider improving extraction")
    print("     Current approach (GLiNER + spaCy) is acceptable for MVP")
else:
    print("  ❌ Graph quality is POOR - Improve entity extraction first")
    print("     Consider: Better NER model, LLM extraction, or rule-based filtering")

print("\n" + "="*80)
print("✅ Validation complete")
print("="*80)
