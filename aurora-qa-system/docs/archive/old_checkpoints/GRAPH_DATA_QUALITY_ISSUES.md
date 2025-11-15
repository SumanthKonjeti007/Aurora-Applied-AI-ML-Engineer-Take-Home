# Knowledge Graph Data Quality Issues

**Date**: 2025-11-11
**Status**: ⚠️ FAIR quality (79% clean, but wrong entities extracted)

---

## Executive Summary

The knowledge graph extraction has **fundamental semantic issues**:
- ✅ 79% clean entities (21% noise filtered)
- ❌ **Wrong entities extracted** - Captures grammatical objects, not semantic entities
- ❌ **Cannot answer key questions** due to missing critical data

**Example**: "Is it possible to get a Bentley for my Paris trip?"
- **Extracted**: `Vikram OWNS "my Paris trip"` ❌
- **Should be**: `Vikram RENTED/BOOKED "Bentley"` ✅

---

## Detailed Findings

### 1. Entity Quality: 21.4% Noise

**Top noise entities** (should have been filtered):
```
for         : 247 occurrences  ⚠️
in          :  92 occurrences  ⚠️
to          :  83 occurrences  ⚠️
on          :  78 occurrences  ⚠️
at          :  69 occurrences  ⚠️
it          :  12 occurrences  ⚠️
```

**Impact**: 696 out of 3247 triples (21%) are noise words

**Mitigation**: Graph building filters these (lines 40-42 in `knowledge_graph.py`)
- 675 noise triples removed → 2572 clean edges

---

### 2. Relationship Extraction Issues

#### OWNS (1638 triples)
**Problem**: Captures grammatical objects, not owned entities

**Examples**:
```
❌ "Change car service to BMW" → OWNS "my regular car service"
   Should be: OWNS "BMW"

❌ "Get a Bentley for Paris trip" → OWNS "my Paris trip"
   Should be: RENTED/BOOKED "Bentley"

❌ "Update my profile" → OWNS "my profile"
   Should be: Ignored (not a real ownership)
```

**Quality**: ⚠️ POOR - Extracts wrong entities

---

#### PLANNING_TRIP_TO (509 triples)
**Problem**: Extracts random words, not destinations

**Examples**:
```
❌ "Looking for a tailor" → PLANNING_TRIP_TO "for"
❌ "Suspect overcharge" → PLANNING_TRIP_TO "overcharge"
❌ "Hotel room with pillows" → PLANNING_TRIP_TO "with"
```

**Quality**: ❌ BROKEN - Useless for answering "Where is X traveling?"

---

#### VISITED (423 triples)
**Problem**: Extracts non-location entities

**Examples**:
```
❌ "Haven't received itinerary" → VISITED "itinerary"
❌ "Noticed a charge" → VISITED "charge"
❌ "Accommodations exceeded expectations" → VISITED "expectations"
```

**Quality**: ❌ BROKEN - Useless for answering "Where has X visited?"

---

#### PREFERS (147 triples)
**Quality**: ✅ 80% GOOD

**Examples**:
```
✅ "I prefer Italian cuisine" → PREFERS "cuisine"
✅ "I prefer rooms with a view" → PREFERS "rooms"
⚠️ "I like the Jaguar E-type" → PREFERS "type" (should be "Jaguar E-type")
⚠️ "I like it" → PREFERS "it" (noise)
```

---

#### RENTED/BOOKED (485 triples)
**Quality**: ⚠️ MIXED (50% useful)

**Examples**:
```
✅ "Need front-row seats" → RENTED/BOOKED "seats"
✅ "Need two tickets" → RENTED/BOOKED "tickets"
❌ "Tickets to the opera" → RENTED/BOOKED "to" (noise)
❌ "Seats for the game on Nov 20" → RENTED/BOOKED "on" (noise)
```

---

### 3. Real-World Question Testing

#### ✅ Can Answer (Partially)
**Q: "What are Hans's preferences?"**
- Found: 10 PREFERS entities
- Quality: 80% (8 meaningful, 2 noise)
- Result: ✅ Can provide partial answer

---

#### ❌ Cannot Answer
**Q: "How many cars does Vikram Desai have?"**

**Messages in data**:
```
1. "Change my car service to the BMW instead of the Mercedes."
2. "Can you ensure a Tesla is waiting at the airport?"
3. "Is it possible to get a Bentley for my Paris trip?"
```

