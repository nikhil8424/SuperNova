"""
NOVA 3D - Automatic Hardware Detection & Telemetry
Detects OS, CPU, RAM, NVIDIA GPU, VRAM, CUDA capabilities, PyTorch version, and storage.
Provides resource-aware presets and warnings.
"""
import platform
import subprocess
import shutil
import psutil
from typing import Dict, Any, Optional
from app.core.logging import logger

def get_cpu_info() -> Dict[str, Any]:
    return {
        "processor": platform.processor(),
        "architecture": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False) or 1,
        "logical_cores": psutil.cpu_count(logical=True) or 1,
        "cpu_percent": psutil.cpu_percent(interval=0.1)
    }

def get_ram_info() -> Dict[str, Any]:
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent": mem.percent
    }

def get_disk_info(path: str = ".") -> Dict[str, Any]:
    disk = psutil.disk_usage(path)
    return {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "free_gb": round(disk.free / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "percent": disk.percent
    }

def get_nvidia_gpu_info() -> Dict[str, Any]:
    """Detects NVIDIA GPU details using nvidia-smi if available."""
    gpu_info = {
        "available": False,
        "name": "N/A",
        "vram_total_mb": 0,
        "vram_used_mb": 0,
        "vram_free_mb": 0,
        "driver_version": "N/A",
        "cuda_version_supported": "N/A",
        "temperature_c": None,
        "gpu_utilization_percent": None
    }

    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return gpu_info

    try:
        # Query query-gpu fields
        query_cmd = [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu",
            "--format=csv,noheader,nounits"
        ]
        result = subprocess.run(
            query_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpu_info["available"] = True
                gpu_info["name"] = parts[0]
                gpu_info["driver_version"] = parts[1]
                gpu_info["vram_total_mb"] = int(float(parts[2]))
                gpu_info["vram_used_mb"] = int(float(parts[3]))
                gpu_info["vram_free_mb"] = int(float(parts[4]))
                if len(parts) >= 7:
                    try:
                        gpu_info["temperature_c"] = float(parts[5])
                        gpu_info["gpu_utilization_percent"] = float(parts[6])
                    except (ValueError, IndexError):
                        pass

        # Check CUDA version line from standard nvidia-smi header
        header_cmd = ["nvidia-smi"]
        h_res = subprocess.run(header_cmd, stdout=subprocess.PIPE, text=True, timeout=5)
        if "CUDA Version:" in h_res.stdout:
            parts = h_res.stdout.split("CUDA Version:")[1].split()[0]
            gpu_info["cuda_version_supported"] = parts.strip()
    except Exception as e:
        logger.warning(f"Error querying nvidia-smi: {e}")

    return gpu_info

def get_pytorch_info() -> Dict[str, Any]:
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
        cuda_build = torch.version.cuda if hasattr(torch.version, 'cuda') else None
        return {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": cuda_avail,
            "cuda_runtime_version": cuda_build,
            "torch_device": device_name
        }
    except ImportError:
        return {
            "installed": False,
            "version": None,
            "cuda_available": False,
            "cuda_runtime_version": None,
            "torch_device": "None"
        }

def get_system_hardware_profile() -> Dict[str, Any]:
    """Aggregates comprehensive hardware telemetry with resource warnings."""
    cpu = get_cpu_info()
    ram = get_ram_info()
    disk = get_disk_info()
    gpu = get_nvidia_gpu_info()
    pytorch = get_pytorch_info()

    # Recommendations & warnings
    warnings = []
    recommendations = []

    if gpu["available"]:
        vram_gb = gpu["vram_total_mb"] / 1024.0
        if vram_gb < 6.0:
            warnings.append(
                f"GPU VRAM is {vram_gb:.1f} GB (below 6 GB recommended for full-res Gaussian Splatting). "
                "Resource-aware profile will be activated: max image dim 1200px, reduced batch size and iterations."
            )
            recommendations.append("Use Resource-Aware reconstruction settings or cloud GPU for complex 30k-iteration scenes.")
    else:
        warnings.append("No dedicated NVIDIA GPU detected or nvidia-smi unavailable. Reconstruction will fall back to CPU modes.")
        recommendations.append("CPU reconstruction is suitable for sparse SfM and mesh inspection. GPU is required for fast Splat training.")

    if ram["total_gb"] < 12.0:
        warnings.append(f"System RAM is {ram['total_gb']} GB (16 GB recommended). Limit extracted frame count to avoid out-of-memory.")

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "platform": platform.platform(),
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "gpu": gpu,
        "pytorch": pytorch,
        "warnings": warnings,
        "recommendations": recommendations,
        "resource_mode": "Resource-Aware (Reduced VRAM)" if (gpu["available"] and gpu["vram_total_mb"] < 6000) else "Standard Performance"
    }
