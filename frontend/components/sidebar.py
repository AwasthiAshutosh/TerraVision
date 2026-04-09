"""
Sidebar Component

Provides the sidebar UI for parameter selection: AOI coordinates,
date ranges, analysis options, and download controls.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Dict, Tuple, List


def render_sidebar() -> Dict:
    """
    Render the sidebar and return user-selected parameters.

    Returns:
        Dictionary with all sidebar parameter values.
    """
    with st.sidebar:
        # App Logo & Title
        from frontend.utils.styles import get_logo_html
        logo_html = get_logo_html(width="7rem", container_style="display: inline-block; margin-bottom: 8px;")

        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 1rem;">
            {logo_html}
            <div style="font-size: 1rem; font-weight: 700; color: #4caf50; margin-top: 4px;">TerraVision</div>
            <div style="font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 2px;">See More. Know More. Protect More.</div>
        </div>
        """, unsafe_allow_html=True)

        # Analysis Mode
        st.markdown('<div class="sidebar-title">📊 Analysis Mode</div>', unsafe_allow_html=True)
        analysis_mode = st.selectbox(
            "Select Analysis",
            options=["NDVI Analysis", "Forest Density", "Change Detection"],
            index=0,
            key="analysis_mode_select",
            help="""
**NDVI Analysis**: Measures vegetation health using satellite imagery to identify lush or stressed forests.\n\n
**Forest Density**: Classifies canopy cover into density categories (e.g., dense, moderate, sparse).\n\n
**Change Detection**: Compares data between two time periods to identify areas of forest loss or gain.\n\n
            """
        )

        st.divider()

        # Area of Interest
        st.markdown('<div class="sidebar-title">📍 Area of Interest</div>', unsafe_allow_html=True)

        aoi_preset = st.selectbox(
            "Preset Region",
            options=[
                "Amazon Rainforest (Brazil)",
                "Congo Basin (DRC)",
                "Borneo (Indonesia)",
                "Western Ghats (India)",
                "Custom Coordinates",
            ],
            index=0,
        )

        # Preset AOI coordinates
        aoi_presets = {
            "Amazon Rainforest (Brazil)": [-60.0, -3.0, -59.0, -2.0],
            "Congo Basin (DRC)": [20.0, -2.0, 21.0, -1.0],
            "Borneo (Indonesia)": [109.5, 0.5, 110.5, 1.5],
            "Western Ghats (India)": [75.5, 11.0, 76.5, 12.0],
        }

        if aoi_preset == "Custom Coordinates":
            col1, col2 = st.columns(2)
            with col1:
                west = st.number_input("West", value=-60.0, format="%.4f", step=0.1)
                south = st.number_input("South", value=-3.0, format="%.4f", step=0.1)
            with col2:
                east = st.number_input("East", value=-59.0, format="%.4f", step=0.1)
                north = st.number_input("North", value=-2.0, format="%.4f", step=0.1)
            bbox = [west, south, east, north]
        else:
            bbox = aoi_presets.get(aoi_preset, [-60.0, -3.0, -59.0, -2.0])
            st.info(f"📐 Bbox: [{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]")

        st.divider()

        # Date Selection
        st.markdown('<div class="sidebar-title">📅 Date Range</div>', unsafe_allow_html=True)

        if analysis_mode == "Change Detection":
            st.caption("**Period 1 (Baseline)**")
            p1_start = st.date_input(
                "P1 Start",
                value=date(2023, 1, 1),
                max_value=date.today(),
                key="p1_start",
            )
            p1_end = st.date_input(
                "P1 End",
                value=date(2023, 6, 30),
                max_value=date.today(),
                key="p1_end",
            )

            st.caption("**Period 2 (Comparison)**")
            p2_start = st.date_input(
                "P2 Start",
                value=date(2024, 1, 1),
                max_value=date.today(),
                key="p2_start",
            )
            p2_end = st.date_input(
                "P2 End",
                value=date(2024, 6, 30),
                max_value=date.today(),
                key="p2_end",
            )
        else:
            start_date = st.date_input(
                "Start Date",
                value=date(2024, 1, 1),
                max_value=date.today(),
            )
            end_date = st.date_input(
                "End Date",
                value=date(2024, 6, 30),
                max_value=date.today(),
            )

        st.divider()

        # Processing Options
        st.markdown('<div class="sidebar-title">⚙️ Processing Options</div>', unsafe_allow_html=True)

        scale = st.slider(
            "Resolution (meters)",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            help="Lower values = higher resolution but slower processing",
        )

        if analysis_mode == "Change Detection":
            change_threshold = st.slider(
                "Change Threshold",
                min_value=0.05,
                max_value=0.5,
                value=0.2,
                step=0.05,
                help="Minimum NDVI difference to flag as change",
            )
        else:
            change_threshold = 0.2

        st.divider()

        # Run Button
        run_clicked = st.button(
            "🚀 Run Analysis",
            type="primary",
            use_container_width=True,
        )

        params_hashable = {
            "analysis_mode": analysis_mode,
            "aoi_preset": aoi_preset,
            "bbox": tuple(bbox),
            "scale": scale,
            "change_threshold": change_threshold,
        }
        if analysis_mode == "Change Detection":
            params_hashable["dates"] = (str(p1_start), str(p1_end), str(p2_start), str(p2_end))
        else:
            params_hashable["dates"] = (str(start_date), str(end_date))

        if run_clicked:
            st.session_state["analysis_active"] = True
            st.session_state["active_mode"] = analysis_mode
            st.session_state["last_run_params"] = params_hashable
        else:
            # Only reset if the analysis mode changed — not for resolution/threshold tweaks
            last_params = st.session_state.get("last_run_params")
            if last_params and last_params.get("analysis_mode") != params_hashable["analysis_mode"]:
                st.session_state["analysis_active"] = False

        run_analysis = run_clicked

        # Footer
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-top: 1rem; color: rgba(255,255,255,0.25); font-size: 0.65rem;">
            Forest observation and analysis system v1.0<br>
            Powered by Google Earth Engine
        </div>
        """, unsafe_allow_html=True)

    # Build result dict
    params = {
        "analysis_mode": analysis_mode,
        "bbox": bbox,
        "aoi_name": aoi_preset,
        "scale": scale,
        "change_threshold": change_threshold,
        "run_analysis": run_analysis,
    }

    if analysis_mode == "Change Detection":
        params["period1_start"] = str(p1_start)
        params["period1_end"] = str(p1_end)
        params["period2_start"] = str(p2_start)
        params["period2_end"] = str(p2_end)
    else:
        params["start_date"] = str(start_date)
        params["end_date"] = str(end_date)

    return params
