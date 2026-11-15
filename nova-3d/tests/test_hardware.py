"""
Unit tests for Hardware Detection & Telemetry
"""
from app.core.hardware import (
    get_cpu_info,
    get_ram_info,
    get_disk_info,
    get_nvidia_gpu_info,
    get_pytorch_info,
    get_system_hardware_profile
)

def test_hardware_queries():
    cpu = get_cpu_info()
    assert cpu["logical_cores"] >= 1
    assert "cpu_percent" in cpu

    ram = get_ram_info()
    assert ram["total_gb"] > 0
    assert 0 <= ram["percent"] <= 100

    disk = get_disk_info()
    assert disk["total_gb"] > 0

    pytorch = get_pytorch_info()
    assert pytorch["installed"] is True

    profile = get_system_hardware_profile()
    assert "os" in profile
    assert "resource_mode" in profile
