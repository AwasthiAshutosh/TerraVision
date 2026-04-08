"""
Map View Component

Renders interactive Folium maps with satellite imagery overlays,
NDVI heatmaps, density classifications, and change detection results.
"""

import folium
import numpy as np
from folium import plugins
from typing import Any, Dict, List, Optional


def create_base_map(
    center: List[float] = None,
    zoom: int = 10,
) -> folium.Map:
    """
    Create a base Folium map with satellite and terrain tile layers.

    Args:
        center: [lat, lon] center point. Defaults to Amazon.
        zoom: Initial zoom level.

    Returns:
        Configured folium.Map instance.
    """
    if center is None:
        center = [-2.5, -59.5]  # Amazon Rainforest

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    # Satellite imagery basemap
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="🛰️ Satellite",
        overlay=False,
    ).add_to(m)

    # OpenStreetMap
    folium.TileLayer(
        tiles="openstreetmap",
        name="🗺️ Streets",
        overlay=False,
    ).add_to(m)

    # Terrain
    folium.TileLayer(
        tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        attr="Stamen Terrain",
        name="⛰️ Terrain",
        overlay=False,
    ).add_to(m)

    return m


def add_ndvi_layer(
    m: folium.Map,
    tile_url: Optional[str] = None,
    demo_grid: Optional[List[List[float]]] = None,
    bbox: Optional[List[float]] = None,
) -> folium.Map:
    """
    Add NDVI visualization layer to the map.

    For live mode: uses GEE tile URL as TileLayer.
    For demo mode: renders a colorized heatmap from synthetic grid data.

    Args:
        m: Base Folium map.
        tile_url: GEE map tile URL (live mode).
        demo_grid: 2D array of NDVI values (demo mode).
        bbox: Bounding box for positioning the overlay.

    Returns:
        Map with NDVI layer added.
    """
    if tile_url:
        # Live GEE tile layer
        folium.TileLayer(
            tiles=tile_url,
            attr="Sentinel-2 NDVI",
            name="🌿 NDVI",
            overlay=True,
            opacity=0.75,
        ).add_to(m)
    elif demo_grid and bbox:
        # Demo mode: render as image overlay
        _add_demo_heatmap(m, demo_grid, bbox, name="🌿 NDVI (Demo)")

    return m


def add_density_layer(
    m: folium.Map,
    tile_url: Optional[str] = None,
    categories: Optional[Dict] = None,
    bbox: Optional[List[float]] = None,
) -> folium.Map:
    """
    Add forest density classification layer to the map.

    Args:
        m: Base Folium map.
        tile_url: GEE classified image tile URL.
        categories: Category definitions with colors.
        bbox: Bounding box for the AOI.

    Returns:
        Map with density layer added.
    """
    if tile_url:
        folium.TileLayer(
            tiles=tile_url,
            attr="Forest Density",
            name="🌲 Density Classification",
            overlay=True,
            opacity=0.7,
        ).add_to(m)

    # Add AOI bounding box
    if bbox:
        _add_aoi_rectangle(m, bbox)

    return m


def add_change_layer(
    m: folium.Map,
    change_tile_url: Optional[str] = None,
    diff_tile_url: Optional[str] = None,
    bbox: Optional[List[float]] = None,
) -> folium.Map:
    """
    Add change detection layers to the map.

    Args:
        m: Base Folium map.
        change_tile_url: Classified change map tile URL.
        diff_tile_url: NDVI difference heatmap tile URL.
        bbox: Bounding box.

    Returns:
        Map with change detection layers.
    """
    if change_tile_url:
        folium.TileLayer(
            tiles=change_tile_url,
            attr="Change Detection",
            name="📊 Change Classification",
            overlay=True,
            opacity=0.7,
        ).add_to(m)

    if diff_tile_url:
        folium.TileLayer(
            tiles=diff_tile_url,
            attr="NDVI Difference",
            name="🔥 NDVI Change Heatmap",
            overlay=True,
            opacity=0.6,
            show=False,
        ).add_to(m)

    if bbox:
        _add_aoi_rectangle(m, bbox)

    return m


