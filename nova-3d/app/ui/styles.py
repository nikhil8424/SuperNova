"""
NOVA 3D - Dark Futuristic Styling & UI Design System
Provides custom CSS styles, glassmorphic cards, gradient headers, and badge widgets.
"""

def get_theme_css() -> str:
    return """
    <style>
    /* Dark Graphite Background & Typography */
    .stApp {
        background-color: #0b0d13;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top Header Bar */
    header[data-testid="stHeader"] {
        background: rgba(11, 13, 19, 0.85);
        backdrop-filter: blur(10px);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #12151f;
        border-right: 1px solid #262c40;
    }

    /* Glassmorphic Cards & Panels */
    .nova-card {
        background: #12151f;
        border: 1px solid #262c40;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .nova-card:hover {
        border-color: #00f0ff;
        transform: translateY(-2px);
    }

    .nova-stat-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00f0ff, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }

    .nova-stat-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* Brand Header Badge */
    .nova-logo-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(0, 240, 255, 0.12);
        border: 1px solid rgba(0, 240, 255, 0.3);
        color: #00f0ff;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Electric Violet & Cyan Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00f0ff 0%, #0284c7 100%);
        color: #000000;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #00f0ff 100%);
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
        color: #000000;
        transform: scale(1.02);
    }

    /* Secondary Buttons */
    .stButton>button[kind="secondary"] {
        background: #1a1e2d;
        color: #f1f5f9;
        border: 1px solid #262c40;
    }
    .stButton>button[kind="secondary"]:hover {
        border-color: #a855f7;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.4);
    }

    /* Status Badges */
    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-running {
        background: rgba(0, 240, 255, 0.15);
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Form Inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #12151f !important;
        border: 1px solid #262c40 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #00f0ff !important;
        box-shadow: 0 0 8px rgba(0, 240, 255, 0.3) !important;
    }

    /* Metric Containers */
    div[data-testid="stMetricValue"] {
        color: #00f0ff;
    }
    </style>
    """
