"""
Forest observation and analysis system — Streamlit Dashboard

Main entry point for the interactive frontend. Provides:
- Interactive map visualization with satellite imagery overlays
- NDVI analysis with gauge charts and statistics
- Forest density classification with donut/bar charts
- Change detection with temporal comparison
"""

import sys
from pathlib import Path

import streamlit as st
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Add project root to path for imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Streamlit Page Configuration (must be first st command)
# ---------------------------------------------------------------------------
from frontend.utils.styles import get_page_icon, get_logo_html

st.set_page_config(
    page_title="TerraVision",
    page_icon=get_page_icon(),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/forest-monitoring-system",
        "About": (
            "Forest observation and analysis system v1.0\n\n"
            "Analyzes Sentinel-2 satellite imagery to monitor forest health, "
            "density, and temporal changes using NDVI and machine learning."
        ),
    },
)

# ---------------------------------------------------------------------------
# Imports (after sys.path fix)
# ---------------------------------------------------------------------------
from frontend.utils.styles import get_custom_css, render_header
from frontend.utils.api_client import (
    get_ndvi,
    get_density,
    get_change_detection,
    check_backend_health,
    NoDataAvailableError,
)
from frontend.components.sidebar import render_sidebar
from frontend.components.map_view import (
    create_base_map,
    add_ndvi_layer,
    add_density_layer,
    add_change_layer,
    finalize_map,
    add_legend,
    get_ndvi_legend_html,
)
from frontend.components.charts import (
    create_ndvi_gauge,
    create_density_donut,
    create_density_bar,
    create_change_chart,
    create_ndvi_comparison,
)
from frontend.components.statistics import (
    render_ndvi_stats,
    render_density_stats,
    render_change_stats,
)

