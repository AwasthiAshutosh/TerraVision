"""
API Client Utility

HTTP client for communicating with the FastAPI backend from
the Streamlit frontend. Uses requests for synchronous API calls.
"""

import requests
from typing import Any, Dict, Optional

import os
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# Use local backend by default, matching .env config
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BASE_URL = os.getenv("API_BASE_URL", f"http://{BACKEND_HOST}:{BACKEND_PORT}")


class NoDataAvailableError(Exception):
    """Raised when the backend reports no satellite data is available."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


def call_api(
    endpoint: str,
    method: str = "POST",
    data: Optional[Dict] = None,
    timeout: int = 60,   # increased timeout
) -> Dict[str, Any]:

    url = f"{BASE_URL}{endpoint}"
    response = None

    for attempt in range(2):  # retry once (important for Render)
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            if attempt == 0:
                continue  # retry once
            raise Exception("⏳ Backend timeout (Render may be waking up). Try again.")

        except requests.ConnectionError:
            raise ConnectionError(
                f"❌ Cannot connect to backend at {BASE_URL}"
            )

        except requests.HTTPError as exc:
            # Parse the error response to distinguish data unavailability
            try:
                error_body = exc.response.json()
                detail = error_body.get("detail", str(exc))
            except Exception:
                detail = str(exc)
                raise Exception(f"🚨 API Error: {detail}")

            # Check if this is a "no data available" error (HTTP 404 with specific type)
            if exc.response.status_code == 404 and isinstance(detail, dict):
                error_type = detail.get("error_type", "")
                if error_type == "no_data_available":
                    raise NoDataAvailableError(
                        message=detail.get("message", "No satellite data available for this request."),
                        details=detail.get("details", {}),
                    )

            # All other HTTP errors are system/validation errors
            error_msg = detail if isinstance(detail, str) else detail.get("message", str(detail))
            raise Exception(f"🚨 API Error: {error_msg}")

        except ValueError:
            # JSON decode error
            resp_text = response.text if response is not None else "(no response)"
            raise Exception(f"🚨 Invalid JSON response: {resp_text}")


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
    try:
        result = call_api("/health", method="GET", timeout=5)
        return True, result
    except Exception as exc:
        return False, str(exc)
