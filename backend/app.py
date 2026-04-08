"""
Forest observation and analysis system — FastAPI Backend

Main application entry point that assembles all routes, middleware,
and startup events into a production-ready API server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.gee.auth import initialize_gee, get_gee_status
from backend.routes import (
    ndvi_router,
    density_router,
    change_detection_router,
)
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize resources on startup (GEE connection) and
    clean up on shutdown.
    """
    logger.info("=" * 60)
    logger.info("Forest observation and analysis system — Starting")
    logger.info("=" * 60)

    # Initialize Google Earth Engine
    gee_ok = initialize_gee()
    if gee_ok:
        logger.info("✓ GEE connected — project: %s", settings.gee.project_id)
    else:
        logger.warning("⚠ Running in DEMO MODE (synthetic data)")

    logger.info("✓ Backend ready at http://%s:%d", settings.server.host, settings.server.port)
    logger.info("✓ API docs at http://%s:%d/docs", settings.server.host, settings.server.port)

    yield  # Application runs here

    logger.info("Shutting down...")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Forest observation and analysis system",
    description=(
        "Analyzes satellite imagery (Sentinel-2) to compute vegetation indices, "
        "classify forest canopy density, detect temporal changes, and provide "
        "ML-based forest type predictions. Built for academic research and "
        "real-world forest monitoring applications."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# CORS Middleware (allow Streamlit frontend to call the API)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------
app.include_router(ndvi_router)
app.include_router(density_router)
app.include_router(change_detection_router)


# ---------------------------------------------------------------------------
# Health Check and Status Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    """API root — health check endpoint."""
    return {
        "service": "Forest observation and analysis system",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with GEE status."""
    return {
        "status": "healthy",
        "gee": get_gee_status(),
        "config": {
            "default_aoi": settings.aoi.bbox,
            "log_level": settings.log_level,
        },
    }


@app.get("/api/status", tags=["Health"])
async def api_status():
    """Get full system status including all available endpoints."""
    return {
        "status": "operational",
        "gee": get_gee_status(),
        "endpoints": {
            "ndvi": "/api/ndvi",
            "density": "/api/density",
            "change_detection": "/api/change-detection",
        },
        "default_aoi": {
            "name": "Amazon Rainforest",
            "bbox": settings.aoi.bbox,
            "center": settings.aoi.center,
        },
    }
