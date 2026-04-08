"""
Satellite Imagery Module

Handles fetching, filtering, and compositing satellite imagery from
Google Earth Engine. Primary support for Sentinel-2 Level-2A with
optional Landsat fallback.
"""

from typing import Dict, List, Optional, Tuple

import ee

from backend.gee.auth import initialize_gee, is_demo_mode
from backend.gee.cloud_mask import mask_sentinel2_clouds
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Sentinel-2 Collection ID (Level-2A = Surface Reflectance)
# ---------------------------------------------------------------------------
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
LANDSAT8_COLLECTION = "LANDSAT/LC08/C02/T1_L2"


def get_sentinel2_collection(
    bbox: List[float],
    start_date: str,
    end_date: str,
    max_cloud_pct: float = 30.0,
) -> ee.ImageCollection:
    """
    Fetch a filtered Sentinel-2 Level-2A image collection.

    Steps:
        1. Define the AOI geometry from the bounding box
        2. Filter by date range
        3. Filter by AOI bounds
        4. Pre-filter by CLOUDY_PIXEL_PERCENTAGE metadata
        5. Apply per-pixel cloud masking via SCL band

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date string "YYYY-MM-DD".
        end_date: End date string "YYYY-MM-DD".
        max_cloud_pct: Maximum cloud cover percentage for pre-filtering.

    Returns:
        Cloud-masked ee.ImageCollection.
    """
    # Create AOI geometry
    aoi = ee.Geometry.Rectangle(bbox)

    # Build filtered collection
    collection = (
        ee.ImageCollection(SENTINEL2_COLLECTION)
        .filterDate(start_date, end_date)
        .filterBounds(aoi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
        .map(mask_sentinel2_clouds)
    )

    logger.info(
        "Sentinel-2 collection filtered (%s to %s)",
        start_date, end_date,
    )

    return collection


def create_composite(
    collection: ee.ImageCollection,
    bbox: List[float],
    method: str = "median",
) -> ee.Image:
    """
    Create a cloud-free composite from an image collection.

    Compositing reduces temporal noise by combining multiple images.
    The median composite is most robust to outliers (cloud residuals).

    Args:
        collection: Cloud-masked ee.ImageCollection.
        bbox: [west, south, east, north] to clip the result.
        method: Compositing method — "median" (default) or "mean".

    Returns:
        Composited ee.Image clipped to the AOI.
    """
    aoi = ee.Geometry.Rectangle(bbox)

    if method == "mean":
        composite = collection.mean()
    else:
        composite = collection.median()

    return composite.clip(aoi)


def compute_ndvi(image: ee.Image) -> ee.Image:
    """
    Compute Normalized Difference Vegetation Index (NDVI).

    Formula:
        NDVI = (NIR - Red) / (NIR + Red)
        Where:  NIR = Band 8 (842nm)
                Red = Band 4 (665nm)

    NDVI values range from -1 to +1:
        - Values near +1: Dense healthy vegetation
        - Values near  0: Bare soil, urban areas
        - Values near -1: Water bodies

    Args:
        image: ee.Image with B8 (NIR) and B4 (Red) bands.

    Returns:
        ee.Image with a single 'NDVI' band.
    """
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return ndvi


def get_ndvi_composite(
    bbox: List[float],
    start_date: str,
    end_date: str,
    scale: int = 100,
) -> Dict:
    """
    Full pipeline: Fetch imagery → Composite → Compute NDVI → Get stats & tile URL.

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date "YYYY-MM-DD".
        end_date: End date "YYYY-MM-DD".
        scale: Spatial resolution in meters for statistics.

    Returns:
        Dictionary with tile_url, stats, and metadata.
    """
    initialize_gee()

    if is_demo_mode():
        return _generate_demo_ndvi(bbox, start_date, end_date)

    # 1. Fetch filtered Sentinel-2 collection
    collection = get_sentinel2_collection(bbox, start_date, end_date)

    # 2. Create median composite
    composite = create_composite(collection, bbox)

    # 3. Compute NDVI
    ndvi = compute_ndvi(composite)

    # 4. Generate visualization parameters
    vis_params = {
        "min": -0.2,
        "max": 0.9,
        "palette": [
            "#d73027",  # Red — barren/water
            "#fc8d59",  # Orange — sparse
            "#fee08b",  # Yellow — moderate
            "#d9ef8b",  # Light green — healthy
            "#91cf60",  # Green — dense
            "#1a9850",  # Dark green — very dense
        ],
    }

    # 5. Get tile URL for map display
    map_id = ndvi.getMapId(vis_params)
    tile_url = map_id["tile_fetcher"].url_format

    # 6. Compute statistics
    aoi = ee.Geometry.Rectangle(bbox)
    stats = ndvi.reduceRegion(
        reducer=ee.Reducer.mean()
            .combine(ee.Reducer.minMax(), sharedInputs=True)
            .combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=aoi,
        scale=scale,
        maxPixels=1e9,
        tileScale=4,
    ).getInfo()

    # 7. Get image count
    image_count = collection.size().getInfo()

    logger.info("NDVI composite generated — mean: %.3f", stats.get("NDVI_mean", 0))

    return {
        "tile_url": tile_url,
        "stats": {
            "mean": round(stats.get("NDVI_mean", 0), 4),
            "min": round(stats.get("NDVI_min", 0), 4),
            "max": round(stats.get("NDVI_max", 0), 4),
            "std_dev": round(stats.get("NDVI_stdDev", 0), 4),
        },
        "metadata": {
            "satellite": "Sentinel-2 L2A",
            "date_range": f"{start_date} to {end_date}",
            "images_used": image_count,
            "scale_meters": scale,
            "bbox": bbox,
            "compositing_method": "median",
        },
        "vis_params": vis_params,
    }


def _generate_demo_ndvi(
    bbox: List[float],
    start_date: str,
    end_date: str,
) -> Dict:
    """
    Generate synthetic NDVI data for demo mode.

    Creates realistic-looking statistics without requiring GEE access.
    The frontend will render a simulated heatmap overlay.
    """
    import numpy as np

    np.random.seed(42)

    logger.info("Generating demo NDVI data for bbox: %s", bbox)

    # Simulate realistic Amazon rainforest NDVI stats
    mean_ndvi = 0.72 + np.random.uniform(-0.05, 0.05)
    return {
        "tile_url": None,
        "demo_mode": True,
        "stats": {
            "mean": round(mean_ndvi, 4),
            "min": round(mean_ndvi - 0.45, 4),
            "max": round(min(mean_ndvi + 0.18, 0.95), 4),
            "std_dev": round(np.random.uniform(0.12, 0.18), 4),
        },
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "date_range": f"{start_date} to {end_date}",
            "images_used": 0,
            "scale_meters": 100,
            "bbox": bbox,
            "compositing_method": "median (simulated)",
        },
        "vis_params": {
            "min": -0.2,
            "max": 0.9,
            "palette": [
                "#d73027", "#fc8d59", "#fee08b",
                "#d9ef8b", "#91cf60", "#1a9850",
            ],
        },
        "demo_grid": _generate_demo_grid(bbox),
    }


def _generate_demo_grid(bbox: List[float], grid_size: int = 50) -> List[List[float]]:
    """
    Generate a grid of simulated NDVI values for demo visualization.

    Uses perlin-noise-like patterns to create realistic spatial variation
    for the Amazon rainforest region.
    """
    import numpy as np

    np.random.seed(42)

    # Create base pattern (mostly dense forest with some clearings)
    x = np.linspace(0, 4 * np.pi, grid_size)
    y = np.linspace(0, 4 * np.pi, grid_size)
    xx, yy = np.meshgrid(x, y)

    # Simulate forest canopy with clearings
    base = 0.7 + 0.15 * np.sin(xx * 0.5) * np.cos(yy * 0.3)
    noise = np.random.normal(0, 0.05, (grid_size, grid_size))

    # Add some "deforested" patches
    clearing1 = np.exp(-((xx - 6) ** 2 + (yy - 4) ** 2) / 4) * 0.5
    clearing2 = np.exp(-((xx - 10) ** 2 + (yy - 8) ** 2) / 3) * 0.4

    ndvi_grid = np.clip(base + noise - clearing1 - clearing2, -0.2, 0.95)

    return ndvi_grid.tolist()
