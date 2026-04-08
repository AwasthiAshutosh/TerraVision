"""
Dataset Preparation for Forest Classification

Extracts training data from Google Earth Engine by sampling
spectral features at labeled land cover points. Uses ESA WorldCover
or similar as reference labels for supervised classification.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple

from backend.utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def extract_training_features(
    bbox: List[float],
    start_date: str,
    end_date: str,
    num_samples: int = 5000,
    scale: int = 100,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract spectral features and labels from GEE for model training.

    Pipeline:
        1. Load Sentinel-2 composite for the AOI
        2. Compute derived indices (NDVI, EVI, SAVI, NDWI)
        3. Load ESA WorldCover as reference labels
        4. Sample stratified random points
        5. Extract pixel values at each sample point

    Feature Stack:
        - B2 (Blue), B3 (Green), B4 (Red)
        - B8 (NIR), B11 (SWIR1), B12 (SWIR2)
        - NDVI, EVI, SAVI, NDWI (derived indices)

    Args:
        bbox: [west, south, east, north] bounding box.
        start_date: Start date string.
        end_date: End date string.
        num_samples: Number of training samples to extract.
        scale: Resolution in meters.

    Returns:
        Tuple of (X_features, y_labels) as numpy arrays.
    """
    try:
        import ee
        from backend.gee.auth import initialize_gee
        from backend.gee.imagery import get_sentinel2_collection, create_composite

        initialize_gee()

        logger.info(
            "Extracting %d training samples from bbox: %s",
            num_samples, bbox,
        )

        aoi = ee.Geometry.Rectangle(bbox)

        # 1. Get Sentinel-2 composite
        collection = get_sentinel2_collection(bbox, start_date, end_date)
        composite = create_composite(collection, bbox)

        # 2. Compute indices
        ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = composite.normalizedDifference(["B3", "B8"]).rename("NDWI")
        evi = composite.expression(
            "2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))",
            {
                "NIR": composite.select("B8"),
                "RED": composite.select("B4"),
                "BLUE": composite.select("B2"),
            },
        ).rename("EVI")
        savi = composite.expression(
            "((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
            {
                "NIR": composite.select("B8"),
                "RED": composite.select("B4"),
            },
        ).rename("SAVI")

        # 3. Stack all features
        features = composite.select(
            ["B2", "B3", "B4", "B8", "B11", "B12"]
        ).addBands([ndvi, evi, savi, ndwi])

        # 4. Load ESA WorldCover for labels
        worldcover = ee.ImageCollection("ESA/WorldCover/v200").first().clip(aoi)
        labeled = features.addBands(worldcover.rename("label"))

        # 5. Sample points
        sample = labeled.stratifiedSample(
            numPoints=num_samples,
            classBand="label",
            region=aoi,
            scale=scale,
            seed=42,
            geometries=False,
        )

        # 6. Extract to arrays
        data = sample.getInfo()
        band_names = ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "EVI", "SAVI", "NDWI"]

        X = []
        y = []
        for feat in data["features"]:
            props = feat["properties"]
            row = [props.get(b, 0) for b in band_names]
            label = props.get("label", -1)
            if label >= 0:
                X.append(row)
                y.append(label)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int32)

        logger.info("Extracted %d samples with %d features", len(X), len(band_names))

        # Save to disk
        save_training_data(X, y, band_names)

        return X, y

    except Exception as exc:
        logger.error("Feature extraction failed: %s", exc)
        logger.info("Generating synthetic training data for demo")
        return generate_synthetic_data(num_samples)


def generate_synthetic_data(
    num_samples: int = 5000,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for demo/testing purposes.

    Creates realistic spectral signatures for 8 land cover classes.
    """
    np.random.seed(42)

    # Class spectral profiles (B2, B3, B4, B8, B11, B12, NDVI, EVI, SAVI, NDWI)
    profiles = {
        0: {"mean": [0.05, 0.06, 0.04, 0.02, 0.01, 0.01, -0.3, -0.2, -0.2, 0.5], "std": 0.01},   # Water
        1: {"mean": [0.12, 0.11, 0.13, 0.15, 0.18, 0.16, 0.07, 0.05, 0.06, -0.1], "std": 0.02},   # Urban
        2: {"mean": [0.15, 0.14, 0.16, 0.18, 0.25, 0.22, 0.06, 0.04, 0.05, -0.1], "std": 0.03},   # Bare Soil
        3: {"mean": [0.05, 0.08, 0.06, 0.25, 0.12, 0.08, 0.61, 0.45, 0.50, -0.5], "std": 0.04},   # Grassland
        4: {"mean": [0.04, 0.07, 0.05, 0.30, 0.10, 0.07, 0.71, 0.55, 0.58, -0.6], "std": 0.03},   # Cropland
        5: {"mean": [0.03, 0.05, 0.04, 0.28, 0.09, 0.06, 0.75, 0.58, 0.62, -0.6], "std": 0.03},   # Shrubland
        6: {"mean": [0.02, 0.04, 0.03, 0.32, 0.08, 0.05, 0.83, 0.65, 0.70, -0.7], "std": 0.02},   # Sparse Forest
        7: {"mean": [0.01, 0.03, 0.02, 0.38, 0.06, 0.04, 0.90, 0.75, 0.80, -0.8], "std": 0.02},   # Dense Forest
    }

    X_list = []
    y_list = []

    samples_per_class = num_samples // len(profiles)

    for class_id, profile in profiles.items():
        mean = np.array(profile["mean"])
        X_class = np.random.normal(mean, profile["std"], (samples_per_class, len(mean)))
        X_list.append(X_class)
        y_list.extend([class_id] * samples_per_class)

    X = np.vstack(X_list).astype(np.float32)
    y = np.array(y_list, dtype=np.int32)

    # Shuffle
    idx = np.random.permutation(len(X))
    X = X[idx]
    y = y[idx]

    logger.info("Generated %d synthetic training samples", len(X))
    save_training_data(X, y)

    return X, y


def save_training_data(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str] = None,
) -> None:
    """Save training data to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    np.save(DATA_DIR / "X_train.npy", X)
    np.save(DATA_DIR / "y_train.npy", y)

    if feature_names:
        with open(DATA_DIR / "feature_names.json", "w") as f:
            json.dump(feature_names, f)

    logger.info("Training data saved to %s", DATA_DIR)


def load_training_data() -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Load training data from disk."""
    x_path = DATA_DIR / "X_train.npy"
    y_path = DATA_DIR / "y_train.npy"

    if x_path.exists() and y_path.exists():
        X = np.load(x_path)
        y = np.load(y_path)
        logger.info("Loaded training data: %d samples, %d features", len(X), X.shape[1])
        return X, y

    logger.warning("No training data found at %s", DATA_DIR)
    return None, None
