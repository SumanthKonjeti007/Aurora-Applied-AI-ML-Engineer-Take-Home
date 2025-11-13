# Tests

This directory contains all testing scripts for the Aurora QA System.

## Test Structure

```
tests/
├── README.md                    # This file
├── test_knowledge_graph.py      # Knowledge graph quality tests
└── manual_tests/                # Manual exploration tests
    ├── test_entity_extraction.py      # Initial entity extraction tests
    ├── test_entity_extraction_v2.py   # Improved extraction tests
    ├── test_llama_33_70b.py          # LLM quality validation
    └── test_models.py                 # Model selection tests
```

## Running Tests

### Knowledge Graph Tests
```bash
python tests/test_knowledge_graph.py
```

Tests:
- Graph statistics (nodes, edges, users)
- User-specific queries
- Entity-based search
- Example question support
- Noise filtering validation

### Manual Tests

These were used during development to validate approach and model selection:

```bash
# Test entity extraction quality
python tests/manual_tests/test_entity_extraction.py

# Test LLM extraction quality
python tests/manual_tests/test_llama_33_70b.py
```

## Test Coverage

- ✅ Knowledge graph building and querying
- ✅ Entity extraction quality
- ✅ LLM model selection
- 🔄 Embedding quality (TODO)
- 🔄 Hybrid retrieval (TODO)
- 🔄 Answer generation (TODO)
- 🔄 End-to-end API tests (TODO)
