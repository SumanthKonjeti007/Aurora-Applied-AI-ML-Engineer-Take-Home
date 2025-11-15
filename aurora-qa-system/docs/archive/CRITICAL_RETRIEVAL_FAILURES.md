# Critical Retrieval Failures - 10-Query Test

**Date:** 2025-11-13
**Session:** Extended Testing Phase
**Status:** CRITICAL ISSUES IDENTIFIED

---

## Summary

**Total Queries:** 10
**Critical Retrieval Failures:** 2 (20%)
**Root Cause:** RRF fusion prioritizes messages that appear in multiple sources, dropping correct answers that rank medium in one source

---

## Failure #1: Query 3 - Louvre Private Tour Requests

### Query
"Which clients requested a private tour of the Louvre?"

### System Answer
- Layla Kawaguchi
- Lorenzo Cavalli ✅
- Sophia Al-Farsi ✅
- Amina Van Den Berg
- Fatima El-Tahir

### Ground Truth
- Vikram Desai ✅ (MISSED)
- Sophia Al-Farsi ✅
- Hans Müller ✅ (MISSED)
- Lorenzo Cavalli ✅
- Lily O'Sullivan ✅ (MISSED)

### Retrieval Analysis

**BM25 Rankings (Missing Users):**
- Lily O'Sullivan: #11 (score: 12.72) - "Louvre private tour"
- Vikram Desai: #12 (score: 12.50) - "private viewing at the Louvre"
- Hans Müller: #15 (score: 11.08) - "behind-the-scenes tour at the Louvre"

**Qdrant Rankings (Missing Users):**
- Vikram Desai: #4 (score: 0.7420) - "Arrange a private viewing at the Louvre"
- Lily O'Sullivan: #6 (score: 0.7393) - "Louvre private tour"
- Hans Müller: #8 (score: 0.7359) - "visit the Louvre after hours privately"

**RRF Top 10 User Distribution:**
- Lorenzo Cavalli: 3 messages
- Sophia Al-Farsi: 4 messages
- Amina Van Den Berg: 2 messages
- Fatima El-Tahir: 1 message
- **MISSING:** Vikram Desai (0), Hans Müller (0), Lily O'Sullivan (0)

### Root Cause

**RRF Bias:** Messages that rank high in BOTH sources get exponentially boosted:
- Lorenzo: #2 Qdrant + #1 BM25 → Dominates top 10
- Sophia: #1 Qdrant + #2/#4 BM25 → Dominates top 10

Messages that rank medium in one source get penalized:
- Vikram: #4 Qdrant + #12 BM25 → Dropped below rank 10
- Lily: #6 Qdrant + #11 BM25 → Dropped below rank 10
- Hans: #8 Qdrant + #15 BM25 → Dropped below rank 10

### Impact

**Recall:** 40% (2 out of 5 ground truth users retrieved)
**Precision:** 100% (but wrong users - Layla, Amina, Fatima also requested tours)

**Verdict:** ❌ CRITICAL - System missed 3/5 correct users

---

## Failure #2: Query 7 - Opera/Symphony/Ballet Tickets with Travel Dates

### Query
"Who asked for opera/symphony/ballet tickets and also mentioned travel dates near those events?"

### System Answer
- Thiago Monteiro
- Fatima El-Tahir ✅
- Sophia Al-Farsi

### Ground Truth
- Fatima El-Tahir ✅ (Dec 3rd, Dec 9th)
- Layla Kawaguchi ✅ (MISSED - Nov 25th)
- Hans Müller ✅ (MISSED - "next weekend")

### User Distribution Analysis

**Retrieved Messages (varies by run due to RRF instability):**
- Run 1: Thiago (6), Fatima (1), Amina (1), Hans (1), Sophia (1)
- Run 2: Thiago (4), Hans (3), Amina (1), Sophia (1), Vikram (1)

**Ground Truth Users Missing:**
- Layla Kawaguchi ❌ (missed in both runs)
- Fatima El-Tahir ⚠️ (1 message in run 1, 0 in run 2)

### Detailed Retrieval Analysis

**Fatima El-Tahir:**
- BM25 Best: **#12** (score: 8.56) - "symphony tickets in Berlin next winter"
- Qdrant Best: **#28** (score: 0.75) - "ballet performance on December 9"
- **Estimated RRF position: 79** → Dropped out of top 10
- **Actual data:** 3 messages with opera/symphony/ballet + dates

