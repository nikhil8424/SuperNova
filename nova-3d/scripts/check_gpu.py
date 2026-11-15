"""
NOVA 3D - Standalone GPU Verification Tool
Checks NVIDIA driver, VRAM, and PyTorch CUDA tensor acceleration.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.hardware import get_nvidia_gpu_info, get_pytorch_info

def main():
    print("=" * 60)
    print("        NOVA 3D - GPU & ACCELERATION DIAGNOSTICS")
    print("=" * 60)

    gpu = get_nvidia_gpu_info()
    if gpu["available"]:
        print(f"[+] NVIDIA GPU Detected:       {gpu['name']}")
        print(f"[+] Dedicated VRAM:            {gpu['vram_total_mb']} MB ({gpu['vram_total_mb'] / 1024:.2f} GB)")
        print(f"[+] Driver Version:            {gpu['driver_version']}")
        print(f"[+] Driver Supported CUDA:     {gpu['cuda_version_supported']}")
    else:
        print("[-] Dedicated NVIDIA GPU not detected via nvidia-smi.")

    torch_info = get_pytorch_info()
    print("-" * 60)
    print(f"[+] PyTorch Version:           {torch_info['version']}")
    print(f"[+] PyTorch CUDA Available:    {torch_info['cuda_available']}")
    print(f"[+] Active Torch Device:       {torch_info['torch_device']}")

    print("=" * 60)
    if gpu["available"] and gpu["vram_total_mb"] < 6000:
        print("[!] RESOURCE NOTICE: System has 4GB VRAM. NOVA 3D will")
        print("    automatically apply resource-aware image and batch presets.")
    print("=" * 60)

if __name__ == "__main__":
    main()
