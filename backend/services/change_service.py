"""
Change Detection Service

Detects temporal changes in forest cover by comparing NDVI composites
from two different time periods. Identifies deforestation, degradation,
and regrowth.

Change Detection Algorithm:
    1. Compute NDVI composite for Period 1 (baseline)
    2. Compute NDVI composite for Period 2 (comparison)
    3. Calculate ΔNDVI = NDVI₂ - NDVI₁
    4. Apply thresholds:
       - ΔNDVI < -threshold  → Forest Loss
       - ΔNDVI > +threshold  → Forest Gain
       - |ΔNDVI| ≤ threshold → Stable/No Change
    5. Calculate area statistics for each change class
"""

from typing import Any, Dict, List

import ee

from backend.gee.auth import initialize_gee, is_demo_mode
from backend.gee.imagery import (
    get_sentinel2_collection, create_composite, compute_ndvi,
    _bbox_seed, _estimate_area_hectares,
)
from backend.utils.exceptions import NoDataAvailableError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def detect_changes(
    bbox: List[float],
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    scale: int = 100,
    change_threshold: float = 0.2,
) -> Dict[str, Any]:
    """
    Detect forest cover changes between two time periods.

    This implements pixel-wise NDVI differencing, the most widely-used
    approach for forest change detection (Lu et al., 2004; Coppin et al., 2004).

    Args:
        bbox: [west, south, east, north] bounding box.
        period1_start: Period 1 start date "YYYY-MM-DD".
        period1_end: Period 1 end date "YYYY-MM-DD".
        period2_start: Period 2 start date "YYYY-MM-DD".
        period2_end: Period 2 end date "YYYY-MM-DD".
        scale: Spatial resolution in meters.
        change_threshold: Minimum NDVI difference to flag change (default 0.2).

    Returns:
        Dictionary with change map tile URL, statistics, and metadata.

    Raises:
        NoDataAvailableError: If no satellite images are available for either period.
    """
    initialize_gee()

    if is_demo_mode():
        return _generate_demo_changes(
            bbox, period1_start, period1_end,
            period2_start, period2_end, change_threshold,
        )

    logger.info(
        "Detecting changes — Period1: %s to %s, Period2: %s to %s",
        period1_start, period1_end, period2_start, period2_end,
    )

    aoi = ee.Geometry.Rectangle(bbox)

    # 1. Compute NDVI for Period 1 (baseline)
    # Raises NoDataAvailableError if no images found
    try:
        collection1 = get_sentinel2_collection(bbox, period1_start, period1_end)
    except NoDataAvailableError:
        raise NoDataAvailableError(
            f"No satellite imagery available for Period 1 ({period1_start} to {period1_end}). "
            f"Try expanding the date range or using a different season.",
            details={"period": "period1", "start": period1_start, "end": period1_end, "bbox": bbox},
        )
    composite1 = create_composite(collection1, bbox)
    ndvi1 = compute_ndvi(composite1)

    # 2. Compute NDVI for Period 2 (comparison)
    try:
        collection2 = get_sentinel2_collection(bbox, period2_start, period2_end)
    except NoDataAvailableError:
        raise NoDataAvailableError(
            f"No satellite imagery available for Period 2 ({period2_start} to {period2_end}). "
            f"Try expanding the date range or using a different season.",
            details={"period": "period2", "start": period2_start, "end": period2_end, "bbox": bbox},
        )
    composite2 = create_composite(collection2, bbox)
    ndvi2 = compute_ndvi(composite2)

    # 3. Calculate NDVI difference (ΔNDVI)
    ndvi_diff = ndvi2.subtract(ndvi1).rename("NDVI_change")

    # 4. Classify changes
    # Class 1 = Forest Loss (negative change exceeding threshold)
    # Class 2 = Stable (no significant change)
    # Class 3 = Forest Gain (positive change exceeding threshold)
    change_classified = (
        ee.Image(2)  # Default: stable
        .where(ndvi_diff.lt(-change_threshold), 1)   # Loss
        .where(ndvi_diff.gt(change_threshold), 3)     # Gain
        .rename("change_class")
        .clip(aoi)
    )

    # 5. Visualization
    vis_params = {
        "min": 1,
        "max": 3,
        "palette": ["#e53935", "#fdd835", "#43a047"],  # Red, Yellow, Green
    }

    map_id = change_classified.getMapId(vis_params)
    tile_url = map_id["tile_fetcher"].url_format

    # 6. Get NDVI difference tile for heatmap view
    diff_vis = {
        "min": -0.5,
        "max": 0.5,
        "palette": ["#b71c1c", "#e53935", "#ffcdd2", "#ffffff", "#c8e6c9", "#43a047", "#1b5e20"],
    }
    diff_map_id = ndvi_diff.getMapId(diff_vis)
    diff_tile_url = diff_map_id["tile_fetcher"].url_format

    # 7. Calculate area statistics
    pixel_area = ee.Image.pixelArea()

    loss_area = (
        pixel_area.updateMask(change_classified.eq(1))
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e9, tileScale=4)
        .get("area")
    )
    gain_area = (
        pixel_area.updateMask(change_classified.eq(3))
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e9, tileScale=4)
        .get("area")
    )
    stable_area = (
        pixel_area.updateMask(change_classified.eq(2))
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=aoi, scale=scale, maxPixels=1e9, tileScale=4)
        .get("area")
    )

    loss_val = ee.Number(loss_area).getInfo() if loss_area is not None else 0
    gain_val = ee.Number(gain_area).getInfo() if gain_area is not None else 0
    stable_val = ee.Number(stable_area).getInfo() if stable_area is not None else 0
    loss_ha = round((loss_val or 0) / 10000, 2)
    gain_ha = round((gain_val or 0) / 10000, 2)
    stable_ha = round((stable_val or 0) / 10000, 2)
    total_ha = loss_ha + gain_ha + stable_ha

    # 8. NDVI statistics for each period
    stats1 = ndvi1.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=scale, maxPixels=1e9, tileScale=4,
    ).getInfo()
    stats2 = ndvi2.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=scale, maxPixels=1e9, tileScale=4,
    ).getInfo()

    logger.info(
        "Change detection complete — Loss: %.1f ha, Gain: %.1f ha, Stable: %.1f ha",
        loss_ha, gain_ha, stable_ha,
    )

    return {
        "change_tile_url": tile_url,
        "diff_tile_url": diff_tile_url,
        "changes": {
            "forest_loss": {
                "area_hectares": loss_ha,
                "percentage": round(loss_ha / total_ha * 100, 1) if total_ha > 0 else 0,
                "color": "#e53935",
                "label": "Forest Loss",
            },
            "stable": {
                "area_hectares": stable_ha,
                "percentage": round(stable_ha / total_ha * 100, 1) if total_ha > 0 else 0,
                "color": "#fdd835",
                "label": "Stable",
            },
            "forest_gain": {
                "area_hectares": gain_ha,
                "percentage": round(gain_ha / total_ha * 100, 1) if total_ha > 0 else 0,
                "color": "#43a047",
                "label": "Forest Gain",
            },
        },
        "total_area_hectares": total_ha,
        "net_change_hectares": round(gain_ha - loss_ha, 2),
        "period1_mean_ndvi": round(stats1.get("NDVI", 0), 4),
        "period2_mean_ndvi": round(stats2.get("NDVI", 0), 4),
        "metadata": {
            "satellite": "Sentinel-2 L2A",
            "period1": f"{period1_start} to {period1_end}",
            "period2": f"{period2_start} to {period2_end}",
            "change_threshold": change_threshold,
            "scale_meters": scale,
            "bbox": bbox,
        },
        "vis_params": vis_params,
    }


