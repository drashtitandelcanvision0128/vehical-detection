"""
Vehicle Detection Web Testing App (Flask)
Simple web interface for testing vehicle detection on images/videos
"""

from flask import Flask, render_template_string, request, send_file, flash, redirect
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import os
import time
from pathlib import Path
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'vehicle-detection-secret-key'

# Increase max upload size to 500MB for large video uploads
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Create static directory for processed videos
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'videos')
os.makedirs(STATIC_DIR, exist_ok=True)
print(f"[INFO] Video output directory: {STATIC_DIR}")

# Vehicle-only classes from COCO dataset
VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',  # Includes bikes, scooters, scooty
    5: 'bus',
    7: 'truck'
}

# Colors for each vehicle class (BGR for OpenCV)
CLASS_COLORS = {
    'car': (0, 255, 0),           # Green
    'motorcycle': (255, 0, 255),  # Magenta (includes bikes, scooty)
    'bus': (0, 255, 255),         # Yellow
    'truck': (0, 0, 255)          # Red
}

# Display names for UI (with scooty included)
DISPLAY_NAMES = {
    'car': 'Car',
    'motorcycle': 'Motorcycle/Scooty',
    'bus': 'Bus',
    'truck': 'Truck'
}

# Check ffmpeg availability
print("[INFO] Checking ffmpeg availability...")
try:
    import subprocess
    ffmpeg_result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if ffmpeg_result.returncode == 0:
        print("[SUCCESS] ffmpeg found - videos will be converted to H264 for browser playback")
    else:
        print("[WARN] ffmpeg not available - videos may not play in browser (only download)")
        print("[INFO] To fix: Install ffmpeg and add to PATH")
except FileNotFoundError:
    print("[WARN] ffmpeg not found - videos may not play in browser (only download)")
    print("[INFO] To fix: Install ffmpeg and add to PATH")
except Exception as e:
    print(f"[WARN] Could not check ffmpeg: {e}")

# Load model
print("[INFO] Loading YOLOv8n model...")
model = YOLO('yolov8n.pt')
print("[INFO] Model ready!")

