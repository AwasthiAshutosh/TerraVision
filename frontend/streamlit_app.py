"""
Forest observation and analysis system — Streamlit Dashboard

Main entry point for the interactive frontend. Provides:
- Interactive map visualization with satellite imagery overlays
- NDVI analysis with gauge charts and statistics
- Forest density classification with donut/bar charts
- Change detection with temporal comparison
- ML prediction results with classification breakdown
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
# Check backend health
# ---------------------------------------------------------------------------
def check_backend():
    """Check if the backend API is running."""
    healthy, info = check_backend_health()
    return healthy, info


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    """Main application entry point."""

    # Check backend status
    backend_ok, backend_info = check_backend()
    demo_mode = False

    if backend_ok:
        gee_info = backend_info.get("gee", {})
        demo_mode = gee_info.get("demo_mode", False)
    else:
        demo_mode = True

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
                    data = response.get("data", {})
                else:
                    data = _get_demo_ndvi_data()
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_ndvi_data()
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
                    data = response.get("data", {})
                else:
                    data = _get_demo_density_data()
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_density_data()
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
                    data = response.get("data", {})
                else:
                    data = _get_demo_change_data()
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                data = _get_demo_change_data()
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
# ---------------------------------------------------------------------------
def _get_demo_ndvi_data():
    import numpy as np
    np.random.seed(42)
    return {
        "tile_url": None,
        "demo_mode": True,
        "stats": {"mean": 0.7234, "min": 0.2734, "max": 0.9134, "std_dev": 0.1456},
        "interpretation": {
            "category": "Dense Healthy Vegetation",
            "description": "High vegetation density indicative of healthy tropical forest.",
            "health": "excellent",
        },
        "metadata": {
            "satellite": "Sentinel-2 L2A (DEMO)",
            "date_range": "Demo data",
            "images_used": 0,
            "scale_meters": 100,
        },
        "demo_grid": np.clip(
            0.7 + 0.15 * np.sin(np.linspace(0, 4*np.pi, 30).reshape(-1,1))
            * np.cos(np.linspace(0, 4*np.pi, 30).reshape(1,-1))
            + np.random.normal(0, 0.05, (30, 30)),
            -0.2, 0.95
        ).tolist(),
    }


def _get_demo_density_data():
    return {
        "tile_url": None,
        "demo_mode": True,
        "total_area_hectares": 11000,
        "categories": {
            "dense_forest": {"label": "Dense Forest", "area_hectares": 6050, "color": "#0a5e1a", "ndvi_range": "0.7 – 1.0", "percentage": 55.0},
            "moderate_forest": {"label": "Moderate Forest", "area_hectares": 2420, "color": "#4caf50", "ndvi_range": "0.5 – 0.7", "percentage": 22.0},
            "sparse_vegetation": {"label": "Sparse Vegetation", "area_hectares": 1320, "color": "#cddc39", "ndvi_range": "0.3 – 0.5", "percentage": 12.0},
            "grassland_crops": {"label": "Grassland/Crops", "area_hectares": 770, "color": "#ffeb3b", "ndvi_range": "0.1 – 0.3", "percentage": 7.0},
            "non_vegetation": {"label": "Non-Vegetation", "area_hectares": 440, "color": "#d32f2f", "ndvi_range": "-1.0 – 0.1", "percentage": 4.0},
        },
    }


def _get_demo_change_data():
    return {
        "change_tile_url": None,
        "diff_tile_url": None,
        "demo_mode": True,
        "changes": {
            "forest_loss": {"area_hectares": 880, "percentage": 8.0, "color": "#e53935", "label": "Forest Loss"},
            "stable": {"area_hectares": 9790, "percentage": 89.0, "color": "#fdd835", "label": "Stable"},
            "forest_gain": {"area_hectares": 330, "percentage": 3.0, "color": "#43a047", "label": "Forest Gain"},
        },
        "total_area_hectares": 11000,
        "net_change_hectares": -550,
        "period1_mean_ndvi": 0.74,
        "period2_mean_ndvi": 0.69,
        "metadata": {"satellite": "Sentinel-2 L2A (DEMO)"},
    }




# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
logo_footer = get_logo_html(width="1rem", vertical_align="middle", margin_right="4px")
st.markdown(f"""
<div class="footer">
    {logo_footer} Forest observation and analysis system v1.0 | 
    Powered by Google Earth Engine & Sentinel-2 | 
    Built with FastAPI + Streamlit
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
main()