**What graph extracted**:
```
❌ Vikram OWNS "my regular car service" (not BMW)
❌ Vikram OWNS "my Paris trip" (not Bentley)
❌ Tesla not extracted at all
```

**Car-related entities found**: 7 (but 0 are actual car brands)

**Why it fails**: GLiNER + spaCy extracts dependency objects ("my car service") instead of named entities ("BMW")

---

**Q: "Where has Layla London visited?"**
- Found: 0 VISITED relationships
- Result: ❌ Cannot answer

---

**Q: "Where is Amira Khan planning to travel?"**
- Found: 0 PLANNING_TRIP_TO relationships
- Result: ❌ Cannot answer

---

## Root Cause Analysis

### Why Extraction Fails

**Current approach**: GLiNER (NER) + spaCy (dependency parsing)

**Problem**: Dependency parsing finds **grammatical objects**, not **semantic entities**

**Example**:
```
Message: "Change my car service to the BMW instead of the Mercedes."

Dependency parse:
  change --[dobj]--> service  ← Extracted as object
         --[prep_to]--> BMW
         --[prep_instead_of]--> Mercedes

Result: OWNS "my regular car service" ❌
Should: OWNS "BMW" + OWNS "Mercedes" ✅
```

**Why this happens**:
1. GLiNER identifies named entities (BMW, Mercedes, Tesla)
2. spaCy dependency parsing finds grammatical relationships
3. Dependency object ("service") is extracted, not the named entities
4. Result: Wrong triples

---

## Impact on Retrieval

### Graph Search Performance

**When it works** ✅:
- User-specific queries with direct relationships
- Example: "Hans's seats" → 2 RENTED/BOOKED "seats" ✅

**When it fails** ❌:
- Entity-specific queries (cars, destinations, places)
- Example: "Vikram's cars" → 0 car brands extracted ❌

### Current Test Results

**Graph-only performance**:
```
✅ "Hans front-row seats"        → 2/2 relevant (100%)
✅ "Hans's preferences"          → 10/10 relevant (100%)
❌ "Vikram's cars"               → 0 car brands (0%)
❌ "Layla's visited places"      → 0 places (0%)
❌ "Amira's travel destinations" → 0 destinations (0%)
```

**Overall**: 40% success rate on test queries

---

## Recommendation

### Short-term (Current MVP)

✅ **Keep current approach** but with **low graph weight**:
- Graph weight: 0.5-0.8 (down from 0.8)
- BM25 weight: 1.5 (primary)
- Semantic weight: 0.7 (secondary)

**Rationale**:
- Graph provides value for user-specific relationship queries
- But BM25 + Semantic are more reliable for entity queries
- 79% clean is acceptable for supplementary retrieval

---

### Medium-term (Production)

Improve entity extraction with **hybrid approach**:

**Option 1: LLM-based extraction**
```python
prompt = """
Extract (subject, relationship, object) from this message:
"{message}"

Focus on:
- OWNS: Actual possessions (cars, items, not "my profile")
- VISITED: Geographic locations only
- PLANNING_TRIP_TO: Destinations only
"""
```

**Cost**: $0.001/message × 3,349 = $3.35
**Quality**: 95%+ (from 79%)

**Option 2: Rule-based post-processing**
```python
# Filter out bad entities
if relationship == "OWNS":
    if entity in ["my profile", "my account", "my card"]:
        skip()  # Not real ownership

if relationship == "VISITED":
    if entity not in location_entities:
        skip()  # Not a place
```

**Cost**: $0
**Quality**: 85-90%

---

### Long-term (Scale)

**Fine-tune GLiNER** on luxury concierge domain:
- Train on labeled examples
- Focus on brands, locations, luxury items
- Expected quality: 90%+

---

## Conclusion

**Current Status**: ⚠️ FAIR (79% clean, but semantically incorrect entities)

**Can we proceed?**
- ✅ YES for MVP (with low graph weight)
- ✅ Graph adds value for some queries
- ⚠️  But BM25 + Semantic are more reliable

**Next steps**:
1. ✅ Keep graph weight low (0.5-0.8)
2. ✅ Rely primarily on BM25 + Semantic
3. ✅ Document limitations in README
4. 🔄 Improve extraction post-MVP if needed

**Overall assessment**: Acceptable for MVP, but improvement needed for production.
