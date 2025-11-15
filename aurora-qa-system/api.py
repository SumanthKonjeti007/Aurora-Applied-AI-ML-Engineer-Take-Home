"""
Aurora QA System - FastAPI Application

Serves both the API endpoints and the static frontend.
Single deployment for frontend + backend + QA system.
"""
import os
import time
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.qa_system import QASystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global QA system instance
qa_system: Optional[QASystem] = None


# ==================== Pydantic Models ====================

class QuestionRequest(BaseModel):
    """Request model for /ask endpoint"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language question about member data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Which clients requested a private tour of the Louvre?"
            }
        }


class AnswerResponse(BaseModel):
    """Response model for successful queries"""
    success: bool = True
    answer: str
    metadata: dict

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "5 clients requested private Louvre tours:\n• Lorenzo Cavalli\n• Sophia Al-Farsi...",
                "metadata": {
                    "route": "LOOKUP",
                    "processing_time_ms": 3245,
                    "sources_count": 20,
                    "confidence": "high"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = False
    error: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "INVALID_QUESTION",
                "message": "Question cannot be empty"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    components: dict
    uptime_seconds: float


# ==================== Lifespan Context Manager ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Aurora QA System...")

    global qa_system

    try:
        # Initialize QA System (loads all indexes)
        start_time = time.time()

        logger.info("Loading QA System components...")
        qa_system = QASystem(
            embedding_path="data/embeddings",
            bm25_path="data/bm25",
            graph_path="data/knowledge_graph.pkl"
        )

        load_time = time.time() - start_time
        logger.info(f"✅ QA System loaded successfully in {load_time:.2f}s")

    except Exception as e:
        logger.error(f"❌ Failed to initialize QA System: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Aurora QA System...")


# ==================== FastAPI App ====================

app = FastAPI(
    title="Aurora QA System API",
    description="Natural language question-answering system for luxury concierge member data",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (in case we need it later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Middleware ====================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ==================== API Endpoints ====================

@app.get("/", include_in_schema=False)
async def root():
    """
    Serve the frontend HTML page
    """
    return FileResponse('static/index.html')


@app.get("/api", response_model=dict)
async def api_info():
    """
    API information and available endpoints
    """
    return {
        "name": "Aurora QA System API",
        "version": "1.0.0",
        "description": "Natural language Q&A system for luxury concierge members",
        "endpoints": {
            "ask": "POST /ask - Submit a question",
            "health": "GET /health - Check system health",
            "docs": "GET /docs - Interactive API documentation"
        },
        "examples": [
            "Which clients requested a private tour of the Louvre?",
            "What are Vikram Desai's dining preferences?",
            "Which clients have plans for December 2025?",
            "Who requested a personal shopper in Milan?"
        ]
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Submit a natural language question and receive an answer

    The system will:
    1. Analyze the question
    2. Route to appropriate pipeline (LOOKUP or ANALYTICS)
    3. Retrieve relevant information
    4. Generate a natural language answer

    Returns a natural language answer with metadata.
    """
    try:
        # Validate QA system is loaded
        if qa_system is None:
            raise HTTPException(
                status_code=503,
                detail="QA System not initialized. Please try again later."
            )

        # Validate question
        question = request.question.strip()
        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        # Process question
        logger.info(f"Processing question: {question}")
        start_time = time.time()

        result = qa_system.answer(
            query=question,
            top_k=20,
            temperature=0.3,
            verbose=False
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate confidence (simple heuristic)
        confidence = calculate_confidence(result)

        # Get sources for transparency
        sources = result.get('sources', [])
        sources_data = []
        for source in sources[:20]:  # Limit to top 20 for UI performance
            sources_data.append({
                "user_id": source.get('user_id', 'Unknown'),
                "text": source.get('text', ''),
                "timestamp": source.get('timestamp', None),
                "score": source.get('score', 0)
            })

        # Format response
        response = AnswerResponse(
            success=True,
            answer=result['answer'],
            metadata={
                "route": result.get('route', 'UNKNOWN'),
                "processing_time_ms": int(processing_time),
                "sources_count": result.get('num_sources', 0),
                "confidence": confidence,
                "model": result.get('model', 'unknown'),
                "query_plans": len(result.get('query_plans', [])),
                "sources": sources_data  # Include actual source messages
            }
        )

        logger.info(f"✅ Answer generated in {processing_time:.0f}ms")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns the status of the QA system and its components.
    """
    try:
        # Check if QA system is loaded
        if qa_system is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "version": "1.0.0",
                    "components": {
                        "qa_system": "not_initialized"
                    },
                    "uptime_seconds": 0
                }
            )

        # Check components
        components = {
            "qa_system": "healthy",
            "qdrant": "connected" if hasattr(qa_system.retriever, 'qdrant_search') else "unknown",
            "bm25": "loaded" if hasattr(qa_system.retriever, 'bm25_search') else "unknown",
            "knowledge_graph": "loaded" if hasattr(qa_system.retriever, 'knowledge_graph') else "unknown",
            "llm": "configured" if qa_system.generator else "unknown"
        }

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            components=components,
            uptime_seconds=time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e)
            }
        )


# ==================== Helper Functions ====================

def calculate_confidence(result: dict) -> str:
    """
    Calculate confidence level based on query results

    Args:
        result: QA system result dictionary

    Returns:
        "high", "medium", or "low"
    """
    try:
        route = result.get('route', 'UNKNOWN')

        # ANALYTICS queries are deterministic
        if route == 'ANALYTICS':
            return "high"

        # For LOOKUP, check source scores
        sources = result.get('sources', [])
        if not sources:
            return "low"

        # Get top 3 source scores
        top_scores = [s.get('score', 0) for s in sources[:3]]
        if not top_scores:
            return "low"

        avg_score = sum(top_scores) / len(top_scores)

        if avg_score > 0.7:
            return "high"
        elif avg_score > 0.5:
            return "medium"
        else:
            return "low"

    except Exception as e:
        logger.warning(f"Failed to calculate confidence: {str(e)}")
        return "medium"


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Track startup time for uptime calculation"""
    app.state.start_time = time.time()
    logger.info("✅ API server started successfully")


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn

    # For local development
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info"
    )
