# Bonus 1: Design Notes

## How My Architecture Evolved

When I first looked at the Aurora dataset (~3,200 messages with temporal data and user information), I needed to design a system that could handle both simple lookups and complex analytical queries. Here's how my thinking evolved:

### Stage 1: MongoDB Full-Text Search (Starting Point)

**Initial thought:** The data is already in JSON with timestamps - why not use MongoDB's built-in `$text` search with date filters?

**What I built:** Basic keyword search with `$gte`/`$lte` date filtering.

**Why it failed:** Tested with "Where did I eat in late March?" - MongoDB matched the keyword "March" but couldn't understand "late" or rank results by relevance. Purely keyword-based search missed the semantic meaning of queries like "romantic dinner spots."

**Key lesson:** Needed semantic understanding, not just keyword matching.

---

### Stage 2: Semantic Search with FAISS (Adding Intelligence)

**Evolution:** Embed all messages using sentence transformers (BAAI/bge-small-en-v1.5), store vectors in FAISS, retrieve top-k similar messages.

**What improved:** Now "romantic dinner spots" could match messages containing "anniversary celebration" or "date night" even without exact keywords. The system understood meaning.

**Why it wasn't enough:** Tested "What restaurants did I visit on March 25th?" - FAISS returned messages about March generally, but couldn't filter to the exact date. Also mixed in other users' activities. Purely semantic search also missed exact entity matches - asking about "Bistro Lamarck" would return similar French restaurants but not necessarily that specific one.

**Key lesson:** Needed BOTH semantic understanding AND precise keyword matching + metadata filtering.

---

### Stage 3: Hybrid Retrieval (Semantic + Keyword)

**Evolution:** Combined FAISS semantic search with BM25 keyword search, merged using Reciprocal Rank Fusion (RRF).

**What improved:**
- BM25 caught exact entity names ("Bistro Lamarck", specific user names, food items)
- FAISS provided semantic understanding
- RRF scoring: `1/(k + rank)` where k=60, elegantly combined both sources

**Why it still wasn't enough:** Temporal and user filtering were post-retrieval - I'd retrieve top-10 results, then filter out wrong dates/users. This wasted top-k slots. Query "Show me User X's visits between March 20-25" would return mixed users and dates, then throw most away.

**Key lesson:** Needed metadata filtering BEFORE retrieval, not after.

---

### Stage 4: Qdrant Vector DB + Knowledge Graph (Structured Filtering)

**Evolution:** Migrated from FAISS to Qdrant Cloud for pre-filtering support. Added NetworkX knowledge graph for relationships.

**Architecture:**
```
Query → Extract filters → Qdrant search (WHERE user_id=X AND date IN range) + BM25 + Graph → RRF
```

**What improved:**
- Qdrant pre-filters: only searches vectors matching metadata criteria
- Knowledge graph captured relationships: User → visited → Restaurant → has_cuisine → French
- Could answer relationship queries: "Who else visited the same restaurants as User X?"

**Why I kept building:** This solved filtering beautifully, but I noticed two distinct query patterns:
- **LOOKUP:** "What did I eat at Le Chateaubriand?" (needs retrieval)
- **ANALYTICS:** "How many times did I visit French restaurants?" (needs aggregation)

Sending both through the same pipeline was inefficient and led to hallucinated counts.

**Key lesson:** Different query types need different handling strategies.

---

### Stage 5: Query Router + Specialized Pipelines (Final Architecture)

**Evolution:** Instead of one-size-fits-all, route queries to specialized handlers.

**Components:**
1. **Query Router (LLM):** Classifies query as LOOKUP / ANALYTICS / CONDITIONAL
2. **Temporal Analyzer:** Extracts dates ("late March" → 2025-03-20 to 2025-03-31)
3. **Hybrid Retriever:** Qdrant + BM25 + Graph with RRF fusion
4. **LLM Decomposer:** For analytics queries, generates aggregation logic
5. **Answer Generator:** Mistral with RAG context for natural language responses

**What this solved:**
- LOOKUP queries get retrieval → direct answer
- ANALYTICS queries get retrieval → LLM computes aggregation → fact-based answer (no hallucination)
- Temporal queries work with relative dates ("yesterday", "last week")
- Each pipeline optimized for its query type

**Trade-off:** More complexity (5 components vs 1), but handles the full spectrum of question types accurately.

---

## Alternative Approaches I Considered

Beyond my iterative evolution, I seriously evaluated these alternative architectures:

### Alternative 1: Fine-Tuned Small Language Model (FLAN-T5)

**The idea:** Fine-tune a 3B parameter model on the Aurora dataset to answer questions directly without retrieval.

**Pros:**
- Fast inference (local model)
- No external API costs after training
- Could memorize patterns ("Layla prefers Japanese food")

**Cons:**
- **Insufficient data:** 3,200 messages aren't enough to fine-tune without overfitting
- **Hallucination risk:** Model might "remember" wrong facts
- **Update problem:** Every new message requires retraining
- **Can't compute:** "How many times did I visit French restaurants?" would be a guess, not actual count

**Why I rejected it:** When precision matters (counts, dates, specific visits), memorization-based models aren't reliable.

---

### Alternative 2: Full-Context LLM (GPT-4 128K Window)

**The idea:** Load all 3,200 messages into GPT-4's context window and ask questions directly.

**Pros:**
- Simplest architecture - no indexing needed
- LLM sees all data at once
- Handles complex reasoning naturally

**Cons:**
- **Cost:** ~$13 per query (320K tokens × GPT-4 pricing)
- **Latency:** 30-60 seconds to process full context
- **Doesn't scale:** Won't work at 100K+ messages
- **Hallucination:** Even with full context, LLMs sometimes miss details in long inputs

