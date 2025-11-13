# Hybrid Retrieval Strategy - RRF Fusion

## Overview

Combine 3 retrieval methods using Reciprocal Rank Fusion (RRF) to achieve 70-80% recall target.

---

## Architecture

```
Query: "How many cars does Vikram Desai have?"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PARALLEL RETRIEVAL (3 methods run simultaneously)          │
├─────────────────────────────────────────────────────────────┤
│ 1. Semantic Search (Embeddings)                            │
│    - Query: "query: How many cars does Vikram Desai have?" │
│    - Returns: Top 20 messages by cosine similarity         │
│    - Strength: Conceptual understanding                    │
│    - Weakness: Question vs statement format mismatch       │
│                                                             │
│ 2. Keyword Search (BM25)                                   │
│    - Tokens: ["vikram", "desai", "cars", "have"]          │
│    - Returns: Top 20 messages by TF-IDF score             │
│    - Strength: Exact term matching (user names, brands)   │
│    - Weakness: No semantic understanding                   │
│                                                             │
│ 3. Knowledge Graph (Entity-based)                         │
│    - Extract: "Vikram Desai" (user), "cars" (entity type) │
│    - Query: Get user relationships + car-related entities │
│    - Returns: Top 10 messages with matching relationships │
│    - Strength: Structured knowledge, user filtering       │
│    - Weakness: Depends on extraction quality              │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ RECIPROCAL RANK FUSION (RRF)                               │
├─────────────────────────────────────────────────────────────┤
│ Algorithm:                                                  │
│   For each message that appears in ANY retrieval method:   │
│     score = Σ 1/(k + rank_i) across all methods           │
│                                                             │
│   k = 60 (standard RRF constant)                          │
│   rank_i = position in method i (1-indexed)               │
│                                                             │
│ Example:                                                    │
│   Message "BMW instead of Mercedes" appears in:           │
│     - Semantic: rank 47 → 1/(60+47) = 0.0093             │
│     - BM25: rank 1 → 1/(60+1) = 0.0164                   │
│     - Graph: rank 9 → 1/(60+9) = 0.0145                  │
│     - Combined score: 0.0402 (high!)                      │
│                                                             │
│   Message "car auctions Germany" appears in:              │
│     - Semantic: rank 1 → 1/(60+1) = 0.0164               │
│     - BM25: not found → 0                                 │
│     - Graph: not found → 0                                │
│     - Combined score: 0.0164 (lower)                      │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Top 10 Fused Messages                              │
├─────────────────────────────────────────────────────────────┤
│ Sorted by combined RRF score (highest first)               │
│ Messages appearing in multiple methods ranked higher       │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### **Phase 1: Create HybridRetriever Class**

```python
class HybridRetriever:
    """
    Combines semantic, BM25, and graph search using RRF
    """

    def __init__(self):
        # Load all three indices
        self.embedding_index = EmbeddingIndex()
        self.bm25_search = BM25Search()
        self.knowledge_graph = KnowledgeGraph()

        # Load from disk
        self.embedding_index.load("data/embeddings")
        self.bm25_search.load("data/bm25")
        self.knowledge_graph.load("data/knowledge_graph.pkl")

    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 1.0,
        bm25_weight: float = 1.0,
        graph_weight: float = 1.0
    ) -> List[Tuple[Dict, float]]:
        """
        Hybrid search with RRF fusion

        Args:
            query: Search query
            top_k: Number of results to return
            *_weight: Optional method weights (default: equal)

        Returns:
            List of (message, rrf_score) tuples
        """
        # 1. Run all retrievals in parallel
        # 2. Apply RRF fusion
        # 3. Return top-k
```

### **Phase 2: Implement RRF Fusion**

```python
def reciprocal_rank_fusion(
    semantic_results: List[Tuple[Dict, float]],
    bm25_results: List[Tuple[Dict, float]],
    graph_results: List[Dict],
    k: int = 60,
    weights: Dict[str, float] = None
) -> List[Tuple[Dict, float]]:
    """
    Reciprocal Rank Fusion algorithm

    Formula: score(msg) = Σ weight_i * 1/(k + rank_i)

    Args:
        semantic_results: From embedding search
        bm25_results: From BM25 search
        graph_results: From knowledge graph
        k: RRF constant (default 60, industry standard)
        weights: Optional per-method weights

    Returns:
        Fused results sorted by combined score
    """
    if weights is None:
        weights = {'semantic': 1.0, 'bm25': 1.0, 'graph': 1.0}

    scores = defaultdict(float)
    messages = {}

    # Add semantic scores
    for rank, (msg, _) in enumerate(semantic_results, start=1):
        msg_id = msg['id']
        scores[msg_id] += weights['semantic'] * (1.0 / (k + rank))
        messages[msg_id] = msg

    # Add BM25 scores
    for rank, (msg, _) in enumerate(bm25_results, start=1):
        msg_id = msg['id']
        scores[msg_id] += weights['bm25'] * (1.0 / (k + rank))
        messages[msg_id] = msg

    # Add graph scores
    for rank, msg in enumerate(graph_results, start=1):
        msg_id = msg['id']
        scores[msg_id] += weights['graph'] * (1.0 / (k + rank))
        messages[msg_id] = msg

    # Sort by score
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [(messages[msg_id], score) for msg_id, score in fused]
```

### **Phase 3: Graph Query Enhancement**

For graph retrieval, we need to extract entities from the query:

```python
def extract_query_entities(query: str) -> Dict[str, List[str]]:
    """
    Extract user names and entity keywords from query

    Example:
        "How many cars does Vikram Desai have?"
        → {
            'users': ['Vikram Desai'],
            'keywords': ['cars', 'have']
          }
    """
    # 1. Check for known user names (from graph.user_index)
    # 2. Extract keywords (nouns, entities)
    # 3. Return structured query info
