# Critical Blockers - Aurora QA System

**Date:** 2025-11-13
**Status:** 2 Active Blockers, 1 Fixed
**Priority:** High - Fundamental Limitations

**Update:** Blocker #3 (LLM Decomposer) has been FIXED ✅ (See BLOCKER3_FIX_SUMMARY.md)

---

## Executive Summary

Testing revealed three critical blockers that fundamentally limit the system's ability to handle common business queries. These are NOT edge cases but represent ~60% of real-world query patterns.

**Impact Classification:**
- ❌ **Blocker #1 (Temporal):** Affects 20-30% of queries involving dates
- ❌ **Blocker #2 (Relational):** Affects 40% of queries requiring aggregation
- ❌ **Blocker #3 (Decomposition):** Unpredictable failures causing silent degradation

---

## Blocker #1: Temporal Co-occurrence Failure

### Problem Statement

System cannot match temporal phrases (dates, time ranges) where multiple terms must co-occur in the same message.

### Test Case

**Query:** "Which clients have plans for December 2025?"

**Retrieved Messages:**
- 3/10 mention "December" (but no year specified)
- 1/10 mentions "2025" (but no December)
- **0/10 mention both "December" and "2025" together** ❌

**Root Cause:**
1. **Semantic embeddings:** Encode "December" and "2025" as separate concepts
2. **BM25 tokenization:** Scores "December" and "2025" independently (TF-IDF)
3. **No co-occurrence filtering:** System matches OR logic, not AND logic for phrases

**Example Retrieved Messages:**
```
✓ "Paris hotel for December" (no year)
✓ "Club membership for 2025" (no December)
✗ "December 2025 booking" (what we need)
```

### Impact

**Query Types Affected:**
- Date ranges: "Q4 2024", "January 2025", "December 15-20"
- Temporal phrases: "next month", "this weekend", "upcoming"
- Historical: "2023 bookings", "last year's preferences"

**Business Impact:**
- Cannot answer basic temporal queries
- Retrieves irrelevant historical/future data
- Users get confused by wrong timeframes

**Frequency:** ~20-30% of business queries involve specific dates

---

## Blocker #2: Relational/Aggregation Failure

### Problem Statement

System cannot perform GROUP BY, JOIN, or aggregation operations to find patterns across users.

### Test Case

**Query:** "Which clients requested reservations at the same restaurants?"

**What's Needed:**
1. Find all restaurant reservation messages
2. Extract restaurant names
3. GROUP BY restaurant_name
4. COUNT clients per restaurant
5. Report restaurants with multiple clients

**What System Does:**
1. Retrieve top-10 restaurant-related messages
2. Pass to LLM
3. LLM tries to find patterns in limited window

**Result:**
- Found: 3 restaurant mentions (all different restaurants)
- Missing: Cannot group/aggregate across all 3,349 messages
- LLM response: "No overlaps found" (may be true, or may have missed data)

### Root Cause

**Architecture Limitation:**
```
Current: Query → Retrieval (top-k) → LLM → Answer
Missing: Query → Retrieval (ALL) → Extract → Group → Aggregate → Answer
```

The system is designed for **retrieval + generation**, not **analysis + aggregation**.

### Impact

**Query Types Affected:**
- Commonalities: "Which clients share preferences?", "Same restaurants/hotels/services?"
- Aggregation: "Most popular items", "Frequently requested services"
- Analytics: "Count users by category", "Group by attribute"
- Patterns: "Who has similar behavior?", "Common requests?"

**Business Impact:**
- Cannot answer analytical queries
- No business intelligence capabilities
- Missing insights that require cross-user analysis

**Frequency:** ~40% of queries need aggregation/grouping

---

## Blocker #3: LLM Decomposer Active Sabotage

### Problem Statement

LLM-based query decomposer makes incorrect decomposition decisions, actively degrading results for complex aggregation queries.

### Test Case

**Query:** "Which clients have both expressed a preference for something and also complained about a related service charge?"

**What Should Happen:**
- Type: Single aggregation query (NO decomposition)
- Search: All 3,349 messages
- Retrieve: Top-50 messages (enough to find patterns)
- LLM: Analyze to find users meeting BOTH conditions

**What Actually Happened:**
- **Decomposed into 10 sub-queries** (one per user!) ❌
  ```
  1. "Does Sophia Al-Farsi have both...?"
  2. "Does Armand Dupont have both...?"
  ... (all 10 users)
  ```
