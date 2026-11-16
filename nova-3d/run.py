"""
NOVA 3D - Master Unified Application Launcher
Launches the Streamlit UI, FastAPI backend, or both concurrently.
"""
import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_api(host="127.0.0.1", port=8000):
    print(f"[*] Starting NOVA 3D FastAPI Backend on http://{host}:{port} ...")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port), "--reload"]
    return subprocess.Popen(cmd, cwd=str(BASE_DIR))

def run_ui(port=8501):
    print(f"[*] Starting NOVA 3D Streamlit Interface on http://localhost:{port} ...")
    ui_env = os.environ.copy()
    ui_env["USERPROFILE"] = str(BASE_DIR)
    ui_env["HOME"] = str(BASE_DIR)
    ui_env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    ui_env["STREAMLIT_SERVER_HEADLESS"] = "true"
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(BASE_DIR / "app" / "ui" / "app.py"),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark"
    ]
    return subprocess.Popen(cmd, cwd=str(BASE_DIR), env=ui_env)

def main():
    parser = argparse.ArgumentParser(description="NOVA 3D Launcher")
    parser.add_argument("--mode", choices=["ui", "api", "both"], default="ui",
                        help="Launch mode: 'ui' (Streamlit UI), 'api' (FastAPI REST API), or 'both'")
    parser.add_argument("--ui-port", type=int, default=8501, help="Port for Streamlit UI")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for FastAPI backend")
    args = parser.parse_args()

    procs = []
    try:
        if args.mode in ("api", "both"):
            p_api = run_api(port=args.api_port)
            procs.append(p_api)
            time.sleep(1)

        if args.mode in ("ui", "both"):
            p_ui = run_ui(port=args.ui_port)
            procs.append(p_ui)

        print("\n=======================================================")
        print("          NOVA 3D — PLATFORM ONLINE")
        print("=======================================================")
        if args.mode in ("ui", "both"):
            print(f" > Web Interface:     http://localhost:{args.ui_port}")
        if args.mode in ("api", "both"):
            print(f" > FastAPI REST Docs: http://127.0.0.1:{args.api_port}/docs")
        print("Press Ctrl+C to terminate all services.\n")

        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\n[!] Shutting down NOVA 3D services...")
        for p in procs:
            p.terminate()

if __name__ == "__main__":
    main()
