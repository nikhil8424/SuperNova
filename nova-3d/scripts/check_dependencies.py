"""
NOVA 3D - Standalone Dependency Health Check
"""
import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.reconstruction.colmap_engine import detect_colmap
from app.reconstruction.gaussian_splat_engine import detect_gaussian_splat_stack

def check_pkg(name):
    try:
        __import__(name)
        print(f"[+] Python Package '{name}': OK")
        return True
    except ImportError as e:
        print(f"[-] Python Package '{name}': MISSING ({e})")
        return False

def main():
    print("=" * 60)
    print("        NOVA 3D - DEPENDENCY DIAGNOSTICS")
    print("=" * 60)

    for pkg in ["fastapi", "uvicorn", "streamlit", "cv2", "trimesh", "plotly", "mediapipe", "sqlalchemy", "psutil"]:
        check_pkg(pkg)

    print("-" * 60)
    colmap = detect_colmap()
    print(f"[*] COLMAP Status: {'INSTALLED' if colmap['installed'] else 'FALLBACK (OpenCV SfM Active)'}")
    print(f"    Info: {colmap['message']}")

    print("-" * 60)
    gs = detect_gaussian_splat_stack()
    print(f"[*] Gaussian Splat Stack Status: {'SPLATFACTO READY' if gs['nerfstudio_installed'] else 'ADAPTIVE PRIMITIVE ACTIVE'}")
    print(f"    Info: {gs['diagnostic']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
