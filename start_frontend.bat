@echo off
REM EY PPT Generator - Streamlit Frontend Launcher
REM This script launches the Streamlit web interface

echo ========================================
echo   EY Presentation Generator
echo   Streamlit Web Interface
echo ========================================
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Using system Python.
)

echo [INFO] Starting Streamlit application...
echo [INFO] The app will open in your default browser
echo [INFO] Press Ctrl+C to stop the server
echo.

streamlit run streamlit_app.py

pause
