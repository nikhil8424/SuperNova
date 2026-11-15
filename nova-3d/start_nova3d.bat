@echo off
title NOVA 3D - AI 3D Reconstruction Platform
cd /d "%~dp0"
echo ========================================================
echo               NOVA 3D - LAUNCH PLATFORM
echo         Reconstruct Reality. Explore Beyond.
echo ========================================================
echo.
echo Starting Streamlit Interface and FastAPI Backend...
python run.py --mode both
pause
