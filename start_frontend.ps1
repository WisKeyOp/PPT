# EY PPT Generator - Streamlit Frontend Launcher (PowerShell)
# This script launches the Streamlit web interface

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  EY Presentation Generator" -ForegroundColor Yellow
Write-Host "  Streamlit Web Interface" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "[WARNING] Virtual environment not found. Using system Python." -ForegroundColor Yellow
}

Write-Host "[INFO] Starting Streamlit application..." -ForegroundColor Green
Write-Host "[INFO] The app will open in your default browser" -ForegroundColor Cyan
Write-Host "[INFO] Access at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "[INFO] Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Launch Streamlit
streamlit run streamlit_app.py

Write-Host ""
Write-Host "[INFO] Streamlit server stopped." -ForegroundColor Yellow
