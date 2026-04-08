"""
Data Export Utilities

Provides functions for exporting analysis results as downloadable
files (GeoJSON, CSV, PDF reports).
"""

import json
import csv
import io
from typing import Any, Dict, List
from datetime import datetime, timezone

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def export_stats_csv(stats: Dict[str, Any]) -> str:
    """
    Export statistics dictionary to CSV string.

    Args:
        stats: Dictionary of statistics to export.

    Returns:
        CSV-formatted string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    for key, value in stats.items():
        writer.writerow([key, value])
    return output.getvalue()


def export_stats_json(stats: Dict[str, Any], indent: int = 2) -> str:
    """
    Export statistics dictionary to formatted JSON string.

    Args:
        stats: Dictionary of statistics to export.
        indent: JSON indentation level.

    Returns:
        JSON-formatted string.
    """
    export_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": "Forest observation and analysis system",
        "data": stats,
    }
    return json.dumps(export_data, indent=indent, default=str)


def create_report_summary(
    ndvi_stats: Dict[str, Any],
    density_stats: Dict[str, Any] = None,
    change_stats: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Create a comprehensive report summary combining all analysis results.

    Args:
        ndvi_stats: NDVI analysis statistics.
        density_stats: Optional density classification statistics.
        change_stats: Optional change detection statistics.

    Returns:
        Combined report dictionary.
    """
    report = {
        "report_title": "Forest Canopy Density Analysis Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ndvi_analysis": ndvi_stats,
    }

    if density_stats:
        report["density_classification"] = density_stats

    if change_stats:
        report["change_detection"] = change_stats

    logger.info("Report summary created with %d sections", len(report) - 2)
    return report


def format_area_hectares(area_sqm: float) -> float:
    """
    Convert area from square meters to hectares.

    Args:
        area_sqm: Area in square meters.

    Returns:
        Area in hectares (rounded to 2 decimal places).
    """
    return round(area_sqm / 10000, 2)
