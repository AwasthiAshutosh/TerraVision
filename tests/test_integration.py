"""
Integration Tests

End-to-end tests for the full analysis pipeline.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestEndToEndPipeline:
    """Test the complete analysis pipeline."""

    def test_full_ndvi_pipeline(self):
        """Test NDVI from request to response."""
        from backend.services.ndvi_service import calculate_ndvi

        result = calculate_ndvi(
            bbox=[-60.0, -3.0, -59.0, -2.0],
            start_date="2024-01-01",
            end_date="2024-06-30",
            scale=100,
        )

        assert "stats" in result
        assert "mean" in result["stats"]
        assert "interpretation" in result
        assert "metadata" in result
        # NDVI mean should be within valid range
        assert -1 <= result["stats"]["mean"] <= 1

    def test_full_density_pipeline(self):
        """Test density classification from request to response."""
        from backend.services.density_service import classify_density

        result = classify_density(
            bbox=[-60.0, -3.0, -59.0, -2.0],
            start_date="2024-01-01",
            end_date="2024-06-30",
            scale=100,
        )

        assert "categories" in result
        assert len(result["categories"]) == 5
        assert "total_area_hectares" in result

    def test_full_change_pipeline(self):
        """Test change detection from request to response."""
        from backend.services.change_service import detect_changes

        result = detect_changes(
            bbox=[-60.0, -3.0, -59.0, -2.0],
            period1_start="2023-01-01",
            period1_end="2023-06-30",
            period2_start="2024-01-01",
            period2_end="2024-06-30",
            scale=100,
        )

        assert "changes" in result
        assert "forest_loss" in result["changes"]
        assert "forest_gain" in result["changes"]
        assert "net_change_hectares" in result



    def test_export_utilities(self):
        """Test data export functions."""
        from backend.utils.export import export_stats_csv, export_stats_json

        stats = {"mean_ndvi": 0.72, "total_area": 11000}

        csv_output = export_stats_csv(stats)
        assert "mean_ndvi" in csv_output
        assert "0.72" in csv_output

        json_output = export_stats_json(stats)
        assert "Forest observation and analysis system" in json_output
        assert "0.72" in json_output