# ---------------------------------------------------------------------------
# Apply custom CSS
# ---------------------------------------------------------------------------
st.markdown(get_custom_css(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers for input-responsive demo data
# ---------------------------------------------------------------------------
def _bbox_seed(bbox, extra=""):
    """Derive a deterministic seed from bbox + optional extra string."""
    import hashlib
    raw = f"{bbox}{extra}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _estimate_area_hectares(bbox):
    """Approximate area of a bbox in hectares."""
    import math
    west, south, east, north = bbox
    mid_lat = math.radians((south + north) / 2)
    width_km = abs(east - west) * 111.32 * math.cos(mid_lat)
    height_km = abs(north - south) * 110.574
    return round(width_km * height_km * 100, 2)


# ---------------------------------------------------------------------------
# Check backend health
# ---------------------------------------------------------------------------
def check_backend():
    """Safe backend check (prevents Streamlit crash)."""
    try:
        healthy, info = check_backend_health()
        return healthy, info
    except Exception:
        return False, {}


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    """Main application entry point."""

    # Check backend status
    backend_ok, backend_info = check_backend()
    demo_mode = not backend_ok

    # Render header
    st.markdown(render_header(demo_mode), unsafe_allow_html=True)

    # Backend status warning
    if not backend_ok:
        st.warning(
            "⚠️ **Backend is not running.** Start it with: "
            "`python run.py` or `uvicorn backend.app:app --reload`\n\n"
            "The dashboard will show placeholder content until the backend is available.",
            icon="🔌",
        )

    # Render sidebar and get parameters
    params = render_sidebar()

    # Use session_state active_mode to determine what analysis to show
    analysis_active = st.session_state.get("analysis_active", False)

    # Main content area
    if analysis_active:
        # Use the stored active_mode so switching the dropdown works immediately
        active_mode = st.session_state.get("active_mode", params["analysis_mode"])
        params["analysis_mode"] = active_mode
        _run_analysis(params, backend_ok)
    else:
        _show_welcome(params, demo_mode)


def _show_welcome(params: dict, demo_mode: bool):
    """Show the welcome/landing state with a base map."""

    # Default map
    bbox = params["bbox"]
    center = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]

    col_map, col_info = st.columns([2, 1])

    with col_map:
        st.markdown("### 🗺️ Selected Area of Interest")
        m = create_base_map(center=center, zoom=10)

        # Add AOI rectangle
        import folium
        folium.Rectangle(
            bounds=[[bbox[1], bbox[0]], [bbox[3], bbox[2]]],
            color="#00e676",
            weight=2,
            fill=True,
            fill_color="#00e676",
            fill_opacity=0.1,
            popup=f"AOI: {params['aoi_name']}",
            tooltip="Click Run Analysis to begin",
        ).add_to(m)

        m = finalize_map(m)
        st_folium(m, width=None, height=500, key="welcome_map")

    with col_info:
        st.markdown("### 🚀 Getting Started")

        st.markdown(f"""
        <div class="analysis-panel">
            <div class="panel-title">📍 Current AOI</div>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">
                <strong>{params['aoi_name']}</strong><br>
                Bounds: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="analysis-panel">
            <div class="panel-title">📊 Available Analyses</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 0.85rem; line-height: 1.8;">
                🌿 <strong>NDVI Analysis</strong> — Vegetation health index<br>
                🌲 <strong>Forest Density</strong> — Canopy cover classification<br>
                📈 <strong>Change Detection</strong> — Temporal forest changes
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.info("👈 Configure parameters in the sidebar and click **Run Analysis** to begin.")

        if demo_mode:
            st.warning(
                "Running in **Demo Mode** with synthetic data. "
                "Connect GEE for real satellite analysis."
            )


def _run_analysis(params: dict, backend_ok: bool):
    """Execute the selected analysis and render results."""

    mode = params["analysis_mode"]
    bbox = params["bbox"]
    center = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]

    if mode == "NDVI Analysis":
        _run_ndvi(params, bbox, center, backend_ok)
    elif mode == "Forest Density":
        _run_density(params, bbox, center, backend_ok)
    elif mode == "Change Detection":
        _run_change_detection(params, bbox, center, backend_ok)


def _run_ndvi(params, bbox, center, backend_ok):
    """Run NDVI analysis and display results."""
    # Use cached result if available and mode hasn't switched
    cache_key = "cached_ndvi_result"
    cached = st.session_state.get(cache_key)

    if cached and not params.get("run_analysis"):
        data = cached
    else:
        with st.spinner("🛰️ Computing NDVI from Sentinel-2 imagery..."):
            try:
                if backend_ok:
                    response = get_ndvi(
                        bbox=bbox,
                        start_date=params["start_date"],
                        end_date=params["end_date"],
                        scale=params["scale"],
                    )
                    data = response.get("data") or response
                else:
                    data = _get_demo_ndvi_data(params)
            except NoDataAvailableError as e:
                st.warning(
                    f"📡 **No Satellite Data Available**\n\n{str(e)}\n\n"
                    "Try adjusting the date range or selecting a different region.",
                    icon="🛰️",
                )
                return
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_ndvi_data(params)
        st.session_state[cache_key] = data

    # Display results
    st.markdown("## 🌿 NDVI Analysis Results")

    # Statistics row
    render_ndvi_stats(data)

    # Map and charts
    col_map, col_charts = st.columns([3, 2])

    with col_map:
        st.markdown("### 🗺️ NDVI Map")
        m = create_base_map(center=center, zoom=11)

        tile_url = data.get("tile_url")
        demo_grid = data.get("demo_grid")
        m = add_ndvi_layer(m, tile_url=tile_url, demo_grid=demo_grid, bbox=bbox)
        m = add_legend(m, get_ndvi_legend_html())
        m = finalize_map(m)

        st_folium(m, width=None, height=500, key="ndvi_map")

    with col_charts:
        st.markdown("### 📊 NDVI Gauge")
        mean_ndvi = data.get("stats", {}).get("mean", 0)
        fig = create_ndvi_gauge(mean_ndvi)
        st.plotly_chart(fig, use_container_width=True)

        # Download button
        import json
        st.download_button(
            label="📥 Download Results (JSON)",
            data=json.dumps(data, indent=2, default=str),
            file_name="ndvi_analysis.json",
            mime="application/json",
        )


def _run_density(params, bbox, center, backend_ok):
    """Run forest density classification and display results."""
    cache_key = "cached_density_result"
    cached = st.session_state.get(cache_key)

    if cached and not params.get("run_analysis"):
        data = cached
    else:
        with st.spinner("🌲 Classifying forest density..."):
            try:
                if backend_ok:
                    response = get_density(
                        bbox=bbox,
                        start_date=params["start_date"],
                        end_date=params["end_date"],
                        scale=params["scale"],
                    )
                    data = response.get("data") or response
                else:
                    data = _get_demo_density_data(params)
            except NoDataAvailableError as e:
                st.warning(
                    f"📡 **No Satellite Data Available**\n\n{str(e)}\n\n"
                    "Try adjusting the date range or selecting a different region.",
                    icon="🛰️",
                )
                return
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_density_data(params)
        st.session_state[cache_key] = data

    st.markdown("## 🌲 Forest Density Classification")

    # Statistics
    render_density_stats(data)

    # Map and charts
    col_map, col_charts = st.columns([3, 2])

    with col_map:
        st.markdown("### 🗺️ Density Map")
        m = create_base_map(center=center, zoom=11)

        tile_url = data.get("tile_url")
        m = add_density_layer(m, tile_url=tile_url, categories=data.get("categories"), bbox=bbox)
        m = finalize_map(m)

        st_folium(m, width=None, height=500, key="density_map")

    with col_charts:
        categories = data.get("categories", {})

        tab1, tab2 = st.tabs(["🍩 Distribution", "📊 Area Breakdown"])

        with tab1:
            fig = create_density_donut(categories)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = create_density_bar(categories)
            st.plotly_chart(fig, use_container_width=True)

        import json
        st.download_button(
            label="📥 Download Results (JSON)",
            data=json.dumps(data, indent=2, default=str),
            file_name="density_classification.json",
            mime="application/json",
        )


def _run_change_detection(params, bbox, center, backend_ok):
    """Run change detection and display results."""
    cache_key = "cached_change_result"
    cached = st.session_state.get(cache_key)

    if cached and not params.get("run_analysis"):
        data = cached
    else:
        with st.spinner("📈 Detecting forest changes..."):
            try:
                if backend_ok:
                    response = get_change_detection(
                        bbox=bbox,
                        p1_start=params["period1_start"],
                        p1_end=params["period1_end"],
                        p2_start=params["period2_start"],
                        p2_end=params["period2_end"],
                        scale=params["scale"],
                        threshold=params["change_threshold"],
                    )
                    data = response.get("data") or response
                else:
                    data = _get_demo_change_data(params)
            except NoDataAvailableError as e:
                st.warning(
                    f"📡 **No Satellite Data Available**\n\n{str(e)}\n\n"
                    "Try adjusting the date ranges or selecting a different region.",
                    icon="🛰️",
                )
                return
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_change_data(params)
        st.session_state[cache_key] = data

    st.markdown("## 📈 Change Detection Results")

    # Statistics
    render_change_stats(data)

    # Map and charts
    col_map, col_charts = st.columns([3, 2])

    with col_map:
        st.markdown("### 🗺️ Change Map")
        m = create_base_map(center=center, zoom=11)

        change_tile = data.get("change_tile_url")
        diff_tile = data.get("diff_tile_url")
        m = add_change_layer(m, change_tile_url=change_tile, diff_tile_url=diff_tile, bbox=bbox)
        m = finalize_map(m)

        st_folium(m, width=None, height=500, key="change_map")

    with col_charts:
        tab1, tab2 = st.tabs(["📊 Change Areas", "📉 NDVI Comparison"])

        with tab1:
            fig = create_change_chart(data.get("changes", {}))
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = create_ndvi_comparison(
                data.get("period1_mean_ndvi", 0),
                data.get("period2_mean_ndvi", 0),
            )
            st.plotly_chart(fig, use_container_width=True)

        import json
        st.download_button(
            label="📥 Download Results (JSON)",
            data=json.dumps(data, indent=2, default=str),
            file_name="change_detection.json",
            mime="application/json",
        )




# ---------------------------------------------------------------------------
# Demo Data Fallbacks (when backend is offline)
# These are input-responsive: different bbox/dates → different results
# ---------------------------------------------------------------------------
def _get_demo_ndvi_data(params):
    """Generate input-responsive demo NDVI data."""
    import numpy as np

    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('start_date','')}{params.get('end_date','')}")
    rng = np.random.RandomState(seed)

    # Derive NDVI from latitude (tropical → higher)
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    base_ndvi = max(0.2, min(0.85, 0.80 - mid_lat * 0.008))
    mean_ndvi = base_ndvi + rng.uniform(-0.08, 0.08)

    # Generate spatially-varied grid
    grid_size = 30
    freq_x = 0.3 + rng.uniform(0, 0.5)
    freq_y = 0.2 + rng.uniform(0, 0.4)
    x = np.linspace(0, 4 * np.pi, grid_size)
    y = np.linspace(0, 4 * np.pi, grid_size)
    xx, yy = np.meshgrid(x, y)
    base = base_ndvi + 0.15 * np.sin(xx * freq_x) * np.cos(yy * freq_y)
    noise = rng.normal(0, 0.05, (grid_size, grid_size))
    cx1, cy1 = rng.uniform(2, 10), rng.uniform(2, 10)
    clearing = np.exp(-((xx - cx1) ** 2 + (yy - cy1) ** 2) / rng.uniform(2, 6)) * rng.uniform(0.2, 0.5)
    demo_grid = np.clip(base + noise - clearing, -0.2, 0.95)

    return {
        "tile_url": None,
        "demo_mode": True,
        "stats": {
            "mean": round(mean_ndvi, 4),
            "min": round(mean_ndvi - rng.uniform(0.30, 0.50), 4),
            "max": round(min(mean_ndvi + rng.uniform(0.10, 0.22), 0.95), 4),
            "std_dev": round(rng.uniform(0.10, 0.20), 4),
        },
        "interpretation": {
            "category": (
                "Dense Healthy Vegetation" if mean_ndvi > 0.7 else
                "Moderate Vegetation" if mean_ndvi > 0.5 else
                "Sparse Vegetation" if mean_ndvi > 0.3 else
                "Minimal Vegetation"
            ),
            "description": (
                "High vegetation density indicative of healthy forest."
                if mean_ndvi > 0.7 else
                "Moderate vegetation cover with mixed land use."
                if mean_ndvi > 0.5 else
                "Sparse vegetation cover, possible degradation."
                if mean_ndvi > 0.3 else
                "Low vegetation signal, bare or cleared land."
            ),
            "health": (
                "excellent" if mean_ndvi > 0.7 else
                "good" if mean_ndvi > 0.5 else
                "moderate" if mean_ndvi > 0.3 else
                "poor"
            ),
        },
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "date_range": f"{params.get('start_date', 'N/A')} to {params.get('end_date', 'N/A')}",
            "images_used": 0,
            "scale_meters": params.get("scale", 100),
        },
        "demo_grid": demo_grid.tolist(),
    }


def _get_demo_density_data(params):
    """Generate input-responsive demo density data."""
    import numpy as np

    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('start_date','')}{params.get('end_date','')}")
    rng = np.random.RandomState(seed)

    total_ha = _estimate_area_hectares(bbox)
    if total_ha < 100:
        total_ha = 11000.0

    # Vary distribution by latitude
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    dense_pct = max(10, min(65, 60 - mid_lat * 0.6 + rng.uniform(-5, 5)))
    moderate_pct = max(8, min(30, 22 + rng.uniform(-5, 5)))
    sparse_pct = max(5, min(20, 10 + mid_lat * 0.15 + rng.uniform(-3, 3)))
    grassland_pct = max(2, min(15, 5 + mid_lat * 0.1 + rng.uniform(-2, 2)))
    non_veg_pct = max(1, 100 - dense_pct - moderate_pct - sparse_pct - grassland_pct)

    pcts = [dense_pct, moderate_pct, sparse_pct, grassland_pct, non_veg_pct]
    pct_sum = sum(pcts)
    pcts = [round(p / pct_sum * 100, 1) for p in pcts]

    cat_defs = [
        ("dense_forest", "Dense Forest", "#0a5e1a", "0.7 – 1.0"),
        ("moderate_forest", "Moderate Forest", "#4caf50", "0.5 – 0.7"),
        ("sparse_vegetation", "Sparse Vegetation", "#cddc39", "0.3 – 0.5"),
        ("grassland_crops", "Grassland/Crops", "#ffeb3b", "0.1 – 0.3"),
        ("non_vegetation", "Non-Vegetation", "#d32f2f", "-1.0 – 0.1"),
    ]

    categories = {}
    for (key, label, color, ndvi_range), pct in zip(cat_defs, pcts):
        categories[key] = {
            "label": label,
            "area_hectares": round(total_ha * pct / 100, 2),
            "color": color,
            "ndvi_range": ndvi_range,
            "percentage": pct,
        }

    return {
        "tile_url": None,
        "demo_mode": True,
        "total_area_hectares": round(total_ha, 2),
        "categories": categories,
    }


def _get_demo_change_data(params):
    """Generate input-responsive demo change detection data."""
    import numpy as np

    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('period1_start','')}{params.get('period2_end','')}")
    rng = np.random.RandomState(seed)

    total_ha = _estimate_area_hectares(bbox)
    if total_ha < 100:
        total_ha = 11000.0

    threshold = params.get("change_threshold", 0.2)
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    mid_lon = abs((bbox[0] + bbox[2]) / 2)

    loss_pct = max(1, min(25, 8 + mid_lat * 0.12 + mid_lon * 0.02 - threshold * 15 + rng.uniform(-4, 4)))
    gain_pct = max(0.5, min(15, 3 + mid_lon * 0.01 + rng.uniform(-1.5, 2.5)))
    stable_pct = round(100 - loss_pct - gain_pct, 1)

    loss_ha = round(total_ha * loss_pct / 100, 2)
    gain_ha = round(total_ha * gain_pct / 100, 2)
    stable_ha = round(total_ha * stable_pct / 100, 2)

    base_ndvi = max(0.3, min(0.85, 0.80 - mid_lat * 0.008))
    p1_ndvi = round(base_ndvi + rng.uniform(-0.03, 0.03), 4)
    p2_ndvi = round(p1_ndvi + (gain_ha - loss_ha) / total_ha, 4)

    return {
        "change_tile_url": None,
        "diff_tile_url": None,
        "demo_mode": True,
        "changes": {
            "forest_loss": {"area_hectares": loss_ha, "percentage": round(loss_pct, 1), "color": "#e53935", "label": "Forest Loss"},
            "stable": {"area_hectares": stable_ha, "percentage": round(stable_pct, 1), "color": "#fdd835", "label": "Stable"},
            "forest_gain": {"area_hectares": gain_ha, "percentage": round(gain_pct, 1), "color": "#43a047", "label": "Forest Gain"},
        },
        "total_area_hectares": round(total_ha, 2),
        "net_change_hectares": round(gain_ha - loss_ha, 2),
        "period1_mean_ndvi": p1_ndvi,
        "period2_mean_ndvi": p2_ndvi,
        "metadata": {"satellite": "Sentinel-2 L2A (DEMO)"},
    }



# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
main()

# ---------------------------------------------------------------------------
# Footer (rendered after main content)
# ---------------------------------------------------------------------------
logo_footer = get_logo_html(width="1rem", vertical_align="middle", margin_right="4px")
st.markdown(f"""
<div class="footer">
    {logo_footer} Forest observation and analysis system v1.0 | 
    Powered by Google Earth Engine & Sentinel-2 | 
    Built with FastAPI + Streamlit
</div>
""", unsafe_allow_html=True)
