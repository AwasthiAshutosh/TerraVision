"""
Custom Styles & Theming

Provides premium CSS styling for the Streamlit dashboard with
dark mode, glassmorphism effects, and modern typography.
"""
from pathlib import Path


def get_page_icon():
    """Return the page icon as a PIL Image if logo exists, else the tree emoji."""
    base_path = Path(__file__).resolve().parent.parent / "assets"
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = base_path / f"logo_transparent{ext}"
        if logo_path.exists():
            try:
                from PIL import Image
                return Image.open(logo_path)
            except Exception:
                pass
    return "🌳"


def get_logo_html(width="2.5rem", vertical_align="middle", margin_right="0px", container_style="") -> str:
    """Return HTML for the logo image or emoji fallback."""
    base_path = Path(__file__).resolve().parent.parent / "assets"
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        logo_path = base_path / f"logo_transparent{ext}"
        if logo_path.exists():
            try:
                import base64
                with open(logo_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                mime = "image/jpeg" if ext in ['.jpg', '.jpeg'] else f"image/{ext[1:]}"
                return f'<img src="data:{mime};base64,{encoded}" style="width: {width}; height: auto; vertical-align: {vertical_align}; margin-right: {margin_right}; {container_style}" />'
            except Exception:
                pass
    
    return f'<span style="font-size: {width}; vertical-align: {vertical_align}; margin-right: {margin_right}; {container_style}">🌳</span>'


def get_custom_css() -> str:
    """Return custom CSS for the Streamlit app."""
    import base64
    from pathlib import Path

    base_path = Path(__file__).resolve().parent.parent / "assets"
    
    extra_css = ""
    vertical_path = base_path / "vertical.jpg"
    if vertical_path.exists():
        with open(vertical_path, "rb") as f:
            v_encoded = base64.b64encode(f.read()).decode()
        extra_css += f"""
    [data-testid="stSidebar"] {{
        background: linear-gradient(rgba(15, 20, 25, 0.5), rgba(15, 20, 25, 0.5)), url('data:image/jpeg;base64,{v_encoded}') !important;
        background-size: cover !important;
        background-position: center !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: transparent !important;
    }}
    """

    belowview_path = base_path / "belowview.jpg"
    if belowview_path.exists():
        with open(belowview_path, "rb") as f:
            b_encoded = base64.b64encode(f.read()).decode()
        extra_css += f"""
    .stApp > header {{
        background: transparent !important;
    }}
    .stApp {{
        background: linear-gradient(rgba(18, 18, 18, 0.85), rgba(18, 18, 18, 0.85)), url('data:image/jpeg;base64,{b_encoded}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    """

    return """
    <style>
    /* ========================================
       GLOBAL STYLES & TYPOGRAPHY
       ======================================== */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap');

    .stApp {
        font-family: 'Open Sans', sans-serif;
    }

    h1, h2, h3, h4, h5, h6, .main-header h1, .panel-title {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* ========================================
       HEADER STYLING
       ======================================== */
    .main-header {
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(10, 61, 23, 0.3);
        position: relative;
        overflow: hidden;
    }

    .circle {
        position: absolute;
        border-radius: 50%;
        border: 1px solid rgba(255, 255, 255, 0.2);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
    }
    .circle-1 { width: 300px; height: 300px; border-width: 1px; border-color: rgba(255, 255, 255, 0.25); }
    .circle-2 { width: 550px; height: 550px; border-width: 2px; border-color: rgba(255, 255, 255, 0.15); }
    .circle-3 { width: 900px; height: 900px; border-width: 1px; border-color: rgba(255, 255, 255, 0.08); }
    .circle-4 { width: 1300px; height: 1300px; border-width: 1px; border-color: rgba(255, 255, 255, 0.04); }

    .main-header h1 {
        color: #4caf50;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        font-family: 'Chantelli Antiqua', 'Outfit', serif !important;
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* ========================================
       STATUS BADGES
       ======================================== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .status-live {
        background: rgba(76, 175, 80, 0.15);
        color: #4caf50;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }

    .status-demo {
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.3);
    }

    /* ========================================
       METRIC CARDS
       ======================================== */
    .metric-card {
        background: linear-gradient(145deg, rgba(26, 107, 60, 0.08), rgba(26, 107, 60, 0.02));
        border: 1px solid rgba(76, 175, 80, 0.15);
        border-radius: 12px;
        padding: 1.25rem;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.15);
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: rgba(255,255,255,0.5);
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #4caf50;
        line-height: 1;
    }

    .metric-description {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.4);
        margin-top: 4px;
    }

    /* ========================================
       ANALYSIS PANEL
       ======================================== */
    .analysis-panel {
        background: linear-gradient(145deg, rgba(30, 30, 30, 0.6), rgba(20, 20, 20, 0.4));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .panel-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: rgba(255,255,255,0.9);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ========================================
       DENSITY LEGEND
       ======================================== */
    .legend-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
    }

    .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        flex-shrink: 0;
    }

    .legend-label {
        font-size: 0.85rem;
        font-weight: 500;
    }

    .legend-value {
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: auto;
        color: rgba(255,255,255,0.6);
    }

    /* ========================================
       CHANGE INDICATORS
       ======================================== */
    .change-positive {
        color: #4caf50;
        font-weight: 700;
    }

    .change-negative {
        color: #e53935;
        font-weight: 700;
    }

    .change-neutral {
        color: #fdd835;
        font-weight: 700;
    }

    /* ========================================
       SIDEBAR STYLING
       ======================================== */
    .sidebar-section {
        padding: 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .sidebar-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: rgba(255,255,255,0.4);
        margin-bottom: 0.75rem;
    }

    /* ========================================
       LOADING ANIMATION
       ======================================== */
    .loading-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* ========================================
       FOOTER
       ======================================== */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: rgba(255,255,255,0.3);
        font-size: 0.75rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin-top: 2rem;
    }

    /* ========================================
       STREAMLIT OVERRIDES
       ======================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
    }

    div[data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
    }
    """ + extra_css + """
    </style>
    """


def render_metric_card(label: str, value: str, description: str = "", icon: str = "") -> str:
    """Render a styled metric card as HTML."""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-description">{description}</div>
    </div>
    """


def render_header(demo_mode: bool = False) -> str:
    """Render the main application header."""
    import base64
    from pathlib import Path
    
    logo_html = get_logo_html(width="4rem", vertical_align="middle", margin_right="0px")
    
    bg_path = Path(__file__).resolve().parent.parent / "assets" / "forest_bg.jpg"
    bg_style = "background: linear-gradient(135deg, #0d4a1e 0%, #1a6b3c 40%, #0f5a28 70%, #0a3d17 100%);"
    if bg_path.exists():
        with open(bg_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        bg_style = f"background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('data:image/jpeg;base64,{encoded}'); background-size: cover; background-position: center;"

    return f"""
    <div class="main-header" style="{bg_style}">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
        <div class="circle circle-4"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative; z-index: 1;">
            <div style="display: flex; align-items: center;">
                <div>
                    <div style="display: flex; align-items: center; gap: 15px;">
                        {logo_html}
                        <h1>TerraVision</h1>
                    </div>
                    <p>A forest observation and analysis system.</p>
                </div>
            </div>
        </div>
    </div>
    """
