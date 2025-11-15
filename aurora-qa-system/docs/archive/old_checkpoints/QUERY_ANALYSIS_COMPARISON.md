# Query Analysis Comparison

## Executive Summary

Testing two entity-specific queries reveals **critical issues with current static weights**:

| Query | Top Result Quality | Semantic Contribution | BM25 Dominance | Graph Contribution |
|-------|-------------------|----------------------|----------------|-------------------|
| **Vikram - Service Expectations** | ✅ Perfect | 0/5 (0%) | 5/5 (100%) | 1/5 (20%) |
| **Lily - Dining Reservations** | ❌ Wrong | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) |

**Key Finding:** Static weights waste resources on semantic search (0% contribution) while BM25 sometimes ranks irrelevant results first.

---

## Query 1: "What are Vikram Desai's specific service expectations?"

### Results Quality: ✅ EXCELLENT

**Top Result (Rank #1):**
> "We didn't enjoy the last hotel; the service was not up to our expectations."
> — Vikram Desai

**Analysis:** Perfect answer! Directly states Vikram's service expectations.

### Retrieval Breakdown

**Semantic Search (Top 10):**
- ❌ 0 messages from Vikram Desai
- ❌ All results from other users (Armand Dupont, Lorenzo Cavalli, etc.)
- ❌ Matched "service expectations" conceptually but ignored entity constraint

**BM25 Search (Top 10):**
- ✅ 10/10 messages from Vikram Desai
- ✅ Strong keyword matching: "Vikram Desai" + "service" + "expectations"
- ✅ Perfect entity filtering

**Graph Search (Top 8):**
- ✅ Detected user: "Vikram Desai"
- ✅ Keywords: service, expectations
- ✅ 8 relevant messages from Vikram

**RRF Fusion:**
- Winner: BM25#2 + Graph#3 → RRF#1
- Perfect result through combined signals

### Weight Efficiency

**Static Weights:**
```
semantic: 0.7  ← Wasted (0% contribution)
bm25:     1.5  ← Perfect (100% contribution)
graph:    0.8  ← Helpful (20% contribution)
```

**Optimal Weights for This Query:**
```
semantic: 0.3  (reduce wastage)
bm25:     2.0  (boost primary contributor)
graph:    1.2  (boost supporting contributor)
```

### Overlap Analysis
```
Semantic ∩ BM25:   0 messages (NO overlap!)
Semantic ∩ Graph:  0 messages (NO overlap!)
BM25 ∩ Graph:      1 message  (helpful redundancy)
```

---

## Query 2: "What dining reservations has Lily O'Sullivan requested for her trip?"

### Results Quality: ⚠️ MIXED

**Top Result (Rank #1):** ❌ WRONG
> "We found the event planner exceptional; thank her personally for us."
> — Lily O'Sullivan

**Problem:** This is about an event planner, NOT dining reservations!

**Better Results (Ranks #2-3):** ✅ CORRECT
- Rank #2: "Any update on the dinner reservation I requested in Venice?"
- Rank #3: "Can you get reservations at Osteria Francescana for the 25th?"

**Analysis:** Correct answers exist but are ranked lower due to BM25 overweighting "Lily O'Sullivan" + "requested" without sufficient "dining" specificity.

### Retrieval Breakdown

**Semantic Search (Top 10):**
- ⚠️ Only 1/10 from Lily O'Sullivan (rank #5)
- ⚠️ Semantic #5 was actually correct: "I'd like reservations at the chef's table in Alinea"
- ❌ But it ranked poorly (0.3355) vs other users' generic messages

**BM25 Search (Top 10):**
- ✅ 10/10 messages from Lily O'Sullivan (good entity filtering)
- ❌ But rank #1 is about "event planner", not dining
- ✅ Ranks #2-3 are correct dining reservations
- **Issue:** BM25 over-matched "Lily O'Sullivan" + "requested" without enough weight on "dining"

**Graph Search (Top 10):**
- ✅ Detected user: "Lily O'Sullivan"
- ⚠️ Detected relationship: "RENTED/BOOKED" (generic, not dining-specific)
- ⚠️ Keywords: dining, reservations, requested
- ⚠️ Returned 10 Lily messages but mostly about bookings (flights, hotels, tickets)
- ❌ 0/10 overlap with final top 10

**RRF Fusion:**
- Winner: BM25#1 → RRF#1 (wrong answer!)
- Should have been: BM25#2 or BM25#3 (correct dining reservations)

### Weight Efficiency

**Static Weights:**
```
semantic: 0.7  ← Wasted (0% contribution to top 5)
bm25:     1.5  ← Dominated (100% contribution) but imprecise
graph:    0.8  ← Wasted (0% contribution)
```

**Issue:** Graph found "RENTED/BOOKED" relationships but not dining-specific ones. BM25 dominated but ranked incorrectly.

### Overlap Analysis
```
Semantic ∩ BM25:   0 messages (NO overlap!)
Semantic ∩ Graph:  0 messages (NO overlap!)
BM25 ∩ Graph:      0 messages (NO overlap!)
```

**Complete disconnection** between all three methods!

---

## Cross-Query Patterns

### Pattern 1: Semantic Search is Consistently Useless for Entity Queries

**Both queries:**
- 0% contribution to top 5 results
- Failed to prioritize entity constraint (user name)
- Matched conceptual terms but ignored specificity

**Conclusion:** For ENTITY_SPECIFIC queries, semantic weight should be low (0.3 or less).

---

### Pattern 2: BM25 Dominates But Can Fail

**Vikram query:**
- ✅ BM25 performed perfectly
- Strong keyword matching found exact answer

**Lily query:**
- ⚠️ BM25 dominated but ranked incorrectly
- Over-matched entity name + generic term ("requested")
- Under-matched specific attribute ("dining")

**Conclusion:** BM25 needs high weight for entity queries BUT needs semantic support when BM25 alone is imprecise.

---

### Pattern 3: Graph Search is Underutilized

**Vikram query:**
- ✅ Graph contributed to #1 result (BM25#2 + Graph#3)
- Found relevant "service" mentions

**Lily query:**
- ❌ Graph detected generic "RENTED/BOOKED" relationship
- Didn't find dining-specific relationships
- 0% contribution

**Conclusion:** Graph needs better relationship detection OR queries need relationship-aware classification.

---

## Implications for Dynamic Weighting

### Finding 1: ENTITY_SPECIFIC Profile Needs Refinement

**Current thinking:**
```python
ENTITY_SPECIFIC = {'semantic': 0.5, 'bm25': 2.0, 'graph': 1.0}
```

**Problem:** Lily query shows BM25=2.0 alone is insufficient. We need semantic as a **tiebreaker** when BM25 results are ambiguous.

**Better approach:**
```python
# If query has entity + specific attribute (dining, service, travel)
ENTITY_SPECIFIC_PRECISE = {
    'semantic': 0.8,  # Use as tiebreaker
    'bm25': 1.8,      # Still primary
    'graph': 1.2      # Boost graph for relationship detection
}
```

### Finding 2: Multi-Intent is NOT the Problem

Both queries are **single-intent** and already show precision issues. Multi-intent decomposition won't fix this.

**Priority:** Fix weight allocation first.

### Finding 3: Graph Needs Relationship-Type Classification

Lily query shows graph detected "RENTED/BOOKED" (generic) when it should detect "DINING" (specific).

**Options:**
1. Improve graph relationship extraction during ingestion
2. Add query-to-relationship mapping in QueryProcessor
3. Use semantic search to filter graph results by attribute

---

## Recommended Architecture

### Phase 1: Enhanced QueryProcessor (Immediate)

```python
class QueryProcessor:
    def classify(self, query: str, name_resolver) -> Dict:
        # Step 1: Detect entity
        entity = name_resolver.resolve(query)

        if entity:
            # Step 2: Detect attribute specificity
            specific_attrs = ['dining', 'service', 'travel', 'booking', 'preferences']
            has_specific_attr = any(attr in query.lower() for attr in specific_attrs)

            if has_specific_attr:
                # High semantic weight for tiebreaking
                return {
                    'type': 'ENTITY_SPECIFIC_PRECISE',
                    'weights': {'semantic': 0.8, 'bm25': 1.8, 'graph': 1.2}
                }
            else:
                # Low semantic weight, high BM25
                return {
                    'type': 'ENTITY_SPECIFIC_BROAD',
                    'weights': {'semantic': 0.3, 'bm25': 2.0, 'graph': 1.0}
                }

        # Conceptual queries
        if any(kw in query.lower() for kw in ['ideas', 'relaxing', 'luxury']):
            return {
                'type': 'CONCEPTUAL',
                'weights': {'semantic': 1.8, 'bm25': 0.5, 'graph': 0.3}
            }

        # Aggregation queries
        if any(phrase in query.lower() for phrase in ['which members', 'who has']):
            return {
                'type': 'AGGREGATION',
                'weights': {'semantic': 1.2, 'bm25': 1.8, 'graph': 0.1}
            }

        # Default
        return {
            'type': 'BALANCED',
            'weights': {'semantic': 0.7, 'bm25': 1.5, 'graph': 0.8}
        }
```

**Key Innovation:** Split ENTITY_SPECIFIC into two profiles based on attribute specificity.

---

### Phase 2: Re-Ranking Layer (Future)

If QueryProcessor doesn't fix Lily query, add a **semantic re-ranker**:

1. Get top 20 from RRF fusion
2. Use semantic similarity to re-rank top 20 based on attribute match
3. Return final top 10

This is more complex but would fix the "event planner" vs "dining" precision issue.

---

## Next Steps

1. ✅ **Implement Enhanced QueryProcessor** (2-3 hours)
   - 4 weight profiles: ENTITY_SPECIFIC_PRECISE, ENTITY_SPECIFIC_BROAD, CONCEPTUAL, AGGREGATION
   - Use NameResolver for entity detection
   - Attribute-aware classification

2. ✅ **Test on Both Queries** (30 mins)
   - Does Lily query now rank dining reservations #1?
   - Does Vikram query still work correctly?

3. ⚠️ **Test on Conceptual Query** (30 mins)
   - "Show me ideas for a relaxing getaway"
   - Verify semantic weight boost helps

4. ❌ **Skip Multi-Intent** (for now)
   - No evidence it's needed yet
   - Fix precision first

---

## Conclusion

**Empirical data proves:**
1. ✅ Static weights waste 0.7 on semantic for entity queries
2. ⚠️ BM25 dominance can produce wrong top results (Lily query)
3. ✅ Simple weight profiles would immediately improve efficiency
4. ⚠️ Attribute-aware classification needed for precision

**Ship QueryProcessor with 4 profiles in the next 1-2 days.**