**Layla Kawaguchi:**
- BM25 Best: **#13** (score: 8.38) - "fashion week calendar" (NOT relevant!)
- Qdrant Best: **#12** (score: 0.77) - "Vienna opera for the night of December 5th" ✅
- **Estimated RRF position: 72** → Dropped out of top 10
- **Actual data:** 4 messages with opera/symphony/ballet + dates
  - "symphony on November 25"
  - "concert at Sydney Opera House this December"
  - "Vienna opera for the night of December 5th"
  - "best seats for the opera in Vienna this December"

**Hans Müller:**
- BM25 Best: **#4** (score: 9.96) - "The seats at the opera were perfect" (PAST TENSE, not a request!)
- Qdrant Best: **#32** (score: 0.75) - "Vienna Opera tickets were misplaced"
- **Estimated RRF position: 75** → Dropped out of top 10
- **Actual data:** 3 messages with requests:
  - "orchestra seats for Phantom of the Opera next weekend"
  - "front-row seating for the Ballet next Saturday"

### Root Cause

**Multi-faceted Failure:**

1. **BM25 Keyword Mismatch:**
   - Query: "opera/symphony/ballet tickets" + "travel dates"
   - Layla's best BM25 match (#13) is about "fashion week" (irrelevant!)
   - Hans's best BM25 match (#4) is past-tense feedback, not a request
   - Fatima's best match (#12) is relevant but too far down

2. **Qdrant Semantic Weakness:**
   - Ground truth users rank #12-#32 in Qdrant
   - Other users rank #1-#10 with similar queries

3. **RRF Fusion Drops Medium Rankers:**
   - Fatima: #12 BM25 + #28 Qdrant → RRF position ~79
   - Layla: #13 BM25 + #12 Qdrant → RRF position ~72
   - Hans: #4 BM25 + #32 Qdrant → RRF position ~75

4. **Message Pollution (Thiago):**
   - Thiago has multiple messages ranking medium in both sources
   - Dominates top 10 with 4-6 messages, crowding out single messages from correct users

### Impact

**Recall:** 33% (1 out of 3 ground truth users retrieved consistently)
**Precision:** 100% (but wrong users - Thiago dominated with 4-6 messages)
**RRF Instability:** Different results across runs (Fatima appeared in run 1, not in run 2)

**Verdict:** ❌ CRITICAL - System missed 2/3 correct users, BM25 keyword mismatch, Qdrant rankings too low

---

## Failure #3: Query 9 - Four Seasons Tokyo Suite Request

### Query
"For Four Seasons Tokyo, what suite type and nights were requested?"

### System Answer
- **Correct:** Thiago Monteiro - Presidential suite, 2 nights ✅
- **HALLUCINATED:** Fatima El-Tahir - 4 nights (suite type not specified) ❌

### Ground Truth
- **Thiago Monteiro:** Presidential suite, 2 nights ✅ (CORRECT)
- **Fatima El-Tahir:** NO MESSAGES about Four Seasons Tokyo

### What Actually Happened

**Messages Retrieved in Top 10:**

**Message #3 (Fatima):**
- "Schedule a spa day at Four Seasons for my wife and me..."
- Mentions: "Four Seasons"
- Does NOT mention: Tokyo, suite, nights, location

**Message #5 (Fatima):**
- "I'm spending 4 nights in Tokyo, and need some exclusive shopping recommendations..."
- Mentions: "4 nights", "Tokyo"
- Does NOT mention: Four Seasons, hotel, suite

**LLM Conflation:**
The LLM incorrectly combined these two separate messages:
- Message #3: "Four Seasons" (unspecified location)
- Message #5: "4 nights in Tokyo" (shopping, not accommodation)
- **Generated:** "Fatima El-Tahir: 4 nights at Four Seasons Tokyo"

### Data Verification

**Fatima's Actual Messages:**
- **Four Seasons messages (3 total):** JFK transfer, New Year's Eve reservation, spa day - NONE mention Tokyo
- **Tokyo messages (5 total):** Sunset view room, sushi restaurant, shopping (4 nights), Aman Tokyo spa, hotel credit card - NONE mention Four Seasons
- **Four Seasons + Tokyo:** **0 messages** ❌

### Root Cause

