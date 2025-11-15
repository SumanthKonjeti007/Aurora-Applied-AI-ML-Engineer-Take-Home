# Aurora Question-Answering System

## About This Project

This is my submission for the Aurora Applied AI/ML Engineer take-home assessment. The goal was to build a question-answering system that can intelligently answer natural language questions about member activity data from Aurora's API.

**Live Demo:** [https://aurora-applied-ai-ml-engineer-take-home-1-b5ah.onrender.com/](https://aurora-applied-ai-ml-engineer-take-home-1-b5ah.onrender.com/)

**Repository:** [https://github.com/SumanthKonjeti007/Aurora-Applied-AI-ML-Engineer-Take-Home](https://github.com/SumanthKonjeti007/Aurora-Applied-AI-ML-Engineer-Take-Home)

---

## My Journey

This assignment turned out to be far more challenging and rewarding than I initially expected. What started as "build a simple RAG system" evolved into a deep dive into the real-world complexities of production AI systems.

I spent considerable time wrestling with questions that don't have textbook answers:
- How do you handle queries that need counting vs queries that need retrieval?
- When does semantic search fail and keyword search succeed (and vice versa)?
- How do you extract temporal information from natural language without hallucinating dates?
- What's the real cost-performance trade-off between different embedding models and LLM providers?

The deployment phase was particularly eye-opening. Discovering that PyTorch-based models consume 4+ GB of disk space and 650+ MB of RAM forced me to rethink my entire architecture. Migrating from sentence-transformers to FastEmbed, optimizing for Render's 512 MB free tier, and ensuring the system maintains quality while fitting these constraints taught me more about production ML than any tutorial could.

What I'm most proud of isn't the code itself, but the thought process behind the decisions. Every architectural choice came from hitting a real limitation, testing an alternative, and measuring the trade-offs. That iterative problem-solving process is what I hope comes through in this work.

---

## What I Built

**Core System:**
- Hybrid retrieval combining Qdrant vector search, BM25 keyword search, and knowledge graph traversal
- LLM-based query router that classifies questions as LOOKUP, ANALYTICS, or CONDITIONAL
- Temporal analyzer using datefinder + LLM fallback for date extraction
- Query decomposer that prevents hallucination on counting/aggregation queries
- FastAPI backend with a clean, responsive frontend

**Tech Stack:**
- **LLM:** Mistral Small (via Mistral API)
- **Vector Search:** Qdrant Cloud
- **Embeddings:** FastEmbed (ONNX-based, much lighter than PyTorch)
- **Keyword Search:** BM25
- **Knowledge Graph:** NetworkX
- **Framework:** FastAPI + Uvicorn
- **Deployment:** Render (free tier)

**Key Optimizations:**
- Replaced sentence-transformers (4 GB) with FastEmbed (200 MB)
- Reduced RAM usage from 650 MB to 250 MB
- Docker image: ~2 GB (was 6+ GB before optimization)
- Query latency: ~2 seconds average
- Cost per query: ~$0.003 (Mistral API)

---

## Bonus Questions

I've prepared detailed responses to both bonus questions:

### [Bonus 1: Design Notes](./BONUS_1_DESIGN_NOTES.md)
An in-depth look at how my architecture evolved from simple MongoDB search to the final hybrid RAG system, plus five alternative approaches I seriously considered (fine-tuned models, full-context LLMs, SQL+Text-to-SQL, multi-agent systems, and pure knowledge graphs). I explain why I chose my approach and what trade-offs I made.

### [Bonus 2: Data Insights](./BONUS_2_DATA_INSIGHTS.md)
A comprehensive analysis of the Aurora dataset, identifying anomalies like incomplete messages, category imbalances, suspiciously uniform temporal distribution, and template-like patterns. I discuss what these findings mean for the QA system and how real production data would differ.

---

## Reflections

This assignment pushed me to think like an AI engineer, not just a software engineer who uses AI tools. The difference is in the decision-making:

Software engineering is about building reliable systems with predictable behavior. AI engineering is about building systems that handle uncertainty, work within cost/latency constraints, and gracefully degrade when they don't know the answer.

I encountered problems I've never seen in traditional backend development:
- How do you debug a system when the "bug" is the LLM choosing the wrong reasoning path?
- How do you balance precision (giving exact answers) with recall (not missing relevant information)?
- When should you trust the LLM's output vs compute the answer programmatically?

These questions don't have right answers, only trade-offs. And understanding those trade-offs—really internalizing them through trial and error—was the most valuable part of this experience.

---

## What's Next

If I were to continue developing this system, here's what I'd tackle:

1. **User feedback loop:** Let users thumbs-up/down answers, use that to fine-tune retrieval weights
2. **Conversation context:** Remember previous questions in a session ("What about Italian restaurants?" should recall we were discussing User X)
3. **Confidence scoring:** Tell the user "I'm 90% confident" vs "I found limited information"
4. **Streaming responses:** Show chunks of the answer as they're generated (better UX for long responses)
5. **Better analytics:** Support time-series queries ("How has my restaurant preference changed over time?")

---

## Acknowledgments

Thank you to the Aurora team for this thoughtful assignment. It struck the perfect balance: complex enough to be interesting, scoped enough to be completable, and open-ended enough to allow for creativity.

I learned more in these few days than I have in months of reading papers and watching tutorials. There's no substitute for building something real, hitting actual constraints, and iterating toward a solution.

Looking forward to discussing this work with you.

**Sumanth Konjeti**
