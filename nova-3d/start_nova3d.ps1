# NOVA 3D - PowerShell Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "              NOVA 3D - LAUNCH PLATFORM" -ForegroundColor Cyan
Write-Host "        Reconstruct Reality. Explore Beyond." -ForegroundColor Magenta
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Launching Streamlit Web UI and FastAPI Backend..." -ForegroundColor Yellow

python run.py --mode both