**Retrieval Pollution + LLM Hallucination:**

1. **Poor Retrieval Filtering:**
   - Query: "Four Seasons Tokyo suite requests"
   - Retrieved: Generic "Four Seasons" messages without location
   - Retrieved: Generic "Tokyo" messages without hotel
   - Neither message answers the question!

2. **No Query Constraint Enforcement:**
   - BM25 ranked "Four Seasons spa day" #3 (no Tokyo, no suite)
   - RRF ranked "4 nights in Tokyo shopping" #5 (no Four Seasons)
   - Both made top 10 despite missing critical constraints

3. **LLM Conflation:**
   - LLM saw "Four Seasons" + "4 nights in Tokyo" in separate messages
   - Incorrectly combined them into "4 nights at Four Seasons Tokyo"
   - Generated answer that appears plausible but is factually incorrect

### Impact

**Severity:** CRITICAL - This is dangerous hallucination

**Danger Level:** HIGH
- Not just missing information (like Query 3, 7)
- **Fabricating information** by combining unrelated facts
- User might trust and act on false information

**Precision:** 50% (1 correct answer, 1 hallucinated answer)

**Verdict:** ❌ CRITICAL - Partial hallucination, dangerous for user trust

---

## Common Patterns: Critical Failure Types

### Pattern A: RRF Fusion Drops Correct Users (Query 3, 7)

**Root Cause:**

1. **RRF favors frequency over relevance:**
   - Users with multiple medium-ranked messages dominate
   - Users with single high-ranked messages get dropped

2. **No diversity enforcement:**
   - System returns 10 messages, but may all be from 2-3 users
   - Correct users with 1-2 messages get crowded out

3. **Weighted average penalizes single-source excellence:**
   - Message ranks #4 Qdrant but #12 BM25 → RRF score drops
   - Message ranks #1 Qdrant AND #1 BM25 → RRF score soars

**Impact:** Missing correct answers (recall failure)

### Pattern B: Retrieval Pollution + LLM Hallucination (Query 9)

**Root Cause:**

1. **Poor query constraint enforcement:**
   - Query requires: "Four Seasons" AND "Tokyo" AND "suite"
   - Retrieval returns: "Four Seasons" OR "Tokyo" (missing conjunctions)
   - Separate messages satisfy parts of query, but not full query

2. **No semantic filtering for multi-constraint queries:**
   - BM25 matches keywords independently
   - Qdrant finds semantically similar but incomplete matches
   - RRF combines them without checking if all constraints are met

3. **LLM conflates partial matches:**
   - Message #3: "Four Seasons" (no Tokyo)
   - Message #5: "4 nights Tokyo" (no Four Seasons)
   - LLM combines: "4 nights at Four Seasons Tokyo" ❌

**Impact:** Fabricated information (precision failure, dangerous hallucination)

### Mathematical Example

**Scenario:** Retrieval for "Louvre tour"

**Message A (Vikram):**
- Qdrant: Rank #4 → RRF score = 1/(60+4) = 0.0156
- BM25: Rank #12 → RRF score = 1/(60+12) = 0.0139
- **Combined:** (0.0156 + 0.0139) / 2 = **0.0148**

**Message B (Lorenzo):**
- Qdrant: Rank #2 → RRF score = 1/(60+2) = 0.0161
- BM25: Rank #1 → RRF score = 1/(60+1) = 0.0164
- **Combined:** (0.0161 + 0.0164) / 2 = **0.0163**

**Result:** Message B (Lorenzo) ranks higher than Message A (Vikram), even though Vikram's Qdrant rank #4 is strong.

But Lorenzo has **3 messages** in top 20, while Vikram has **2 messages**. So Lorenzo dominates the top 10 with 3 slots, Vikram gets 0.

---

## Impact Assessment

### Severity: CRITICAL

**Total Failures:** 3 out of 10 queries (30%)

**Failure Types:**
- **Pattern A (RRF Fusion):** 2 queries (Query 3, 7) - Recall failures
- **Pattern B (Hallucination):** 1 query (Query 9) - Precision failure, dangerous

**Affected Query Types:**
- Aggregation queries ("Which clients...") - Pattern A
- Multi-user comparison queries - Pattern A
- Multi-constraint queries ("X AND Y AND Z") - Pattern B
- Any query requiring diversity in results - Pattern A

