"""
NOVA 3D - Master Application Streamlit Entrypoint
Renders the navigation sidebar, branding header, custom CSS design system,
and dynamically routes to all 12 platform modules.
"""
import streamlit as st

# Configure page setup
st.set_page_config(
    page_title="NOVA 3D — 3D Reconstruction & Exploration",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.ui.styles import get_theme_css
from app.ui.dashboard import render_dashboard
from app.ui.projects import render_create_project, render_projects_manager
from app.ui.reconstruction import render_reconstruction_view
from app.ui.machine_explorer import render_machine_explorer
from app.ui.scene_viewer import render_scene_viewer
from app.ui.processing_monitor import render_processing_monitor
from app.ui.gesture_studio import render_gesture_studio
from app.ui.analytics import render_analytics
from app.ui.asset_library import render_asset_library
from app.ui.settings import render_settings
from app.ui.documentation import render_documentation

# Inject Dark Graphite & Electric Theme CSS
st.markdown(get_theme_css(), unsafe_allow_html=True)

# Navigation Items (Prompt Section 3 Specification)
NAV_ITEMS = [
    "Dashboard",
    "Create Project",
    "Environment Reconstruction",
    "Object Reconstruction",
    "Machine Explorer",
    "Scene Viewer",
    "Processing Monitor",
    "Gesture Studio",
    "Metrics & Analytics",
    "Asset Library",
    "Settings",
    "Documentation"
]

NAV_ICONS = {
    "Dashboard": "📊",
    "Create Project": "➕",
    "Environment Reconstruction": "🏛️",
    "Object Reconstruction": "📦",
    "Machine Explorer": "⚙️",
    "Scene Viewer": "🌐",
    "Processing Monitor": "⏱️",
    "Gesture Studio": "🖐️",
    "Metrics & Analytics": "📈",
    "Asset Library": "🗄️",
    "Settings": "🛠️",
    "Documentation": "📖"
}

# Initialize session state for navigation
if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "Dashboard"

def navigate_to(page_name: str):
    if page_name in NAV_ITEMS:
        st.session_state["active_nav"] = page_name
        st.rerun()

# Sidebar Brand Header
with st.sidebar:
    st.markdown("""
    <div style="text-align: left; padding: 10px 0 16px 0;">
        <div style="font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em;">
            <span style="color: #00f0ff;">NOVA</span> <span style="color: #a855f7;">3D</span>
        </div>
        <div style="font-size: 0.78rem; color: #94a3b8; font-weight: 500;">
            Reconstruct Reality. Explore Beyond.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation Radio Selector
    selected_page = st.radio(
        "Navigation",
        options=NAV_ITEMS,
        index=NAV_ITEMS.index(st.session_state["active_nav"]),
        format_func=lambda x: f"{NAV_ICONS.get(x, '•')} {x}",
        label_visibility="collapsed"
    )

    if selected_page != st.session_state["active_nav"]:
        st.session_state["active_nav"] = selected_page
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.75rem; color: #64748b; line-height: 1.4;">
        <strong>NOVA 3D Platform v1.0</strong><br>
        Python-First Architecture<br>
        OpenCV • SfM • Gaussian Splats • MediaPipe
    </div>
    """, unsafe_allow_html=True)

# Main Content Routing
active_page = st.session_state["active_nav"]

if active_page == "Dashboard":
    render_dashboard(navigate_fn=navigate_to)
elif active_page == "Create Project":
    render_create_project(navigate_fn=navigate_to)
elif active_page == "Environment Reconstruction":
    render_reconstruction_view(reconstruction_mode="environment", navigate_fn=navigate_to)
elif active_page == "Object Reconstruction":
    render_reconstruction_view(reconstruction_mode="object", navigate_fn=navigate_to)
elif active_page == "Machine Explorer":
    render_machine_explorer(navigate_fn=navigate_to)
elif active_page == "Scene Viewer":
    render_scene_viewer(navigate_fn=navigate_to)
elif active_page == "Processing Monitor":
    render_processing_monitor(navigate_fn=navigate_to)
elif active_page == "Gesture Studio":
    render_gesture_studio()
elif active_page == "Metrics & Analytics":
    render_analytics(navigate_fn=navigate_to)
elif active_page == "Asset Library":
    render_asset_library(navigate_fn=navigate_to)
elif active_page == "Settings":
    render_settings()
elif active_page == "Documentation":
    render_documentation()
