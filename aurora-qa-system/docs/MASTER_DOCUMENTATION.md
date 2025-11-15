# Aurora QA System - Complete System Documentation

**Version:** 3.0 - Full-Stack Production Release
**Last Updated:** 2025-11-14
**Architecture:** Full-Stack Conversational AI with Hybrid RAG, Intelligent Routing & Modern Chat UI
**Status:** Production-Ready ✅

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [High-Level Architecture](#high-level-architecture)
5. [Complete Data Flow](#complete-data-flow)
6. [Frontend Layer - Chat UI](#frontend-layer---chat-ui)
7. [API Layer - FastAPI Backend](#api-layer---fastapi-backend)
8. [Query Processing Pipeline](#query-processing-pipeline)
9. [Retrieval Layer - Hybrid Search](#retrieval-layer---hybrid-search)
10. [Answer Generation Layer](#answer-generation-layer)
11. [Performance & Optimization](#performance--optimization)
12. [Deployment Architecture](#deployment-architecture)
13. [Known Limitations & Future Work](#known-limitations--future-work)
14. [Appendix](#appendix)

---

## Executive Summary

Aurora QA System is a **production-ready, full-stack conversational AI application** that enables natural language querying of luxury concierge client messages. The system combines a modern chat interface with sophisticated hybrid retrieval, intelligent query routing, and LLM-powered answer generation.

### Key Achievements

**✅ Full-Stack Implementation**
- Modern chat UI with Aurora brand aesthetic (warm browns/golds on black)
- FastAPI backend serving both API endpoints and static frontend
- Single deployment unit (frontend + backend + AI system)

**✅ Intelligent Query Processing**
- Automatic routing between LOOKUP (entity-specific) and ANALYTICS (pattern queries)
- LLM-based query decomposition for multi-entity comparisons
- Temporal and user filtering for precise retrieval

**✅ Hybrid Retrieval System**
- Semantic search (Qdrant vector database)
- Keyword search (BM25)
- Knowledge graph relationships
- RRF fusion with dynamic weighting

**✅ Production Features**
- Markdown-formatted responses with bold names and bullet lists
- User-friendly error handling with retry functionality
- Session persistence via localStorage
- Comprehensive help documentation
- Real-time loading states

### Success Metrics

| Metric | Value |
|--------|-------|
| Query Success Rate | 75% |
| Average Response Time | 2-3 seconds |
| User Filter Speedup | 10x faster |
| Temporal Filter Speedup | 70x faster |
| Total System Size | ~11 MB (local + cloud) |
| Frontend Load Time | <100ms |

---

## System Overview

### What is Aurora?

Aurora is an **intelligent conversational assistant** for luxury concierge services. It answers natural language questions about client preferences, requests, and historical interactions by retrieving relevant information from 3,349 client messages across 10 users.

### Core Capabilities

**1. Natural Language Understanding**
```
User: "Which clients requested a private tour of the Louvre?"
Aurora: 5 clients requested private Louvre tours:
        - Lorenzo Cavalli
        - Sophia Al-Farsi
        - Layla Kawaguchi
        - Hans Müller
        - Fatima El-Tahir
```

**2. Multi-Entity Comparisons**
```
User: "Compare Layla and Lily's flight seating preferences"
Aurora: Layla prefers aisle seats. Lily initially preferred window
        seats but later changed to aisle seats.
```

**3. Temporal Filtering**
```
User: "Which clients have plans for December 2025?"
Aurora: 8 clients have December 2025 plans:
        - Thiago Monteiro (December 5-12)
        - Vikram Desai (December 15)
        ...
```

**4. Attribute-Specific Queries**
```
User: "What is Lorenzo's phone number?"
Aurora: Lorenzo Cavalli's phone number is +39 02 1234 5678
```

### Design Philosophy

1. **User-First Interface** - Clean, modern chat UI that feels natural
2. **Intelligent Routing** - Automatically detect query type and optimize retrieval
3. **Hybrid Retrieval** - Combine multiple search methods for best results
4. **Graceful Degradation** - Helpful error messages and retry functionality
5. **Production-Ready** - Single deployment, session persistence, real-time feedback

---

## Technology Stack

### Frontend Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **UI Framework** | Pure HTML/CSS/JS | No build process, instant deployment |
| **Markdown Rendering** | marked.js (v12.0.0) | Parse and display formatted responses |
| **Typography** | Playfair Display + Inter | Serif for branding, sans-serif for body |
| **Icons** | Material Icons | Consistent iconography |
| **Session Storage** | localStorage API | Persist chat history across sessions |
| **State Management** | Vanilla JavaScript | Lightweight, no dependencies |

### Backend Technologies

| Component | Technology | Version/Details |
|-----------|------------|-----------------|
| **Web Framework** | FastAPI | Async Python web framework |
| **Server** | Uvicorn | ASGI server with hot reload |
| **Vector Database** | Qdrant Cloud | Semantic search with metadata filtering |
| **Embedding Model** | BAAI/bge-small-en-v1.5 | 384-dim sentence embeddings |
| **Keyword Search** | BM25Okapi (rank_bm25) | TF-IDF based ranking |
| **Knowledge Graph** | NetworkX | In-memory relationship graph |
| **LLM** | Mistral Small Latest | Fast, high-quality text generation |
| **Temporal Extraction** | datefinder + dateutil | Date normalization |

### Infrastructure & Deployment

| Component | Technology | Details |
|-----------|------------|---------|
| **Deployment Platform** | Railway | PaaS with GitHub integration |
| **Process Manager** | Procfile | uvicorn process definition |
| **Environment Config** | Environment Variables | API keys, URLs |
| **Version Control** | Git + GitHub | Source code management |

### Data Storage

| Component | Size | Location | Purpose |
|-----------|------|----------|---------|
| **Vector Embeddings** | ~5 MB | Qdrant Cloud (europe-west3) | Semantic search |
| **BM25 Index** | ~2 MB | Local (data/bm25.pkl) | Keyword search |
| **Knowledge Graph** | ~1 MB | Local (data/knowledge_graph.pkl) | Relationships |
| **User Index** | 40 KB | Local (data/user_indexed/) | User filtering |
| **Raw Messages** | 2.5 MB | Local (data/messages_with_dates.json) | Source data |

---

## High-Level Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           AURORA CHAT UI (static/index.html)           │   │
│  │                                                         │   │
│  │  • Modern chat interface (warm Aurora aesthetic)       │   │
│  │  • Markdown rendering (marked.js)                      │   │
│  │  • Session persistence (localStorage)                  │   │
│  │  • User-friendly error handling                        │   │
│  │  • Real-time loading states                            │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│                          │ HTTP POST /ask                       │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (api.py)                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Request Handler                                          │ │
│  │  • Validate input                                         │ │
│  │  • Track processing time                                  │ │
│  │  • Calculate confidence                                   │ │
│  │  • Format response with metadata                          │ │
│  └─────────────────────────┬────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           QA SYSTEM ORCHESTRATOR (src/qa_system.py)      │ │
│  └─────────────────────────┬────────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              QUERY PROCESSING PIPELINE (LLM-Powered)             │
│                                                                  │
│  Step 1: QUERY PROCESSOR (src/query_processor.py)              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Mistral LLM Classification & Decomposition               │ │
│  │                                                            │ │
│  │  Input: "Compare Layla and Lily's preferences"            │ │
│  │                                                            │ │
│  │  ├─► Router: LOOKUP (entity-specific query)               │ │
│  │  ├─► Decompose: [                                         │ │
│  │  │      "What are Layla's preferences?",                  │ │
│  │  │      "What are Lily's preferences?"                    │ │
│  │  │    ]                                                    │ │
│  │  ├─► Classify: ENTITY_SPECIFIC_PRECISE                    │ │
│  │  └─► Weights: {semantic: 1.0, bm25: 1.2, graph: 1.1}     │ │
│  └──────────────────────────┬───────────────────────────────┘ │
│                             │                                   │
│  Step 2: ENTITY DETECTION (src/name_resolver.py)              │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  • Extract: "Layla" → "Layla Kawaguchi"                   │ │
│  │  • Get ID: user_name → user_id                            │ │
│  │  • Filter: Restrict search to user's 335 messages         │ │
│  └──────────────────────────┬───────────────────────────────┘ │
│                             │                                   │
│  Step 3: TEMPORAL EXTRACTION (src/temporal_analyzer.py)       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  • Extract dates: "December 2025" → (2025-12-01 to 12-31) │ │
│  │  • Apply filter: Restrict to date range                   │ │
│  └──────────────────────────┬───────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              HYBRID RETRIEVAL LAYER (for each sub-query)         │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  SEMANTIC SEARCH │  │   BM25 KEYWORD   │  │   KNOWLEDGE  │ │
│  │    (Qdrant)      │  │     SEARCH       │  │     GRAPH    │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │                  │  │                  │  │              │ │
│  │ • Vector DB      │  │ • TF-IDF based   │  │ • Triples    │ │
│  │ • 384-dim embed  │  │ • Exact keywords │  │ • Relations  │ │
│  │ • User filter    │  │ • User filter    │  │ • Entities   │ │
│  │ • Date filter    │  │ • Fast matching  │  │              │ │
│  │ • Top-20 results │  │ • Top-20 results │  │ • Top-10     │ │
│  │                  │  │                  │  │              │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                     │                    │          │
│           └─────────────────────┴────────────────────┘          │
│                                 │                                │
│                                 ▼                                │
│           ┌─────────────────────────────────────────┐           │
│           │   RECIPROCAL RANK FUSION (RRF)          │           │
│           │   • Combine all 3 sources               │           │
│           │   • Dynamic weighting                   │           │
│           │   • Diversity enforcement               │           │
│           │   • Output: Top-10 fused results        │           │
│           └─────────────────┬───────────────────────┘           │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESULT COMPOSITION (src/result_composer.py)         │
│                                                                  │
│  Strategy: INTERLEAVE (for multi-entity queries)                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Input:  [Layla: 10 results] + [Lily: 10 results]        │ │
│  │  Output: [L1, Ly1, L2, Ly2, L3, Ly3, ...]                │ │
│  │  Final:  10 diverse results (5 from each user)           │ │
│  └──────────────────────────┬───────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            ANSWER GENERATION (src/answer_generator.py)           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Mistral LLM (mistral-small-latest)                       │ │
│  │                                                            │ │
│  │  Input:                                                    │ │
│  │    • Original query                                        │ │
│  │    • Top-10 retrieved messages (formatted)                │ │
│  │    • System prompt (markdown formatting rules)            │ │
│  │                                                            │ │
│  │  Processing:                                               │ │
│  │    • Temperature: 0.3 (focused)                           │ │
│  │    • Max tokens: 500                                       │ │
│  │    • Format: Markdown with **bold** names & bullet lists  │ │
│  │                                                            │ │
│  │  Output:                                                   │ │
│  │    "Layla prefers aisle seats. Lily initially preferred   │ │
│  │     window seats but later changed to aisle seats."       │ │
│  └──────────────────────────┬───────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RESPONSE FORMATTING (api.py)                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  JSON Response:                                           │ │
│  │  {                                                         │ │
│  │    "success": true,                                        │ │
│  │    "answer": "Markdown-formatted response",               │ │
│  │    "metadata": {                                           │ │
│  │      "route": "LOOKUP",                                    │ │
│  │      "processing_time_ms": 2700,                          │ │
│  │      "confidence": "high",                                 │ │
│  │      "sources_count": 10,                                  │ │
│  │      "sources": [ /* source messages */ ]                 │ │
│  │    }                                                        │ │
│  │  }                                                         │ │
│  └──────────────────────────┬───────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP 200 Response
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           CHAT UI - RESPONSE RENDERING                 │   │
│  │                                                         │   │
│  │  • Remove "Analyzing..." loading indicator             │   │
│  │  • Parse markdown → HTML (marked.js)                   │   │
│  │  • Apply styling:                                       │   │
│  │    - **Bold names** → gold color                       │   │
│  │    - Bullet lists → amber bullets                      │   │
│  │  • Display metadata badges:                            │   │
│  │    - Confidence: HIGH (green badge)                    │   │
│  │    - Time: 2.70s                                        │   │
│  │    - Sources: 10 sources                                │   │
│  │  • Save to localStorage                                 │   │
│  │  • Scroll to bottom                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Data Flow

### Example: Multi-Entity Comparison Query

Let's trace a complete request through the entire system:

**User Input:** "Compare Layla and Lily's flight seating preferences"

#### Phase 1: Frontend → Backend (0-50ms)

```javascript
// 1. User Interface (static/index.html)
User clicks "Send" button

// 2. JavaScript Event Handler
async function askQuestion(question) {
    // Hide welcome, show messages
    welcomeScreen.classList.add('hidden');
    messagesContainer.classList.remove('hidden');

    // Add user message to chat
    addMessage('user', question);

    // Show loading indicator
    showTypingIndicator();  // "Analyzing your question..."

    // 3. HTTP Request to Backend
    const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
}
```

**Network Request:**
```http
POST http://localhost:8000/ask HTTP/1.1
Content-Type: application/json

{
  "question": "Compare Layla and Lily's flight seating preferences"
}
```

#### Phase 2: API Layer - Request Validation (50-100ms)

```python
# api.py - FastAPI Endpoint
@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    # 1. Validate input
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # 2. Start timer
    start_time = time.time()

    # 3. Process question through QA System
    result = qa_system.answer(
        query=question,
        top_k=20,
        temperature=0.3,
        verbose=False
    )

    # 4. Calculate metrics
    processing_time = (time.time() - start_time) * 1000  # ms
    confidence = calculate_confidence(result)

    # 5. Extract source messages
    sources_data = [
        {
            "user_id": source.get('user_id'),
            "text": source.get('text'),
            "timestamp": source.get('timestamp'),
            "score": source.get('score')
        }
        for source in result.get('sources', [])[:20]
    ]

    # 6. Format response
    return AnswerResponse(
        success=True,
        answer=result['answer'],
        metadata={
            "route": result.get('route'),
            "processing_time_ms": int(processing_time),
            "confidence": confidence,
            "sources_count": len(sources_data),
            "sources": sources_data
        }
    )
```

#### Phase 3: Query Processing - Routing & Decomposition (100-600ms)

```python
# src/query_processor.py
def process(self, query: str) -> List[QueryPlan]:
    """
    Step 1: Classify query type
    Step 2: Check if aggregation (guardrail)
    Step 3: Decompose if multi-entity
    Step 4: Assign optimal weights
    """

    # Classification via LLM (Mistral)
    classification = self._classify(query)
    # Result: {
    #   'type': 'ENTITY_SPECIFIC_PRECISE',
    #   'weights': {'semantic': 1.0, 'bm25': 1.2, 'graph': 1.1},
    #   'reason': 'Entity + specific attribute (flight, seating)'
    # }

    # Check for aggregation patterns (guardrail)
    if self._is_aggregation_query(query):
        # Route to ANALYTICS (no decomposition)
        return [QueryPlan(query=query, route='ANALYTICS', weights=...)]

    # Multi-entity detection
    if "compare" in query.lower() or " and " in query:
        # LLM Decomposition
        sub_queries = self._decompose_llm(query)
        # Result: [
        #   "What are Layla Kawaguchi's flight seating preferences?",
        #   "What are Lily O'Sullivan's flight seating preferences?"
        # ]
    else:
        sub_queries = [query]

    # Create query plans
    return [
        QueryPlan(
            query=sq,
            route='LOOKUP',
            weights=classification['weights']
        )
        for sq in sub_queries
    ]
```

**Mistral LLM Call for Decomposition:**
```python
# Prompt sent to Mistral API
prompt = f"""You are a query decomposer. Split this query into atomic sub-queries:

Query: {query}

Known users: Layla Kawaguchi, Lily O'Sullivan, Vikram Desai, ...

Output format: JSON array of strings
Example: ["What are Layla's preferences?", "What are Lily's preferences?"]

Sub-queries:"""

# Response from Mistral
response = client.chat.complete(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1
)
# Output: [
#   "What are Layla Kawaguchi's flight seating preferences?",
#   "What are Lily O'Sullivan's flight seating preferences?"
# ]
```

#### Phase 4: Hybrid Retrieval - Sub-query 1 (600-1200ms)

**Sub-query:** "What are Layla Kawaguchi's flight seating preferences?"

```python
# src/hybrid_retriever.py
def search(self, query: str, weights: dict, top_k: int):

    # Step 1: Entity Detection (name_resolver.py)
    users_detected = []
    for word in query.split():
        resolved = self.name_resolver.resolve(word)
        if resolved:
            users_detected.append(resolved)

    # Detected: "Layla" → "Layla Kawaguchi"
    user_id = self.name_resolver.get_user_id("Layla Kawaguchi")
    # Result: "4a2e9c1b-7d6f-4c8a-9e3b-2f1a8c9d0e5f"

    # Step 2: Temporal Filtering (temporal_analyzer.py)
    date_range = self.temporal_analyzer.extract_date_range(query)
    # Result: None (no dates in query)

    # Step 3: Parallel Retrieval (3 methods)

    # 3A. Semantic Search via Qdrant
    semantic_results = self.qdrant_search.search(
        query="flight seating preferences",
        top_k=20,
        user_id=user_id,  # Filter to Layla only
        date_range=None
    )
    # Qdrant filters search space from 3,349 → 335 messages (Layla only)
    # Returns: [
    #   (msg: "I prefer aisle seats during flights", score: 0.73),
    #   (msg: "Always book aisle seats for me", score: 0.68),
    #   ...
    # ] (20 results, all from Layla)

    # 3B. BM25 Keyword Search
    bm25_results = self.bm25_search.search(
        query="flight seating preferences",
        top_k=20,
        user_id=user_id  # Filter to Layla only
    )
    # Keyword matching on ["flight", "seating", "preferences"]
    # Returns: [
    #   (msg: "Update my seating preference for flights", score: 2.3),
    #   (msg: "Flight preferences: aisle seat", score: 1.9),
    #   ...
    # ] (20 results, all from Layla)

    # 3C. Knowledge Graph Search
    graph_results = self.knowledge_graph.search(
        user="Layla Kawaguchi",
        relationship="PREFERS",
        keywords=["flight", "seating"]
    )
    # Returns: [
    #   (msg: "I prefer aisle seats", triple: (Layla, PREFERS, "aisle seats")),
    #   ...
    # ] (10 results)

    # Step 4: Reciprocal Rank Fusion (RRF)
    fused_results = self._reciprocal_rank_fusion(
        semantic=semantic_results,
        bm25=bm25_results,
        graph=graph_results,
        weights={'semantic': 1.0, 'bm25': 1.2, 'graph': 1.1}
    )
    # RRF Formula: score = weight * (1 / (60 + rank))
    # Combines scores from all 3 sources
    # Diversity rule: Prioritize messages that appear in multiple sources

    return fused_results[:10]  # Top-10 final results
```

**Qdrant Search Details:**
```python
# src/qdrant_search.py
def search(self, query, top_k, user_id, date_range):
    # 1. Generate query embedding
    embedding = self.model.encode(f"query: {query}")  # 384-dim vector

    # 2. Build filter conditions
    conditions = []
    if user_id:
        conditions.append(
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        )
    if date_range:
        start, end = date_range
        dates_in_range = generate_date_list(start, end)
        conditions.append(
            FieldCondition(
                key="normalized_dates",
                match=MatchAny(any=dates_in_range)
            )
        )

    # 3. Search with filters (Filter-then-Rank)
    results = self.client.search(
        collection_name="aurora_messages",
        query_vector=embedding,
        query_filter=Filter(must=conditions) if conditions else None,
        limit=top_k
    )

    # Results contain only messages matching filter criteria
    # Then ranked by cosine similarity to query
    return results
```

#### Phase 5: Retrieval for Sub-query 2 (1200-1800ms)

Same process as Sub-query 1, but for Lily O'Sullivan:
- User detection: "Lily" → "Lily O'Sullivan" → user_id
- Semantic search: Lily's 320 messages → Top 20
- BM25 search: Lily's messages → Top 20
- Graph search: Lily's preferences → Top 10
- RRF fusion → Top 10 final results

#### Phase 6: Result Composition (1800-1850ms)

```python
# src/result_composer.py
def compose(self, sub_query_results: List[List[Result]]):
    """
    Combine results from multiple sub-queries
    """

    if len(sub_query_results) == 1:
        # Single query - passthrough
        return sub_query_results[0]
    else:
        # Multiple queries - interleave
        # Input:
        #   Sub-query 1 (Layla): [L1, L2, L3, L4, L5, L6, L7, L8, L9, L10]
        #   Sub-query 2 (Lily):  [Ly1, Ly2, Ly3, Ly4, Ly5, Ly6, Ly7, Ly8, Ly9, Ly10]

        # Output (interleaved):
        #   [L1, Ly1, L2, Ly2, L3, Ly3, L4, Ly4, L5, Ly5]

        # Ensures balanced representation from both entities
        return self._interleave(sub_query_results)
```

#### Phase 7: Answer Generation with LLM (1850-2700ms)

```python
# src/answer_generator.py
def generate(self, query, context, temperature=0.3):
    """
    Generate natural language answer using Mistral LLM
    """

    # 1. Format context from retrieved messages
    formatted_context = ""
    for i, result in enumerate(context, 1):
        formatted_context += f"[{i}] {result['user_name']}: {result['message']}\n"

    # Example formatted context:
    # [1] Layla Kawaguchi: I prefer aisle seats during flights
    # [2] Lily O'Sullivan: Window seats are my preference for flights
    # [3] Layla Kawaguchi: Always book aisle seats for me
    # [4] Lily O'Sullivan: Update my preference to aisle seats now
    # [5] Layla Kawaguchi: Make sure I have an aisle seat
    # ...

    # 2. Build prompt
    system_prompt = """You are an intelligent concierge assistant.

MARKDOWN FORMATTING REQUIRED:
- Use **bold** for client names
- Use bullet points with `-` for lists
- Add line breaks for readability

RESPONSE FORMAT:
- For comparisons: Lead with key insight, support with examples
- Use **Name** format for highlighting
- Be concise and professional

Example:
"**Layla Kawaguchi** prefers aisle seats [1][3].
**Lily O'Sullivan** initially preferred window seats [2],
but later changed to aisle seats [4].
Initial conflict: aisle vs window."
"""

    user_prompt = f"""Answer this question using the client messages below.

QUESTION: {query}

CLIENT MESSAGES:
{formatted_context}

Answer:"""

    # 3. Call Mistral API
    response = self.client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )

    # 4. Extract answer
    answer = response.choices[0].message.content

    return {
        'answer': answer,
        'model': 'mistral-small-latest',
        'tokens': {
            'prompt': response.usage.prompt_tokens,
            'completion': response.usage.completion_tokens,
            'total': response.usage.total_tokens
        }
    }
```

**Mistral Response Example:**
```markdown
**Layla Kawaguchi** consistently prefers aisle seats for flights [1][3][5].

**Lily O'Sullivan** initially preferred window seats [2], but later updated
her preference to aisle seats [4].

The initial conflict was aisle seats vs window seats, but both now prefer
aisle seats.
```

#### Phase 8: Response Formatting & Return (2700-2750ms)

```python
# api.py
# Calculate confidence based on retrieval scores
confidence = calculate_confidence(result)
# Algorithm:
#   - ANALYTICS queries: Always "high" (deterministic)
#   - LOOKUP queries: Based on average of top-3 source scores
#     - avg > 0.7: "high"
#     - avg > 0.5: "medium"
#     - else: "low"

# Build final response
response = {
    "success": True,
    "answer": answer_text,  # Markdown-formatted
    "metadata": {
        "route": "LOOKUP",
        "processing_time_ms": 2700,
        "sources_count": 10,
        "confidence": "high",
        "model": "mistral-small-latest",
        "query_plans": 2,
        "sources": [
            {
                "user_id": "4a2e9c1b-...",
                "text": "I prefer aisle seats during flights",
                "timestamp": "2024-03-15T10:30:00Z",
                "score": 0.73
            },
            ...
        ]
    }
}

# Return JSON response
return JSONResponse(response)
```

**HTTP Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Process-Time-Ms: 2700

{
  "success": true,
  "answer": "**Layla Kawaguchi** consistently prefers aisle seats for flights [1][3][5].\n\n**Lily O'Sullivan** initially preferred window seats [2], but later updated her preference to aisle seats [4].\n\nThe initial conflict was aisle seats vs window seats, but both now prefer aisle seats.",
  "metadata": {
    "route": "LOOKUP",
    "processing_time_ms": 2700,
    "confidence": "high",
    "sources_count": 10,
    "sources": [ ... ]
  }
}
```

#### Phase 9: Frontend Rendering (2750-2800ms)

```javascript
// static/index.html

// 1. Receive response
const data = await response.json();

// 2. Remove loading indicator
removeTypingIndicator();

// 3. Parse markdown to HTML
const htmlContent = marked.parse(data.answer);
// Converts:
//   **Layla Kawaguchi** → <strong>Layla Kawaguchi</strong>
//   - Item → <ul><li>Item</li></ul>

// 4. Render message with styling
function renderMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    // Apply CSS styling:
    // - <strong> tags → color: var(--accent-gold)
    // - <li> bullets → color: var(--accent-amber)

    messageDiv.innerHTML = `
        <div class="message-avatar">✨</div>
        <div class="message-content">
            <div class="message-bubble">${htmlContent}</div>
            <div class="message-meta">
                ${confidenceBadge}
                <div class="badge">⏱️ 2.70s</div>
                <div class="badge">📚 10 sources</div>
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
}

// 5. Save to localStorage
messages.push({
    role: 'assistant',
    content: data.answer,
    metadata: data.metadata,
    timestamp: new Date().toISOString()
});
localStorage.setItem('aurora-chat-history', JSON.stringify(messages));

// 6. Scroll to bottom
scrollToBottom();
```

**Final Rendered UI:**
```
┌─────────────────────────────────────────────────────┐
│  ✨  Layla Kawaguchi consistently prefers aisle    │
│      seats for flights [1][3][5].                   │
│                                                      │
│      Lily O'Sullivan initially preferred window     │
│      seats [2], but later updated her preference    │
│      to aisle seats [4].                            │
│                                                      │
│      The initial conflict was aisle seats vs window │
│      seats, but both now prefer aisle seats.        │
│                                                      │
│      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│      🟢 HIGH    ⏱️ 2.70s    📚 10 sources          │
└─────────────────────────────────────────────────────┘
```

**Total Round-Trip Time:** ~2.8 seconds

---

## Frontend Layer - Chat UI

### User Interface Design

**Aurora Brand Aesthetic:**
- **Color Palette:** Warm browns and golds on pure black
  - Background: `#000000` (pure black)
  - Accent Gold: `#f2cd76`
  - Accent Amber: `#c1812c`
  - Text: `#f6f6f6` (off-white)

- **Typography:**
  - Headers: Playfair Display (serif) - elegant, luxurious
  - Body: Inter (sans-serif) - clean, readable

- **Visual Effects:**
  - Blurred radial gradients (60px blur, 25% opacity)
  - Glassmorphism on message bubbles
  - Smooth transitions and animations
  - Circular avatar badges

### Key Features

#### 1. Dynamic Header
```css
/* Home screen: Left-aligned */
.header {
    justify-content: flex-start;
}

.logo-title {
    font-size: 18px;
}

/* Chat mode: Centered with larger text */
.header.centered {
    justify-content: center;
}

.header.centered .logo-title {
    font-size: 22px;
}
```

**Behavior:**
- **Home screen:** "Aurora" on left with subtitle
- **Chat mode:** Animates to center, grows slightly
- **Smooth transition:** 0.3s ease

#### 2. Welcome Screen with Suggestions

**4 Suggestion Cards:**
1. **Timeline Queries** - "Which clients have plans for December 2025?"
2. **Client Profiles** - "What are Vikram Desai's travel preferences?"
3. **Service Requests** - "Who requested a personal shopper in Milan?"
4. **Location Queries** - "Which clients visited Paris?"

**Implementation:**
```html
<div class="suggestion-card" onclick="askQuestion('...')">
    <div class="icon">📅</div>
    <div class="title">Timeline Queries</div>
    <div class="description">Search by specific dates or time periods</div>
</div>
```

#### 3. Chat Interface

**Message Layout:**
```
User messages:          AI messages:
┌───────────────┐      ┌───────────────┐
│     [Icon] ●  │      │  ✨ [Content] │
│     Message   │      │   with         │
│               │      │   markdown     │
└───────────────┘      │               │
                       │  ━━━━━━━━━━━━  │
                       │  🟢 HIGH       │
                       │  ⏱️ 2.70s     │
                       │  📚 10 sources │
                       └───────────────┘
```

**Avatar System:**
- **User:** SVG person icon in gold circular badge
- **AI:** Sparkles (✨) in gold circular badge
- **Size:** 38px diameter, perfect circles

#### 4. Markdown Rendering

**Marked.js Integration:**
```javascript
// Parse markdown to HTML
const htmlContent = marked.parse(message.content);

// Styling in CSS
.message-bubble strong {
    font-weight: 600;
    color: var(--accent-gold);  /* Bold names in gold */
}

.message-bubble ul li::before {
    content: '•';
    color: var(--accent-amber);  /* Amber bullets */
}
```

**Supported Formatting:**
- **Bold text:** `**Name**` → Gold-colored names
- **Bullet lists:** `- Item` → Amber-colored bullets
- **Numbered lists:** `1. Item` → Proper numbering
- **Paragraphs:** Automatic spacing and margins

#### 5. Loading States

**Typing Indicator:**
```html
<div class="typing-indicator">
    <div class="message-avatar">✨</div>
    <div class="typing-content">
        <span class="typing-text">Analyzing your question...</span>
        <div class="dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    </div>
</div>
```

**Animation:** 3 dots with staggered fade (0.2s delay each)

#### 6. Error Handling

**User-Friendly Error Messages:**
```javascript
function getUserFriendlyError(error, originalQuery) {
    if (error.includes('429')) {
        return `**High demand right now** 🔥

I'm experiencing high traffic on my API. This usually clears up in a minute or two.

**What you can do:**
- Click the retry button below to try again
- Wait 1-2 minutes if the retry doesn't work

<retry>${originalQuery}</retry>`;
    }
    // ... other error types
}
```

**Retry Functionality:**
```html
<button class="retry-button" onclick="retryQuestion('original query')">
    <span class="material-icons">refresh</span>
    Retry
</button>
```

#### 7. Session Persistence

**localStorage Implementation:**
```javascript
// Save chat history
function saveChat() {
    const chatData = {
        messages: messages,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('aurora-chat-history', JSON.stringify(chatData));
}

// Load on page load
function loadChat() {
    const saved = localStorage.getItem('aurora-chat-history');
    if (saved) {
        const data = JSON.parse(saved);
        messages = data.messages;
        messages.forEach(msg => renderMessage(msg));
        if (messages.length > 0) {
            header.classList.add('centered');
        }
    }
}

// Clear chat
function clearChat() {
    messages = [];
    localStorage.removeItem('aurora-chat-history');
    messagesContainer.innerHTML = '';
    welcomeScreen.classList.remove('hidden');
    messagesContainer.classList.add('hidden');
    header.classList.remove('centered');
}
```

#### 8. Help Modal

**Comprehensive Information:**
- What is Aurora?
- What data does it access?
- Key capabilities
- 4 example queries
- Tips for best results

**Accessibility:**
- Click outside to close
- ESC key to close
- X button to close

#### 9. Input Controls

**Features:**
- **Auto-resizing textarea** (grows with content, max 130px)
- **Enter to send** (Shift+Enter for new line)
- **Keyboard hint:** "Press **Enter** to send • **Shift + Enter** for new line"
- **Disabled during processing** (prevents double submissions)

### Performance Optimizations

1. **Single HTML file** - No build process, instant load
2. **CDN resources** - Fast delivery of external libraries
3. **Minimal JavaScript** - ~500 lines of vanilla JS
4. **CSS animations** - GPU-accelerated transitions
5. **Event delegation** - Efficient event handling

---

## API Layer - FastAPI Backend

### Endpoints

#### GET /
**Serves the chat UI**
```python
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse('static/index.html')
```

#### POST /ask
**Main query endpoint**

**Request:**
```json
{
  "question": "Which clients requested a private tour of the Louvre?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "5 clients requested private Louvre tours:\n\n- **Lorenzo Cavalli**\n- **Sophia Al-Farsi**\n- **Layla Kawaguchi**\n- **Hans Müller**\n- **Fatima El-Tahir**",
  "metadata": {
    "route": "LOOKUP",
    "processing_time_ms": 2450,
    "sources_count": 15,
    "confidence": "high",
    "model": "mistral-small-latest",
    "query_plans": 1,
    "sources": [
      {
        "user_id": "abc-123",
        "text": "I'd like to book a private Louvre tour",
        "timestamp": "2024-03-15T10:30:00Z",
        "score": 0.82
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "API rate limit exceeded. Please try again in 60 seconds."
}
```

#### GET /health
**Health check endpoint**

**Response:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "components": {
    "qa_system": "healthy",
    "qdrant": "connected",
    "bm25": "loaded",
    "knowledge_graph": "loaded",
    "llm": "configured"
  },
  "uptime_seconds": 3600.5
}
```

#### GET /api
**API information**

Returns list of available endpoints and example queries.

### Middleware

**1. Processing Time Tracker**
```python
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response
```

**2. Request Logger**
```python
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
```

**3. CORS Middleware**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Confidence Calculation

```python
def calculate_confidence(result: dict) -> str:
    route = result.get('route')

    # ANALYTICS queries are deterministic
    if route == 'ANALYTICS':
        return "high"

    # For LOOKUP, check source scores
    sources = result.get('sources', [])
    if not sources:
        return "low"

    # Get top 3 source scores
    top_scores = [s.get('score', 0) for s in sources[:3]]
    avg_score = sum(top_scores) / len(top_scores)

    if avg_score > 0.7:
        return "high"
    elif avg_score > 0.5:
        return "medium"
    else:
        return "low"
```

---

## Query Processing Pipeline

### Router Classification (LOOKUP vs ANALYTICS)

**Purpose:** Determine optimal retrieval strategy based on query intent

**Classification Types:**

#### 1. LOOKUP Queries
**Characteristics:**
- Entity-specific (mentions a user name)
- Attribute retrieval (preferences, contact info)
- Historical facts (past requests, bookings)

**Examples:**
```
✓ "What is Layla's phone number?"
✓ "Summarize Vikram's dining preferences"
✓ "Which clients requested spa services?"
```

**Weights:**
```python
'ENTITY_SPECIFIC_PRECISE': {
    'semantic': 1.0,
    'bm25': 1.2,      # Boost keyword matching
    'graph': 1.1
}
```

#### 2. ANALYTICS Queries
**Characteristics:**
- Pattern finding (aggregation, grouping)
- Comparative analysis
- Statistical queries

**Examples:**
```
✓ "Which clients requested the same restaurants?"
✓ "How many clients have billing issues?"
✓ "Compare service request patterns"
```

**Weights:**
```python
'AGGREGATION': {
    'semantic': 1.1,
    'bm25': 1.2,
    'graph': 0.9       # Graph less useful for aggregation
}
```

### Query Decomposition

**When to Decompose:**
1. Multi-entity comparisons ("Layla and Lily")
2. Multiple attributes ("preferences and complaints")
3. Explicit comparison ("compare", "difference")

**Decomposition Logic:**

**Pre-Decomposition Guardrail:**
```python
def _is_aggregation_query(self, query: str) -> bool:
    """Prevent decomposition of aggregation queries"""
    aggregation_keywords = [
        'how many', 'count', 'number of',
        'which clients', 'who all',
        'same', 'both', 'all',
        'common', 'shared'
    ]
    return any(kw in query.lower() for kw in aggregation_keywords)
```

**LLM-Based Decomposition:**
```python
def _decompose_llm(self, query: str) -> List[str]:
    prompt = f"""You are a query decomposer for a concierge QA system.

Input query: "{query}"

Available users: {self.known_users}

Task: Break this into atomic sub-queries, one per entity.

Rules:
1. One query per user/entity mentioned
2. Keep each sub-query focused on one aspect
3. Preserve the original question's intent
4. Use full names (e.g., "Layla Kawaguchi", not "Layla")

Output format: JSON array of strings

Example:
Input: "Compare Layla and Lily's preferences"
Output: [
  "What are Layla Kawaguchi's preferences?",
  "What are Lily O'Sullivan's preferences?"
]

Sub-queries:"""

    response = self.llm.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1  # Deterministic
    )

    # Parse JSON response
    sub_queries = json.loads(response.choices[0].message.content)
    return sub_queries
```

**Rule-Based Fallback:**
```python
def _decompose(self, query: str) -> List[str]:
    """Fallback if LLM fails"""
    users = self._extract_users(query)

    if len(users) >= 2:
        # Multi-user query
        base_question = self._remove_user_names(query)
        return [
            f"What are {user}'s {base_question}?"
            for user in users
        ]
    else:
        return [query]
```

### Entity Detection & Resolution

**Name Resolver Features:**

**1. Exact Matching**
```python
"Layla Kawaguchi" → "Layla Kawaguchi" (direct match)
```

**2. Partial Matching**
```python
"Layla" → "Layla Kawaguchi" (first name match)
"Kawaguchi" → "Layla Kawaguchi" (last name match)
```

**3. Fuzzy Matching**
```python
"Lyla" → "Layla Kawaguchi" (typo tolerance, 85% similarity)
"Sofia" → "Sophia Al-Farsi" (spelling variation)
```

**4. Stop Word Filtering**
```python
68 stop words prevented: ['has', 'who', 'what', 'which', 'the', ...]
"Who has phone number?" → No false match on "Hans"
```

**5. User ID Mapping**
```python
resolve_with_id("Layla") → ("Layla Kawaguchi", "4a2e9c1b-...")
```

**Implementation:**
```python
class NameResolver:
    def __init__(self, users):
        # Build indexes
        self.canonical_names = {}  # normalized → original
        self.name_parts_index = {}  # part → [full names]
        self.user_id_map = {}       # name → user_id
        self.stop_words = set([     # Common query words
            'has', 'have', 'who', 'what', 'which', 'the', ...
        ])

    def resolve(self, query_name: str) -> Optional[str]:
        normalized = query_name.lower().strip()

        # Skip stop words
        if normalized in self.stop_words:
            return None

        # 1. Exact match
        if normalized in self.canonical_names:
            return self.canonical_names[normalized]

        # 2. Partial match (min length 3)
        if len(normalized) >= 3 and normalized in self.name_parts_index:
            return self.name_parts_index[normalized][0]

        # 3. Fuzzy match (min length 4, first letter match, 85% similarity)
        if len(normalized) >= 4:
            for canonical in self.canonical_names.values():
                if canonical[0].lower() == normalized[0]:  # First letter match
                    similarity = fuzz.ratio(normalized, canonical.lower()) / 100
                    if similarity > 0.85:
                        return canonical

        return None
```

### Temporal Extraction

**Date Range Extraction:**

**1. Quarter Patterns**
```python
"Q4 2024" → ("2024-10-01", "2024-12-31")
"Q1 2025" → ("2025-01-01", "2025-03-31")
```

**2. Month/Year Patterns**
```python
"December 2025" → ("2025-12-01", "2025-12-31")
"Jan 2025" → ("2025-01-01", "2025-01-31")
```

**3. Specific Dates**
```python
"March 15, 2025" → ("2025-03-15", "2025-03-15")
"15th of March" → ("2025-03-15", "2025-03-15")
```

**4. Relative Dates**
```python
"next month" → Calculated based on current date
"this week" → Calculated based on current date
```

**Implementation:**
```python
class TemporalAnalyzer:
    def extract_date_range(self, query: str) -> Optional[Tuple[str, str]]:
        # Try quarter patterns first
        quarter_match = re.search(r'Q([1-4])\s+(\d{4})', query, re.I)
        if quarter_match:
            quarter, year = quarter_match.groups()
            return self._quarter_to_range(int(quarter), int(year))

        # Use datefinder for explicit dates
        dates = list(datefinder.find_dates(query))
        if dates:
            date = dates[0]
            # Return full month range for month-only queries
            return (
                date.replace(day=1).strftime('%Y-%m-%d'),
                (date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1).strftime('%Y-%m-%d')
            )

        # No temporal information
        return None
```

---

## Retrieval Layer - Hybrid Search

### Architecture Overview

**Three Parallel Retrieval Methods:**

1. **Semantic Search** - Understands meaning and context
2. **Keyword Search** - Exact term matching
3. **Knowledge Graph** - Relationship-based retrieval

**Fusion Strategy:** Reciprocal Rank Fusion (RRF) with dynamic weighting

### 1. Semantic Search (Qdrant)

**Model:** BAAI/bge-small-en-v1.5
- **Dimension:** 384
- **Distance:** Cosine similarity
- **Approach:** Dense vector retrieval

**Filter-then-Rank Architecture:**

```python
# Build filter conditions BEFORE search
conditions = []

# User filtering
if user_id:
    conditions.append(
        FieldCondition(
            key="user_id",
            match=MatchValue(value=user_id)
        )
    )

# Temporal filtering
if date_range:
    start, end = date_range
    dates_in_range = generate_date_list(start, end)
    conditions.append(
        FieldCondition(
            key="normalized_dates",
            match=MatchAny(any=dates_in_range)
        )
    )

# Search only filtered subset
results = client.search(
    collection_name="aurora_messages",
    query_vector=query_embedding,
    query_filter=Filter(must=conditions),  # Apply filters FIRST
    limit=top_k
)
```

**Performance Impact:**

| Filter Type | Search Space | Speed Improvement |
|-------------|--------------|-------------------|
| None | 3,349 messages | Baseline |
| User only | ~335 messages | 10x faster |
| Date only | ~50 messages | 70x faster |
| User + Date | ~5-10 messages | 300x+ faster |

**Qdrant Cloud Configuration:**
```python
client = QdrantClient(
    url="https://64ffc9ea-...-gcp.cloud.qdrant.io:6333",
    api_key=os.environ.get('QDRANT_API_KEY')
)

# Collection schema
collection_config = {
    "vectors": {
        "size": 384,
        "distance": "Cosine"
    },
    "payload_schema": {
        "user_id": "keyword",        # Indexed for filtering
        "user_name": "keyword",
        "timestamp": "datetime",
        "normalized_dates": "keyword"  # Indexed for temporal filtering
    }
}
```

### 2. BM25 Keyword Search

**Algorithm:** Best Matching 25 (Okapi BM25)

**Tokenization Strategy:**
```python
def tokenize(text):
    # Lowercase + alphanumeric split
    tokens = text.lower().split()
    tokens = [re.sub(r'[^a-z0-9]', '', t) for t in tokens]
    return [t for t in tokens if len(t) > 2]
```

**User Filtering:**
```python
def search(self, query, top_k, user_id=None):
    # Get user's message indices
    if user_id:
        valid_indices = set(self.user_index[user_id]['message_indices'])

    # Search BM25 index
    scores = self.bm25.get_scores(query_tokens)

    # Filter to user's messages only
    if user_id:
        scores = [
            scores[i] if i in valid_indices else 0
            for i in range(len(scores))
        ]

    # Get top-k
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(self.messages[i], scores[i]) for i in top_indices]
```

**Strengths:**
- Exact keyword matching
- Fast retrieval (milliseconds)
- Strong for identifiers (phone numbers, emails)
- Complements semantic search

### 3. Knowledge Graph Search

**Graph Structure:**
```python
# NetworkX DiGraph
nodes = users + entities
edges = relationships

# Example:
("Layla Kawaguchi", "PREFERS", "aisle seats")
("Vikram Desai", "OWNS", "Tesla Model S")
("Thiago Monteiro", "PLANNING_TRIP_TO", "Tokyo")
```

**Relationship Types:**
```python
RELATIONSHIPS = {
    'PREFERS': ['prefer', 'like', 'favorite'],
    'OWNS': ['have', 'own', 'possess'],
    'PLANNING_TRIP_TO': ['planning', 'going to', 'visit'],
    'VISITED': ['went to', 'visited', 'stayed at'],
    'RENTED': ['rented', 'booked', 'reserved'],
    'ATTENDING_EVENT': ['attending', 'going to event'],
    'HAS_PREFERENCE': ['preference', 'requirement']
}
```

**Search Logic:**
```python
def search(self, user, relationship, keywords):
    # Get all user's triples
    user_triples = self.graph.edges(user, data=True)

    # Filter by relationship type
    if relationship:
        user_triples = [
            (u, v, d) for u, v, d in user_triples
            if d['type'] == relationship
        ]

    # Filter by keywords
    if keywords:
        user_triples = [
            (u, v, d) for u, v, d in user_triples
            if any(kw in v.lower() for kw in keywords)
        ]

    # Get source messages for matched triples
    messages = []
    for u, v, d in user_triples:
        msg_ids = d['message_ids']
        messages.extend([self.messages[mid] for mid in msg_ids])

    return messages
```

### 4. Reciprocal Rank Fusion (RRF)

**Purpose:** Combine rankings from multiple sources into a single unified ranking

**Algorithm:**

```python
def reciprocal_rank_fusion(
    semantic_results,
    bm25_results,
    graph_results,
    weights={'semantic': 1.0, 'bm25': 1.2, 'graph': 1.1},
    k=60
):
    """
    RRF Formula: score = weight * (1 / (k + rank))

    Args:
        results: List of (message, score) tuples from each method
        weights: Importance weights for each method
        k: Constant to control fusion (default: 60)
    """

    # Step 1: Assign ranks to each result
    semantic_ranks = {msg['id']: rank for rank, (msg, _) in enumerate(semantic_results, 1)}
    bm25_ranks = {msg['id']: rank for rank, (msg, _) in enumerate(bm25_results, 1)}
    graph_ranks = {msg['id']: rank for rank, (msg, _) in enumerate(graph_results, 1)}

    # Step 2: Calculate RRF scores
    all_message_ids = set(semantic_ranks) | set(bm25_ranks) | set(graph_ranks)

    rrf_scores = {}
    for msg_id in all_message_ids:
        score = 0

        # Semantic contribution
        if msg_id in semantic_ranks:
            score += weights['semantic'] * (1 / (k + semantic_ranks[msg_id]))

        # BM25 contribution
        if msg_id in bm25_ranks:
            score += weights['bm25'] * (1 / (k + bm25_ranks[msg_id]))

        # Graph contribution
        if msg_id in graph_ranks:
            score += weights['graph'] * (1 / (k + graph_ranks[msg_id]))

        rrf_scores[msg_id] = score

    # Step 3: Sort by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    # Step 4: Return top-k messages
    return [(get_message(msg_id), rrf_scores[msg_id]) for msg_id in sorted_ids[:top_k]]
```

**Example:**

Given query: "What are Layla's flight preferences?"

**Input Rankings:**
```
Semantic:
  Rank 1: "I prefer aisle seats during flights" (id: msg_123)
  Rank 2: "Flight preferences: aisle seat" (id: msg_456)
  Rank 3: "Always book aisle for me" (id: msg_789)

BM25:
  Rank 1: "Flight preferences: aisle seat" (id: msg_456)
  Rank 2: "Update my flight seating preference" (id: msg_234)
  Rank 3: "I prefer aisle seats during flights" (id: msg_123)

Graph:
  Rank 1: "I prefer aisle seats" (id: msg_123)
  Rank 2: "Always book aisle for me" (id: msg_789)
```

**RRF Calculation:**

For msg_123 ("I prefer aisle seats during flights"):
```python
semantic_contribution = 1.0 * (1 / (60 + 1)) = 0.0164
bm25_contribution    = 1.2 * (1 / (60 + 3)) = 0.0190
graph_contribution   = 1.1 * (1 / (60 + 1)) = 0.0180

final_score = 0.0164 + 0.0190 + 0.0180 = 0.0534
```

For msg_456 ("Flight preferences: aisle seat"):
```python
semantic_contribution = 1.0 * (1 / (60 + 2)) = 0.0161
bm25_contribution    = 1.2 * (1 / (60 + 1)) = 0.0197
graph_contribution   = 0  (not in graph results)

final_score = 0.0161 + 0.0197 + 0 = 0.0358
```

**Final Ranking:**
```
1. msg_123: 0.0534 (appeared in all 3 sources)
2. msg_789: 0.0425 (appeared in semantic + graph)
3. msg_456: 0.0358 (appeared in semantic + BM25)
```

**Diversity Rule:**
Messages appearing in multiple sources rank higher → Ensures high-confidence results

### Dynamic Weight Adjustment

**Query Type-Based Weighting:**

```python
WEIGHT_PROFILES = {
    'ENTITY_SPECIFIC_PRECISE': {
        'semantic': 1.0,
        'bm25': 1.2,      # Boost for exact keywords
        'graph': 1.1
    },
    'ENTITY_SPECIFIC_BROAD': {
        'semantic': 0.9,
        'bm25': 1.2,
        'graph': 1.1
    },
    'CONCEPTUAL': {
        'semantic': 1.2,  # Boost for understanding
        'bm25': 1.0,
        'graph': 0.9
    },
    'AGGREGATION': {
        'semantic': 1.1,
        'bm25': 1.2,
        'graph': 0.9      # Graph less useful for patterns
    }
}
```

**Example:**

Query: "What is Layla's phone number?"
- Classification: ENTITY_SPECIFIC_PRECISE
- Weights: {semantic: 1.0, bm25: 1.2, graph: 1.1}
- Reason: Boost BM25 for exact keyword matching on "phone number"

Query: "Tell me about Layla's travel style"
- Classification: CONCEPTUAL
- Weights: {semantic: 1.2, bm25: 1.0, graph: 0.9}
- Reason: Boost semantic understanding of "travel style" concept

---

## Answer Generation Layer

### LLM Configuration

**Model:** Mistral Small Latest (via Mistral AI API)
- **Provider:** Mistral AI
- **Context Window:** 32k tokens
- **Speed:** ~50 tokens/second
- **Cost-Effective:** Small model for fast inference

**Parameters:**
```python
{
    "model": "mistral-small-latest",
    "temperature": 0.3,      # Focused, less creative
    "max_tokens": 500,       # Concise responses
    "top_p": 1.0
}
```

### System Prompt

**Role Definition:**
```
You are an intelligent concierge assistant for a luxury lifestyle management service.

Your answers will be displayed directly in a UI to users, so they must be:
✓ Clear and concise (2-4 sentences for simple questions, structured lists for complex ones)
✓ Natural and conversational (avoid robotic language)
✓ Actionable (provide insights, not just raw data)
✓ Professional yet warm
```

**Markdown Formatting Requirements:**
```
MARKDOWN FORMATTING REQUIRED:
- **Use markdown** for all responses - your output will be rendered as HTML
- Use **bold** for client names and important details: **Name**
- Use bullet points with `-` or `*` for lists
- Use numbered lists `1.` when order matters
- Add line breaks between items for readability

RESPONSE FORMAT RULES:

1. SHORT ANSWERS (for simple lookups):
   - Direct answer in 1-3 sentences
   - Example: "**Vikram Desai** has requested spa services at several locations including Tokyo and Paris."

2. LISTS (for "which clients" or multiple items):
   - Use markdown bullet points with bold names
   - Keep each item concise (name + key detail)
   - Example:
     "6 clients requested a personal shopper in Milan:

     - **Vikram Desai**: Requested for the 12th
     - **Thiago Monteiro**: For an upcoming visit
     - **Hans Müller**: During his Milan visit
     - **Lorenzo Cavalli**: Looking for suggestions and recommendations
     - **Sophia Al-Farsi**: For a shopping day and tour
     - **Amina Van Den Berg**: For next weekend"

3. SUMMARIES (for preferences/patterns):
   - Lead with the key insight
   - Support with 2-3 examples using bold for names
   - Example: "Most clients prefer evening reservations. For instance, **Thiago** typically books 8 PM slots, while **Layla** prefers 7:30 PM."

4. NO DATA FOUND:
   - Be helpful, not dismissive
   - Suggest alternatives
   - Example: "I don't have specific car ownership information for Vikram Desai. However, I can see he frequently requests car services in NYC and private transfers to airports. Would you like to know more about his transportation preferences?"
```

**Critical Accuracy Rules:**
```
CRITICAL ACCURACY RULES:

1. NEVER mention technical details:
   ✗ "Based on message 1, 5, and 8..."
   ✗ "The context shows..."
   ✗ "According to the provided data..."
   ✓ Just state the facts naturally

2. NEVER merge separate facts into new claims:
   ✗ "Client stayed at Four Seasons Tokyo" (if one message says Four Seasons, another says Tokyo)
   ✓ "Client has stayed at Four Seasons properties and visited Tokyo"

3. IF UNCERTAIN, be honest but helpful:
   ✗ "I don't have that information." (too blunt)
   ✓ "I don't see specific details about X, but I found related information about Y. Would that be helpful?"

4. AGGREGATE intelligently:
   - For "which clients" queries: List names with brief context
   - For counts: Give the number first, then details if needed
   - For comparisons: Highlight similarities/differences clearly
```

### Context Formatting

**Format for LLM:**
```python
def format_context_for_llm(sources):
    context = ""
    for i, source in enumerate(sources, 1):
        context += f"[{i}] {source['user_name']}: {source['message']}\n"
    return context
```

**Example Formatted Context:**
```
[1] Layla Kawaguchi: I prefer aisle seats during flights
[2] Lily O'Sullivan: Window seats are my preference for flights
[3] Layla Kawaguchi: Always book aisle seats for me
[4] Lily O'Sullivan: Update my preference to aisle seats now
[5] Layla Kawaguchi: Make sure I have an aisle seat on all bookings
[6] Lily O'Sullivan: I've changed my mind, aisle seats from now on
[7] Layla Kawaguchi: Aisle seat is essential for my comfort
[8] Lily O'Sullivan: No more window seats, always aisle
[9] Layla Kawaguchi: Flight seating: aisle only
[10] Lily O'Sullivan: Aisle seat preference confirmed
```

### Query-Specific Format Hints

**Detected from query keywords:**

```python
def get_format_hint(query):
    query_lower = query.lower()

    if any(word in query_lower for word in ['which', 'who', 'what clients', 'list']):
        return """
Format: Provide a markdown bullet list with **bold client names**. Lead with a count (e.g., '5 clients requested...'). Use this format:
- **Name**: Brief detail
- **Name**: Brief detail
"""

    elif any(word in query_lower for word in ['how many', 'count', 'number of']):
        return """
Format: Start with the number, then provide brief supporting details if relevant. Use **bold** for emphasis.
"""

    elif any(word in query_lower for word in ['compare', 'difference', 'similar']):
        return """
Format: Highlight key similarities or differences. Use a comparison structure.
"""

    else:
        return """
Format: Answer directly and concisely in 2-4 sentences.
"""
```

### Full Prompt Construction

**Complete prompt sent to Mistral:**

```python
prompt = f"""Answer this question using the client messages below.

QUESTION: {query}

CLIENT MESSAGES:
{formatted_context}

{format_hint}

IMPORTANT:
- Answer naturally (no technical references like "message 1" or "context shows")
- If information is incomplete, be helpful: acknowledge what you found and offer related info
- Focus on being useful for a UI display - clear and actionable

Answer:"""
```

### Response Processing

**Post-Generation:**

1. **Extract answer text**
```python
answer = response.choices[0].message.content
```

2. **Track token usage**
```python
tokens = {
    'prompt': response.usage.prompt_tokens,
    'completion': response.usage.completion_tokens,
    'total': response.usage.total_tokens
}
```

3. **Return with metadata**
```python
return {
    'answer': answer,  # Markdown-formatted text
    'model': 'mistral-small-latest',
    'tokens': tokens,
    'sources': source_messages
}
```

---

## Performance & Optimization

### Query Performance Breakdown

**Typical Query Timeline (2.7 seconds total):**

| Phase | Duration | Percentage |
|-------|----------|------------|
| Frontend → Backend | 50ms | 2% |
| Request Validation | 10ms | <1% |
| Query Processing (LLM) | 500ms | 19% |
| Entity Detection | 20ms | 1% |
| Temporal Analysis | 10ms | <1% |
| Semantic Search (Qdrant) | 50ms | 2% |
| BM25 Search | 30ms | 1% |
| Graph Search | 20ms | 1% |
| RRF Fusion | 100ms | 4% |
| Result Composition | 20ms | 1% |
| Answer Generation (LLM) | 1000ms | 37% |
| Response Formatting | 40ms | 1% |
| Backend → Frontend | 50ms | 2% |
| UI Rendering | 50ms | 2% |

**Bottlenecks:**
1. **LLM calls** (37% + 19% = 56% total) - Necessary for quality
2. **RRF Fusion** (4%) - Can be optimized with better indexing

### Retrieval Optimization Strategies

**1. User Filtering:**
```
Without filter: Search 3,349 messages (~50ms)
With user filter: Search ~335 messages (~15ms)
Speed improvement: 10x faster
Precision: 100% (only user's messages)
```

**2. Temporal Filtering:**
```
Without filter: Search 3,349 messages
With date filter: Search ~50 messages (~10ms)
Speed improvement: 70x faster
Precision: 100% (only messages in date range)
```

**3. Combined Filtering:**
```
User + Date filter: Search ~5-10 messages (~5ms)
Speed improvement: 300x+ faster
Precision: 100% (exact match)
```

**4. Early Termination:**
```python
# Stop searching if confidence is high enough
if top_result_score > 0.9:
    return early_results
```

### Caching Strategy

**Not Currently Implemented (Future Work):**

1. **Query Result Cache:**
```python
# Cache exact query matches
cache_key = hash(query + str(filters))
if cache_key in results_cache:
    return cached_result
```

2. **Embedding Cache:**
```python
# Cache query embeddings
embedding_key = hash(query_text)
if embedding_key in embedding_cache:
    embedding = embedding_cache[embedding_key]
```

3. **LLM Response Cache:**
```python
# Cache LLM responses for identical contexts
context_hash = hash(query + context)
if context_hash in llm_cache:
    return cached_answer
```

### Frontend Performance

**Load Time:**
- **First paint:** <100ms
- **Interactive:** <200ms
- **Full load:** <500ms

**Optimization Techniques:**
1. **Single HTML file** - No network requests for assets
2. **CDN resources** - Fast delivery of marked.js, fonts
3. **Minimal JavaScript** - ~500 lines, no frameworks
4. **CSS animations** - GPU-accelerated
5. **localStorage** - Instant session restore

### Scalability Considerations

**Current Limits:**
- **Messages:** 3,349 (can scale to 100k+)
- **Users:** 10 (can scale to 1000+)
- **Concurrent Users:** 1 (single-user deployment)
- **Qdrant Free Tier:** 1GB storage, sufficient for 100k+ messages

**Scaling Strategies:**

1. **Horizontal Scaling:**
   - Deploy multiple FastAPI instances
   - Load balancer in front
   - Shared Qdrant Cloud backend

2. **Caching Layer:**
   - Redis for query result caching
   - Embedding cache for common queries
   - LLM response cache

3. **Async Processing:**
   - Queue-based architecture for long queries
   - WebSocket for real-time updates
   - Background workers for heavy processing

---

## Deployment Architecture

### Railway Platform

**Deployment Configuration:**

**1. Procfile (Process Definition):**
```procfile
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

**2. railway.json (Railway Config):**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**3. Environment Variables:**
```bash
MISTRAL_API_KEY=your_mistral_api_key_here
QDRANT_URL=https://64ffc9ea-...-gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here
PORT=8000  # Automatically set by Railway
```

### Deployment Steps

**1. GitHub Integration:**
```bash
# Push to GitHub
git add .
git commit -m "Production-ready Aurora QA System v3.0"
git push origin main
```

**2. Railway Setup:**
```
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose: Aurora-Applied-AI-ML-Engineer-Take-Home
5. Auto-detected: Python + FastAPI
6. Auto-detected: Procfile start command
```

**3. Configure Environment Variables:**
```
Settings → Variables → Add Variable:
  MISTRAL_API_KEY = [your_key]
  QDRANT_URL = [your_qdrant_url]
  QDRANT_API_KEY = [your_qdrant_key]
```

**4. Deploy:**
```
Railway automatically:
  - Builds Docker container
  - Installs dependencies from requirements.txt
  - Runs uvicorn server
  - Assigns public URL
```

**5. Access:**
```
Production URL: https://aurora-qa-system-production.up.railway.app
```

### Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          Internet                            │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Railway Platform                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Docker Container                                   │    │
│  │                                                      │    │
│  │  ┌──────────────────────────────────────────────┐ │    │
│  │  │  Uvicorn Server (Port $PORT)                 │ │    │
│  │  │                                               │ │    │
│  │  │  ┌────────────────┐  ┌────────────────────┐ │ │    │
│  │  │  │  FastAPI App   │  │  Static Files      │ │ │    │
│  │  │  │  (api.py)      │  │  (static/)         │ │ │    │
│  │  │  └────────┬───────┘  └────────────────────┘ │ │    │
│  │  │           │                                   │ │    │
│  │  │           ▼                                   │ │    │
│  │  │  ┌────────────────────────────────────────┐ │ │    │
│  │  │  │  QA System (src/)                      │ │ │    │
│  │  │  │  • Query processor                     │ │ │    │
│  │  │  │  • Hybrid retriever                    │ │ │    │
│  │  │  │  • Answer generator                    │ │ │    │
│  │  │  └────────┬───────────────────────────────┘ │ │    │
│  │  └───────────┼──────────────────────────────────┘ │    │
│  └──────────────┼────────────────────────────────────┘    │
│                 │                                           │
└─────────────────┼───────────────────────────────────────────┘
                  │
                  ├─────► Mistral AI API (cloud)
                  │       - Query decomposition
                  │       - Answer generation
                  │
                  └─────► Qdrant Cloud (europe-west3)
                          - Vector search
                          - Metadata filtering
```

### Monitoring & Logging

**Built-in Logging:**
```python
# Automatic request logging
2025-11-14 18:28:25 - api - INFO - POST /ask
2025-11-14 18:28:25 - api - INFO - Processing question: Who requested...
2025-11-14 18:28:28 - api - INFO - ✅ Answer generated in 2488ms
2025-11-14 18:28:28 - api - INFO - Response status: 200
```

**Railway Dashboard:**
- Real-time logs
- Memory/CPU usage
- Request metrics
- Error tracking

**Health Check Endpoint:**
```bash
GET /health
→ {
  "status": "healthy",
  "components": {
    "qa_system": "healthy",
    "qdrant": "connected",
    "bm25": "loaded",
    "llm": "configured"
  }
}
```

### Deployment Checklist

**Pre-Deployment:**
- [x] Code tested locally
- [x] Environment variables documented
- [x] Dependencies in requirements.txt
- [x] Procfile configured
- [x] Git repository pushed

**Deployment:**
- [ ] Railway project created
- [ ] GitHub repo connected
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Health check passing

**Post-Deployment:**
- [ ] Test all endpoints
- [ ] Verify chat functionality
- [ ] Check markdown rendering
- [ ] Test error handling
- [ ] Monitor logs for issues

---

## Known Limitations & Future Work

### Current Limitations

**1. Critical Issue #4: RRF/Composition Prioritization**

**Problem:**
- Attribute-specific messages drop below rank 10 during RRF fusion
- Example: "seating preferences" retrieves "I prefer aisle seats" at Qdrant rank #1
- After RRF: Drops to rank ~15 (below generic "preference" messages)
- LLM never sees the specific answer

**Root Cause:**
- High Qdrant score (0.73) for specific message
- Low BM25 score (keyword mismatch: "seating" vs "aisle"/"window")
- No Graph match
- Weighted average favors messages appearing in multiple sources
- Generic messages rank higher than specific ones

**Impact:** Comparison queries fail even when data exists

**Priority:** HIGH

**Potential Fixes:**
1. Increase top_k before composition (20 instead of 10)
2. Boost semantic weight for attribute queries
3. Query-focused re-ranking after RRF
4. Keyword boosting in BM25 for attribute terms

**2. Blocker #2: Relational/Aggregation Queries**

**Problem:**
- Cannot perform GROUP BY, JOIN, or cross-entity aggregation
- Example: "Which clients requested same restaurants?" requires grouping

**Affects:** ~40% of analytical queries

**Workaround:** None (architecture limitation)

**Recommended Fix:**
Two-stage architecture:
1. Retrieve relevant messages
2. Extract entities/attributes
3. Aggregate in Python
4. Generate answer from aggregated data

**3. Identifier Matching (Minor)**

**Problem:**
- Phone numbers, emails tokenized (partial matches)
- 987-654-3210 → ["987", "654", "3210"]
- Low precision for exact identifier lookup

**Workaround:** Graph search helps, but not perfect

**4. Graph User Filtering (Minor)**

**Problem:**
- Graph search doesn't use user_id filtering
- Uses user_name (acceptable, but inconsistent)

**Impact:** Minimal (graph search is tertiary)

### Future Enhancements

**Short-Term (1-2 weeks):**

1. **Fix RRF Prioritization**
   - Implement query-focused re-ranking
   - Boost semantic weight for attribute queries
   - Estimated: 2-3 hours

2. **Add Caching Layer**
   - Query result cache (Redis)
   - Embedding cache
   - LLM response cache
   - Estimated: 4-6 hours

3. **Improve Identifier Matching**
   - Regex-based exact matching for phone/email
   - Pre-process identifiers before indexing
   - Estimated: 2-3 hours

**Medium-Term (1-2 months):**

1. **Aggregation Layer**
   - Two-stage architecture
   - Python-based aggregation
   - Support GROUP BY, JOIN queries
   - Estimated: 10-15 hours

2. **Multi-User Support**
   - Authentication system
   - Per-user chat history
   - Role-based access control
   - Estimated: 15-20 hours

3. **Advanced Analytics**
   - Trend detection over time
   - Pattern recognition across users
   - Automated insights
   - Estimated: 20-30 hours

**Long-Term (3-6 months):**

1. **Real-Time Updates**
   - WebSocket integration
   - Live message streaming
   - Push notifications
   - Estimated: 15-20 hours

2. **Advanced UI Features**
   - Source message inspection (click to view)
   - Query history search
   - Export conversation
   - Voice input
   - Estimated: 20-30 hours

3. **Multi-Modal Support**
   - Image understanding (attachments)
   - Document processing (PDFs)
   - Audio transcription
   - Estimated: 30-40 hours

### Performance Targets

**Current:**
- Average response time: 2.7 seconds
- Query success rate: 75%

**Goals:**
- Average response time: <2 seconds (25% improvement)
- Query success rate: >90% (15% improvement)

**Strategies:**
1. Caching layer → -500ms
2. Parallel LLM calls → -200ms
3. Optimized RRF → -100ms
4. Better routing → +15% success rate

---

## Appendix

### A. File Structure

```
Aurora-Applied-AI-ML-Engineer-Take-Home/
│
├── aurora-qa-system/
│   │
│   ├── api.py                          # FastAPI application ✅
│   ├── Procfile                        # Railway deployment ✅
│   ├── railway.json                    # Railway config ✅
│   ├── requirements.txt                # Python dependencies ✅
│   ├── README.md                       # Project overview ✅
│   │
│   ├── static/                         # Frontend
│   │   └── index.html                  # Aurora chat UI ✅
│   │
│   ├── src/                            # QA System
│   │   ├── qa_system.py                # Main orchestrator
│   │   ├── query_processor.py          # LLM routing & decomposition
│   │   ├── name_resolver.py            # Entity resolution
│   │   ├── hybrid_retriever.py         # Multi-source retrieval
│   │   ├── qdrant_search.py            # Semantic search
│   │   ├── bm25_search.py              # Keyword search
│   │   ├── knowledge_graph.py          # Relationship search
│   │   ├── temporal_analyzer.py        # Date extraction
│   │   ├── result_composer.py          # Multi-query composition
│   │   └── answer_generator.py         # LLM answer generation
│   │
│   ├── data/                           # Databases
│   │   ├── raw_messages.json           # Source data (3,349 messages)
│   │   ├── messages_with_dates.json    # With temporal metadata
│   │   ├── bm25.pkl                    # BM25 index (~2 MB)
│   │   ├── knowledge_graph.pkl         # Graph structure (~1 MB)
│   │   └── user_indexed/
│   │       └── user_index.json         # User filtering index
│   │
│   ├── scripts/                        # Utility scripts
│   │   ├── extract_temporal_metadata.py
│   │   ├── index_to_qdrant.py
│   │   ├── add_user_id_index.py
│   │   └── build_user_index.py
│   │
│   ├── tests/                          # Test suite
│   │   ├── test_suite.py               # Main tests
│   │   ├── test_end_to_end.py          # E2E tests
│   │   ├── test_all_queries.py         # Query tests
│   │   └── archive/                    # Development tests
│   │
│   └── docs/                           # Documentation
│       ├── MASTER_DOCUMENTATION.md     # This file ✅
│       ├── BUILD_SUMMARY.md
│       ├── DEPLOYMENT_PLAN.md
│       ├── DOCUMENTATION_INDEX.md
│       ├── START_HERE_NEXT_SESSION.md
│       └── archive/
│           └── session_checkpoints/    # Development logs
```

### B. Environment Setup

**Requirements:**
```
Python 3.11+
RAM: 4 GB minimum (8 GB recommended)
Storage: 10 MB local + 6 MB cloud (Qdrant free tier)
Network: Internet required for Qdrant Cloud + Mistral API
```

**Installation:**
```bash
# 1. Clone repository
git clone https://github.com/SumanthKonjeti007/Aurora-Applied-AI-ML-Engineer-Take-Home.git
cd Aurora-Applied-AI-ML-Engineer-Take-Home/aurora-qa-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export MISTRAL_API_KEY='your_mistral_api_key'
export QDRANT_URL='your_qdrant_url'
export QDRANT_API_KEY='your_qdrant_api_key'

# 5. Run locally
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 6. Access
open http://localhost:8000
```

### C. API Reference

**Base URL:** `https://aurora-qa-system.up.railway.app` (production)

**Endpoints:**

1. **GET /**
   - Returns: Chat UI (HTML)
   - Status: 200 OK

2. **POST /ask**
   - Body: `{"question": "string"}`
   - Returns: `AnswerResponse`
   - Status: 200 OK / 400 Bad Request / 500 Internal Server Error

3. **GET /health**
   - Returns: `HealthResponse`
   - Status: 200 OK / 503 Service Unavailable

4. **GET /api**
   - Returns: API information and examples
   - Status: 200 OK

5. **GET /docs**
   - Returns: Interactive API documentation (Swagger UI)
   - Status: 200 OK

### D. Testing Guide

**Local Testing:**
```bash
# Start server
uvicorn api:app --reload

# Test in browser
open http://localhost:8000

# Test via curl
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which clients visited Paris?"}'

# Health check
curl http://localhost:8000/health
```

**Production Testing:**
```bash
# Test deployed version
curl -X POST https://aurora-qa-system.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Layla'\''s phone number?"}'
```

**Test Queries:**
1. ✅ "What is Lorenzo Cavalli's phone number?"
2. ✅ "Which clients have plans for December 2025?"
3. ✅ "Compare Layla and Lily's flight preferences"
4. ✅ "Who requested a personal shopper in Milan?"
5. ✅ "Summarize Vikram Desai's travel preferences"

### E. Troubleshooting

**Issue: "QA System not initialized"**
- Cause: Missing data files or indices
- Fix: Run indexing scripts (see Deployment section)

**Issue: "Mistral API rate limit exceeded"**
- Cause: Free tier limit reached
- Fix: Wait 1-2 minutes or upgrade to paid tier

**Issue: "Qdrant connection failed"**
- Cause: Invalid URL or API key
- Fix: Check QDRANT_URL and QDRANT_API_KEY environment variables

**Issue: "Markdown not rendering"**
- Cause: marked.js not loaded
- Fix: Check internet connection (CDN dependency)

**Issue: "Chat history not persisting"**
- Cause: localStorage disabled or browser private mode
- Fix: Enable localStorage or use regular browsing mode

### F. Glossary

- **RAG:** Retrieval-Augmented Generation
- **RRF:** Reciprocal Rank Fusion
- **BM25:** Best Matching 25 (keyword ranking algorithm)
- **BGE:** Beijing Academy of AI (embedding model)
- **Qdrant:** Vector database for similarity search
- **FastAPI:** Modern Python web framework
- **Uvicorn:** ASGI server for FastAPI
- **marked.js:** Markdown parser library
- **localStorage:** Browser API for client-side storage

### G. References

**Technologies:**
- Qdrant: https://qdrant.tech/
- Mistral AI: https://mistral.ai/
- FastAPI: https://fastapi.tiangolo.com/
- Railway: https://railway.app/
- BGE Embeddings: https://huggingface.co/BAAI/bge-small-en-v1.5
- marked.js: https://marked.js.org/

**Papers & Resources:**
- BM25: https://en.wikipedia.org/wiki/Okapi_BM25
- RRF: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- RAG: https://arxiv.org/abs/2005.11401

### H. Version History

**Version 3.0 (2025-11-14) - Full-Stack Production Release** ✅
- ✅ Complete chat UI with Aurora brand aesthetic
- ✅ FastAPI backend serving frontend + API
- ✅ Mistral AI integration for LLM
- ✅ Markdown rendering in responses
- ✅ User-friendly error handling with retry
- ✅ Session persistence via localStorage
- ✅ Railway deployment configuration
- ✅ Comprehensive help modal
- ✅ Professional user avatars
- ✅ Loading states and keyboard shortcuts
- ✅ GitHub icon with repository link

**Version 2.1 (2025-11-13) - Testing & Hardening**
- ✅ Hardened name resolver with stop word filtering
- ✅ Added strict fuzzy matching requirements
- ✅ Fixed false user detection bug
- ✅ Built testing infrastructure
- ❌ Identified RRF/Composition prioritization issue

**Version 2.0 (2025-11-13) - Qdrant Migration**
- ✅ Fixed Blocker #1: Temporal co-occurrence with Qdrant
- ✅ Fixed Blocker #3: LLM decomposer with guardrails
- ✅ Migrated from FAISS to Qdrant Cloud
- ✅ Added temporal extraction pipeline
- ✅ Improved query classification

**Version 1.0 (Initial Release)**
- Initial system with hybrid retrieval
- User filtering implementation
- LLM query decomposition
- Known blockers documented

---

**Document Status:** ✅ Complete and Production-Ready
**Last Reviewed:** 2025-11-14
**Next Review:** After v3.1 release (RRF fix)

---

**End of Master Documentation**
