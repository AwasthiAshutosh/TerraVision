from .ndvi import router as ndvi_router
from .density import router as density_router
from .change_detection import router as change_detection_router
from .ml_prediction import router as ml_prediction_router

__all__ = [
    "ndvi_router",
    "density_router",
    "change_detection_router",
    "ml_prediction_router",
]