def add_legend(m: folium.Map, legend_html: str) -> folium.Map:
    """Add a custom HTML legend to the map."""
    legend = folium.Element(legend_html)
    m.get_root().html.add_child(legend)
    return m


def finalize_map(m: folium.Map) -> folium.Map:
    """
    Add final controls to the map (layer control, fullscreen, minimap).
    """
    # Layer switcher
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Fullscreen button
    plugins.Fullscreen(position="topleft").add_to(m)

    # Mini map for context
    mini_map = plugins.MiniMap(toggle_display=True, position="bottomleft")
    m.add_child(mini_map)

    # Mouse position
    plugins.MousePosition(position="bottomright").add_to(m)

    return m


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def _add_aoi_rectangle(m: folium.Map, bbox: List[float]) -> None:
    """Draw the AOI bounding box on the map."""
    west, south, east, north = bbox
    folium.Rectangle(
        bounds=[[south, west], [north, east]],
        color="#00e676",
        weight=2,
        fill=False,
        dash_array="8",
        popup="Area of Interest",
        tooltip="AOI Boundary",
    ).add_to(m)


def _add_demo_heatmap(
    m: folium.Map,
    grid: List[List[float]],
    bbox: List[float],
    name: str = "Demo Layer",
) -> None:
    """
    Render demo NDVI grid as a colored image overlay using heatmap.

    For demo mode, we create a grid of circle markers colored by NDVI value.
    """
    west, south, east, north = bbox
    grid_arr = np.array(grid)
    rows, cols = grid_arr.shape

    # Create a feature group for the demo layer
    fg = folium.FeatureGroup(name=name, overlay=True)

    # Sample grid (don't render all 2500 points — use every 3rd)
    step = max(1, rows // 20)

    lat_step = (north - south) / rows
    lon_step = (east - west) / cols

    for i in range(0, rows, step):
        for j in range(0, cols, step):
            ndvi = grid_arr[i, j]
            color = _ndvi_to_color(ndvi)
            lat = south + i * lat_step
            lon = west + j * lon_step

            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=0,
                popup=f"NDVI: {ndvi:.3f}",
            ).add_to(fg)

    fg.add_to(m)


def _ndvi_to_color(ndvi: float) -> str:
    """Map an NDVI value to a color string."""
    if ndvi > 0.7:
        return "#1a9850"
    elif ndvi > 0.5:
        return "#91cf60"
    elif ndvi > 0.3:
        return "#d9ef8b"
    elif ndvi > 0.1:
        return "#fee08b"
    elif ndvi > 0.0:
        return "#fc8d59"
    else:
        return "#d73027"


def get_ndvi_legend_html() -> str:
    """Generate NDVI color legend HTML."""
    return """
    <div style="
        position: fixed;
        bottom: 50px;
        right: 10px;
        z-index: 1000;
        background: rgba(0,0,0,0.8);
        border-radius: 8px;
        padding: 12px 16px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        color: white;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    ">
        <div style="font-weight: 700; margin-bottom: 8px; font-size: 13px;">NDVI Legend</div>
        <div style="display: flex; align-items: center; gap: 6px; margin: 4px 0;">
            <span style="width:14px;height:14px;background:#1a9850;border-radius:3px;display:inline-block;"></span>
            Dense (>0.7)
        </div>
        <div style="display: flex; align-items: center; gap: 6px; margin: 4px 0;">
            <span style="width:14px;height:14px;background:#91cf60;border-radius:3px;display:inline-block;"></span>
            Moderate (0.5–0.7)
        </div>
        <div style="display: flex; align-items: center; gap: 6px; margin: 4px 0;">
            <span style="width:14px;height:14px;background:#d9ef8b;border-radius:3px;display:inline-block;"></span>
            Sparse (0.3–0.5)
        </div>
        <div style="display: flex; align-items: center; gap: 6px; margin: 4px 0;">
            <span style="width:14px;height:14px;background:#fee08b;border-radius:3px;display:inline-block;"></span>
            Grassland (0.1–0.3)
        </div>
        <div style="display: flex; align-items: center; gap: 6px; margin: 4px 0;">
            <span style="width:14px;height:14px;background:#d73027;border-radius:3px;display:inline-block;"></span>
            Non-Veg (<0.1)
        </div>
    </div>
    """
