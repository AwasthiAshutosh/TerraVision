"""
Model Evaluation Metrics

Provides comprehensive metrics for evaluating classification models:
- Accuracy, Precision, Recall, F1 Score
- Intersection over Union (IoU) per class
- Cohen's Kappa
- Confusion matrix analysis
"""

import numpy as np
from typing import Any, Dict, List, Optional
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    cohen_kappa_score,
    confusion_matrix,
)

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_iou(y_true: np.ndarray, y_pred: np.ndarray, class_labels: List[str]) -> Dict[str, float]:
    """
    Calculate Intersection over Union (IoU) for each class.

    IoU = TP / (TP + FP + FN)

    This is the standard metric for segmentation tasks and provides
    a stricter evaluation than accuracy alone.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        class_labels: List of class names.

    Returns:
        Dictionary mapping class names to IoU scores.
    """
    cm = confusion_matrix(y_true, y_pred)
    iou_scores = {}

    for i, label in enumerate(class_labels):
        if i < len(cm):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            denominator = tp + fp + fn

            if denominator > 0:
                iou = tp / denominator
            else:
                iou = 0.0

            iou_scores[label] = round(float(iou), 4)

    # Mean IoU
    iou_values = list(iou_scores.values())
    iou_scores["mean_iou"] = round(float(np.mean(iou_values)), 4) if iou_values else 0.0

    return iou_scores


def calculate_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_labels: List[str],
) -> Dict[str, Any]:
    """
    Calculate all evaluation metrics.

    Includes:
        - Overall Accuracy
        - Weighted Precision, Recall, F1
        - Per-class IoU
        - Mean IoU (mIoU)
        - Cohen's Kappa coefficient

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        class_labels: List of class names.

    Returns:
        Comprehensive metrics dictionary.
    """
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_weighted": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "recall_weighted": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "cohens_kappa": round(float(cohen_kappa_score(y_true, y_pred)), 4),
        "iou": calculate_iou(y_true, y_pred, class_labels),
    }

    logger.info(
        "Evaluation — Accuracy: %.4f, F1: %.4f, mIoU: %.4f, Kappa: %.4f",
        metrics["accuracy"],
        metrics["f1_weighted"],
        metrics["iou"]["mean_iou"],
        metrics["cohens_kappa"],
    )

    return metrics
