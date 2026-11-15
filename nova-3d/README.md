# NOVA 3D — AI-Powered 3D Reconstruction & Interactive Exploration Platform

> **Reconstruct Reality. Explore Beyond.**

NOVA 3D is a unified, production-quality Python platform that transforms ordinary smartphone videos into explorable 3D representations of real-world environments and objects, inspects structured 3D CAD/mechanical models at the component level with exploded views, and enables hands-free viewer control via optical hand tracking.

---

## Key Highlights

- **100% Python-First Architecture:** Backend, frontend, computer vision, 3D reconstruction, machine exploration, and gesture tracking are completely driven in Python. No separate JavaScript, Node, or React build step required.
- **Two Integrated 3D Representations:**
  1. *Gaussian Splatting & Sparse Points:* Photorealistic scene reconstruction from monocular video sequences.
  2. *Structured 3D Meshes:* GLB/GLTF product and machine assemblies with component-level selection, isolation, and exploded-view animations.
- **Computer Vision Pipeline:** OpenCV video frame sampling, Laplacian blur detection, exposure analysis, and histogram duplicate filtering.
- **Structure from Motion (SfM):** Direct subprocess integration of COLMAP with an automatic OpenCV SfM feature matching and triangulation fallback engine.
- **Webcam Gesture Studio:** 21-landmark hand tracking via MediaPipe supporting 9 defined gestures with confidence thresholds, cooldown timers, and temporal smoothing.
- **FastAPI REST API & Interactive UI:** Complete OpenAPI documentation at `/docs` and a futuristic dark graphite Streamlit interface.

---

## Navigation Modules (12 Full Views)

1. **Dashboard:** Live project metrics, completed jobs, asset counts, real-time CPU/RAM/VRAM/Storage telemetry.
2. **Create Project:** Set up dedicated workspaces for Environment Reconstruction, Object Reconstruction, or Machine Exploration.
3. **Environment Reconstruction:** Ingest slow walkthrough videos, configure extraction intervals, and launch reconstruction.
4. **Object Reconstruction:** Ingest multi-angle 360° captures of individual subjects.
5. **Machine Explorer:** Load GLB/GLTF assemblies, explore the hierarchical component tree, isolate parts, and adjust the exploded-view slider.
6. **Scene Viewer:** Orbit, pan, and zoom through 3D Gaussian splat point clouds, sparse SfM points, and camera trajectories.
7. **Processing Monitor:** Live background queue tracking, stage progress percentages, logs, and cancellation/retry controls.
8. **Gesture Studio:** Local camera landmark tracking, HUD overlay, 9-gesture classifier, and sensitivity calibration.
9. **Metrics & Analytics:** Structure from Motion reprojection errors, registration ratios, training metrics, and downloadable audit reports.
10. **Asset Library:** Central repository of uploaded videos, generated splats, and CAD models.
11. **Settings & Diagnostics:** Host hardware inspection, path configuration, and resource-aware preset adjustments.
12. **Documentation:** Built-in technical manual and video capture guidance.

---

## Architecture

