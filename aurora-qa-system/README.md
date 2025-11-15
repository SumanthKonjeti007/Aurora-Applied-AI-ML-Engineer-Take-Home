# Aurora QA System

A production-ready question-answering system for luxury concierge services, powered by hybrid retrieval and natural language generation.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export MISTRAL_API_KEY='your_key_here'

# Start server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Visit: `http://localhost:8000`

### API Endpoints

- **GET /** - Beautiful web UI
- **POST /ask** - Submit questions
- **GET /health** - System health check
- **GET /docs** - API documentation

## Features

- Natural language question answering
- Hybrid retrieval (semantic + keyword + graph)
- Beautiful modern UI (Tailwind CSS)
- Multiple query types (lookup, analytics, temporal)
- Embedded vector database (Qdrant)
- Production-ready deployment

## Architecture

```
FastAPI App (api.py)
├── Frontend UI (static/index.html)
├── QA System (src/)
│   ├── Query Processor
│   ├── Hybrid Retriever (Qdrant + BM25 + Graph)
│   └── Answer Generator (Mistral LLM)
└── Data (data/)
    ├── Qdrant Database
    ├── BM25 Index
    └── Knowledge Graph
```

## Documentation

All documentation is in the `docs/` folder:

- **[START HERE](docs/START_HERE_NEXT_SESSION.md)** - Quick start guide
- **[Deployment Plan](docs/DEPLOYMENT_PLAN.md)** - Step-by-step deployment
- **[Build Summary](docs/BUILD_SUMMARY.md)** - What we built
- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Guide to all docs

## Project Structure

```
aurora-qa-system/
├── api.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── Procfile               # Railway deployment
├── railway.json           # Railway config
├── src/                   # QA system modules
├── static/                # Frontend UI
├── data/                  # Databases & indexes
├── docs/                  # Documentation
├── tests/                 # Test files
└── scripts/               # Utility scripts
```

## Deployment

Deploy to Railway in 3 steps:

```bash
# 1. Push to GitHub
git push origin main

# 2. Deploy on Railway
# - Connect GitHub repo
# - Set MISTRAL_API_KEY env variable
# - Deploy automatically

# 3. Done!
# Visit: https://your-app.up.railway.app
```

See [DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md) for detailed instructions.

## Example Queries

- "Which clients requested a private tour of the Louvre?"
- "Which clients have plans for December 2025?"
- "Which clients requested a personal shopper in Milan?"
- "Which clients have similar preferences for spa services?"

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: HTML + Tailwind CSS
- **Vector DB**: Qdrant (embedded)
- **Search**: BM25
- **Graph**: NetworkX
- **LLM**: Mistral Small
- **Embeddings**: BGE-small-en-v1.5

## Status

**Production Ready** - All tests passed, fully documented, ready to deploy.

## License

Built for Aurora Applied AI/ML Engineer Take-Home Assignment.
