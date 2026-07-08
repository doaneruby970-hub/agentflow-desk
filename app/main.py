"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tickets import router as tickets_router
from app.api.knowledge import router as knowledge_router
from app.api.metrics import router as metrics_router
from app.core.config import settings

app = FastAPI(
    title="AgentFlow Desk",
    description="Production-grade Python backend for AI-powered support workflow automation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets_router)
app.include_router(knowledge_router)
app.include_router(metrics_router)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "provider": settings.llm_provider,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AgentFlow Desk API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
