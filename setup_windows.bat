@echo off
REM Setup script for Vehicle Detection System on Windows

echo ==========================================
echo Vehicle Detection System - Setup Script
echo ==========================================
echo.

REM Check for Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    exit /b 1
)
echo OK: Python found

REM Create virtual environment
echo [2/4] Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Created virtual environment
)

REM Activate and install packages
echo [3/4] Activating environment and installing packages...
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip wheel setuptools

REM Install PyTorch CPU version (faster on edge devices)
echo [4/4] Installing PyTorch and dependencies...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install other requirements
pip install -r requirements.txt

echo.
echo ==========================================
echo Setup complete!
echo ==========================================
echo.
echo To activate the environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To download the YOLO model, run:
echo   python vehicle_detector.py --help
echo.
echo To test the detector:
echo   python test_detector.py
echo.
echo To run with webcam:
echo   python vehicle_detector.py --source 0
echo.
echo To run with video file:
echo   python vehicle_detector.py --source video.mp4
echo.

pause
