"""
Unit Tests — NDVI Calculation

Tests the core NDVI computation logic, validation, and interpretation.
"""

import sys
from pathlib import Path

import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestNDVICalculation:
    """Tests for NDVI formula and interpretation."""

    def test_ndvi_formula_basic(self):
        """
        Test NDVI formula: NDVI = (NIR - Red) / (NIR + Red)
        """
        # Dense vegetation: NIR >> Red
        nir, red = 0.5, 0.1
        ndvi = (nir - red) / (nir + red)
        assert ndvi == pytest.approx(0.6667, rel=1e-3)

    def test_ndvi_formula_water(self):
        """Water bodies should have negative NDVI."""
        nir, red = 0.05, 0.1
        ndvi = (nir - red) / (nir + red)
        assert ndvi < 0

    def test_ndvi_formula_bare_soil(self):
        """Bare soil should have NDVI near zero."""
        nir, red = 0.15, 0.14
        ndvi = (nir - red) / (nir + red)
        assert -0.1 < ndvi < 0.1

    def test_ndvi_formula_dense_forest(self):
        """Dense forest should have high NDVI (>0.6)."""
        nir, red = 0.45, 0.05
        ndvi = (nir - red) / (nir + red)
        assert ndvi > 0.7

    def test_ndvi_range(self):
        """NDVI should always be between -1 and 1."""
        test_cases = [
            (0.5, 0.1),
            (0.1, 0.5),
            (0.0, 0.3),
            (0.3, 0.0),
            (0.5, 0.5),
        ]
        for nir, red in test_cases:
            if nir + red > 0:
                ndvi = (nir - red) / (nir + red)
                assert -1.0 <= ndvi <= 1.0, f"NDVI {ndvi} out of range for NIR={nir}, Red={red}"

    def test_ndvi_zero_division(self):
        """Handle edge case where NIR + Red = 0."""
        nir, red = 0.0, 0.0
        # In practice, we check for zero denominator
        denominator = nir + red
        ndvi = 0.0 if denominator == 0 else (nir - red) / denominator
        assert ndvi == 0.0


class TestNDVIInterpretation:
    """Test NDVI value interpretation."""

    def test_dense_forest_interpretation(self):
        """NDVI > 0.7 should be classified as Dense Healthy Vegetation."""
        from backend.services.ndvi_service import _interpret_ndvi
        result = _interpret_ndvi(0.8)
        assert result["category"] == "Dense Healthy Vegetation"
        assert result["health"] == "excellent"

    def test_moderate_interpretation(self):
        """NDVI 0.5-0.7 should be Moderate Vegetation."""
        from backend.services.ndvi_service import _interpret_ndvi
        result = _interpret_ndvi(0.6)
        assert result["category"] == "Moderate Vegetation"
        assert result["health"] == "good"

    def test_sparse_interpretation(self):
        """NDVI 0.3-0.5 should be Sparse Vegetation."""
        from backend.services.ndvi_service import _interpret_ndvi
        result = _interpret_ndvi(0.4)
        assert result["category"] == "Sparse Vegetation"
        assert result["health"] == "moderate"

    def test_minimal_interpretation(self):
        """NDVI 0.1-0.3 should be Minimal Vegetation."""
        from backend.services.ndvi_service import _interpret_ndvi
        result = _interpret_ndvi(0.2)
        assert result["category"] == "Minimal Vegetation"
        assert result["health"] == "poor"

    def test_non_vegetated_interpretation(self):
        """NDVI < 0.1 should be Non-Vegetated."""
        from backend.services.ndvi_service import _interpret_ndvi
        result = _interpret_ndvi(0.05)
        assert result["category"] == "Non-Vegetated"
        assert result["health"] == "none"


class TestNDVIValidation:
    """Test input validation for NDVI requests."""

    def test_valid_bbox(self):
        """Valid bounding box should pass validation."""
        from backend.utils.validators import NDVIRequest
        request = NDVIRequest(
            bbox=[-60.0, -3.0, -59.0, -2.0],
            start_date="2024-01-01",
            end_date="2024-06-30",
        )
        assert request.bbox == [-60.0, -3.0, -59.0, -2.0]

    def test_invalid_bbox_order(self):
        """West > East should fail validation."""
        from backend.utils.validators import NDVIRequest
        with pytest.raises(Exception):
            NDVIRequest(
                bbox=[-59.0, -3.0, -60.0, -2.0],  # west > east
                start_date="2024-01-01",
                end_date="2024-06-30",
            )

    def test_scale_range(self):
        """Scale must be between 10 and 1000."""
        from backend.utils.validators import NDVIRequest
        request = NDVIRequest(
            bbox=[-60.0, -3.0, -59.0, -2.0],
            start_date="2024-01-01",
            end_date="2024-06-30",
            scale=100,
        )
        assert request.scale == 100

        with pytest.raises(Exception):
            NDVIRequest(
                bbox=[-60.0, -3.0, -59.0, -2.0],
                start_date="2024-01-01",
                end_date="2024-06-30",
                scale=5,  # Below min
            )


class TestDensityThresholds:
    """Test density classification thresholds."""

    def test_default_thresholds_coverage(self):
        """Default thresholds should cover entire NDVI range."""
        from backend.services.density_service import DEFAULT_THRESHOLDS

        ranges = [(t["min"], t["max"]) for t in DEFAULT_THRESHOLDS.values()]
        # Check that min starts at -1.0 and max reaches 1.0
        min_val = min(r[0] for r in ranges)
        max_val = max(r[1] for r in ranges)
        assert min_val <= -0.5, f"Minimum threshold {min_val} should cover negative NDVI"
        assert max_val >= 0.9, f"Maximum threshold {max_val} should cover high NDVI"

    def test_threshold_continuity(self):
        """Thresholds should be continuous (no gaps)."""
        from backend.services.density_service import DEFAULT_THRESHOLDS

        sorted_thresh = sorted(DEFAULT_THRESHOLDS.values(), key=lambda x: x["min"])
        for i in range(len(sorted_thresh) - 1):
            assert sorted_thresh[i]["max"] == sorted_thresh[i + 1]["min"], (
                f"Gap between {sorted_thresh[i]['label']} and {sorted_thresh[i+1]['label']}"
            )
