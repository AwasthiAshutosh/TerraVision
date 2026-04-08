"""
Statistics Component

Renders summary statistics panels with styled metric cards
for each analysis type.
"""

import streamlit as st
from typing import Any, Dict


def render_ndvi_stats(data: Dict[str, Any]) -> None:
    """
    Render NDVI analysis statistics as metric cards.

    Args:
        data: NDVI analysis result from the API.
    """
    stats = data.get("stats", {})
    interpretation = data.get("interpretation", {})
    metadata = data.get("metadata", {})

    # Metric row
    cols = st.columns(4)

    with cols[0]:
        st.metric(
            label="Mean NDVI",
            value=f"{stats.get('mean', 0):.4f}",
            help="Average NDVI across the AOI",
        )

    with cols[1]:
        st.metric(
            label="Min NDVI",
            value=f"{stats.get('min', 0):.4f}",
        )

    with cols[2]:
        st.metric(
            label="Max NDVI",
            value=f"{stats.get('max', 0):.4f}",
        )

    with cols[3]:
        st.metric(
            label="Std Dev",
            value=f"{stats.get('std_dev', 0):.4f}",
            help="Spatial variability of NDVI",
        )

    # Interpretation card
    if interpretation:
        health_emoji = {
            "excellent": "🟢",
            "good": "🔵",
            "moderate": "🟡",
            "poor": "🟠",
            "none": "🔴",
        }
        emoji = health_emoji.get(interpretation.get("health", ""), "⚪")

        st.markdown(f"""
        <div class="analysis-panel">
            <div class="panel-title">{emoji} {interpretation.get('category', 'Unknown')}</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem; margin: 0;">
                {interpretation.get('description', '')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Metadata expander
    with st.expander("📋 Processing Metadata"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Satellite:** {metadata.get('satellite', 'N/A')}")
            st.write(f"**Date Range:** {metadata.get('date_range', 'N/A')}")
        with col2:
            st.write(f"**Images Used:** {metadata.get('images_used', 'N/A')}")
            st.write(f"**Resolution:** {metadata.get('scale_meters', 'N/A')}m")


def render_density_stats(data: Dict[str, Any]) -> None:
    """
    Render forest density classification statistics.

    Args:
        data: Density classification result from the API.
    """
    categories = data.get("categories", {})
    total_ha = data.get("total_area_hectares", 0)

    # Total area header
    st.metric(
        label="Total Analyzed Area",
        value=f"{total_ha:,.0f} hectares",
    )

    # Category breakdown
    st.markdown("#### Density Breakdown")

    for key, cat in categories.items():
        color = cat.get("color", "#666")
        label = cat.get("label", key)
        area = cat.get("area_hectares", 0)
        pct = cat.get("percentage", 0)

        st.markdown(f"""
        <div class="legend-item">
            <div class="legend-color" style="background: {color};"></div>
            <span class="legend-label">{label}</span>
            <span class="legend-value">{area:,.0f} ha ({pct:.1f}%)</span>
        </div>
        """, unsafe_allow_html=True)


def render_change_stats(data: Dict[str, Any]) -> None:
    """
    Render change detection statistics.

    Args:
        data: Change detection result from the API.
    """
    changes = data.get("changes", {})
    net_change = data.get("net_change_hectares", 0)
    p1_ndvi = data.get("period1_mean_ndvi", 0)
    p2_ndvi = data.get("period2_mean_ndvi", 0)

    # Main metric row
    cols = st.columns(3)

    loss = changes.get("forest_loss", {})
    gain = changes.get("forest_gain", {})
    stable = changes.get("stable", {})

    with cols[0]:
        st.metric(
            label="🔴 Forest Loss",
            value=f"{loss.get('area_hectares', 0):,.0f} ha",
            delta=f"{loss.get('percentage', 0):.1f}%",
            delta_color="inverse",
        )

    with cols[1]:
        st.metric(
            label="🟢 Forest Gain",
            value=f"{gain.get('area_hectares', 0):,.0f} ha",
            delta=f"{gain.get('percentage', 0):.1f}%",
            delta_color="normal",
        )

    with cols[2]:
        delta_color = "normal" if net_change >= 0 else "inverse"
        st.metric(
            label="📊 Net Change",
            value=f"{net_change:+,.0f} ha",
            delta=f"{'Gain' if net_change >= 0 else 'Loss'}",
            delta_color=delta_color,
        )

    # NDVI comparison
    st.markdown("#### NDVI Change")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Period 1 Mean NDVI", f"{p1_ndvi:.4f}")
    with col2:
        st.metric("Period 2 Mean NDVI", f"{p2_ndvi:.4f}")
    with col3:
        ndvi_change = p2_ndvi - p1_ndvi
        st.metric("ΔNDVI", f"{ndvi_change:+.4f}")


