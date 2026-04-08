"""
NDVI Service

Business logic layer for NDVI computation. Orchestrates GEE imagery
modules and returns structured results for the API layer.
"""

from typing import Dict, Any, List

from backend.gee.imagery import get_ndvi_composite
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_ndvi(
    bbox: List[float],
    start_date: str,
    end_date: str,
    scale: int = 100,
) -> Dict[str, Any]:
    """
    Calculate NDVI for a given AOI and date range.

    This is the main entry point for NDVI analysis. It wraps the GEE
    imagery pipeline and adds interpretation metadata.

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date "YYYY-MM-DD".
        end_date: End date "YYYY-MM-DD".
        scale: Spatial resolution in meters.

    Returns:
        Dictionary with tile_url, stats, metadata, and interpretation.
    """
    logger.info(
        "Calculating NDVI — bbox: %s, dates: %s to %s, scale: %dm",
        bbox, start_date, end_date, scale,
    )

    # Get NDVI composite from GEE (or demo data)
    result = get_ndvi_composite(bbox, start_date, end_date, scale)

    # Add interpretation of the mean NDVI value
    mean_ndvi = result["stats"]["mean"]
    result["interpretation"] = _interpret_ndvi(mean_ndvi)

    logger.info(
        "NDVI calculation complete — mean: %.4f (%s)",
        mean_ndvi,
        result["interpretation"]["category"],
    )

    return result


def _interpret_ndvi(mean_ndvi: float) -> Dict[str, str]:
    """
    Provide human-readable interpretation of NDVI values.

    Based on established remote sensing literature:
    - Tucker, C.J. (1979) "Red and photographic infrared linear combinations
      for monitoring vegetation"

    Args:
        mean_ndvi: Mean NDVI value for the AOI.

    Returns:
        Dictionary with category and description.
    """
    if mean_ndvi > 0.7:
        return {
            "category": "Dense Healthy Vegetation",
            "description": (
                "The area shows very high vegetation density, indicative of "
                "healthy, closed-canopy forest. This NDVI range is typical of "
                "tropical rainforests and dense deciduous forests."
            ),
            "health": "excellent",
        }
    elif mean_ndvi > 0.5:
        return {
            "category": "Moderate Vegetation",
            "description": (
                "The area shows moderate vegetation cover. This range indicates "
                "open canopy forests, mixed vegetation, or agricultural areas "
                "with active crop growth."
            ),
            "health": "good",
        }
    elif mean_ndvi > 0.3:
        return {
            "category": "Sparse Vegetation",
            "description": (
                "Sparse vegetation cover detected. This may indicate degraded "
                "forests, scrubland, grassland, or early-stage regrowth areas."
            ),
            "health": "moderate",
        }
    elif mean_ndvi > 0.1:
        return {
            "category": "Minimal Vegetation",
            "description": (
                "Very low vegetation signal. The area is likely bare soil, "
                "recently cleared land, or transitional landscape."
            ),
            "health": "poor",
        }
    else:
        return {
            "category": "Non-Vegetated",
            "description": (
                "No significant vegetation detected. The area may be water, "
                "urban, rock, or heavily degraded land."
            ),
            "health": "none",
        }
