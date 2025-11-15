# Next Session - Start Here

**Date:** 2025-11-13
**Last Session:** Prompt Fix + RRF Analysis
**Ready For:** RRF Diversity Filter Implementation

---

## Quick Context (30 seconds)

**Current Status:** 60% pass rate (6/10 queries passing)

**What We Fixed Last Session:**
- ✅ Prompt fix (Query 9 hallucination improved)

**What We Need To Fix Now:**
- ❌ RRF fusion dropping correct users (Query 3, 7, March 25th)

**The Solution:** Add diversity filter to RRF (30 minutes)

**Expected Result:** 60% → 75-80% pass rate

---

## Immediate Action Plan

### Step 1: Read Full Context (2 min)
```bash
cat SESSION_CHECKPOINT_RRF_FIX.md
```
**Key sections:**
- "The RRF Problem Explained" (page 1)
- "Implementation Plan for Next Session" (page 2)

---

### Step 2: Implement Diversity Filter (30 min)

**File to edit:** `src/hybrid_retriever.py`

**Two changes needed:**

**Change 1: Add new function (after line 460)**
```python
def _diversify_by_user(self, results, max_per_user=2, top_k=10):
    """Ensure no single user dominates results"""
    diversified = []
    user_counts = {}

    for msg, score in results:
        user = msg.get('user_name', 'Unknown')
        if user_counts.get(user, 0) < max_per_user:
            diversified.append((msg, score))
            user_counts[user] = user_counts.get(user, 0) + 1
            if len(diversified) >= top_k:
                break

    return diversified
```

**Change 2: Update search method (around line 530)**

Find:
```python
return fused_results[:top_k]
```

Replace with:
```python
wide_net = fused_results[:100]
diverse_results = self._diversify_by_user(wide_net, max_per_user=2, top_k=top_k)
return diverse_results
```

---

### Step 3: Test (10 min)

Run these 3 failing queries:

```bash
# Query 3 (currently missing Vikram, Hans, Lily)
python test_data_flow.py "Which clients requested a private tour of the Louvre?"

# Query 7 (currently missing Layla, Fatima)
python test_data_flow.py "Who asked for opera/symphony/ballet tickets and also mentioned travel dates near those events?"

# March 25th (currently missing Thiago)
python test_data_flow.py "Who had plans on March 25th, 2025?"
```

**Expected:** All 3 should now include the missing users ✅

---

### Step 4: Verify No Regressions (5 min)

Run 2 passing queries to ensure they still work:

```bash
python test_data_flow.py "What are Fatima El-Tahir's plans for next month?"
python test_data_flow.py "Who said a restaurant bill missed loyalty discounts?"
```

**Expected:** Both should still pass ✅

---

## The Problem We're Fixing

**Visual Example:**

**BEFORE (current):**
```
RRF produces 100 ranked messages:
Position 1:  Lorenzo   ✅ Sent to LLM
Position 2:  Sophia    ✅ Sent to LLM
Position 3:  Lorenzo   ✅ Sent to LLM
Position 4:  Sophia    ✅ Sent to LLM
Position 5:  Amina     ✅ Sent to LLM
Position 6:  Sophia    ✅ Sent to LLM
Position 7:  Fatima    ✅ Sent to LLM
Position 8:  Sophia    ✅ Sent to LLM
Position 9:  Amina     ✅ Sent to LLM
Position 10: Lorenzo   ✅ Sent to LLM
─── CUT OFF ───
Position 72: Lily      ❌ DROPPED (we need this!)
Position 75: Hans      ❌ DROPPED (we need this!)
Position 79: Vikram    ❌ DROPPED (we need this!)
```

**AFTER (with diversity):**
```
RRF produces 100, we take all 100, then apply diversity:

1. Lorenzo   ✅ (Lorenzo: 1)
2. Sophia    ✅ (Sophia: 1)
3. Lorenzo   ✅ (Lorenzo: 2 MAX)
4. Sophia    ✅ (Sophia: 2 MAX)
5. Amina     ✅ (Amina: 1)
6. Sophia    ❌ SKIP (already has 2)
7. Fatima    ✅ (Fatima: 1)
8. Sophia    ❌ SKIP (already has 2)
9. Amina     ✅ (Amina: 2 MAX)
10. Lorenzo  ❌ SKIP (already has 2)
...continue through 100...
72. Lily     ✅ (Lily: 1) ← Now included!
75. Hans     ✅ (Hans: 1) ← Now included!
79. Vikram   ✅ (Vikram: 1) ← Now included!
```

---

## Success Criteria

**Query 3 (Louvre):**
- ✅ Should include: Vikram, Hans, Lily (currently missing)
- ✅ Should still include: Lorenzo, Sophia (currently there)

**Query 7 (Opera):**
- ✅ Should include: Layla, Fatima (currently missing/inconsistent)
- ✅ Thiago limited to max 2 messages (currently 4-6)

**March 25th:**
- ✅ Should include: Thiago (currently missing)
- ✅ Should still include: Armand, Amina (currently there)

**Pass rate:** 60% → 75-80%

---

## After Implementation

**User has a question waiting.**

Once RRF fix is tested and working, ask user:
> "RRF diversity filter is working! What was your question?"

---

## Files You'll Need

**To Edit:**
- `src/hybrid_retriever.py` (add diversity filter)

**To Test With:**
- `test_data_flow.py` (run queries)

**For Reference:**
- `SESSION_CHECKPOINT_RRF_FIX.md` (full context)
- `CRITICAL_RETRIEVAL_FAILURES.md` (problem analysis)

---

## Estimated Timeline

- Implementation: 20 minutes
- Testing: 10 minutes
- **Total: 30 minutes**

Then address user's pending question.

---

**Ready to start!** 🚀

Open `SESSION_CHECKPOINT_RRF_FIX.md` for full details, or just follow the 4 steps above.
