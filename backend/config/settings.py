"""
Forest observation and analysis system — Backend Configuration

Central configuration module that loads environment variables and
provides typed, validated settings to all other modules.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Load .env from project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


class GEESettings(BaseModel):
    """Google Earth Engine configuration."""
    project_id: str = Field(
        default_factory=lambda: os.getenv("GEE_PROJECT_ID", ""),
        description="GCP project with Earth Engine API enabled",
    )
    service_account_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEE_SERVICE_ACCOUNT_KEY"),
        description="Optional path to service-account JSON key",
    )


class ServerSettings(BaseModel):
    """Backend server configuration."""
    host: str = Field(
        default_factory=lambda: os.getenv("BACKEND_HOST", "127.0.0.1"),
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")),
    )
    frontend_port: int = Field(
        default_factory=lambda: int(os.getenv("FRONTEND_PORT", "8501")),
    )


class AOISettings(BaseModel):
    """Default Area of Interest bounding box (Amazon Rainforest)."""
    west: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_AOI_WEST", "-60.0")),
    )
    south: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_AOI_SOUTH", "-3.0")),
    )
    east: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_AOI_EAST", "-59.0")),
    )
    north: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_AOI_NORTH", "-2.0")),
    )

    @property
    def bbox(self) -> List[float]:
        """Return [west, south, east, north] list."""
        return [self.west, self.south, self.east, self.north]

    @property
    def center(self) -> List[float]:
        """Return [lat, lon] center of the bounding box."""
        return [(self.south + self.north) / 2, (self.west + self.east) / 2]


class AppSettings(BaseModel):
    """Top-level application settings."""
    gee: GEESettings = Field(default_factory=GEESettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    aoi: AOISettings = Field(default_factory=AOISettings)
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
    )
    demo_mode: bool = Field(
        default_factory=lambda: os.getenv("DEMO_MODE", "false").lower() == "true",
    )


# ---------------------------------------------------------------------------
# Singleton settings instance
# ---------------------------------------------------------------------------
settings = AppSettings()
