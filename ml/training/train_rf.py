"""
Random Forest Classifier Training

Trains a scikit-learn Random Forest classifier for forest type
classification using spectral features from Sentinel-2 imagery.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix

from ml.training.prepare_data import load_training_data, generate_synthetic_data
from ml.evaluation.metrics import calculate_all_metrics
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "random_forest_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"
REPORT_PATH = MODEL_DIR / "training_report.json"

# Class names mapping
CLASS_NAMES = [
    "Water", "Urban", "Bare Soil", "Grassland",
    "Cropland", "Shrubland", "Sparse Forest", "Dense Forest",
]


def train_random_forest(
    n_estimators: int = 200,
    max_depth: int = 20,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train a Random Forest classifier for forest type classification.

    Steps:
        1. Load or generate training data
        2. Split into train/test sets (stratified)
        3. Standardize features (optional but helpful)
        4. Train Random Forest with tuned hyperparameters
        5. Evaluate on test set
        6. Save model and report

    Args:
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
        test_size: Fraction of data for testing (0-1).
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary with training report (accuracy, per-class metrics).
    """
    logger.info("=" * 50)
    logger.info("Training Random Forest Classifier")
    logger.info("=" * 50)

    # 1. Load data
    X, y = load_training_data()
    if X is None:
        logger.info("No saved data found — generating synthetic training data")
        X, y = generate_synthetic_data(num_samples=5000)

    logger.info("Dataset: %d samples, %d features, %d classes",
                len(X), X.shape[1], len(np.unique(y)))

    # 2. Map labels to sequential 0-N
    unique_labels = sorted(np.unique(y))
    label_map = {old: new for new, old in enumerate(unique_labels)}
    y_mapped = np.array([label_map[label] for label in y])

    # Determine class names for mapped labels
    active_classes = [CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"Class_{i}"
                      for i in unique_labels]

    # 3. Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_mapped,
        test_size=test_size,
        random_state=random_state,
        stratify=y_mapped,
    )
    logger.info("Train: %d samples, Test: %d samples", len(X_train), len(X_test))

    # 4. Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Train model
    logger.info(
        "Training with n_estimators=%d, max_depth=%d",
        n_estimators, max_depth,
    )

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
        verbose=0,
    )

    model.fit(X_train_scaled, y_train)

    # 6. Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = model.score(X_test_scaled, y_test)

    # Cross-validation
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring="accuracy")

    # Classification report
    report = classification_report(
        y_test, y_pred,
        target_names=active_classes,
        output_dict=True,
    )

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)

    # Feature importance
    feature_names = ["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "EVI", "SAVI", "NDWI"]
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    feature_ranking = {
        feature_names[i] if i < len(feature_names) else f"feat_{i}": round(float(importances[i]), 4)
        for i in sorted_idx
    }

    # Calculate additional metrics
    additional_metrics = calculate_all_metrics(y_test, y_pred, active_classes)

    logger.info("=" * 50)
    logger.info("Test Accuracy: %.4f", accuracy)
    logger.info("CV Accuracy: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())
    logger.info("=" * 50)

    # 7. Save model and scaler
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    logger.info("Model saved to %s", MODEL_PATH)

    # 8. Save report
    training_report = {
        "model_type": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "max_features": "sqrt",
            "class_weight": "balanced",
        },
        "dataset": {
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_features": X.shape[1],
            "num_classes": len(active_classes),
            "class_names": active_classes,
        },
        "performance": {
            "test_accuracy": round(accuracy, 4),
            "cv_accuracy_mean": round(float(cv_scores.mean()), 4),
            "cv_accuracy_std": round(float(cv_scores.std()), 4),
            "per_class_report": {
                k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()}
                for k, v in report.items() if k not in ["accuracy"]
            },
        },
        "feature_importance": feature_ranking,
        "additional_metrics": additional_metrics,
    }

    with open(REPORT_PATH, "w") as f:
        json.dump(training_report, f, indent=2, default=str)

    logger.info("Training report saved to %s", REPORT_PATH)

    return training_report


if __name__ == "__main__":
    report = train_random_forest()
    print(f"\n✓ Training complete! Accuracy: {report['performance']['test_accuracy']:.4f}")
