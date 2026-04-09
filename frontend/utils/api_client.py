"""
API Client Utility

HTTP client for communicating with the FastAPI backend from
the Streamlit frontend. Uses requests for synchronous API calls.
"""

import requests
from typing import Any, Dict, Optional

BASE_URL = "https://terravision-cyyu.onrender.com"


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
            try:
                error_detail = exc.response.json().get("detail", str(exc))
            except Exception:
                error_detail = str(exc)
            raise Exception(f"🚨 API Error: {error_detail}")

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
