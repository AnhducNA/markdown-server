"""FastAPI application entrypoint for Markdown Output Server."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure directory structure on startup."""
    logger.info("Starting up Markdown Output API Server...")
    settings.ensure_directories()
    logger.info(f"Storage directories initialized at {settings.output_dir}")
    yield
    logger.info("Shutting down Markdown Output API Server...")


app = FastAPI(
    title="Markdown Output API Server",
    description=(
        "Standardized Pipeline converting PDF, DOCX, and Web URLs into normalized Markdown "
        "and Unified Document Models ready for Qdrant and RAG ingestion."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Markdown Output API Server is active.",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
