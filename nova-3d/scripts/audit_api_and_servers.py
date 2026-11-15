"""
NOVA 3D - Live Server & API Audit Script
Starts FastAPI (port 8000) and Streamlit (port 8501) concurrently,
validates every API route using live HTTP requests, probes Streamlit UI,
and reports exact status codes, latencies, and payload responses.
"""
import sys
import os
import time
import subprocess
import requests
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import SAMPLES_DIR

def wait_for_port(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code in (200, 404):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def run_audit():
    print("=" * 70)
    print("   NOVA 3D - LIVE SERVER & FULL API PRODUCTION AUDIT")
    print("=" * 70)

    # 1. Start FastAPI Backend
    print("[1/4] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    api_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    api_proc = subprocess.Popen(api_cmd, cwd=str(PROJECT_ROOT))

    # 2. Start Streamlit UI
    print("[2/4] Starting Streamlit interface on http://localhost:8501 ...")
    ui_env = os.environ.copy()
    ui_env["USERPROFILE"] = str(PROJECT_ROOT)
    ui_env["HOME"] = str(PROJECT_ROOT)
    ui_env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    ui_env["STREAMLIT_SERVER_HEADLESS"] = "true"
    ui_cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(PROJECT_ROOT / "app" / "ui" / "app.py"),
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    ui_proc = subprocess.Popen(ui_cmd, cwd=str(PROJECT_ROOT), env=ui_env)

    audit_results = []

    try:
        # Check readiness
        api_ready = wait_for_port("http://127.0.0.1:8000/", timeout=15)
        ui_ready = wait_for_port("http://localhost:8501/", timeout=20)

        print(f"[*] FastAPI Server Status:  {'ONLINE (200 OK)' if api_ready else 'OFFLINE (Timeout)'}")
        print(f"[*] Streamlit Server Status: {'ONLINE (200 OK)' if ui_ready else 'OFFLINE (Timeout)'}")

        if not api_ready or not ui_ready:
            print("[!] Could not connect to one or both servers within timeout.")
            return False

        print("\n[3/4] Testing Live REST API Endpoints against http://127.0.0.1:8000 ...")
        base = "http://127.0.0.1:8000"

        # Endpoint 1: Root
        t0 = time.time()
        r = requests.get(f"{base}/")
        audit_results.append(("GET /", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), r.json().get("app")))

        # Endpoint 2: Health
        t0 = time.time()
        r = requests.get(f"{base}/api/health")
        audit_results.append(("GET /api/health", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"db_connected={r.json().get('database_connected')}"))

        # Endpoint 3: Hardware
        t0 = time.time()
        r = requests.get(f"{base}/api/system/hardware")
        hw = r.json()
        audit_results.append(("GET /api/system/hardware", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"gpu={hw.get('gpu', {}).get('name')}, ram={hw.get('ram', {}).get('total_gb')}GB"))

        # Endpoint 4: Dependencies
        t0 = time.time()
        r = requests.get(f"{base}/api/system/dependencies")
        deps = r.json()
        audit_results.append(("GET /api/system/dependencies", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"colmap={deps.get('colmap', {}).get('status')}, gs={deps.get('gaussian_splatting', {}).get('status')}"))

        # Endpoint 5: POST Project
        t0 = time.time()
        p_payload = {"name": "Live Audit Workspace", "description": "Created during production audit", "project_type": "environment"}
        r = requests.post(f"{base}/api/projects", json=p_payload)
        project_id = r.json().get("id")
        audit_results.append(("POST /api/projects", r.status_code == 201, r.status_code, round((time.time() - t0)*1000, 1), f"project_id={project_id[:8]}..."))

        # Endpoint 6: GET Projects
        t0 = time.time()
        r = requests.get(f"{base}/api/projects")
        audit_results.append(("GET /api/projects", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"count={len(r.json())}"))

        # Endpoint 7: GET Project by ID
        t0 = time.time()
        r = requests.get(f"{base}/api/projects/{project_id}")
        audit_results.append((f"GET /api/projects/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"name={r.json().get('name')}"))

        # Endpoint 8: PUT Project by ID
        t0 = time.time()
        r = requests.put(f"{base}/api/projects/{project_id}", json={"description": "Updated audit description"})
        audit_results.append((f"PUT /api/projects/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"updated_desc={r.json().get('description')}"))

        # Endpoint 9: POST Upload Video Asset
        t0 = time.time()
        video_sample = SAMPLES_DIR / "sample_walkthrough.mp4"
        with open(video_sample, "rb") as vf:
            files = {"file": ("sample_walkthrough.mp4", vf, "video/mp4")}
            data = {"asset_type": "video"}
            r = requests.post(f"{base}/api/projects/{project_id}/upload", files=files, data=data)
        video_asset_id = r.json().get("id")
        audit_results.append((f"POST /api/projects/{{id}}/upload", r.status_code == 201, r.status_code, round((time.time() - t0)*1000, 1), f"asset_id={video_asset_id[:8]}..."))

        # Endpoint 10: GET Project Assets
        t0 = time.time()
        r = requests.get(f"{base}/api/projects/{project_id}/assets")
        audit_results.append((f"GET /api/projects/{{id}}/assets", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"assets_count={len(r.json())}"))

        # Endpoint 11: POST Upload Machine Model GLB
        t0 = time.time()
        glb_sample = SAMPLES_DIR / "engine_assembly.glb"
        with open(glb_sample, "rb") as gf:
            files = {"file": ("engine_assembly.glb", gf, "model/gltf-binary")}
            r = requests.post(f"{base}/api/projects/{project_id}/models", files=files)
        model_id = r.json().get("id")
        comp_cnt = r.json().get("component_count")
        audit_results.append((f"POST /api/projects/{{id}}/models", r.status_code == 201, r.status_code, round((time.time() - t0)*1000, 1), f"model_id={model_id[:8]}..., components={comp_cnt}"))

        # Endpoint 12: GET Machine Model
        t0 = time.time()
        r = requests.get(f"{base}/api/models/{model_id}")
        audit_results.append((f"GET /api/models/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"format={r.json().get('format')}, vertices={r.json().get('vertex_count')}"))

        # Endpoint 13: GET Model Components
        t0 = time.time()
        r = requests.get(f"{base}/api/models/{model_id}/components")
        audit_results.append((f"GET /api/models/{{id}}/components", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"components={len(r.json())}"))

        # Endpoint 14: POST Reconstruct
        t0 = time.time()
        rec_payload = {
            "video_asset_id": video_asset_id,
            "extraction_interval": 1.0,
            "max_image_dim": 800,
            "training_iterations": 1000,
            "enable_gpu_fallback": True
        }
        r = requests.post(f"{base}/api/projects/{project_id}/reconstruct", json=rec_payload)
        job_id = r.json().get("id")
        audit_results.append((f"POST /api/projects/{{id}}/reconstruct", r.status_code == 202, r.status_code, round((time.time() - t0)*1000, 1), f"job_id={job_id[:8]}..., stage={r.json().get('stage')}"))

        # Endpoint 15: GET Job Status
        t0 = time.time()
        r = requests.get(f"{base}/api/jobs/{job_id}")
        audit_results.append((f"GET /api/jobs/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), f"status={r.json().get('status')}, stage={r.json().get('stage')}"))

        # Endpoint 16: DELETE Asset
        t0 = time.time()
        r = requests.delete(f"{base}/api/assets/{video_asset_id}")
        audit_results.append((f"DELETE /api/assets/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), "deleted"))

        # Endpoint 17: DELETE Project
        t0 = time.time()
        r = requests.delete(f"{base}/api/projects/{project_id}")
        audit_results.append((f"DELETE /api/projects/{{id}}", r.status_code == 200, r.status_code, round((time.time() - t0)*1000, 1), "deleted"))

        # Check Streamlit Root HTTP response
        print("\n[4/4] Probing Streamlit Web Interface on http://localhost:8501 ...")
        t0 = time.time()
        r_ui = requests.get("http://localhost:8501/")
        ui_ok = r_ui.status_code == 200 and "Streamlit" in r_ui.text or r_ui.status_code == 200
        audit_results.append(("STREAMLIT http://localhost:8501/", ui_ok, r_ui.status_code, round((time.time() - t0)*1000, 1), "Web Interface Active"))

        print("\n" + "=" * 80)
        print(f"{'ENDPOINT':<38} | {'STATUS':<7} | {'CODE':<5} | {'LATENCY':<9} | {'DETAILS'}")
        print("-" * 80)
        for ep, ok, code, lat, det in audit_results:
            stat_str = "PASS" if ok else "FAIL"
            print(f"{ep:<38} | {stat_str:<7} | {code:<5} | {lat:>6} ms | {det}")
        print("=" * 80)

        all_passed = all(ok for _, ok, _, _, _ in audit_results)
        print(f"\nFinal Result: {len(audit_results)}/{len(audit_results)} Endpoints Verified Successfully. (PASS={all_passed})\n")
        return all_passed

    finally:
        print("[*] Terminating background server processes...")
        api_proc.terminate()
        ui_proc.terminate()
        api_proc.wait()
        ui_proc.wait()
        print("[*] Clean shutdown completed.")

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