**Danger Levels:**
- **Pattern A:** Medium - Users get incomplete information
- **Pattern B:** HIGH - Users get fabricated information, may trust and act on it

### Comparison to Test #4 (Seating Preferences)

**Same Root Cause:**
- Test #4: Attribute-specific messages dropped below rank 10
- Query 3: Correct users dropped below rank 10
- Query 7: Correct users crowded out by over-represented user

**All 3 failures share:** RRF fusion does not enforce diversity or prioritize single-source excellence

---

## Proposed Fixes

### Fix 1: Increase top_k Before Composition (Quick Fix)

**Current:** Take top 10 after RRF
**Proposed:** Take top 20 after RRF, then diversify to top 10

**Pros:**
- Simple to implement
- Preserves existing RRF logic
- Increases recall

**Cons:**
- Doesn't fix root cause
- May introduce noise

**Estimated Effort:** 30 minutes

---

### Fix 2: Enforce User Diversity in Top-K (Recommended)

**Algorithm:**
```python
def diversify_by_user(results, max_per_user=2, top_k=10):
    """
    Ensure no single user dominates the top-k results

    Args:
        results: RRF-ranked messages
        max_per_user: Maximum messages per user (default: 2)
        top_k: Target number of results (default: 10)

    Returns:
        Diversified top-k results
    """
    diversified = []
    user_counts = {}

    for msg, score in results:
        user = msg['user_name']
        if user_counts.get(user, 0) < max_per_user:
            diversified.append((msg, score))
            user_counts[user] = user_counts.get(user, 0) + 1

            if len(diversified) >= top_k:
                break

    return diversified
```

**Application:**
- Apply after RRF fusion, before composition
- Ensures top 10 contains messages from at least 5 users (if max_per_user=2)

**Pros:**
- Fixes both Query 3 and Query 7 failures
- Simple to implement
- Maintains relevance while enforcing diversity

**Cons:**
- May exclude highly relevant messages from same user
- Requires tuning max_per_user parameter

**Estimated Effort:** 1-2 hours (implementation + testing)

---

### Fix 3: Hybrid Ranking with Single-Source Boosting

**Strategy:** Boost messages that rank in top 10 of ANY single source

```python
def hybrid_rank_with_boost(semantic_results, bm25_results, graph_results, weights, k=60):
    """
    RRF with boosting for single-source excellence
    """
    # Standard RRF
    fused = _reciprocal_rank_fusion(semantic_results, bm25_results, graph_results, k, weights)

    # Identify messages in top 10 of any source
    top_semantic_ids = {r['id'] for r, _ in semantic_results[:10]}
    top_bm25_ids = {r['id'] for r, _ in bm25_results[:10]}

    # Boost messages that rank top 10 in any source
    boosted = []
    for msg, score in fused:
        boost = 1.0
        if msg['id'] in top_semantic_ids or msg['id'] in top_bm25_ids:
            boost = 1.2  # 20% boost
        boosted.append((msg, score * boost))

    # Re-sort by boosted scores
    boosted.sort(key=lambda x: x[1], reverse=True)
    return boosted
```

