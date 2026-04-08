"""
API Endpoint Tests

Tests FastAPI endpoints using the TestClient.
Ensures all routes return correct status codes and response structure.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints."""

    def test_root(self):
        """Root endpoint should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Forest observation and analysis system"
        assert data["status"] == "operational"

    def test_health(self):
        """Health endpoint should return GEE status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "gee" in data
        assert "status" in data

    def test_api_status(self):
        """API status should list all available endpoints."""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert "ndvi" in data["endpoints"]
        assert "density" in data["endpoints"]
        assert "change_detection" in data["endpoints"]

class TestNDVIEndpoint:
    """Test NDVI API endpoint."""

    def test_ndvi_valid_request(self):
        """Valid NDVI request should return 200."""
        response = client.post("/api/ndvi/", json={
            "bbox": [-60.0, -3.0, -59.0, -2.0],
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "scale": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "stats" in data["data"]
        assert "mean" in data["data"]["stats"]

    def test_ndvi_invalid_bbox(self):
        """Invalid bounding box should return 422."""
        response = client.post("/api/ndvi/", json={
            "bbox": [-59.0, -3.0, -60.0, -2.0],  # west > east
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
        })
        assert response.status_code == 422

    def test_ndvi_missing_fields(self):
        """Missing required fields should return 422."""
        response = client.post("/api/ndvi/", json={
            "bbox": [-60.0, -3.0, -59.0, -2.0],
        })
        assert response.status_code == 422


class TestDensityEndpoint:
    """Test forest density API endpoint."""

    def test_density_valid_request(self):
        """Valid density request should return 200."""
        response = client.post("/api/density/", json={
            "bbox": [-60.0, -3.0, -59.0, -2.0],
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "scale": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "categories" in data["data"]

    def test_density_thresholds_endpoint(self):
        """Thresholds endpoint should return default thresholds."""
        response = client.get("/api/density/thresholds")
        assert response.status_code == 200
        data = response.json()
        assert "dense_forest" in data["data"]


class TestChangeDetectionEndpoint:
    """Test change detection API endpoint."""

    def test_change_valid_request(self):
        """Valid change detection request should return 200."""
        response = client.post("/api/change-detection/", json={
            "bbox": [-60.0, -3.0, -59.0, -2.0],
            "period1_start": "2023-01-01",
            "period1_end": "2023-06-30",
            "period2_start": "2024-01-01",
            "period2_end": "2024-06-30",
            "scale": 100,
            "change_threshold": 0.2,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "changes" in data["data"]