# HTML Template - English Only, No Emojis, With Clipboard Paste Support
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection Testing App</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; text-align: center; }
        h3 { color: #555; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .upload-section { margin: 20px 0; padding: 20px; border: 2px dashed #ccc; border-radius: 5px; text-align: center; }
        .upload-section:hover { border-color: #4CAF50; }
        .paste-section { margin: 20px 0; padding: 20px; border: 2px dashed #2196F3; border-radius: 5px; text-align: center; background: #f0f8ff; }
        .paste-section:hover { border-color: #1976D2; background: #e3f2fd; }
        input[type="file"] { margin: 10px 0; }
        input[type="submit"] { 
            background: #4CAF50; color: white; padding: 12px 30px; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
        }
        input[type="submit"]:hover { background: #45a049; }
        .btn-paste { 
            background: #2196F3; color: white; padding: 12px 30px; 
            border: none; border-radius: 5px; cursor: pointer; font-size: 16px;
            margin: 5px;
        }
        .btn-paste:hover { background: #1976D2; }
        .result { margin-top: 30px; padding: 20px; background: #f9f9f9; border-radius: 5px; }
        .success { color: #4CAF50; font-weight: bold; }
        .error { color: #f44336; font-weight: bold; }
        .stats { margin: 15px 0; padding: 15px; background: white; border-left: 4px solid #4CAF50; }
        img { max-width: 100%; height: auto; border-radius: 5px; }
        .class-info { margin: 10px 0; padding: 10px; background: #e8f5e9; border-radius: 3px; }
        .conf-slider { margin: 15px 0; }
        .conf-slider label { display: block; margin-bottom: 5px; }
        .conf-slider input { width: 200px; }
        .preview-box { max-width: 100%; max-height: 300px; margin: 10px 0; display: none; }
        .instructions { color: #666; font-size: 14px; margin: 10px 0; }
        @keyframes loading {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(0%); }
            100% { transform: translateX(100%); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vehicle Detection Testing App</h1>
        <p style="text-align: center; color: #666;">Upload or paste an image to detect vehicles</p>
        
        <div class="class-info">
            <strong>Detects only:</strong> Car (Green), Motorcycle/Scooty (Magenta), Bus (Yellow), Truck (Red)<br>
            <strong>Ignores:</strong> People, animals, buildings, and other objects
        </div>
        
        <!-- Upload Section with Drag & Drop, Copy/Paste Option -->
        <div class="upload-section" id="dropZone" style="transition: all 0.3s;">
            <h3>Upload Image or Video</h3>
            
            <!-- Drag & Drop Zone -->
            <div id="dragDropArea" style="border: 3px dashed #ccc; border-radius: 10px; padding: 40px 20px; margin: 15px 0; background: #fafafa; cursor: pointer;">
                <p style="font-size: 18px; color: #666; margin: 0;">
                    <strong>Drag & Drop</strong> files here<br>
                    <span style="font-size: 14px;">or click to browse</span>
                </p>
                <p style="font-size: 12px; color: #999; margin-top: 10px;">
                    Supports: JPG, PNG, MP4, AVI, MOV
                </p>
            </div>
            
            <form action="/" method="POST" enctype="multipart/form-data" id="uploadForm">
                <input type="file" name="file" id="fileInput" accept=".jpg,.jpeg,.png,.mp4,.avi,.mov" style="display: none;">
                <input type="hidden" name="pasted_image" id="pastedImageData">
                
                <!-- Selected file display -->
                <div id="selectedFileDisplay" style="display: none; margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 5px; color: #1976D2;">
                    <strong>Selected:</strong> <span id="fileName"></span>
                </div>
                
                <!-- OR Divider -->
                <div style="margin: 15px 0; color: #666;">- OR -</div>
                
                <!-- Copy/Paste Button -->
                <button type="button" class="btn-paste" id="copyPasteBtn" onclick="enablePasteMode()">
                    Copy to Dashboard (Paste Image)
                </button>
                <p id="pasteInstructions" style="color: #2196F3; font-size: 14px; display: none; margin-top: 10px;">
                    Paste mode active! Press Ctrl+V to paste image from clipboard
                </p>
                
                <br>
                
                <!-- Webcam Button -->
                <button type="button" class="btn-paste" id="webcamBtn" onclick="startWebcam()" style="background: #9C27B0;">
                    Start Webcam (Live Detection)
                </button>
                <p id="webcamInstructions" style="color: #9C27B0; font-size: 14px; display: none; margin-top: 10px;">
                    Webcam active! Close this tab or click Stop to end detection
                </p>
                
                <br><br>
                <div class="conf-slider">
                    <label>Confidence Threshold: <span id="confValue">0.4</span></label>
                    <input type="range" name="confidence" min="0.1" max="1.0" step="0.05" value="0.4" 
                           oninput="document.getElementById('confValue').textContent = this.value">
                </div>
                <br>
                <input type="submit" value="Detect Vehicles" id="detectBtn">
                <div id="loadingIndicator" style="display: none; margin-top: 15px; padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">
                    <span style="color: #856404;">
                        <strong>Processing...</strong> Please wait while we detect vehicles.<br>
                        <small>For videos, this may take a while depending on length.</small>
                    </span>
                    <div style="margin-top: 10px;">
                        <div style="width: 100%; height: 4px; background: #ddd; border-radius: 2px; overflow: hidden;">
                            <div style="width: 50%; height: 100%; background: #ffc107; animation: loading 1s infinite ease-in-out;"></div>
                        </div>
                    </div>
                </div>
            </form>
            
            <!-- Pasted Image Preview (inside upload section) -->
            <div id="pastePreviewContainer" style="display: none; margin-top: 20px; padding: 10px; border: 2px solid #4CAF50; border-radius: 5px;">
                <p style="color: #4CAF50; font-weight: bold; margin-bottom: 10px;">Image ready for detection:</p>
                <img id="pastedPreview" style="max-width: 100%; max-height: 300px; border-radius: 5px;" alt="Pasted image preview">
                <button type="button" onclick="clearPastedImage()" style="margin-top: 10px; background: #f44336; color: white; padding: 5px 15px; border: none; border-radius: 3px; cursor: pointer;">
                    Clear Image
                </button>
            </div>
        </div>
        
        <!-- Webcam Section -->
        <div id="webcamSection" style="display: none; margin: 20px 0; padding: 20px; border: 2px solid #9C27B0; border-radius: 5px; background: #f3e5f5;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <h3 style="color: #9C27B0; margin: 0;">Live Webcam Detection</h3>
                    <!-- Status Badge -->
                    <div id="detectionStatusBadge" style="padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; background: #FFC107; color: #333;">
                        Waiting...
                    </div>
                </div>
                <button type="button" onclick="stopWebcam()" style="background: #f44336; color: white; padding: 8px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                    Stop Webcam
                </button>
            </div>
            
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <!-- Original Webcam Feed -->
                <div style="flex: 1; min-width: 300px;">
                    <p style="color: #666; font-weight: bold; margin-bottom: 5px;">Original Feed:</p>
                    <video id="webcamVideo" autoplay playsinline style="width: 100%; max-width: 640px; border-radius: 5px; background: #000;"></video>
                </div>
                
                <!-- Detection Output -->
                <div style="flex: 1; min-width: 300px;">
                    <p style="color: #666; font-weight: bold; margin-bottom: 5px;">Detection Output:</p>
                    <canvas id="detectionCanvas" style="width: 100%; max-width: 640px; border-radius: 5px; background: #000;"></canvas>
                </div>
            </div>
            
            <!-- Webcam Stats - Enhanced with visual feedback -->
            <div id="webcamStats" style="margin-top: 15px; padding: 15px; background: white; border-radius: 5px; border-left: 5px solid #9C27B0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <strong style="color: #333;">Detection Status:</strong> 
                        <span id="webcamStatsText" style="color: #666; font-size: 16px;">Waiting for frames...</span>
                    </div>
                    <div id="detectionActivity" style="padding: 8px 15px; border-radius: 5px; font-weight: bold; background: #f5f5f5; color: #666;">
                        No vehicles detected
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 13px; color: #999;">
                    <strong>Tip:</strong> Point camera at vehicles to see detection boxes. Green boxes = detected vehicles.
                </div>
            </div>
        </div>
        
        
        {% if result %}
        <div class="result">
            <h3>Detection Result</h3>
            <p class="{{ 'success' if result.success else 'error' }}">{{ result.message }}</p>
            
            {% if result.stats %}
            <div class="stats">
                <strong>Processing Time:</strong> {{ result.stats.time }}<br>
                <strong>Vehicles Detected:</strong> {{ result.stats.count }}<br>
                {% if result.stats.breakdown %}
                <strong>Breakdown:</strong><br>
                {% for class_name, count in result.stats.breakdown.items() %}
                &nbsp;&nbsp;- {% if class_name == 'motorcycle' %}Motorcycle/Scooty{% else %}{{ class_name|title }}{% endif %}: {{ count }}<br>
                {% endfor %}
                {% endif %}
            </div>
            {% endif %}
            
            {% if result.image %}
            <h4>Processed Image:</h4>
            <img src="data:image/jpeg;base64,{{ result.image }}" alt="Detection Result">
            {% endif %}
            
            {% if result.video_path %}
            <h4>Video Detection Result:</h4>
            
            <!-- Video Stats -->
            {% if result.stats %}
            <div class="stats" style="margin-bottom: 15px;">
                <strong>Processing Time:</strong> {{ result.stats.time }}<br>
                <strong>Total Vehicles:</strong> {{ result.stats.count }}<br>
                {% if result.stats.breakdown %}
                <strong>Breakdown:</strong><br>
                {% for class_name, count in result.stats.breakdown.items() %}
                &nbsp;&nbsp;- {% if class_name == 'motorcycle' %}Motorcycle/Scooty{% else %}{{ class_name|title }}{% endif %}: {{ count }}<br>
                {% endfor %}
                {% endif %}
            </div>
            {% endif %}
            
            <!-- First Frame Preview (Large and Prominent) -->
            {% if result.stats and result.stats.first_frame %}
            <div style="margin-bottom: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px; border: 2px solid #4CAF50;">
                <p style="color: #2E7D32; font-weight: bold; font-size: 16px; margin-bottom: 10px; text-align: center;">
                    Detection Preview - First Frame
                </p>
                <img src="data:image/jpeg;base64,{{ result.stats.first_frame }}" 
                     style="max-width: 100%; max-height: 500px; border-radius: 5px; display: block; margin: 0 auto;"
                     alt="Video First Frame with Detections">
                <p style="color: #666; font-size: 13px; margin-top: 10px; text-align: center;">
                    This shows the first frame with vehicle detection boxes
                </p>
            </div>
            {% endif %}
            
            <!-- Video Player (Simple HTML5 Video) -->
            <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 20px;">
                <p style="color: #fff; font-weight: bold; margin-bottom: 15px;">Full Video with Detection:</p>
                <video width="100%" height="auto" controls 
                       style="max-height: 500px; border-radius: 5px;"
                       preload="metadata">
                    <source src="/view/videos/{{ result.video_path }}?t={{ result.timestamp }}" type="video/mp4">
                    <p style="color: #fff; padding: 20px;">
                        Your browser does not support video playback.<br>
                        Use the buttons below to view or download.
                    </p>
                </video>
            </div>
            
            <!-- Action Buttons -->
            <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;">
                <a href="/view/videos/{{ result.video_path }}?t={{ result.timestamp }}" target="_blank" 
                   style="background: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Open in New Tab
                </a>
                <a href="/download/{{ result.video_path }}?t={{ result.timestamp }}" download 
                   style="background: #2196F3; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Download Video
                </a>
            </div>
            
            {% endif %}
        </div>
        {% endif %}
        
        <hr style="margin-top: 40px;">
        <p style="text-align: center; color: #666;">
            Vehicle Detection System - YOLOv8 + Flask
        </p>
    </div>
    
    <script>
        let pasteModeActive = false;
        const MAX_IMAGE_WIDTH = 1280;  // Max width for compressed images
        const MAX_IMAGE_HEIGHT = 720;  // Max height for compressed images
        const JPEG_QUALITY = 0.85;     // JPEG compression quality (0-1)
        
        // Compress image before uploading
        function compressImage(dataUrl, callback) {
            const img = new Image();
            img.onload = function() {
                let width = img.width;
                let height = img.height;
                
                // Calculate new dimensions while maintaining aspect ratio
                if (width > MAX_IMAGE_WIDTH) {
                    height = Math.round(height * (MAX_IMAGE_WIDTH / width));
                    width = MAX_IMAGE_WIDTH;
                }
                if (height > MAX_IMAGE_HEIGHT) {
                    width = Math.round(width * (MAX_IMAGE_HEIGHT / height));
                    height = MAX_IMAGE_HEIGHT;
                }
                
                // Create canvas and resize
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                // Compress to JPEG with specified quality
                const compressedDataUrl = canvas.toDataURL('image/jpeg', JPEG_QUALITY);
                
                console.log('Original size: ' + Math.round(dataUrl.length / 1024) + 'KB');
                console.log('Compressed size: ' + Math.round(compressedDataUrl.length / 1024) + 'KB');
                
                callback(compressedDataUrl);
            };
            img.src = dataUrl;
        }
        
        // Enable paste mode and auto-read clipboard when button is clicked
        async function enablePasteMode() {
            pasteModeActive = true;
            document.getElementById('copyPasteBtn').textContent = 'Reading clipboard...';
            document.getElementById('copyPasteBtn').style.background = '#FF9800';
            document.getElementById('pasteInstructions').style.display = 'block';
            document.getElementById('pasteInstructions').textContent = 'Reading image from clipboard...';
            
            try {
                // Try to read clipboard directly using Clipboard API
                const clipboardItems = await navigator.clipboard.read();
                let imageFound = false;
                
                for (const item of clipboardItems) {
                    // Look for image types
                    const imageType = item.types.find(type => type.startsWith('image/'));
                    
                    if (imageType) {
                        const blob = await item.getType(imageType);
                        const reader = new FileReader();
                        
                        reader.onload = function(event) {
                            const originalData = event.target.result;
                            
                            // Compress the image
                            compressImage(originalData, function(compressedData) {
                                // Store compressed image
                                document.getElementById('pastedImageData').value = compressedData;
                                
                                // Show preview
                                const preview = document.getElementById('pastedPreview');
                                preview.src = compressedData;
                                document.getElementById('pastePreviewContainer').style.display = 'block';
                                
                                // Clear file input
                                document.getElementById('fileInput').value = '';
                                
                                // Update button
                                document.getElementById('copyPasteBtn').textContent = 'Image Pasted - Ready to Detect';
                                document.getElementById('copyPasteBtn').style.background = '#4CAF50';
                                document.getElementById('pasteInstructions').textContent = 'Image auto-pasted! Click Detect Vehicles';
                                document.getElementById('pasteInstructions').style.color = '#4CAF50';
                            });
                        };
                        
                        reader.readAsDataURL(blob);
                        imageFound = true;
                        break;
                    }
                }
                
                if (!imageFound) {
                    // No image in clipboard, fallback to Ctrl+V mode
                    document.getElementById('copyPasteBtn').textContent = 'Paste Mode Active - Press Ctrl+V';
                    document.getElementById('copyPasteBtn').style.background = '#4CAF50';
                    document.getElementById('pasteInstructions').textContent = 'No image found in clipboard. Please copy an image first, then click again or press Ctrl+V';
                    document.getElementById('pasteInstructions').style.color = '#f44336';
                    
                    // Keep listening for paste event as fallback
                    window.focus();
                }
                
            } catch (err) {
                console.error('Clipboard API error:', err);
                // Permission denied or not supported - fallback to Ctrl+V mode
                document.getElementById('copyPasteBtn').textContent = 'Paste Mode Active - Press Ctrl+V';
                document.getElementById('copyPasteBtn').style.background = '#4CAF50';
                document.getElementById('pasteInstructions').textContent = 'Please press Ctrl+V to paste your image';
                window.focus();
            }
        }
        
        // Clear pasted image
        function clearPastedImage() {
            document.getElementById('pastedImageData').value = '';
            document.getElementById('pastedPreview').src = '';
            document.getElementById('pastePreviewContainer').style.display = 'none';
            document.getElementById('fileInput').value = '';
            
            // Reset button
            pasteModeActive = false;
            document.getElementById('copyPasteBtn').textContent = 'Copy to Dashboard (Paste Image)';
            document.getElementById('copyPasteBtn').style.background = '#2196F3';
            document.getElementById('pasteInstructions').style.display = 'none';
        }
        
        // Handle clipboard paste
        document.addEventListener('paste', function(e) {
            const items = e.clipboardData.items;
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    const reader = new FileReader();
                    
                    reader.onload = function(event) {
                        const originalData = event.target.result;
                        
                        // Compress the image
                        compressImage(originalData, function(compressedData) {
                            // Store compressed image in hidden input
                            document.getElementById('pastedImageData').value = compressedData;
                            
                            // Show preview
                            const preview = document.getElementById('pastedPreview');
                            preview.src = compressedData;
                            document.getElementById('pastePreviewContainer').style.display = 'block';
                            
                            // Clear file input since we're using pasted image
                            document.getElementById('fileInput').value = '';
                            
                            // Update button text
                            document.getElementById('copyPasteBtn').textContent = 'Image Pasted - Ready to Detect';
                            document.getElementById('copyPasteBtn').style.background = '#4CAF50';
                            document.getElementById('pasteInstructions').textContent = 'Image compressed and ready! Click "Detect Vehicles"';
                            document.getElementById('pasteInstructions').style.color = '#4CAF50';
                        });
                    };
                    
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        });
        
        // Show loading indicator
        function showLoading() {
            const fileInput = document.getElementById('fileInput');
            const pastedData = document.getElementById('pastedImageData').value;
            
            if (!fileInput.value && !pastedData) {
                alert('Please either upload a file OR click "Copy to Dashboard" and paste an image (Ctrl+V)');
                return false;
            }
            
            // Show loading indicator
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('detectBtn').disabled = true;
            document.getElementById('detectBtn').value = 'Processing...';
            
            // Allow form to submit
            return true;
        }
        
        // Handle form submission
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            const pastedData = document.getElementById('pastedImageData').value;
            
            if (!fileInput.value && !pastedData) {
                e.preventDefault();
                alert('Please either upload a file OR click "Copy to Dashboard" and paste an image (Ctrl+V)');
                return false;
            }
            
            // Show loading indicator
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('detectBtn').disabled = true;
            document.getElementById('detectBtn').value = 'Processing...';
            
            // Allow form to submit normally
            return true;
        });
        
        // Also handle paste when file input changes (clear pasted data)
        document.getElementById('fileInput').addEventListener('change', function() {
            if (this.value) {
                document.getElementById('pastedImageData').value = '';
                document.getElementById('pastePreviewContainer').style.display = 'none';
                // Show selected filename
                const fileName = this.files[0] ? this.files[0].name : '';
                document.getElementById('fileName').textContent = fileName;
                document.getElementById('selectedFileDisplay').style.display = 'block';
            }
        });
        
        // Drag and Drop functionality
        const dragDropArea = document.getElementById('dragDropArea');
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight drop zone when dragging over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            dragDropArea.style.borderColor = '#4CAF50';
            dragDropArea.style.background = '#e8f5e9';
            dragDropArea.style.transform = 'scale(1.02)';
        }
        
        function unhighlight(e) {
            dragDropArea.style.borderColor = '#ccc';
            dragDropArea.style.background = '#fafafa';
            dragDropArea.style.transform = 'scale(1)';
        }
        
        // Handle dropped files
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                const file = files[0];
                const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'video/mp4', 'video/avi', 'video/quicktime'];
                
                if (validTypes.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|mp4|avi|mov)$/i)) {
                    // Set the file to the input
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                    
                    // Show filename
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('selectedFileDisplay').style.display = 'block';
                    document.getElementById('pastedImageData').value = '';
                    document.getElementById('pastePreviewContainer').style.display = 'none';
                    
                    // Update drop zone text
                    dragDropArea.innerHTML = `
                        <p style="font-size: 18px; color: #4CAF50; margin: 0;">
                            <strong>File ready!</strong><br>
                            <span style="font-size: 14px; color: #666;">${file.name}</span>
                        </p>
                        <p style="font-size: 12px; color: #999; margin-top: 10px;">
                            Click "Detect Vehicles" to process
                        </p>
                    `;
                } else {
                    alert('Invalid file type. Please upload: JPG, PNG, MP4, AVI, or MOV');
                }
            }
        }
        
        // Click on drop zone to open file browser
        dragDropArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Webcam variables
        let webcamStream = null;
        let webcamInterval = null;
        let isWebcamRunning = false;
        
        // Start webcam
        async function startWebcam() {
            try {
                // Get user media
                webcamStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { width: 640, height: 480 } 
                });
                
                // Show webcam video element
                const webcamVideo = document.getElementById('webcamVideo');
                webcamVideo.srcObject = webcamStream;
                
                // Show webcam section
                document.getElementById('webcamSection').style.display = 'block';
                document.getElementById('webcamInstructions').style.display = 'block';
                document.getElementById('webcamBtn').textContent = 'Webcam Running...';
                document.getElementById('webcamBtn').disabled = true;
                document.getElementById('webcamBtn').style.background = '#ccc';
                
                // Hide upload section
                document.getElementById('dropZone').style.display = 'none';
                
                // Set canvas size to match video
                const detectionCanvas = document.getElementById('detectionCanvas');
                detectionCanvas.width = 640;
                detectionCanvas.height = 480;
                
                // Reset status indicators
                updateDetectionStatus('waiting', 'Initializing...');
                
                isWebcamRunning = true;
                
                // Start frame processing loop
                processWebcamFrame();
                
                console.log('[INFO] Webcam started successfully');
                
            } catch (err) {
                console.error('[ERROR] Could not start webcam:', err);
                alert('Could not access webcam. Please make sure you have granted camera permissions.');
            }
        }
        
        // Update detection status indicators
        function updateDetectionStatus(status, message) {
            const statusBadge = document.getElementById('detectionStatusBadge');
            const activityDiv = document.getElementById('detectionActivity');
            
            if (status === 'waiting') {
                statusBadge.textContent = 'Waiting...';
                statusBadge.style.background = '#FFC107';
                statusBadge.style.color = '#333';
                activityDiv.textContent = 'Initializing...';
                activityDiv.style.background = '#f5f5f5';
                activityDiv.style.color = '#666';
            } else if (status === 'processing') {
                statusBadge.textContent = 'Processing...';
                statusBadge.style.background = '#2196F3';
                statusBadge.style.color = 'white';
                activityDiv.textContent = 'Detecting...';
                activityDiv.style.background = '#e3f2fd';
                activityDiv.style.color = '#1976D2';
            } else if (status === 'detected') {
                statusBadge.textContent = 'DETECTED!';
                statusBadge.style.background = '#4CAF50';
                statusBadge.style.color = 'white';
                activityDiv.textContent = message;
                activityDiv.style.background = '#e8f5e9';
                activityDiv.style.color = '#2E7D32';
            } else if (status === 'none') {
                statusBadge.textContent = 'Scanning...';
                statusBadge.style.background = '#FF9800';
                statusBadge.style.color = 'white';
                activityDiv.textContent = 'No vehicles detected';
                activityDiv.style.background = '#fff3e0';
                activityDiv.style.color = '#E65100';
            }
        }
        
        // Process webcam frames
        async function processWebcamFrame() {
            if (!isWebcamRunning) return;
            
            const webcamVideo = document.getElementById('webcamVideo');
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            
            // Draw current frame to canvas
            ctx.drawImage(webcamVideo, 0, 0, 640, 480);
            
            // Get frame as base64
            const frameData = detectionCanvas.toDataURL('image/jpeg', 0.8);
            
            // Remove data URL prefix
            const base64Data = frameData.split(',')[1];
            const imageData = base64Data; // This is already base64
            
            // Update status to processing
            updateDetectionStatus('processing', 'Detecting...');
            
            try {
                // Send frame to server for detection
                const confThreshold = document.querySelector('input[name="confidence"]').value;
                const formData = new FormData();
                formData.append('image', frameData);
                formData.append('confidence', confThreshold);
                
                // Convert data URL to blob
                const response = await fetch('/webcam_detect', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    if (result.image) {
                        // Draw processed image to canvas
                        const img = new Image();
                        img.onload = function() {
                            ctx.drawImage(img, 0, 0, 640, 480);
                        };
                        img.src = 'data:image/jpeg;base64,' + result.image;
                        
                        // Update stats and status based on detection results
                        document.getElementById('webcamStatsText').textContent = 
                            `Vehicles: ${result.count} | ${result.breakdown || 'No detections'}`;
                        
                        if (result.count > 0) {
                            updateDetectionStatus('detected', `${result.count} vehicle(s) detected: ${result.breakdown}`);
                        } else {
                            updateDetectionStatus('none', 'No vehicles detected');
                        }
                    }
                } else {
                    console.error('[ERROR] Detection failed:', response.status);
                    updateDetectionStatus('none', 'Detection error');
                }
            } catch (err) {
                console.error('[ERROR] Frame processing error:', err);
                updateDetectionStatus('none', 'Processing error');
            }
            
            // Schedule next frame (limit to ~10 FPS to reduce server load)
            if (isWebcamRunning) {
                setTimeout(processWebcamFrame, 100);
            }
        }
        
        // Stop webcam
        function stopWebcam() {
            isWebcamRunning = false;
            
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
            }
            
            // Hide webcam section
            document.getElementById('webcamSection').style.display = 'none';
            document.getElementById('webcamInstructions').style.display = 'none';
            
            // Reset button
            document.getElementById('webcamBtn').textContent = 'Start Webcam (Live Detection)';
            document.getElementById('webcamBtn').disabled = false;
            document.getElementById('webcamBtn').style.background = '#9C27B0';
            
            // Show upload section
            document.getElementById('dropZone').style.display = 'block';
            
            // Clear canvas
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
            
            console.log('[INFO] Webcam stopped');
        }
    </script>
</body>
</html>
"""


def detect_vehicles_image(image_data, conf_threshold=0.4):
    """Process image and detect vehicles"""
    start_time = time.time()
    
    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        return None, "Error: Could not decode image"
    
    height, width = image.shape[:2]
    print(f"\n{'='*60}")
    print("IMAGE PROCESSING STARTED")
    print(f"{'='*60}")
    print(f"Resolution: {width}x{height}")
    print(f"Confidence Threshold: {conf_threshold}")
    print(f"{'='*60}\n")
    
    # Run detection
    results = model.predict(
        image,
        imgsz=640,
        conf=conf_threshold,
        verbose=False,
        classes=list(VEHICLE_CLASSES.keys())
    )
    
    # Process detections
    detections = []
    class_counts = {}
    annotated = image.copy()
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for box in boxes:
            class_id = int(box.cls.item())
            conf = float(box.conf.item())
            
            if class_id in VEHICLE_CLASSES:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                class_name = VEHICLE_CLASSES[class_id]
                
                detections.append({'class': class_name, 'conf': conf})
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                # Draw box
                color = CLASS_COLORS[class_name]
                cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Draw label
                # Use display name (Motorcycle/Scooty instead of just motorcycle)
                display_name = DISPLAY_NAMES.get(class_name, class_name)
                label = f"{display_name}: {conf:.2f}"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                            (int(x1) + label_w, int(y1)), color, -1)
                cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    
    # Add stats
    processing_time = time.time() - start_time
    cv2.rectangle(annotated, (0, 0), (300, 80), (0, 0, 0), -1)
    cv2.putText(annotated, f"Vehicles: {len(detections)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(annotated, f"Time: {processing_time:.3f}s", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Print summary to terminal
    print(f"\n{'='*60}")
    print("IMAGE PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Vehicles Detected: {len(detections)}")
    print(f"Processing Time: {processing_time:.3f}s")
    if class_counts:
        print(f"Breakdown:")
        for cls, count in class_counts.items():
            display_name = DISPLAY_NAMES.get(cls, cls)
            print(f"  - {display_name}: {count}")
    print(f"{'='*60}\n")
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', annotated)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare message
    if len(detections) > 0:
        message = f"SUCCESS: Detected {len(detections)} vehicle(s)"
    else:
        message = "NO VEHICLES DETECTED"
    
    return img_base64, message, {
        'time': f"{processing_time:.3f}s",
        'count': len(detections),
        'breakdown': class_counts
    }


def extract_video_first_frame(video_path):
    """Extract first frame from video as base64 image for preview"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            # Resize to reasonable size for preview
            height, width = frame.shape[:2]
            max_width = 640
            if width > max_width:
                ratio = max_width / width
                new_height = int(height * ratio)
                frame = cv2.resize(frame, (max_width, new_height))
            # Convert to RGB and encode
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode('.jpg', frame_rgb)
            return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"[WARN] Could not extract first frame: {e}")
    return None


def detect_vehicles_video(video_path, output_path, conf_threshold=0.4):
    """Process video and detect vehicles with terminal progress output"""
    start_time = time.time()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR] Could not open video file")
        return None, "Error: Could not open video", None
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n{'='*60}")
    print("VIDEO PROCESSING STARTED")
    print(f"{'='*60}")
    print(f"Resolution: {frame_width}x{frame_height}")
    print(f"FPS: {fps:.1f}")
    print(f"Total Frames: {total_frames}")
    print(f"Confidence Threshold: {conf_threshold}")
    print(f"{'='*60}\n")
    
    # Try multiple codecs in order of browser compatibility
    # H264 is required for browser playback, mp4v only works in desktop players
    codecs_to_try = [
        ('avc1', 'H264'),  # Most compatible with browsers
        ('H264', 'H264'),  # Alternative H264 identifier
        ('X264', 'X264'),  # Another H264 variant
        ('h264', 'H264'),  # Lowercase variant
        ('MP4V', 'MPEG-4'),  # Less compatible but common
        ('mp4v', 'MPEG-4'),  # Lowercase variant
    ]
    
    writer = None
    used_codec = None
    
    for fourcc_code, codec_name in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
            writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            if writer.isOpened():
                used_codec = codec_name
                print(f"[INFO] Successfully using {codec_name} codec ({fourcc_code})")
                break
            else:
                writer.release()
                writer = None
        except Exception as e:
            print(f"[DEBUG] Codec {fourcc_code} failed: {e}")
            continue
    
    if writer is None or not writer.isOpened():
        print("[ERROR] Could not open video writer with any codec")
        return None, "Error: Could not create output video - no compatible codec found"
    
    total_detections = 0
    frame_count = 0
    class_counts = {}
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            try:
                results = model.predict(
                    frame,
                    imgsz=480,
                    conf=conf_threshold,
                    verbose=False,
                    classes=list(VEHICLE_CLASSES.keys())
                )
            except Exception as e:
                print(f"[ERROR] Detection failed on frame {frame_count}: {e}")
                # Write original frame without detection if detection fails
                writer.write(frame)
                frame_count += 1
                continue
            
            annotated = frame.copy()
            frame_detections = 0
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for box in boxes:
                    class_id = int(box.cls.item())
                    conf = float(box.conf.item())
                    
                    if class_id in VEHICLE_CLASSES:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        class_name = VEHICLE_CLASSES[class_id]
                        
                        frame_detections += 1
                        total_detections += 1
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1
                        
                        color = CLASS_COLORS[class_name]
                        cv2.rectangle(annotated, (int(x1), int(y1)), 
                                    (int(x2), int(y2)), color, 2)
                        
                        # Use display name (Motorcycle/Scooty instead of just motorcycle)
                        display_name = DISPLAY_NAMES.get(class_name, class_name)
                        label = f"{display_name}: {conf:.2f}"
                        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                                    (int(x1) + label_w, int(y1)), color, -1)
                        cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Add frame info
            cv2.putText(annotated, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            writer.write(annotated)
            frame_count += 1
            
            # Print progress every 30 frames
            if frame_count % 30 == 0 or frame_count == 1:
                elapsed = time.time() - start_time
                progress_pct = (frame_count / total_frames * 100) if total_frames > 0 else 0
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                print(f"[PROGRESS] Frame {frame_count}/{total_frames} ({progress_pct:.1f}%) | "
                      f"Vehicles: {total_detections} | FPS: {current_fps:.1f}")
    
    finally:
        cap.release()
        if writer:
            writer.release()
        # Ensure file is fully written and closed
        time.sleep(0.2)
        
        # Verify video was created and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"[INFO] Output video file size: {file_size / 1024 / 1024:.2f} MB")
            if file_size == 0:
                print("[ERROR] Video file is empty!")
            elif used_codec and 'H264' not in used_codec:
                # Try to convert to H264 using ffmpeg if available
                print("[INFO] Attempting to convert video to H264 for browser compatibility...")
                try:
                    import subprocess
                    temp_converted = output_path.replace('.mp4', '_h264.mp4')
                    result = subprocess.run([
                        'ffmpeg', '-y', '-i', output_path,
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                        '-c:a', 'aac', '-movflags', '+faststart',
                        temp_converted
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and os.path.exists(temp_converted):
                        # Replace original with converted
                        os.replace(temp_converted, output_path)
                        used_codec = 'H264 (ffmpeg converted)'
                        print("[SUCCESS] Video converted to H264 for browser playback")
                    else:
                        print(f"[WARN] ffmpeg conversion failed: {result.stderr[:200]}")
                        if os.path.exists(temp_converted):
                            os.remove(temp_converted)
                except FileNotFoundError:
                    print("[INFO] ffmpeg not found - install ffmpeg for better browser compatibility")
                except Exception as e:
                    print(f"[WARN] ffmpeg conversion error: {e}")
        else:
            print("[ERROR] Video file was not created!")
    
    processing_time = time.time() - start_time
    avg_fps = frame_count / processing_time if processing_time > 0 else 0
    
    # Print final summary
    print(f"\n{'='*60}")
    print("VIDEO PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Frames Processed: {frame_count}")
    print(f"Total Vehicles Detected: {total_detections}")
    print(f"Processing Time: {processing_time:.1f}s")
    print(f"Average FPS: {avg_fps:.1f}")
    if class_counts:
        print(f"Breakdown:")
        for cls, count in class_counts.items():
            display_name = DISPLAY_NAMES.get(cls, cls)
            print(f"  - {display_name}: {count}")
    print(f"{'='*60}\n")
    
    # Add codec info to message
    codec_info = f" (Codec: {used_codec})" if used_codec else " (Codec: unknown)"
    
    if total_detections > 0:
        message = f"SUCCESS: Processed {frame_count} frames, detected {total_detections} vehicles{codec_info}"
    else:
        message = f"NO VEHICLES: Processed {frame_count} frames, no vehicles detected{codec_info}"
    
    # Extract first frame for preview
    first_frame = extract_video_first_frame(output_path)
    
    return output_path, message, {
        'time': f"{processing_time:.1f}s ({avg_fps:.1f} FPS)",
        'count': total_detections,
        'breakdown': class_counts,
        'codec': used_codec if used_codec else 'unknown',
        'first_frame': first_frame
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    
    if request.method == 'POST':
        # Get confidence threshold
        conf_threshold = float(request.form.get('confidence', 0.4))
        
        # Check for pasted image first
        pasted_image_data = request.form.get('pasted_image', '')
        
        if pasted_image_data and pasted_image_data.startswith('data:image'):
            # Handle pasted image from clipboard
            try:
                # Extract base64 data from data URL
                # Format: data:image/png;base64,xxxxxx
                base64_data = pasted_image_data.split(',')[1]
                file_data = base64.b64decode(base64_data)
                
                # Process as image
                img_base64, message, stats = detect_vehicles_image(file_data, conf_threshold)
                
                result = {
                    'success': stats['count'] > 0,
                    'message': message,
                    'image': img_base64,
                    'stats': stats
                }
                
                return render_template_string(HTML_TEMPLATE, result=result)
            except Exception as e:
                flash(f'Error processing pasted image: {str(e)}')
                return redirect(request.url)
        
        # Handle regular file upload
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        # Read file data
        file_data = file.read()
        filename = file.filename.lower()
        
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            # Process image
            img_base64, message, stats = detect_vehicles_image(file_data, conf_threshold)
            
            result = {
                'success': stats['count'] > 0,
                'message': message,
                'image': img_base64,
                'stats': stats
            }
            
        elif filename.endswith(('.mp4', '.avi', '.mov')):
            # Process video
            # Save uploaded video temporarily
            temp_input = tempfile.mktemp(suffix='.mp4')
            with open(temp_input, 'wb') as f:
                f.write(file_data)
            
            # Create output path in static directory for reliable serving
            timestamp = int(time.time())
            temp_output = os.path.join(STATIC_DIR, f'processed_{timestamp}.mp4')
            
            video_path, message, stats = detect_vehicles_video(temp_input, temp_output, conf_threshold)
            
            # Clean up input
            os.remove(temp_input)
            
            # Use relative path from static folder
            video_filename = os.path.basename(temp_output)
            
            result = {
                'success': stats['count'] > 0,
                'message': message,
                'video_path': video_filename,
                'timestamp': timestamp,
                'stats': stats
            }
            
            # Store output path for cleanup later
            if not hasattr(app, 'temp_videos'):
                app.temp_videos = {}
            app.temp_videos[video_filename] = temp_output
            
        else:
            flash('Unsupported file format. Use: JPG, PNG, MP4, AVI, MOV')
            return redirect(request.url)
    
    return render_template_string(HTML_TEMPLATE, result=result)


@app.route('/download/<path:filename>')
def download(filename):
    if hasattr(app, 'temp_videos') and filename in app.temp_videos:
        return send_file(app.temp_videos[filename], as_attachment=True)
    return "File not found", 404


@app.route('/webcam_detect', methods=['POST'])
def webcam_detect():
    """Process webcam frame for live detection"""
    try:
        # Get image data from request
        image_data = request.get_data()
        conf_threshold = float(request.form.get('confidence', 0.4))
        
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return {'error': 'Could not decode image'}, 400
        
        # Run detection
        results = model.predict(
            image,
            imgsz=640,
            conf=conf_threshold,
            verbose=False,
            classes=list(VEHICLE_CLASSES.keys())
        )
        
        # Process detections
        detections = []
        class_counts = {}
        annotated = image.copy()
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            
            for box in boxes:
                class_id = int(box.cls.item())
                conf = float(box.conf.item())
                
                if class_id in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    class_name = VEHICLE_CLASSES[class_id]
                    
                    detections.append({'class': class_name, 'conf': conf})
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                    
                    # Draw box
                    color = CLASS_COLORS[class_name]
                    cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    
                    # Draw label
                    display_name = DISPLAY_NAMES.get(class_name, class_name)
                    label = f"{display_name}: {conf:.2f}"
                    (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(annotated, (int(x1), int(y1) - label_h - 10),
                                (int(x1) + label_w, int(y1)), color, -1)
                    cv2.putText(annotated, label, (int(x1), int(y1) - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # Add stats overlay
        cv2.rectangle(annotated, (0, 0), (300, 80), (0, 0, 0), -1)
        cv2.putText(annotated, f"Vehicles: {len(detections)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', annotated)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Prepare breakdown text
        breakdown_text = ""
        if class_counts:
            breakdown_text = ", ".join([f"{DISPLAY_NAMES.get(cls, cls)}: {count}" for cls, count in class_counts.items()])
        
        return {
            'image': img_base64,
            'count': len(detections),
            'breakdown': breakdown_text
        }
        
    except Exception as e:
        print(f"[ERROR] Webcam detection failed: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}, 500


@app.route('/view/<path:filename>')
def view_video(filename):
    """Serve video for inline viewing in browser with proper headers"""
    # Handle 'videos/' prefix in the URL
    if filename.startswith('videos/'):
        filename = filename[7:]  # Remove 'videos/' prefix
    
    # First check static directory
    static_path = os.path.join(STATIC_DIR, filename)
    if os.path.exists(static_path) and os.path.getsize(static_path) > 0:
        video_path = static_path
    elif hasattr(app, 'temp_videos') and filename in app.temp_videos:
        video_path = app.temp_videos[filename]
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            return "Video file not ready or empty", 404
    else:
        return "File not found", 404
    
    # Add cache control headers to prevent caching issues
    response = send_file(
        video_path, 
        mimetype='video/mp4', 
        as_attachment=False,
        conditional=True  # Support range requests for video seeking
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Accept-Ranges'] = 'bytes'
    return response


def main():
    print("="*50)
    print("Vehicle Detection Web App")
    print("="*50)
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