def _generate_demo_changes(
    bbox: List[float],
    p1_start: str, p1_end: str,
    p2_start: str, p2_end: str,
    threshold: float,
) -> Dict[str, Any]:
    """
    Generate synthetic change detection data for demo mode.

    Uses bbox + dates + threshold to produce varied, input-responsive results.
    """
    import numpy as np

    seed = _bbox_seed(bbox, f"{p1_start}{p1_end}{p2_start}{p2_end}")
    rng = np.random.RandomState(seed)
    logger.info("Generating demo change detection data for bbox: %s", bbox)

    # Use actual bbox area
    total_ha = _estimate_area_hectares(bbox)
    if total_ha < 100:
        total_ha = 11000.0

    # Derive loss/gain from latitude, longitude,  and threshold
    # Higher threshold → less detected change
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    mid_lon = abs((bbox[0] + bbox[2]) / 2)
    loss_pct = max(1, min(25, 8 + mid_lat * 0.12 + mid_lon * 0.02 - threshold * 15 + rng.uniform(-4, 4)))
    gain_pct = max(0.5, min(15, 3 + mid_lon * 0.01 + rng.uniform(-1.5, 2.5)))
    stable_pct = 100 - loss_pct - gain_pct

    loss_ha = round(total_ha * loss_pct / 100, 2)
    gain_ha = round(total_ha * gain_pct / 100, 2)
    stable_ha = round(total_ha * stable_pct / 100, 2)

    # Derive NDVI from latitude
    base_ndvi = max(0.3, min(0.85, 0.80 - mid_lat * 0.008))
    p1_ndvi = round(base_ndvi + rng.uniform(-0.03, 0.03), 4)
    p2_ndvi = round(p1_ndvi + (gain_ha - loss_ha) / total_ha, 4)

    return {
        "change_tile_url": None,
        "diff_tile_url": None,
        "demo_mode": True,
        "changes": {
            "forest_loss": {
                "area_hectares": loss_ha,
                "percentage": round(loss_pct, 1),
                "color": "#e53935",
                "label": "Forest Loss",
            },
            "stable": {
                "area_hectares": stable_ha,
                "percentage": round(stable_pct, 1),
                "color": "#fdd835",
                "label": "Stable",
            },
            "forest_gain": {
                "area_hectares": gain_ha,
                "percentage": round(gain_pct, 1),
                "color": "#43a047",
                "label": "Forest Gain",
            },
        },
        "total_area_hectares": round(total_ha, 2),
        "net_change_hectares": round(gain_ha - loss_ha, 2),
        "period1_mean_ndvi": p1_ndvi,
        "period2_mean_ndvi": p2_ndvi,
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "period1": f"{p1_start} to {p1_end}",
            "period2": f"{p2_start} to {p2_end}",
            "change_threshold": threshold,
            "scale_meters": 100,
            "bbox": bbox,
        },
        "vis_params": {"min": 1, "max": 3, "palette": ["#e53935", "#fdd835", "#43a047"]},
    }
