"""
Google Earth Engine Authentication & Initialization

Handles GEE authentication with graceful fallback to demo mode.
Supports both interactive auth (already authenticated) and
service account auth for production deployment.
"""

import ee
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level state
_initialized = False
_demo_mode = settings.demo_mode


def initialize_gee() -> bool:
    """
    Initialize Google Earth Engine.

    Attempts to initialize with the configured project ID.
    Falls back to demo mode if initialization fails.

    Returns:
        True if GEE was initialized successfully, False if in demo mode.
    """
    global _initialized, _demo_mode

    if _initialized:
        return not _demo_mode

    if _demo_mode:
        logger.warning("Running in DEMO MODE — using synthetic data")
        _initialized = True
        return False

    try:
        # Try initializing with project ID (user has already authenticated)
        if settings.gee.service_account_key:
            # Service account authentication (for production/deployment)
            credentials = ee.ServiceAccountCredentials(
                email=None,
                key_file=settings.gee.service_account_key,
            )
            ee.Initialize(credentials, project=settings.gee.project_id)
            logger.info(
                "GEE initialized with service account for project: %s",
                settings.gee.project_id,
            )
        else:
            # Interactive authentication (user has run ee.Authenticate() before)
            ee.Initialize(project=settings.gee.project_id)
            logger.info(
                "GEE initialized for project: %s",
                settings.gee.project_id,
            )

        _initialized = True
        return True

    except Exception as exc:
        logger.error("GEE initialization failed: %s", exc)
        logger.warning("Falling back to DEMO MODE")
        _demo_mode = True
        _initialized = True
        return False


def is_demo_mode() -> bool:
    """Check if the system is running in demo mode."""
    if not _initialized:
        initialize_gee()
    return _demo_mode


def get_gee_status() -> dict:
    """
    Get current GEE connection status.

    Returns:
        Dictionary with status information.
    """
    if not _initialized:
        initialize_gee()

    return {
        "initialized": _initialized,
        "demo_mode": _demo_mode,
        "project_id": settings.gee.project_id if not _demo_mode else None,
    }
