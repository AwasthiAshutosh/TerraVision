"""
API Client Utility

HTTP client for communicating with the FastAPI backend from
the Streamlit frontend. Uses httpx for async support.
"""

import requests
from typing import Any, Dict, Optional

API_BASE_URL = "http://127.0.0.1:8000"


def call_api(
    endpoint: str,
    method: str = "POST",
    data: Optional[Dict] = None,
    timeout: int = 300,
) -> Dict[str, Any]:
    """
    Call the FastAPI backend.

    Args:
        endpoint: API endpoint path (e.g., "/api/ndvi").
        method: HTTP method ("GET" or "POST").
        data: Request body for POST requests.
        timeout: Request timeout in seconds.

    Returns:
        Response JSON as dictionary.

    Raises:
        ConnectionError: If the backend is not reachable.
        Exception: For other API errors.
    """
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)

        response.raise_for_status()
        return response.json()

    except requests.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to backend at {API_BASE_URL}. "
            "Make sure the FastAPI server is running."
        )
    except requests.HTTPError as exc:
        error_detail = "Unknown error"
        try:
            error_detail = exc.response.json().get("detail", str(exc))
        except Exception:
            error_detail = str(exc)
        raise Exception(f"API Error: {error_detail}")


def get_ndvi(bbox, start_date, end_date, scale=100):
    """Fetch NDVI analysis from the backend."""
    return call_api("/api/ndvi/", data={
        "bbox": bbox,
        "start_date": start_date,
        "end_date": end_date,
        "scale": scale,
    })


def get_density(bbox, start_date, end_date, scale=100, thresholds=None):
    """Fetch forest density classification from the backend."""
    data = {
        "bbox": bbox,
        "start_date": start_date,
        "end_date": end_date,
        "scale": scale,
    }
    if thresholds:
        data["thresholds"] = thresholds
    return call_api("/api/density/", data=data)


def get_change_detection(bbox, p1_start, p1_end, p2_start, p2_end, scale=100, threshold=0.2):
    """Fetch change detection results from the backend."""
    return call_api("/api/change-detection/", data={
        "bbox": bbox,
        "period1_start": p1_start,
        "period1_end": p1_end,
        "period2_start": p2_start,
        "period2_end": p2_end,
        "scale": scale,
        "change_threshold": threshold,
    })





def check_backend_health():
    """Check if the backend is running and healthy."""
    try:
        result = call_api("/health", method="GET", timeout=5)
        return True, result
    except Exception as exc:
        return False, str(exc)