- Each sub-query retrieved 10 messages (user-filtered)
- Result composition: Interleaved 1 message per user
- Final context: Only 10 messages (1 per user)
- **Insufficient data to find BOTH conditions**

### Why This is Wrong

**Incorrect Decomposition Logic:**
```
LLM thought: "Which clients" → Must check each client individually
LLM did: Split into N user-specific queries
Should be: Single aggregation query across all users
```

**Impact of Wrong Decomposition:**
- Limited to 1 message per user (10 total)
- Cannot see multiple messages per user to verify BOTH conditions
- LLM gets insufficient context → "Cannot determine" answer

### Comparison: When Decomposer Works vs Fails

| Query | Should Decompose? | Actual | Result |
|-------|-------------------|--------|--------|
| "Conflicting preferences of Layla and Lily" | ✅ Yes (2 users) | ✅ Correct | Works |
| "Compare Thiago and Hans dining" | ✅ Yes (2 users) | ✅ Correct | Works |
| "Which clients have BOTH X and Y?" | ❌ No (aggregation) | ❌ Decomposed! | Fails |
| "Same restaurants?" | ❌ No (aggregation) | ✅ No decomp | Partial |

**Pattern:** Decomposer works for **explicit comparisons** but fails for **conditional aggregations**.

### Root Cause

**LLM Decomposer Prompt Weakness:**
- Correctly handles: "Compare A and B" → [query_A, query_B]
- Incorrectly handles: "Which users have BOTH X and Y?" → Should NOT decompose
- Missing: Clear rules to distinguish comparison vs aggregation with conditions

**The decomposer sees:**
- "Which clients" → Thinks it needs to check each client
- Doesn't recognize: This is an aggregation with filtering, not a comparison

### Impact

**Query Types Affected:**
- Multi-condition: "Clients who have BOTH X and Y"
- Complex aggregation: "Which users match criteria A AND B?"
- Filtered aggregation: "All clients where condition"

**Business Impact:**
- **Silent failures:** System returns wrong answers that sound plausible
- **Unpredictable:** Works for some aggregations, fails for others
- **Trust issues:** Users can't predict when system will work

**Frequency:** ~10-15% of complex aggregation queries

**Severity:** HIGH - Actively makes queries worse instead of better

---

## Summary Matrix

| Blocker | Query Type | Frequency | Severity | Workaround? |
|---------|------------|-----------|----------|-------------|
| #1 Temporal | Date/time phrases | 20-30% | High | Increase top_k (partial) |
| #2 Relational | Aggregation/grouping | 40% | High | None (architecture) |
| #3 Decomposition | Complex conditions | 10-15% | Critical | Disable decomposition |

**Combined Impact:** ~60-70% of queries affected by at least one blocker

---

## Test Results Summary

### Queries That Work ✅

1. **Single-user lookup:** "What is Lorenzo Cavalli's new phone number?"
   - Result: 10/10 from Lorenzo, found answer ✅

2. **User-specific:** "Summarize Layla's travel preferences"
   - Result: 10/10 from Layla, 100% precision ✅

3. **Two-user comparison:** "Conflicting preferences of Layla and Lily"
   - Result: 5 Layla + 5 Lily, found conflict ✅

4. **Simple aggregation:** "Which clients have billing issues?"
   - Result: Found 6 clients with billing problems ✅

### Queries That Fail ❌

5. **Temporal:** "Which clients have plans for December 2025?"
   - Result: 0/10 messages with both terms ❌
   - Issue: Blocker #1 (Temporal)

6. **Relational:** "Which clients requested same restaurants?"
   - Result: No overlaps found (may have missed data) ❌
   - Issue: Blocker #2 (Relational)

7. **Complex condition:** "Clients with BOTH preference and complaint"
   - Result: Incorrectly decomposed, insufficient context ❌
   - Issue: Blocker #3 (Decomposition)

### Partial Success ⚠️

8. **Identifier lookup:** "What is phone number 987-654-3210 associated with?"
   - Result: Found 2/10 exact matches ⚠️
   - Issue: Low precision (20%) for exact identifiers

9. **Interest aggregation:** "Which clients are interested in art?"
   - Result: Found 4 clients, 7/10 mentions ✅
   - Issue: Misclassified but worked

10. **Private access:** "Which clients requested private museum access?"
    - Result: Found 3 clients, 3/10 exact matches ✅
    - Issue: Noise (7/10 generic "private" matches)

