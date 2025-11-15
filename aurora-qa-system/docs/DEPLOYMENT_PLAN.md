# 🚀 Aurora QA System - Deployment Plan & Checklist

**Goal**: Deploy complete QA system with beautiful UI in a single, simple deployment.

**Target Platform**: Railway (one-click deployment, free tier)

**Architecture**: All-in-One (Frontend + Backend + Data in single deployment)

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Railway Deployment (Single App)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                   │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  GET /                  → static/index.html            │   │
│  │  POST /ask              → QA System → Answer           │   │
│  │  GET /health            → System status                │   │
│  │  GET /docs              → Swagger UI (auto)            │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    QA System Pipeline                    │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  Query Processor → Hybrid Retriever → Composer →       │   │
│  │  Answer Generator / Graph Analytics                     │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Data Storage                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  • Qdrant (embedded mode) → data/qdrant/              │   │
│  │  • BM25 Index → data/bm25/                             │   │
│  │  • Knowledge Graph → data/knowledge_graph.pkl          │   │
│  │  • Embeddings → (Qdrant stores them)                   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                              │ HTTPS
                              │
                        User Browser
                  (https://aurora-qa.up.railway.app)
```

---

## 📁 Final Project Structure

```
aurora-qa-system/
│
├── api.py                          # FastAPI app (NEW)
├── requirements.txt                # Python dependencies (UPDATE)
├── Procfile                        # Deployment command (NEW)
├── railway.json                    # Railway config (NEW)
├── .env.example                    # Environment template (NEW)
├── .gitignore                      # Git ignore rules (UPDATE)
│
├── static/                         # Frontend files (NEW FOLDER)
│   └── index.html                  # Single-page UI with Tailwind
│
├── src/                            # Existing QA System
│   ├── __init__.py
│   ├── qa_system.py               ✅ (exists)
│   ├── query_processor.py         ✅ (exists)
│   ├── hybrid_retriever.py        ✅ (exists)
│   ├── answer_generator.py        ✅ (exists, improved)
│   ├── graph_analytics.py         ✅ (exists, improved)
│   ├── result_composer.py         ✅ (exists)
│   ├── name_resolver.py           ✅ (exists)
│   ├── temporal_analyzer.py       ✅ (exists)
│   ├── qdrant_search.py           ✅ (exists)
│   ├── bm25_search.py             ✅ (exists)
│   └── knowledge_graph.py         ✅ (exists)
│
└── data/                           # Data files (existing)
    ├── qdrant/                    ✅ (exists)
    ├── bm25/                      ✅ (exists)
    ├── knowledge_graph.pkl        ✅ (exists)
    └── messages.json              ✅ (exists)
```

---

## ✅ Phase 1: Create API Layer (api.py)

### Tasks:

- [ ] **1.1** Create `api.py` file
  - [ ] Import FastAPI, QASystem, required dependencies
  - [ ] Initialize FastAPI app with CORS (just in case)
  - [ ] Define Pydantic request/response models

- [ ] **1.2** Create `/ask` endpoint
  - [ ] POST method
  - [ ] Accept `{"question": "..."}`
  - [ ] Integrate QASystem
  - [ ] Return `{"success": true/false, "answer": "...", "metadata": {...}}`
  - [ ] Add error handling (try/catch)
  - [ ] Add input validation

- [ ] **1.3** Create `/health` endpoint
  - [ ] GET method
  - [ ] Check QA system components status
  - [ ] Return system health info

- [ ] **1.4** Create `/` (root) endpoint
  - [ ] Serve static/index.html
  - [ ] Use FileResponse

- [ ] **1.5** Add startup event
  - [ ] Initialize QA System on startup
  - [ ] Load all indexes (Qdrant, BM25, KG)
  - [ ] Cache QA system instance
  - [ ] Add logging

- [ ] **1.6** Add middleware
  - [ ] Request logging
  - [ ] Processing time tracking
  - [ ] Error handling middleware

### Expected Result:
```python
# api.py structure:
from fastapi import FastAPI
from src.qa_system import QASystem

app = FastAPI(title="Aurora QA System")
qa_system = None

@app.on_event("startup")
async def startup():
    global qa_system
    qa_system = QASystem()

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    result = qa_system.answer(request.question)
    return format_response(result)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return FileResponse('static/index.html')
```

---

## ✅ Phase 2: Create Frontend (static/index.html)

### Tasks:

- [ ] **2.1** Create HTML structure
  - [ ] Basic HTML5 template
  - [ ] Meta tags (viewport, charset, description)
  - [ ] Title: "Aurora QA System"
  - [ ] Link Tailwind CSS CDN
  - [ ] Link Google Fonts (Inter)

- [ ] **2.2** Create UI layout
  - [ ] Header with title and subtitle
  - [ ] Main question input (textarea)
  - [ ] Ask button
  - [ ] Example questions section (clickable chips)
  - [ ] Answer display area (hidden initially)
  - [ ] Loading state
  - [ ] Error state

- [ ] **2.3** Add styling
  - [ ] Gradient background (purple/blue)
  - [ ] Glass-morphism card effect
  - [ ] Smooth transitions
  - [ ] Hover effects
  - [ ] Focus states
  - [ ] Responsive design (mobile-first)

- [ ] **2.4** Add JavaScript functionality
  - [ ] `askQuestion()` function (API call)
  - [ ] Loading state management
  - [ ] Error handling
  - [ ] Answer rendering with formatting
  - [ ] Example question click handlers
  - [ ] Enter key to submit
  - [ ] Clear answer button

- [ ] **2.5** Add UX enhancements
  - [ ] Auto-focus on input
  - [ ] Disable submit while loading
  - [ ] Fade-in animation for answer
  - [ ] Processing time display
  - [ ] Copy answer button (optional)

### Design Specs:
```
Colors:
- Background: gradient(indigo-500, purple-500, pink-500)
- Cards: glass-morphism (white/10, blur(10px))
- Primary: blue-500
- Text: white

Typography:
- Font: Inter
- Heading: 4xl, bold
- Body: base, regular
- Answer: lg, medium

Spacing:
- Container: max-w-4xl, mx-auto
- Padding: p-8
- Margins: mb-4, mb-8
- Border radius: rounded-2xl, rounded-3xl
```

### Expected Result:
A single, beautiful HTML file that:
- ✅ Loads instantly (no build)
- ✅ Looks modern and elegant
- ✅ Works on all devices
- ✅ Calls `/ask` API endpoint
- ✅ Displays answers beautifully

---

## ✅ Phase 3: Create Deployment Files

### Tasks:

- [ ] **3.1** Create/Update `requirements.txt`
  ```txt
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  pydantic==2.5.0
  mistralai==1.9.11
  sentence-transformers==2.2.2
  torch==2.1.0
  qdrant-client==1.7.0
  rank-bm25==0.2.2
  python-dateutil==2.9.0
  datefinder==0.7.3
  ```

- [ ] **3.2** Create `Procfile`
  ```
  web: uvicorn api:app --host 0.0.0.0 --port $PORT
  ```

- [ ] **3.3** Create `railway.json`
  ```json
  {
    "build": {
      "builder": "NIXPACKS"
    },
    "deploy": {
      "startCommand": "uvicorn api:app --host 0.0.0.0 --port $PORT",
      "healthcheckPath": "/health",
      "restartPolicyType": "ON_FAILURE",
      "restartPolicyMaxRetries": 10
    }
  }
  ```

- [ ] **3.4** Create `.env.example`
  ```env
  # API Keys
  MISTRAL_API_KEY=your_mistral_api_key_here

  # Server Config
  PORT=8000

  # Optional
  LOG_LEVEL=info
  ```

- [ ] **3.5** Update `.gitignore`
  ```
  __pycache__/
  *.pyc
  .env
  .DS_Store
  venv/
  *.log
  ```

---

## ✅ Phase 4: Local Testing

### Pre-Testing Checklist:
- [ ] All files created
- [ ] Requirements installed locally
- [ ] Environment variables set
- [ ] Data files present

### Testing Tasks:

- [ ] **4.1** Test API locally
  ```bash
  uvicorn api:app --reload
  ```
  - [ ] Server starts without errors
  - [ ] QA system loads on startup
  - [ ] No import errors

- [ ] **4.2** Test `/health` endpoint
  ```bash
  curl http://localhost:8000/health
  ```
  - [ ] Returns 200 OK
  - [ ] Shows system status

- [ ] **4.3** Test `/ask` endpoint (via curl)
  ```bash
  curl -X POST http://localhost:8000/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "Which clients visited Paris?"}'
  ```
  - [ ] Returns valid JSON
  - [ ] Answer is natural language
  - [ ] Response time reasonable (<5s)

- [ ] **4.4** Test frontend
  - [ ] Open http://localhost:8000/
  - [ ] UI loads and looks good
  - [ ] Can type question
  - [ ] Submit button works
  - [ ] Answer displays correctly
  - [ ] Example questions work
  - [ ] Mobile view responsive

- [ ] **4.5** Test various queries
  - [ ] "Which clients requested Louvre tours?"
  - [ ] "How many cars does Vikram Desai have?"
  - [ ] "Which clients have plans for December 2025?"
  - [ ] "Personal shopper in Milan?"
  - [ ] "Similar spa preferences?"
  - [ ] Error case: empty question
  - [ ] Error case: very long question (1000+ chars)

### Expected Results:
- ✅ All endpoints working
- ✅ UI beautiful and functional
- ✅ Answers are natural and formatted
- ✅ No errors in console/logs
- ✅ Reasonable performance

---

## ✅ Phase 5: Railway Deployment

### Pre-Deployment Checklist:
- [ ] GitHub repo created
- [ ] All code committed and pushed
- [ ] Data files included (if < 100MB)
- [ ] Railway account created
- [ ] MISTRAL_API_KEY ready

### Deployment Tasks:

- [ ] **5.1** Push to GitHub
  ```bash
  git add .
  git commit -m "Ready for deployment: API + UI + QA System"
  git push origin main
  ```

- [ ] **5.2** Create Railway project
  - [ ] Go to railway.app
  - [ ] Click "New Project"
  - [ ] Select "Deploy from GitHub repo"
  - [ ] Authorize GitHub
  - [ ] Select aurora-qa-system repo

- [ ] **5.3** Configure Railway
  - [ ] Railway auto-detects Python
  - [ ] Verify start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
  - [ ] Add environment variables:
    - [ ] `MISTRAL_API_KEY` = [your key]
    - [ ] `PORT` = 8000 (optional, Railway sets this)

- [ ] **5.4** Initial deploy
  - [ ] Watch build logs
  - [ ] Verify no errors during build
  - [ ] Wait for deployment (3-5 minutes)
  - [ ] Get deployment URL

- [ ] **5.5** Verify deployment
  - [ ] Visit https://[your-app].up.railway.app/health
  - [ ] Check status is "healthy"
  - [ ] Visit root URL
  - [ ] UI loads correctly

- [ ] **5.6** Test production
  - [ ] Submit test questions
  - [ ] Verify answers are correct
  - [ ] Check response times
  - [ ] Test on mobile device

### Troubleshooting Checklist:
If deployment fails:
- [ ] Check Railway build logs for errors
- [ ] Verify all dependencies in requirements.txt
- [ ] Check environment variables are set
- [ ] Verify data files are present
- [ ] Check memory limits (Railway free: 512MB)
- [ ] Review Railway docs: railway.app/docs

---

## ✅ Phase 6: Post-Deployment

### Tasks:

- [ ] **6.1** Performance testing
  - [ ] Test with 5-10 different queries
  - [ ] Measure average response time
  - [ ] Check memory usage
  - [ ] Verify cold start time

- [ ] **6.2** Documentation
  - [ ] Document deployment URL
  - [ ] Create API documentation
  - [ ] Add usage examples
  - [ ] Update master document

- [ ] **6.3** Optional enhancements
  - [ ] Add custom domain (optional)
  - [ ] Set up monitoring (Railway dashboard)
  - [ ] Add Google Analytics (optional)
  - [ ] Add more example questions

---

## 📊 Success Criteria

### Must Have (MVP):
- ✅ Single URL deployment (frontend + backend)
- ✅ Beautiful, responsive UI
- ✅ Natural language Q&A works
- ✅ All query types supported (LOOKUP + ANALYTICS)
- ✅ Reasonable performance (< 5s response time)
- ✅ Error handling
- ✅ Mobile-friendly

### Nice to Have (Post-MVP):
- ⏸️ Custom domain
- ⏸️ Confidence scores
- ⏸️ Follow-up suggestions
- ⏸️ Answer sources expandable
- ⏸️ Query history
- ⏸️ Dark mode toggle

---

## 🚨 Risk Mitigation

### Potential Issues & Solutions:

| Risk | Impact | Solution |
|------|--------|----------|
| Data files too large for Git | High | Use Git LFS or download on startup |
| Railway free tier limits | Medium | Monitor usage, upgrade if needed |
| Cold start latency | Low | Accept for MVP, add warming later |
| Qdrant embedded mode slow | Low | Profile and optimize if needed |
| LLM API rate limits | Medium | Add rate limiting on frontend |
| Memory constraints (512MB) | High | Optimize model loading, use smaller models |

---

## 📈 Timeline Estimate

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: API Layer | 45 min | 45 min |
| Phase 2: Frontend | 60 min | 1h 45min |
| Phase 3: Deployment Files | 15 min | 2h |
| Phase 4: Local Testing | 30 min | 2h 30min |
| Phase 5: Railway Deploy | 30 min | 3h |
| Phase 6: Post-Deploy | 30 min | 3h 30min |
| **TOTAL** | **~3.5 hours** | |

---

## ✅ Current Status

### Completed:
- ✅ QA System (all components)
- ✅ Hybrid retrieval pipeline
- ✅ Answer generation with improved prompts
- ✅ Graph analytics
- ✅ Data preprocessing and indexing

### In Progress:
- 🔄 API layer creation
- 🔄 Frontend UI development
- 🔄 Deployment setup

### Pending:
- ⏳ Local testing
- ⏳ Railway deployment
- ⏳ Documentation update

---

## 📝 Notes & Decisions

### Key Architectural Decisions:
1. **All-in-One Deployment** - Simplifies setup, avoids CORS
2. **Qdrant Embedded Mode** - No external database needed
3. **Single HTML File** - No build process, instant loading
4. **Tailwind CDN** - No npm, no bundler
5. **Railway Platform** - Easy deployment, persistent storage

### Trade-offs Accepted:
- ✅ Larger repo size (data files included) → Simpler deployment
- ✅ Embedded Qdrant → Easier setup, slight performance trade-off
- ✅ Single HTML → Less modular, but simpler
- ✅ Railway free tier limits → Acceptable for MVP/demo

---

## 🎯 Final Deliverables

1. ✅ **Working Application**
   - URL: https://[project-name].up.railway.app
   - Frontend at `/`
   - API at `/ask`
   - Health check at `/health`
   - API docs at `/docs`

2. ✅ **Code Repository**
   - Clean, organized structure
   - All files committed
   - README with instructions

3. ✅ **Documentation**
   - Master document updated
   - Deployment guide
   - API documentation
   - Architecture diagrams

---

## 🚀 Ready to Start!

**Next Immediate Steps:**
1. Create `api.py` ← START HERE
2. Create `static/index.html`
3. Test locally
4. Deploy to Railway

**Let's build! 🎉**
