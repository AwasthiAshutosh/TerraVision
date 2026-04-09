"""
Charts Component

Renders interactive Plotly charts for NDVI distribution,
density breakdown, change statistics, and ML predictions.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List, Optional


# Color Palette
FOREST_COLORS = {
    "primary": "#4caf50",
    "secondary": "#81c784",
    "accent": "#1b5e20",
    "danger": "#e53935",
    "warning": "#fdd835",
    "success": "#43a047",
    "bg_dark": "rgba(0,0,0,0)",
    "text": "rgba(255,255,255,0.8)",
    "text_muted": "rgba(255,255,255,0.4)",
}


def _base_layout(title: str = "") -> dict:
    """Return common Plotly layout settings for dark theme."""
    return dict(
        title=dict(text=title, font=dict(size=16, color=FOREST_COLORS["text"])),
        paper_bgcolor=FOREST_COLORS["bg_dark"],
        plot_bgcolor=FOREST_COLORS["bg_dark"],
        font=dict(family="Inter, sans-serif", color=FOREST_COLORS["text"]),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=FOREST_COLORS["text"]),
        ),
    )


def create_ndvi_gauge(mean_ndvi: float) -> go.Figure:
    """
    Create an NDVI gauge chart showing the mean value with color zones.

    Args:
        mean_ndvi: Mean NDVI value (range -1 to 1).

    Returns:
        Plotly Figure with a gauge chart.
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=mean_ndvi,
        title={"text": "Mean NDVI", "font": {"size": 16, "color": FOREST_COLORS["text"]}},
        number={"font": {"size": 36, "color": FOREST_COLORS["primary"]}},
        gauge={
            "axis": {"range": [-0.2, 1.0], "tickcolor": FOREST_COLORS["text_muted"]},
            "bar": {"color": FOREST_COLORS["primary"], "thickness": 0.3},
            "bgcolor": "rgba(255,255,255,0.05)",
            "steps": [
                {"range": [-0.2, 0.1], "color": "rgba(211, 47, 47, 0.3)"},
                {"range": [0.1, 0.3], "color": "rgba(255, 235, 59, 0.3)"},
                {"range": [0.3, 0.5], "color": "rgba(205, 220, 57, 0.3)"},
                {"range": [0.5, 0.7], "color": "rgba(76, 175, 80, 0.3)"},
                {"range": [0.7, 1.0], "color": "rgba(27, 94, 32, 0.4)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.8,
                "value": mean_ndvi,
            },
        },
    ))

    fig.update_layout(**_base_layout(), height=280)
    return fig


def create_density_donut(categories: Dict[str, Any]) -> go.Figure:
    """
    Create a donut chart showing forest density distribution.

    Args:
        categories: Dictionary of density categories with area and color data.

    Returns:
        Plotly Figure with a donut chart.
    """
    labels = [cat["label"] for cat in categories.values()]
    values = [cat["area_hectares"] for cat in categories.values()]
    colors = [cat["color"] for cat in categories.values()]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.3)", width=2)),
        textinfo="percent+label",
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>Area: %{value:,.0f} ha<br>Share: %{percent}<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout("Forest Density Distribution"),
        height=380,
        showlegend=False,
        annotations=[dict(
            text="<b>Density</b>",
            x=0.5, y=0.5,
            font_size=14,
            font_color=FOREST_COLORS["text"],
            showarrow=False,
        )],
    )

    return fig


def create_density_bar(categories: Dict[str, Any]) -> go.Figure:
    """
    Create a horizontal bar chart of area per density category.

    Args:
        categories: Dictionary of density categories.

    Returns:
        Plotly Figure with horizontal bar chart.
    """
    labels = [cat["label"] for cat in categories.values()]
    areas = [cat["area_hectares"] for cat in categories.values()]
    colors = [cat["color"] for cat in categories.values()]

    fig = go.Figure(go.Bar(
        y=labels,
        x=areas,
        orientation="h",
        marker_color=colors,
        text=[f"{a:,.0f} ha" for a in areas],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Area: %{x:,.0f} hectares<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout("Area by Density Class (Hectares)"),
        height=320,
        xaxis=dict(
            title="Area (hectares)",
            gridcolor="rgba(255,255,255,0.05)",
        ),
        yaxis=dict(autorange="reversed"),
    )

    return fig


def create_change_chart(changes: Dict[str, Any]) -> go.Figure:
    """
    Create a bar chart showing forest change statistics.

    Args:
        changes: Dictionary with loss, stable, and gain data.

    Returns:
        Plotly Figure with change detection bar chart.
    """
    labels = [ch["label"] for ch in changes.values()]
    areas = [ch["area_hectares"] for ch in changes.values()]
    colors = [ch["color"] for ch in changes.values()]

    fig = go.Figure(go.Bar(
        x=labels,
        y=areas,
        marker_color=colors,
        text=[f"{a:,.0f} ha" for a in areas],
        textposition="outside",
        textfont=dict(size=12, color=FOREST_COLORS["text"]),
        hovertemplate="<b>%{x}</b><br>Area: %{y:,.0f} hectares<extra></extra>",
    ))

    fig.update_layout(
        **_base_layout("Forest Change Analysis"),
        height=380,
        yaxis=dict(
            title="Area (hectares)",
            gridcolor="rgba(255,255,255,0.05)",
        ),
    )

    return fig


def create_ndvi_comparison(period1_ndvi: float, period2_ndvi: float) -> go.Figure:
    """
    Create a comparison chart for NDVI between two periods.

    Args:
        period1_ndvi: Mean NDVI for period 1.
        period2_ndvi: Mean NDVI for period 2.

    Returns:
        Plotly Figure with comparison chart.
    """
    change = period2_ndvi - period1_ndvi
    change_pct = (change / period1_ndvi * 100) if period1_ndvi != 0 else 0

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=["Period 1 (Baseline)", "Period 2 (Current)"],
        y=[period1_ndvi, period2_ndvi],
        marker_color=[FOREST_COLORS["secondary"], FOREST_COLORS["primary"]],
        text=[f"{period1_ndvi:.4f}", f"{period2_ndvi:.4f}"],
        textposition="outside",
        textfont=dict(size=14, color=FOREST_COLORS["text"]),
    ))

    title_text = f"NDVI Comparison (Δ = {change:+.4f}, {change_pct:+.1f}%)"

    fig.update_layout(
        **_base_layout(title_text),
        height=320,
        yaxis=dict(
            title="Mean NDVI",
            range=[0, 1],
            gridcolor="rgba(255,255,255,0.05)",
        ),
    )

    return fig