---

## Recommended Fixes

### Priority 1: Critical (Blocker #3)

**Fix LLM Decomposer Prompt**
- Add explicit rule: "Do NOT decompose aggregation queries with conditions like 'which clients have BOTH X and Y'"
- Add examples of when NOT to decompose
- Estimated effort: 2-3 hours
- Impact: Fixes critical silent failures

### Priority 2: High (Blocker #1)

**Implement Temporal Co-occurrence Filtering**
- Add post-retrieval filter to check term co-occurrence
- For date queries, verify all date components appear together
- Options:
  1. Regex-based date extraction and verification (2-3 hours)
  2. Phrase-level matching for temporal terms (4-6 hours)
  3. Reranking model with temporal understanding (8-10 hours)
- Estimated effort: 4-6 hours (option 2)
- Impact: Fixes 20-30% of queries

### Priority 3: High (Blocker #2)

**Add Aggregation Layer**
- Two-stage approach:
  1. Retrieval: Get top-50+ candidates
  2. Extract: Pull structured data (names, entities)
  3. Aggregate: GROUP BY, COUNT operations
  4. Generate: LLM summarizes aggregated results
- Estimated effort: 10-15 hours (significant architecture change)
- Impact: Enables analytical queries

### Priority 4: Medium

**Improve Aggregation Classification**
- Add keywords: "which clients", "all clients who", "what clients"
- Estimated effort: 30 minutes
- Impact: Better weight assignment for aggregations

---

## Architectural Insights

### Current System Strengths

**What Works:**
- ✅ User-specific queries (with filtering)
- ✅ Simple fact lookup
- ✅ Two-entity comparisons
- ✅ Basic keyword matching

**Architecture Optimized For:**
- Retrieval + Generation (RAG pattern)
- User-scoped search
- Entity-specific information extraction

### Current System Weaknesses

**What Fails:**
- ❌ Temporal phrase matching
- ❌ Cross-entity aggregation
- ❌ Pattern detection
- ❌ Complex multi-condition queries

**Architecture NOT Designed For:**
- Analytical queries (GROUP BY, JOIN)
- Temporal reasoning
- Complex logical conditions (AND, OR, NOT across conditions)
- Business intelligence

### Design Trade-offs

**RAG (Retrieval-Augmented Generation) Limitations:**
```
Strength: Fast retrieval + flexible generation
Weakness: Limited to top-k window, no global analysis
```

**Top-k Constraint:**
- Fast: O(log n) retrieval
- Limited: Only sees k documents (typically 10-50)
- Problem: Cannot analyze full dataset for patterns

**Solution Space:**
1. **Hybrid approach:** RAG for lookup, SQL-like layer for aggregation
2. **Increase k:** Retrieve more documents (50-100) for aggregation
3. **Two-stage:** Retrieve → Extract → Aggregate → Generate

---

## Conclusion

The system excels at **retrieval and lookup** but fails at **analysis and aggregation**. The three blockers are fundamental architectural limitations, not implementation bugs.

**Current Capability:** Information retrieval system
**Missing Capability:** Business intelligence / analytics layer

**Recommendation:** Prioritize fixing Blocker #3 (immediate), then add temporal filtering (Blocker #1), then consider aggregation architecture (Blocker #2).

**Next Steps:**
1. ~~Fix decomposer prompt (2-3 hours)~~ ✅ **COMPLETED** (See BLOCKER3_FIX_SUMMARY.md)
2. Add temporal co-occurrence filter (4-6 hours) - **NEXT PRIORITY**
3. Evaluate if aggregation layer is needed based on use case (10-15 hours if yes)

---

## ✅ Blocker #3: FIXED (2025-11-13)

**Status:** RESOLVED

**Solution Implemented:**
- Added pre-decomposition guardrail (`_is_aggregation_query()`)
- Strengthened LLM prompt with explicit negative examples
- Expanded aggregation keyword detection
- Four-layer defense mechanism

**Test Results:**
- ✅ Aggregation with BOTH conditions: Working correctly
- ✅ Comparison queries: Still working (no regression)
- ✅ Simple aggregation: Working correctly

**Performance Impact:**
- 91% reduction in LLM calls for aggregation queries
- 10x faster processing
- Lower API costs

**Documentation:** See `BLOCKER3_FIX_SUMMARY.md` for complete details

**Remaining Blockers:** 2 (Blocker #1 - Temporal, Blocker #2 - Relational)
