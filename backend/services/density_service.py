"""
Forest Density Classification Service

Classifies NDVI values into forest canopy density categories using
scientifically-defined thresholds based on peer-reviewed literature.

Thresholds are derived from:
- Rikimaru et al. (2002) "Tropical forest cover density mapping"
- Hansen et al. (2013) "High-resolution global maps of 21st-century
  forest cover change"

Default Classification Scheme:
    NDVI > 0.7    → Dense Forest (closed canopy, >70% crown cover)
    0.5 – 0.7     → Moderate Forest (open canopy, 40-70% crown cover)
    0.3 – 0.5     → Sparse Vegetation (scrub, degraded, 10-40% cover)
    0.1 – 0.3     → Grassland/Crops (agricultural, <10% tree cover)
    NDVI < 0.1    → Non-Vegetation (urban, water, bare soil)
"""

from typing import Any, Dict, List, Optional

import ee

from backend.gee.auth import initialize_gee, is_demo_mode
from backend.gee.imagery import get_sentinel2_collection, create_composite, compute_ndvi
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Default density thresholds
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    "dense_forest": {"min": 0.7, "max": 1.0, "label": "Dense Forest", "color": "#0a5e1a"},
    "moderate_forest": {"min": 0.5, "max": 0.7, "label": "Moderate Forest", "color": "#4caf50"},
    "sparse_vegetation": {"min": 0.3, "max": 0.5, "label": "Sparse Vegetation", "color": "#cddc39"},
    "grassland_crops": {"min": 0.1, "max": 0.3, "label": "Grassland/Crops", "color": "#ffeb3b"},
    "non_vegetation": {"min": -1.0, "max": 0.1, "label": "Non-Vegetation", "color": "#d32f2f"},
}


def classify_density(
    bbox: List[float],
    start_date: str,
    end_date: str,
    scale: int = 100,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Classify forest canopy density from NDVI values.

    Pipeline:
        1. Fetch Sentinel-2 imagery → cloud mask → composite
        2. Compute NDVI
        3. Reclassify pixels into density categories
        4. Calculate area statistics per category
        5. Return tile URL + statistics

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date "YYYY-MM-DD".
        end_date: End date "YYYY-MM-DD".
        scale: Spatial resolution in meters.
        thresholds: Optional custom thresholds dict.

    Returns:
        Dictionary with tile_url, category areas, and metadata.
    """
    initialize_gee()
    thresholds = thresholds or DEFAULT_THRESHOLDS

    if is_demo_mode():
        return _generate_demo_density(bbox, start_date, end_date, thresholds)

    logger.info("Classifying forest density for bbox: %s", bbox)

    # 1. Fetch and composite imagery
    collection = get_sentinel2_collection(bbox, start_date, end_date)
    composite = create_composite(collection, bbox)
    ndvi = compute_ndvi(composite)

    # 2. Create classified image (each pixel gets a class value 1-5)
    aoi = ee.Geometry.Rectangle(bbox)
    classified = ee.Image(0).rename("density_class")

    class_value = 1
    for key, thresh in thresholds.items():
        mask = ndvi.gte(thresh["min"]).And(ndvi.lt(thresh["max"]))
        classified = classified.where(mask, class_value)
        class_value += 1

    classified = classified.clip(aoi)

    # 3. Visualization parameters
    class_colors = [t["color"] for t in thresholds.values()]
    vis_params = {
        "min": 1,
        "max": len(thresholds),
        "palette": class_colors,
    }

    map_id = classified.getMapId(vis_params)
    tile_url = map_id["tile_fetcher"].url_format

    # 4. Calculate area per category
    pixel_area = ee.Image.pixelArea()
    categories = {}

    class_value = 1
    for key, thresh in thresholds.items():
        class_mask = classified.eq(class_value)
        area = (
            pixel_area.updateMask(class_mask)
            .reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=aoi,
                scale=scale,
                maxPixels=1e9,
                tileScale=4,
            )
            .get("area")
        )
        area_val = ee.Number(area).getInfo() if area is not None else None
        area_ha = round((area_val or 0) / 10000, 2)

        categories[key] = {
            "label": thresh["label"],
            "area_hectares": area_ha,
            "color": thresh["color"],
            "ndvi_range": f"{thresh['min']} – {thresh['max']}",
        }
        class_value += 1

    # 5. Calculate total and percentages
    total_ha = sum(c["area_hectares"] for c in categories.values())
    for cat in categories.values():
        cat["percentage"] = (
            round(cat["area_hectares"] / total_ha * 100, 1) if total_ha > 0 else 0
        )

    logger.info("Density classification complete — %d categories", len(categories))

    return {
        "tile_url": tile_url,
        "categories": categories,
        "total_area_hectares": round(total_ha, 2),
        "metadata": {
            "satellite": "Sentinel-2 L2A",
            "date_range": f"{start_date} to {end_date}",
            "scale_meters": scale,
            "bbox": bbox,
            "thresholds_used": {k: {"min": v["min"], "max": v["max"]} for k, v in thresholds.items()},
        },
        "vis_params": vis_params,
    }


def _generate_demo_density(
    bbox: List[float],
    start_date: str,
    end_date: str,
    thresholds: Dict,
) -> Dict[str, Any]:
    """Generate synthetic density classification for demo mode."""
    import numpy as np

    np.random.seed(42)
    logger.info("Generating demo density data")

    # Simulate Amazon rainforest distribution (mostly dense forest)
    total_ha = 11000.0
    categories = {
        "dense_forest": {
            "label": "Dense Forest", "area_hectares": round(total_ha * 0.55, 2),
            "color": "#0a5e1a", "ndvi_range": "0.7 – 1.0", "percentage": 55.0,
        },
        "moderate_forest": {
            "label": "Moderate Forest", "area_hectares": round(total_ha * 0.22, 2),
            "color": "#4caf50", "ndvi_range": "0.5 – 0.7", "percentage": 22.0,
        },
        "sparse_vegetation": {
            "label": "Sparse Vegetation", "area_hectares": round(total_ha * 0.12, 2),
            "color": "#cddc39", "ndvi_range": "0.3 – 0.5", "percentage": 12.0,
        },
        "grassland_crops": {
            "label": "Grassland/Crops", "area_hectares": round(total_ha * 0.07, 2),
            "color": "#ffeb3b", "ndvi_range": "0.1 – 0.3", "percentage": 7.0,
        },
        "non_vegetation": {
            "label": "Non-Vegetation", "area_hectares": round(total_ha * 0.04, 2),
            "color": "#d32f2f", "ndvi_range": "-1.0 – 0.1", "percentage": 4.0,
        },
    }

    return {
        "tile_url": None,
        "demo_mode": True,
        "categories": categories,
        "total_area_hectares": total_ha,
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "date_range": f"{start_date} to {end_date}",
            "scale_meters": 100,
            "bbox": bbox,
        },
        "vis_params": {"min": 1, "max": 5, "palette": [t["color"] for t in thresholds.values()]},
    }
