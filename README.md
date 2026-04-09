# 🌳 Forest observation and analysis system

A satellite-powered forest analysis platform that uses **Sentinel-2 imagery** and **Google Earth Engine** to compute vegetation indices, classify forest canopy density, and detect temporal changes.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red.svg)
![GEE](https://img.shields.io/badge/Google_Earth_Engine-Enabled-orange.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Usage](#usage)
- [API Reference](#api-reference)

- [Algorithmic Details](#algorithmic-details)
- [Testing](#testing)
- [Deployment](#deployment)

---

## 🔭 Overview

This system functions as a simplified version of **Global Forest Watch**, providing:

1. **NDVI Analysis** — Compute Normalized Difference Vegetation Index from Sentinel-2 imagery
2. **Forest Density Classification** — Classify pixels into 5 canopy density categories
3. **Change Detection** — Detect deforestation, degradation, and regrowth between time periods
4. **Interactive Dashboard** — Streamlit-based UI with interactive maps, charts, and downloads
5. **Input-Responsive Fallback** — Mathematically generates unique, location-mapped data when Earth Engine is offline.
6. **Graceful Error Handling** — Distinguishes between internal failures and satellite data unavailability with descriptive UI warnings.

---

## 🏗️ Architecture

```
┌─────────────────┐     HTTP/JSON     ┌──────────────────┐
│                 │ ◄───────────────► │                  │
│  Streamlit UI   │                   │  FastAPI Backend │
│  (Port 8501)    │                   │  (Port 8000)     │
│                 │                   │                  │
│  • Folium Maps  │                   │  • Routes        │
│  • Plotly Charts│                   │  • Services      │
│                 │                   │                  │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                               │ Earth Engine API
                                               │
                                      ┌────────▼─────────┐
                                      │  Google Earth    │
                                      │  Engine          │
                                      │                  │
                                      │  • Sentinel-2 L2A│
                                      │  • ESA WorldCover│
                                      └──────────────────┘
```

---

## ⚡ Setup

### Prerequisites

- Python 3.10+
- Google Cloud project with Earth Engine API enabled
- GEE authentication completed (`ee.Authenticate()`)

### Installation

```bash
# 1. Navigate to the project
cd forest-monitoring-system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Edit .env with your GEE project ID (already set if cloned)
```

### GEE Authentication (one-time)

```python
import ee
ee.Authenticate()
```

---

## 🚀 Usage

### Quick Start (Both Servers)

```bash
python run.py
```

This starts:
- **Backend** at http://127.0.0.1:8000 (API docs at `/docs`)
- **Frontend** at http://127.0.0.1:8501

### Individual Servers

```bash
# Backend only
python run.py --backend

# Frontend only
python run.py --frontend

```

### Using the Dashboard

1. Open http://127.0.0.1:8501 in your browser
2. Select an **Analysis Mode** from the sidebar (NDVI, Density, Change Detection)
3. Choose an **Area of Interest** (preset or custom coordinates)
4. Set the **date range** for analysis
5. Adjust **resolution** as needed
6. Click **🚀 Run Analysis**
7. View results on the interactive map and charts
8. **Download** results as JSON

### ⚠️ Important Considerations & Trade-offs

When working with satellite imagery through Google Earth Engine (GEE), users must carefully balance three primary factors: **Time Range**, **Area of Interest (Land Size)**, and **Spatial Resolution**. 

Because GEE imposes strict computational limits (e.g., timeouts, payload constraints, and memory usage limits per request), maximizing one of these factors typically requires reducing another.

- **Time Range (Temporal Depth):** Calculating indices over long time periods (e.g., several years) requires aggregating massive stacks of imagery. While vital for detecting long-term deforestation trends, extensive date ranges significantly increment processing duration.
- **Area of Interest (Spatial Extent):** Analyzing expansive geographical polygons (e.g., an entire state or country) dramatically inflates the number of pixels processed. Exceptionally large boundaries often trigger Earth Engine timeout errors unless the resolution scale is adjusted.
- **Spatial Resolution (Scale/Distance):** High resolution (e.g., 10m/pixel for Sentinel-2) provides granular, unparalleled detail but is extremely resource-intensive. Lowering the resolution (e.g., setting the scale to 100m or 500m per pixel) sacrifices micro-level visual clarity but is strictly necessary for processing large land masses rapidly.

**Best Practices for Maintaining Optimization:**
1. **Local, High-Detail Analysis:** For tightly bounded regions (e.g., a specific local forest block or neighborhood), you can utilize a granular scale (10m - 30m) across a moderate time range.
2. **Regional, Trend-Based Analysis:** For analyzing massive geographic regions or country-wide statistics, you **must** increase the scale distance (e.g., 100m - 500m per pixel) and restrict the temporal depth. By maintaining this trade-off, you ensure backend endpoints remain responsive and avoid GEE allocation overages.
3. **Iterative Exploration:** We recommend starting with a smaller time range and a higher scale distance to quickly validate data availability, subsequently refining parameters as needed.

---

## 📡 API Reference

### Base URL: `http://127.0.0.1:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed status with GEE info |
| `/api/status` | GET | System status and available endpoints |
| `/api/ndvi/` | POST | Compute NDVI |
| `/api/density/` | POST | Classify forest density |
| `/api/density/thresholds` | GET | Get default thresholds |
| `/api/change-detection/` | POST | Detect temporal changes |

### Example: NDVI Request

```bash
curl -X POST http://127.0.0.1:8000/api/ndvi/ \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": [-60.0, -3.0, -59.0, -2.0],
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "scale": 100
  }'
```

### Interactive Docs

Visit http://127.0.0.1:8000/docs for the auto-generated Swagger UI.

---


## 🧮 Algorithmic Details

### NDVI Formula
```
NDVI = (NIR - Red) / (NIR + Red)
     = (B8 - B4) / (B8 + B4)
```

| NDVI Range | Interpretation |
|-----------|----------------|
| > 0.7 | Dense healthy vegetation |
| 0.5 – 0.7 | Moderate vegetation |
| 0.3 – 0.5 | Sparse vegetation |
| 0.1 – 0.3 | Minimal vegetation |
| < 0.1 | Non-vegetated |

### Cloud Masking

Uses Sentinel-2 **Scene Classification Layer (SCL)** band:
- **Keep:** Vegetation (4), Bare Soil (5), Water (6), Low Cloud Prob (7)
- **Mask:** Cloud Shadow (3), Medium/High Cloud (8,9,10), Snow (11)

### Change Detection

```
ΔNDVI = NDVI_period2 - NDVI_period1

If ΔNDVI < -0.2  → Forest Loss
If ΔNDVI > +0.2  → Forest Gain
Otherwise         → Stable
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ndvi.py -v
pytest tests/test_api.py -v
pytest tests/test_integration.py -v
```

---

## 🚢 Deployment

### Backend (Render/GCP)

```bash
# Build
pip install -r requirements.txt

# Run
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

### Frontend (Streamlit Cloud)

1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set `frontend/streamlit_app.py` as main file
4. Add environment variables in Streamlit Cloud settings

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEE_PROJECT_ID` | GCP project with GEE API | Required |
| `BACKEND_HOST` | Backend host | 127.0.0.1 |
| `BACKEND_PORT` | Backend port | 8000 |
| `API_BASE_URL` | Override backend URL for the frontend | `http://{BACKEND_HOST}:{BACKEND_PORT}` |
| `DEMO_MODE` | Use synthetic data | false |
| `LOG_LEVEL` | Logging level | INFO |

---

## 📁 Project Structure

```
forest-monitoring-system/
├── backend/
│   ├── app.py                 # FastAPI entry point
│   ├── config/settings.py     # Environment configuration
│   ├── routes/                # API endpoints
│   ├── services/              # Business logic
│   ├── gee/                   # Earth Engine integration
│   └── utils/                 # Logging, validation, export
├── frontend/
│   ├── streamlit_app.py       # Streamlit dashboard
│   ├── components/            # UI components
│   └── utils/                 # API client, styling

├── tests/                     # Unit & integration tests
├── requirements.txt
├── run.py                     # Launcher script
└── README.md
```

---

## 📄 License

MIT License — see LICENSE for details.

---

Built with ❤️ using Google Earth Engine, FastAPI, and Streamlit.