**Why I rejected it:** Budget constraints and latency. This would cost hundreds of dollars just for testing.

---

### Alternative 3: SQL Database + Text-to-SQL

**The idea:** Extract structured data (user, restaurant, cuisine, timestamp) into PostgreSQL, convert questions to SQL.

**Schema:**
```sql
CREATE TABLE visits (
    user_id UUID,
    restaurant TEXT,
    cuisine TEXT,
    timestamp TIMESTAMP
);
```

**Pros:**
- Perfect for aggregations: `SELECT cuisine, COUNT(*) GROUP BY cuisine`
- Temporal filtering is native SQL
- No hallucination - SQL results are exact

**Cons:**
- **No semantic search:** Can't handle "romantic spots" - requires exact column matches
- **Entity extraction bottleneck:** Must pre-extract restaurants/cuisines from free text (error-prone)
- **Text-to-SQL reliability:** LLMs often generate incorrect SQL for complex queries
- **Loses unstructured data:** "The vibe was immaculate" doesn't fit into columns

**Why I rejected it:** The dataset is unstructured text, not neat rows. Would need NLP to extract structured data first - that's the hard problem SQL doesn't solve.

---

### Alternative 4: Multi-Agent System (LangGraph)

**The idea:** Deploy specialized agents:
- Retrieval Agent (searches messages)
- Analytics Agent (counts/aggregates)
- Temporal Agent (date reasoning)
- Synthesis Agent (combines results)

**Pros:**
- Modular - each agent focuses on one task
- Parallelizable (run retrieval + analytics simultaneously)
- Easier debugging - inspect each agent's output

**Cons:**
- **Over-engineered:** Multi-agent shines at 100K+ documents, overkill for 3,200
- **Coordination complexity:** Who calls whom? What if agents disagree?
- **Latency:** Sequential calls add up (5 agents × 2s = 10s)
- **Infrastructure:** Need agent state management, message queues

**Why I rejected it:** Adds architectural complexity without clear benefits at this scale. My query router achieves similar specialization with simpler design.

---

### Alternative 5: Pure Knowledge Graph (Neo4j)

**The idea:** Model everything as graph nodes/edges:
```
(User)-[:VISITED]->(Restaurant)-[:HAS_CUISINE]->(Cuisine)
(User)-[:SENT {timestamp}]->(Message)
```

Query with Cypher:
```cypher
MATCH (u:User)-[:VISITED]->(r:Restaurant)-[:HAS_CUISINE]->(c:Cuisine {name: "French"})
RETURN count(r)
```

**Pros:**
- Relationship queries are native: "Who visited the same restaurants as User X?"
- Temporal paths: "Users who visited within 7 days"
- Visual exploration in Neo4j Browser

**Cons:**
- **No semantic search:** Can't match "romantic spots" to "anniversary dinner"
- **Entity extraction required:** Must pre-extract all relationships from text
- **Text-to-Cypher is harder:** Less training data than text-to-SQL
- **Loses free text:** Can't capture "The ambiance was perfect" in graph edges

**Why I rejected it:** Would need to solve the hard problem (extracting structured data from text) before the graph becomes useful.

---

## Why I Chose Hybrid RAG with Query Routing

### My Decision Process

When I laid out all five alternatives, I asked myself: what does this system REALLY need to do?

**Must-haves:**
1. Understand "romantic dinner spots" (semantic search)
2. Give exact counts, not guesses (no hallucination on numbers)
3. Filter by date ranges and users efficiently
4. Work with raw message text, not pre-extracted data
5. Stay under $0.01 per query (budget constraint)
6. Respond in under 3 seconds (user experience)

**How each alternative stacked up:**

**Fine-tuned T5:**
- Fast and cheap once trained
- Would guess at counts instead of computing them
- 3,200 messages too small to avoid overfitting
- **Verdict:** Not reliable enough for factual queries

**Full-Context GPT-4:**
- Handles everything, super simple architecture
- $13 per query - I'd burn through budget in 10 test queries
- 45+ second latency kills UX
- **Verdict:** Technically works, financially impossible

**SQL + Text-to-SQL:**
- Perfect for "COUNT visits by cuisine"
- No hallucination on aggregations
- Can't do semantic search ("romantic" doesn't match "anniversary")
- Would need to extract restaurants/cuisines from text first (chicken-and-egg)
- **Verdict:** Great for structured data, but my data isn't structured yet

**Multi-Agent System:**
- Clean separation of concerns
- Easier debugging
- Coordination overhead (who manages the agents?)
- 10+ second latency from sequential calls
- Feels like building a Ferrari for a 5-mile commute
- **Verdict:** Over-engineered for 3,200 messages

**Pure Neo4j Graph:**
- Amazing for "Who visited the same places as User X?"
- Visual graph exploration is cool
- No semantic search capability
- Still need to extract entities from text before building graph
- **Verdict:** Solves the wrong problem first - I need to understand text before graphing relationships

**My hybrid approach:**
- Qdrant handles semantic search with metadata filtering
- BM25 catches exact entity names
- Knowledge graph adds relationship queries
- Query router prevents hallucinated aggregations
- ~$0.003 per query (Mistral Small API)
- ~2 second average response
- More complex than pure LLM, but each component solves a real problem

**The deciding factor:** I needed semantic understanding (rules out SQL/Graph-only), precision on counts (rules out fine-tuned models), reasonable cost (rules out GPT-4), and good latency (rules out multi-agent). My approach was the only one that hit all six requirements without major compromises.

**Honest reflection:** If I had unlimited budget, I'd probably use full-context Claude Opus - it's the simplest architecture. But at $13/query, I'd need to charge users or severely limit usage. The hybrid RAG approach gives me 90% of the quality at 0.02% of the cost.
