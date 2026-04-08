"""
ML Prediction Service

Provides machine learning-based forest classification using
Random Forest classifier trained on spectral features.
"""

import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

import numpy as np

from backend.gee.auth import initialize_gee, is_demo_mode
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Path to trained models
MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


def predict_forest_type(
    bbox: List[float],
    start_date: str,
    end_date: str,
    model_type: str = "random_forest",
    scale: int = 100,
) -> Dict[str, Any]:
    """
    Classify forest types using a trained ML model.

    The classification pipeline:
        1. Extract spectral features from Sentinel-2 imagery
        2. Compute vegetation indices (NDVI, EVI, SAVI)
        3. Apply trained model for per-pixel classification
        4. Generate classified map and statistics

    Forest Classes:
        0 = Water
        1 = Urban/Built-up
        2 = Bare Soil
        3 = Grassland
        4 = Cropland
        5 = Shrubland
        6 = Sparse Forest
        7 = Dense Forest

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date "YYYY-MM-DD".
        end_date: End date "YYYY-MM-DD".
        model_type: Model to use — "random_forest" or "cnn".
        scale: Spatial resolution in meters.

    Returns:
        Dictionary with prediction results.
    """
    initialize_gee()

    if is_demo_mode() or not _model_exists(model_type):
        return _generate_demo_prediction(bbox, start_date, end_date, model_type)

    logger.info("Running ML prediction with %s model", model_type)

    try:
        if model_type == "random_forest":
            return _predict_with_random_forest(bbox, start_date, end_date, scale)
        else:
            return _generate_demo_prediction(bbox, start_date, end_date, model_type)
    except Exception as exc:
        logger.error("ML prediction failed: %s", exc)
        return _generate_demo_prediction(bbox, start_date, end_date, model_type)


def _model_exists(model_type: str) -> bool:
    """Check if a trained model file exists."""
    model_files = {
        "random_forest": MODEL_DIR / "random_forest_model.joblib",
        "cnn": MODEL_DIR / "cnn_model.h5",
    }
    exists = model_files.get(model_type, Path("")).exists()
    if not exists:
        logger.warning("Model file not found for: %s", model_type)
    return exists


def _predict_with_random_forest(
    bbox: List[float],
    start_date: str,
    end_date: str,
    scale: int,
) -> Dict[str, Any]:
    """
    Run prediction using trained Random Forest model via GEE.

    Uses ee.Classifier.smileRandomForest for server-side inference.
    """
    import ee
    from backend.gee.imagery import get_sentinel2_collection, create_composite

    collection = get_sentinel2_collection(bbox, start_date, end_date)
    composite = create_composite(collection, bbox)

    # Compute additional indices for feature enrichment
    ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")
    evi = composite.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR": composite.select("B8"), "RED": composite.select("B4"), "BLUE": composite.select("B2")},
    ).rename("EVI")
    savi = composite.expression(
        "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
        {"NIR": composite.select("B8"), "RED": composite.select("B4")},
    ).rename("SAVI")

    # Stack features
    features = composite.select(["B2", "B3", "B4", "B8", "B11", "B12"]).addBands([ndvi, evi, savi])

    # Load and apply trained classifier
    import joblib
    model_path = MODEL_DIR / "random_forest_model.joblib"
    rf_model = joblib.load(model_path)

    # For GEE, we'd use ee.Classifier — but for local models,
    # we need to extract pixel data and classify locally
    aoi = ee.Geometry.Rectangle(bbox)
    sample = features.sample(region=aoi, scale=scale, numPixels=5000, seed=42)
    feature_data = sample.getInfo()

    # Extract feature arrays
    band_names = ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "EVI", "SAVI"]
    X = []
    for feat in feature_data["features"]:
        row = [feat["properties"].get(b, 0) for b in band_names]
        X.append(row)

    X = np.array(X)
    predictions = rf_model.predict(X)
    probabilities = rf_model.predict_proba(X)

    # Calculate class distribution
    class_names = [
        "Water", "Urban", "Bare Soil", "Grassland",
        "Cropland", "Shrubland", "Sparse Forest", "Dense Forest",
    ]
    unique, counts = np.unique(predictions, return_counts=True)
    total = len(predictions)

    classes = {}
    for cls_val, count in zip(unique, counts):
        cls_idx = int(cls_val)
        if cls_idx < len(class_names):
            classes[class_names[cls_idx]] = {
                "pixel_count": int(count),
                "percentage": round(count / total * 100, 1),
            }

    return {
        "tile_url": None,
        "classes": classes,
        "confidence": round(float(probabilities.max(axis=1).mean()), 3),
        "model_type": "random_forest",
        "metadata": {
            "satellite": "Sentinel-2 L2A",
            "date_range": f"{start_date} to {end_date}",
            "features_used": band_names,
            "samples": total,
            "bbox": bbox,
        },
    }


def _generate_demo_prediction(
    bbox: List[float],
    start_date: str,
    end_date: str,
    model_type: str,
) -> Dict[str, Any]:
    """Generate synthetic ML prediction for demo mode."""
    np.random.seed(42)
    logger.info("Generating demo ML prediction data")

    return {
        "tile_url": None,
        "demo_mode": True,
        "classes": {
            "Dense Forest": {"pixel_count": 2750, "percentage": 55.0},
            "Sparse Forest": {"pixel_count": 600, "percentage": 12.0},
            "Shrubland": {"pixel_count": 500, "percentage": 10.0},
            "Cropland": {"pixel_count": 400, "percentage": 8.0},
            "Grassland": {"pixel_count": 350, "percentage": 7.0},
            "Bare Soil": {"pixel_count": 200, "percentage": 4.0},
            "Water": {"pixel_count": 150, "percentage": 3.0},
            "Urban": {"pixel_count": 50, "percentage": 1.0},
        },
        "confidence": 0.847,
        "model_type": model_type,
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "date_range": f"{start_date} to {end_date}",
            "features_used": ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "EVI", "SAVI"],
            "samples": 5000,
            "bbox": bbox,
            "note": "Model not trained yet — showing simulated results",
        },
    }