**Pros:**
- Rewards single-source excellence (Vikram #4 Qdrant gets boosted)
- Maintains RRF benefits
- No diversity constraints

**Cons:**
- More complex
- Requires parameter tuning
- Doesn't directly address user over-representation

**Estimated Effort:** 2-3 hours

---

### Fix 4: Query-Type Adaptive Weighting

**Strategy:** Adjust RRF weights based on query type

**For Aggregation Queries ("Which clients..."):**
- Increase semantic weight (favor Qdrant)
- Reduce keyword weight (BM25 often matches too many generic words)
- Apply diversity enforcement

**Implementation:**
```python
# In query_processor.py
if query_type == "AGGREGATION":
    weights = {
        'semantic': 1.5,  # Boost from 1.0
        'bm25': 0.5,      # Reduce from 1.0
        'graph': 1.0
    }
```

**Pros:**
- Tailored to specific query types
- Addresses root cause for aggregation queries
- Maintains performance on other query types

**Cons:**
- Query type detection must be accurate
- Requires testing across all query types

**Estimated Effort:** 3-4 hours

---

### Fix 5: Multi-Constraint Query Validation (For Hallucination Prevention)

**Strategy:** Validate that retrieved messages satisfy ALL query constraints

**For Query 9:** "Four Seasons Tokyo suite requests"
- Extract constraints: ["Four Seasons", "Tokyo", "suite"]
- Filter messages that contain ALL three terms
- Reject partial matches

**Implementation:**
```python
def validate_multi_constraint(query, messages, min_constraint_coverage=0.8):
    """
    Filter messages to ensure they satisfy multiple query constraints

    Args:
        query: Original query string
        messages: Retrieved messages
        min_constraint_coverage: Minimum fraction of constraints that must be present

    Returns:
        Filtered messages that satisfy constraint threshold
    """
    # Extract key entities/constraints from query
    constraints = extract_constraints(query)  # ["Four Seasons", "Tokyo", "suite"]

    filtered = []
    for msg, score in messages:
        text = msg.get('message', '').lower()

        # Count how many constraints are satisfied
        satisfied = sum(1 for c in constraints if c.lower() in text)
        coverage = satisfied / len(constraints)

        if coverage >= min_constraint_coverage:
            filtered.append((msg, score))

    return filtered
```

**Application:**
- Apply after RRF fusion, before sending to LLM
- For conjunctive queries ("X AND Y AND Z"), require 100% constraint coverage
- For disjunctive queries ("X OR Y"), require 50% coverage

**Expected Impact:**
- Query 9: Would REJECT Fatima's messages (neither contains all 3 constraints)
- Would only send Thiago's message to LLM
- Prevents hallucination from partial matches

**Pros:**
- Directly addresses hallucination risk
- Simple to implement for common query patterns
- High precision improvement

**Cons:**
- May be too strict for some queries
- Requires constraint extraction logic
- May reduce recall if constraints are too rigid

**Estimated Effort:** 3-4 hours (constraint extraction + validation logic + testing)

---

### Fix 6: LLM Prompt Engineering (Quick Hallucination Mitigation)

**Strategy:** Add explicit instructions to prevent conflation

**Current Prompt Template:**
```
Based on the provided context, answer the following question:
{query}

Context:
{messages}
```

**Improved Prompt Template:**
```
Based on the provided context, answer the following question:
{query}

Context:
{messages}

IMPORTANT INSTRUCTIONS:
1. Only use information explicitly stated in the messages above
2. Do NOT combine facts from different messages unless they refer to the same event
3. If a message mentions only PART of what the question asks for, do NOT fill in missing details
4. If no message fully answers the question, say "No information available" rather than making assumptions

Example of what NOT to do:
- Message 1: "Book Four Seasons spa"
- Message 2: "4 nights in Tokyo"
- WRONG: "4 nights at Four Seasons Tokyo" (combines unrelated messages)
- CORRECT: "Message 1 mentions Four Seasons (location unspecified), Message 2 mentions Tokyo stay (hotel unspecified)"
```

**Expected Impact:**
- Query 9: LLM would recognize messages are about different things
- Would not conflate "Four Seasons spa" with "4 nights Tokyo shopping"
- More conservative answers, fewer hallucinations

**Pros:**
- Extremely quick to implement (prompt change only)
- No code changes required
- Can deploy immediately

**Cons:**
- LLMs may still hallucinate despite instructions
- Increases prompt length (token cost)
- Effectiveness varies by model

**Estimated Effort:** 15-30 minutes

---

## Recommended Action Plan

### Phase 1: Quick Wins (30-45 min)
1. **Implement Fix #6 (LLM Prompt Engineering)** - 15-30 min
   - Update prompt in `src/answer_generator.py`
   - Add explicit anti-hallucination instructions
   - Re-test Query 9 immediately

2. **Implement Fix #2 (User Diversity Enforcement)** - 30 min
   - Add `_diversify_by_user()` to `src/hybrid_retriever.py`
   - Apply after RRF fusion
   - Re-test Query 3 and Query 7

### Phase 2: Validation & Testing (1 hour)
1. Re-run all 3 failed queries:
   - Query 3 (Louvre) - Verify Vikram, Hans, Lily now appear
   - Query 7 (Opera/ballet) - Verify Layla, Fatima appear, Thiago limited to 2 messages
   - Query 9 (Four Seasons Tokyo) - Verify no Fatima hallucination

2. Quick regression test on all 10 queries
3. Document pass rate improvement

### Phase 3: Comprehensive Fixes (3-4 hours)
1. **Implement Fix #5 (Multi-Constraint Validation)** - 3-4 hours
   - Add constraint extraction logic
   - Filter messages before LLM generation
   - Test on multi-constraint queries

2. **Implement Fix #4 (Query-Type Adaptive Weighting)** - 2-3 hours
   - Adjust weights for aggregation queries
   - Test across all query types

### Phase 4: Long-Term (Future)
1. Implement query-focused re-ranking (from Test #4)
2. Add user feedback loop to refine weights
3. Consider neural re-ranker for final top 10
4. Fine-tune Qdrant embedding model for domain

---

## Testing Verification

### Re-Test Queries After Fix

**Query 3:** Should retrieve Vikram, Hans, Lily in top 10
**Query 7:** Should retrieve Layla, Hans in top 10 (without Thiago dominating)
**Query 4 (from 5-query checkpoint):** Should retrieve seating preference messages

### Success Criteria

- **Recall:** ≥80% for aggregation queries
- **User Diversity:** No single user has >30% of top 10 messages
- **Precision:** Maintained at current level

---

## Files to Modify

### For Fix #2 (User Diversity):
1. `src/hybrid_retriever.py` - Add `_diversify_by_user()` method
2. `src/hybrid_retriever.py` - Apply after RRF fusion (line ~530)

### For Fix #4 (Adaptive Weighting):
1. `src/query_processor.py` - Adjust weights based on query type (line ~150-200)
2. Test with different weight combinations

---

## Related Issues

**From 5-Query Checkpoint:**
- Test #4: Seating preferences - RRF fusion issue (Critical Issue #4 in MASTER_DOCUMENTATION.md)

**Total Failures by Type:**

**Pattern A - RRF Fusion (Recall Issues):**
- Test #4 (checkpoint): Seating preferences (1/5 queries)
- Query 3 (10-query): Louvre tours (1/10 queries)
- Query 7 (10-query): Opera/ballet tickets (1/10 queries)
- **Combined:** 3/15 queries (20% failure rate)

**Pattern B - Hallucination (Precision Issues):**
- Query 9 (10-query): Four Seasons Tokyo (1/10 queries)
- **Combined:** 1/15 queries (7% failure rate)

**Total Critical Failures:** 4/15 queries (27%)

---

## Conclusion

### Two Root Causes Identified

**Root Cause A - RRF Fusion Without Diversity:**
1. User over-representation (Thiago with 4-6 messages in top 10)
2. Single-source excellence penalized (Vikram #4 Qdrant → dropped to position 79)
3. Low recall for aggregation queries (missing 60% of correct users)
4. **Impact:** 20% of queries fail with incomplete answers

**Root Cause B - Retrieval Pollution + LLM Hallucination:**
1. Multi-constraint queries retrieve partial matches ("Four Seasons" OR "Tokyo" instead of AND)
2. No validation that messages satisfy all constraints
3. LLM conflates unrelated messages into fabricated facts
4. **Impact:** 7% of queries fail with dangerous hallucinations

### Priority Assessment

**HIGH PRIORITY - Pattern A (RRF Fusion):**
- **Impact:** 20% failure rate, users get incomplete information
- **Danger:** Medium - Missing information, not fabricating
- **Fix:** User Diversity Enforcement (#2) + Adaptive Weighting (#4)
- **Effort:** 3-4 hours

**CRITICAL PRIORITY - Pattern B (Hallucination):**
- **Impact:** 7% failure rate, users get fabricated information
- **Danger:** HIGH - False information may be trusted and acted upon
- **Quick Fix:** LLM Prompt Engineering (#6) - 15-30 min
- **Comprehensive Fix:** Multi-Constraint Validation (#5) - 3-4 hours
- **Total Effort:** 4 hours

### Recommended Immediate Actions

1. **Fix #6 (LLM Prompt)** - 15-30 min - Mitigate hallucination risk NOW
2. **Fix #2 (User Diversity)** - 30 min - Improve recall for aggregation queries
3. **Re-test all 3 failures** - 30 min - Verify improvements
4. **Expected pass rate:** 60% → 80%+ (12/15 queries)

---

**Next Steps:** Implement Fix #6 (hallucination prevention) and Fix #2 (diversity enforcement) immediately, then re-test Query 3, 7, and 9 to verify improvement.