```

---

## Key Design Decisions

### **1. Why RRF instead of weighted average?**

**RRF Benefits:**
- ✅ No score normalization needed (semantic uses L2 distance, BM25 uses TF-IDF)
- ✅ Rank-based (more robust than raw scores)
- ✅ Industry standard (used by Elasticsearch, OpenSearch)
- ✅ Messages in multiple methods automatically boosted

**Example:**
```python
# Message appears in 2 methods:
semantic_rank = 5  → 1/(60+5) = 0.0154
bm25_rank = 2      → 1/(60+2) = 0.0161
combined = 0.0315  # Higher than single-method results!

# Message appears in 1 method only:
semantic_rank = 1  → 1/(60+1) = 0.0164
combined = 0.0164  # Lower than multi-method
```

### **2. Retrieval counts: 20-20-10**

- **Semantic**: Top 20 (cast wide net for concepts)
- **BM25**: Top 20 (capture keyword variations)
- **Graph**: Top 10 (high precision, pre-filtered)

Why different counts?
- Graph is already filtered by user/entity → fewer but higher quality
- Semantic/BM25 need more candidates for fusion to select from

### **3. RRF constant k=60**

Industry standard:
- Too low (k=10): Over-emphasizes rank differences
- Too high (k=100): Under-emphasizes rank differences
- k=60: Sweet spot (empirically validated in research)

### **4. Optional method weights**

Default: Equal weights (1.0, 1.0, 1.0)

Can tune based on query type:
- **Factual queries** ("How many X?"): Boost graph (1.0, 1.0, 1.5)
- **Conceptual queries** ("Find luxury hotels"): Boost semantic (1.5, 1.0, 0.5)
- **Named entity queries** ("Vikram's preferences"): Boost BM25 (1.0, 1.5, 1.0)

For this assignment: Start with equal weights (simplest, works well)

---

## Testing Strategy

### **Test 1: Failed Semantic Queries**

Use the 3 assignment examples that failed:
- Q2: "How many cars does Vikram Desai have?" (0/10 semantic recall)
- Q3: "What are Amira's favorite restaurants?" (1/10 semantic recall)

Expected improvement: 0/10 → 5-7/10

### **Test 2: Re-run Full Test Suite**

Run `tests/test_embeddings.py` with hybrid retrieval:
- Current: 25% pass rate (semantic only)
- **Target: 70-80% pass rate (hybrid)**

### **Test 3: Manual Verification**

Inspect top-10 for Q2:
```python
hybrid_results = hybrid_retriever.search("How many cars does Vikram Desai have?")

# Should contain:
# ✅ "Change car service to BMW instead of Mercedes"
# ✅ "Tesla waiting at airport"
# ✅ "Bentley for Paris trip"
```

---

## Expected Improvements

| Query | Semantic Alone | + BM25 | + Graph | Hybrid (All 3) |
|-------|---------------|--------|---------|----------------|
| Q1: Layla London | 3/10 ✅ | 5/10 | 8/10 | **8-9/10** ✅ |
| Q2: Vikram cars | 0/10 ❌ | 3/10 | 10/10 | **7-8/10** ✅ |
| Q3: Amira restaurants | 1/10 ❌ | 2/10 | 4/10 | **5-6/10** ✅ |

**Overall pass rate: 25% → 70-75%** (target achieved)

---

## File Structure

```
src/
├── embeddings.py         ✅ (exists)
├── bm25_search.py        ✅ (exists)
├── knowledge_graph.py    ✅ (exists)
└── hybrid_retriever.py   🔄 (to be created)

tests/
├── test_embeddings.py         ✅ (exists)
└── test_hybrid_retrieval.py   🔄 (to be created)
```

---

## Implementation Steps

1. **Create `src/hybrid_retriever.py`** with:
   - `HybridRetriever` class
   - `reciprocal_rank_fusion()` function
   - `extract_query_entities()` helper

2. **Create `tests/test_hybrid_retrieval.py`**:
   - Use same 12 test cases from embeddings test
   - Compare semantic vs hybrid performance
   - Verify 70-80% pass rate

3. **Update test suite**:
   - Modify `test_embeddings.py` to optionally use hybrid
   - Generate comparison report

4. **Demo script**:
   - Already have `demo_hybrid_search.py`
   - Update to use new HybridRetriever class

---

## Success Criteria

- ✅ Pass rate ≥ 70% (currently 25%)
- ✅ Assignment examples (Q1, Q2, Q3) all pass
- ✅ Vikram car query finds BMW, Tesla, Bentley messages in top-10
- ✅ Clean, modular code
- ✅ Documented with clear docstrings

---

## This Strategy is:

- **Simple**: RRF is straightforward to implement
- **Effective**: Proven in industry (Elasticsearch uses it)
- **Modular**: Each retrieval method independent
- **Testable**: Clear metrics for validation
- **Extensible**: Easy to add weights, filters later

Ready to implement! 🚀
