#!/bin/bash
# Setup script for Vehicle Detection System on Raspberry Pi 5

echo "=========================================="
echo "Vehicle Detection System - Setup Script"
echo "=========================================="
echo ""

# Update system
echo "[1/6] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "[2/6] Installing system dependencies..."
sudo apt-get install -y \
    libcamera-dev \
    libcamera-apps \
    python3-picamera2 \
    python3-opencv \
    libopencv-dev \
    python3-pip \
    python3-venv \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libtiff5-dev \
    libjpeg-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libdc1394-22-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev

# Create virtual environment
echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "[4/6] Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install PyTorch (CPU version for Raspberry Pi)
echo "[5/6] Installing PyTorch (CPU version)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
echo "[6/6] Installing Python packages..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To download the YOLO model, run:"
echo "  python3 -c \"from ultralytics import YOLO; YOLO('yolov8n.pt')\""
echo ""
echo "To test the detector with webcam:"
echo "  python3 vehicle_detector.py --source 0"
echo ""
echo "To test with a video file:"
echo "  python3 vehicle_detector.py --source /path/to/video.mp4"
echo ""
