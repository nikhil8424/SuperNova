"""
Unit tests for Security & Input Validation
"""
from pathlib import Path
from app.core.security import (
    validate_file_upload,
    generate_secure_filename,
    sanitize_filename,
    validate_safe_path
)

def test_sanitize_filename():
    unsafe = "../../../etc/passwd"
    clean = sanitize_filename(unsafe)
    assert "/" not in clean
    assert "\\" not in clean
    assert "passwd" in clean

def test_generate_secure_filename():
    orig = "my_video.mp4"
    sec = generate_secure_filename(orig, prefix="vid")
    assert sec.startswith("vid_")
    assert sec.endswith(".mp4")
    assert len(sec) > 10

def test_validate_safe_path(temp_dir):
    base = temp_dir / "base"
    base.mkdir()
    child = base / "project" / "file.txt"
    outside = temp_dir / "other" / "file.txt"

    assert validate_safe_path(child, base_dir=base) is True
    assert validate_safe_path(outside, base_dir=base) is False

def test_validate_file_upload():
    # Empty file
    valid, msg = validate_file_upload(b"", "test.mp4", "video")
    assert valid is False

    # Disallowed extension
    valid, msg = validate_file_upload(b"testcontent", "malicious.exe", "video")
    assert valid is False

    # Valid glb header
    valid_glb_bytes = b"glTF" + b"\x00" * 40
    valid, msg = validate_file_upload(valid_glb_bytes, "model.glb", "model")
    assert valid is True