```text
nova-3d/
├── app/
│   ├── config.py                  # System parameters, theme colors, paths
│   ├── main.py                    # FastAPI server & route registration
│   ├── api/
│   │   ├── routes/                # Projects, Assets, Jobs, Machine, Scenes, System
│   │   └── dependencies.py        # Database dependencies & security filters
│   ├── core/
│   │   ├── database.py            # SQLAlchemy engine & session factory
│   │   ├── hardware.py            # Automatic CPU/RAM/GPU telemetry & VRAM checks
│   │   ├── logging.py             # Structured system & project logger
│   │   └── security.py            # Path traversal prevention & file header validation
│   ├── models/                    # SQLAlchemy ORM models (Project, Job, Asset, Scene, Component)
│   ├── schemas/                   # Pydantic schemas for API serialization
│   ├── reconstruction/
│   │   ├── video_processor.py     # OpenCV video validation & metadata
│   │   ├── frame_extractor.py     # Sampling, resizing, blur & duplicate detection
│   │   ├── image_quality.py       # Laplacian sharpness & exposure scoring
│   │   ├── colmap_engine.py       # COLMAP wrapper + OpenCV SfM Triangulator fallback
│   │   ├── gaussian_splat_engine.py # Splatfacto dataset conversion & Gaussian primitives
│   │   └── pipeline.py            # End-to-end background orchestration
│   ├── machine/
│   │   ├── model_loader.py        # Trimesh & pygltflib scene graph inspection
│   │   ├── component_tree.py      # Hierarchy, visibility toggles, isolation
│   │   └── exploded_view.py       # Directional separation vectors & assembly restoration
│   ├── gestures/
│   │   ├── hand_tracker.py        # MediaPipe 21-landmark tracking & HUD
│   │   ├── gesture_classifier.py  # 9 gesture classification rules
│   │   ├── gesture_mapper.py      # Viewer action definitions
│   │   └── calibration.py         # Temporal smoothing buffer & cooldown timers
│   ├── workers/
│   │   └── local_worker.py        # Multithreaded asynchronous background job queue
│   └── ui/                        # Complete Streamlit UI design system
│       ├── app.py                 # Sidebar navigation router
│       ├── dashboard.py           # Real-time telemetry & quick launch
│       ├── machine_explorer.py    # Exploded view & CAD inspection
│       ├── scene_viewer.py        # WebGL 3D point cloud & Gaussian viewer
│       ├── gesture_studio.py      # Camera landmark studio
│       └── ...
├── data/
│   ├── projects/                  # Isolated project directories
│   ├── samples/                   # Pre-calibrated engine_assembly.glb & walkthrough.mp4
│   └── logs/                      # System log files
├── tests/                         # 24 automated pytest tests
├── scripts/                       # GPU and dependency diagnostic tools
├── requirements.txt               # Pinned verified dependencies
└── run.py                         # Master unified launcher
```

---

## Installation & Setup

### 1. Requirements
- Python 3.11+
- Windows 11, Linux, or macOS
- Dedicated NVIDIA GPU (recommended for fast training; CPU fallback is included)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Hardware & Subsystems
```bash
python scripts/check_gpu.py
python scripts/check_dependencies.py
```

### 4. Run Automated Test Suite
```bash
python -m pytest tests -v
```

---

## Running NOVA 3D

Launch the full platform using `run.py`:

```bash
# Launch Streamlit Interface (Default)
python run.py

# Launch both Streamlit UI and FastAPI Backend concurrently
python run.py --mode both

# Launch only FastAPI Backend
python run.py --mode api
```

- **Web Interface:** [http://localhost:8501](http://localhost:8501)
- **FastAPI OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Gesture Interaction Reference

| Gesture | Mapped Action | Target |
|---|---|---|
| **Open Palm** | Pause / neutralize interaction | Viewer |
| **Index Pointing** | Hover / focus 3D component | Raycaster |
| **Pinch** | Select / grab component | Component |
| **Horizontal Movement** | Rotate camera orbit | Camera |
| **Vertical Movement** | Adjust camera elevation | Camera |
| **Two-Hand Spread** | Zoom in closer | Camera |
| **Two-Hand Contraction**| Zoom out | Camera |
| **Closed Fist** | Release selection / pause | Viewer |
| **Swipe** | Cycle next part or viewpoint | Navigation |

*Mouse and keyboard alternatives are permanently available across all viewers.*

---

## Quality Evaluation Protocol

In accordance with rigorous computer vision methodology:
- **PSNR** and **SSIM** are only presented when verified reference ground-truth images and an aligned evaluation trajectory are provided.
- For casual smartphone videos, **Mean Reprojection Error (pixels)** and **Registration Ratio (%)** serve as the primary geometric evaluation metrics.

---

## License

Proprietary engineering blueprint and software — NOVA 3D Team.
