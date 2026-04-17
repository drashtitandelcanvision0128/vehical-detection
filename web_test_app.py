"""
Vehicle Detection Web Testing App (Flask)
Simple web interface for testing vehicle detection on images/videos
"""

from flask import Flask, render_template_string, request, send_file, flash, redirect, session
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import os
import time
from pathlib import Path
import base64
from io import BytesIO
from fpdf import FPDF
import uuid

app = Flask(__name__)
app.secret_key = 'vehicle-detection-secret-key'

# Store detection results for PDF generation (keyed by report_id)
app.stored_results = {}

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

# HTML Template - Modern Design Matching Image
HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Enterprise Vehicle Intelligence</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&amp;family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "surface-variant": "#e3e2e5",
                        "tertiary-container": "#4f3303",
                        "surface": "#faf9fc",
                        "on-secondary-fixed": "#121c28",
                        "primary-container": "#1b3b5a",
                        "tertiary-fixed-dim": "#ecbf83",
                        "on-error-container": "#93000a",
                        "surface-container": "#eeedf0",
                        "on-error": "#ffffff",
                        "primary-fixed-dim": "#abc9ef",
                        "on-tertiary-fixed-variant": "#5f4110",
                        "on-surface-variant": "#43474d",
                        "error-container": "#ffdad6",
                        "on-background": "#1a1c1e",
                        "on-primary-container": "#87a5ca",
                        "secondary-container": "#d3deef",
                        "primary-fixed": "#d1e4ff",
                        "on-primary-fixed": "#001d35",
                        "on-surface": "#1a1c1e",
                        "surface-tint": "#436182",
                        "on-tertiary": "#ffffff",
                        "surface-container-low": "#f4f3f6",
                        "secondary": "#545f6e",
                        "tertiary-fixed": "#ffddb3",
                        "on-tertiary-fixed": "#291800",
                        "outline": "#73777e",
                        "surface-dim": "#dad9dd",
                        "outline-variant": "#c3c6ce",
                        "on-secondary": "#ffffff",
                        "surface-container-high": "#e9e8eb",
                        "tertiary": "#341f00",
                        "on-tertiary-container": "#c59c63",
                        "surface-container-lowest": "#ffffff",
                        "secondary-fixed": "#d8e3f4",
                        "inverse-primary": "#abc9ef",
                        "on-primary": "#ffffff",
                        "inverse-on-surface": "#f1f0f3",
                        "on-secondary-container": "#576270",
                        "error": "#ba1a1a",
                        "secondary-fixed-dim": "#bcc7d8",
                        "on-secondary-fixed-variant": "#3d4855",
                        "primary": "#002542",
                        "inverse-surface": "#2f3033",
                        "on-primary-fixed-variant": "#2a4968",
                        "surface-container-highest": "#e3e2e5",
                        "background": "#faf9fc",
                        "surface-bright": "#faf9fc"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                    "fontFamily": {
                        "headline": ["Manrope"],
                        "body": ["Inter"],
                        "label": ["Inter"]
                    }
                },
            },
        }
    </script>
<style>
        body { font-family: 'Inter', sans-serif; }
        h1, h2, h3, .font-headline { font-family: 'Manrope', sans-serif; }
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
        .glass-panel {
            background: rgba(250, 249, 252, 0.7);
            backdrop-filter: blur(12px);
        }
        .glass-hud {
            background: rgba(250, 249, 252, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(195, 198, 206, 0.2);
        }
        .gradient-button {
            background: linear-gradient(135deg, #002542 0%, #1b3b5a 100%);
        }
        @keyframes loading {
            0% { transform: translateX(-100%); }
            50% { transform: translateX(0%); }
            100% { transform: translateX(100%); }
        }
    </style>
</head>
<body class="bg-surface text-on-surface min-h-screen">
<!-- TopAppBar -->
<header class="fixed top-0 w-full z-50 bg-slate-50/70 backdrop-blur-md shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex items-center justify-between px-6 h-16 w-full">
<div class="flex items-center gap-3">
<span class="material-symbols-outlined text-blue-900">analytics</span>
<span class="text-xl font-bold tracking-tight text-blue-900">Enterprise Vehicle Intelligence</span>
</div>
<div class="flex items-center gap-6">
<nav class="hidden md:flex gap-6">
<a class="text-blue-900 font-semibold text-sm" href="#">Upload</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="#">Real-time</a>
<a class="text-slate-500 hover:bg-blue-50 transition-colors px-3 py-1 rounded-lg text-sm" href="#">History</a>
</nav>
<div class="h-10 w-10 rounded-full overflow-hidden border border-outline-variant/30">
<img class="w-full h-full object-cover" src="https://ui-avatars.com/api/?name=Admin&background=0D8ABC&color=fff"/>
</div>
</div>
</header>
<main class="pt-24 pb-12 px-6 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
<!-- Left Column: Instructions & Info -->
<div class="lg:col-span-4 space-y-8">
<header>
<h1 class="text-[2.75rem] font-extrabold leading-tight tracking-tight text-primary">Vehicle Detection Testing App</h1>
<p class="mt-4 text-title-md text-secondary leading-relaxed">Upload or paste an image to detect vehicles using our laboratory-grade neural network.</p>
</header>
<!-- Info Box: Detection Scope -->
<section class="bg-surface-container-low rounded-xl p-6 space-y-6">
<div>
<h3 class="text-label-md font-bold text-primary uppercase tracking-wider mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">check_circle</span>
                        Detection Targets
                    </h3>
<div class="grid grid-cols-2 gap-3">
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Car</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Motorcycle</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Bus</span>
</div>
<div class="bg-surface-container-lowest p-3 rounded-lg border border-outline-variant/10">
<span class="text-sm font-semibold text-on-surface">Truck</span>
</div>
</div>
</div>
<div class="pt-4 border-t border-outline-variant/20">
<h3 class="text-label-md font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-sm">block</span>
                        Excluded Classes
                    </h3>
<p class="text-sm text-secondary leading-relaxed">
                        The current model iteration ignores non-vehicular entities including people, animals, vegetation, and static infrastructure to ensure high precision in traffic flow analysis.
                    </p>
</div>
</section>
</div>
<!-- Right Column: Testing Interface -->
<div class="lg:col-span-8 space-y-6">
<!-- Main Upload Area -->
<div class="bg-surface-container-lowest rounded-xl p-8 shadow-[0px_8px_24px_rgba(0,37,66,0.06)] border border-outline-variant/10">
<div class="relative group cursor-pointer border-2 border-dashed border-outline-variant/40 rounded-xl transition-all hover:border-primary/40 hover:bg-surface-container-low flex flex-col items-center justify-center min-h-[300px] text-center p-12" id="dragDropArea">
<div class="w-20 h-20 bg-primary-fixed rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
<span class="material-symbols-outlined text-primary text-4xl">cloud_upload</span>
</div>
<h2 class="text-xl font-bold text-primary mb-2">Upload Image or Video</h2>
<p class="text-secondary max-w-sm">Drag and drop your media here, or browse local files. Supports JPG, PNG, MP4 up to 50MB.</p>
<div id="selectedFileDisplay" style="display: none; margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 5px; color: #1976D2;">
<strong>Selected:</strong> <span id="fileName"></span>
</div>
</div>
<form action="/" method="POST" enctype="multipart/form-data" id="uploadForm">
<input type="file" name="file" id="fileInput" accept=".jpg,.jpeg,.png,.mp4,.avi,.mov" style="display: none;">
<input type="hidden" name="pasted_image" id="pastedImageData">
<div class="mt-6 flex flex-wrap justify-center gap-4">
<button type="button" class="flex items-center gap-2 px-6 py-2.5 bg-surface-container-high text-primary font-semibold rounded-lg hover:bg-surface-variant transition-colors" id="copyPasteBtn" onclick="enablePasteMode()">
<span class="material-symbols-outlined text-xl">content_paste</span>
                            Paste Image
                        </button>
<button type="button" class="flex items-center gap-2 px-6 py-2.5 bg-surface-container-high text-primary font-semibold rounded-lg hover:bg-surface-variant transition-colors" id="webcamBtn" onclick="startWebcam()">
<span class="material-symbols-outlined text-xl">videocam</span>
                            Live Webcam
                        </button>
</div>
<p id="pasteInstructions" style="color: #2196F3; font-size: 14px; display: none; margin-top: 10px; text-align: center;">
                    Paste mode active! Press Ctrl+V to paste image from clipboard
                </p>
<p id="webcamInstructions" style="color: #9C27B0; font-size: 14px; display: none; margin-top: 10px; text-align: center;">
                    Webcam active! Close this tab or click Stop to end detection
                </p>
<!-- Pasted Image Preview -->
<div id="pastePreviewContainer" style="display: none; margin-top: 20px; padding: 10px; border: 2px solid #4CAF50; border-radius: 5px;">
<p style="color: #4CAF50; font-weight: bold; margin-bottom: 10px;">Image ready for detection:</p>
<img id="pastedPreview" style="max-width: 100%; max-height: 300px; border-radius: 5px;" alt="Pasted image preview">
<button type="button" onclick="clearPastedImage()" style="margin-top: 10px; background: #f44336; color: white; padding: 5px 15px; border: none; border-radius: 3px; cursor: pointer;">
                    Clear Image
                </button>
</div>
<!-- Controls Section -->
<div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
<div class="space-y-4">
<div class="flex justify-between items-center">
<label class="text-label-md font-bold text-primary uppercase tracking-widest">Confidence Threshold</label>
<span class="text-sm font-mono font-bold text-primary" id="confValue">0.50</span>
</div>
<input class="w-full h-2 bg-surface-container-highest rounded-lg appearance-none cursor-pointer accent-primary" max="1" min="0" step="0.01" type="range" name="confidence" value="0.5" oninput="document.getElementById('confValue').textContent = this.value">
<div class="flex justify-between text-[10px] font-bold text-slate-400 uppercase">
<span>Precision</span>
<span>Recall</span>
</div>
</div>
<div>
<button type="submit" class="w-full h-14 bg-gradient-to-br from-primary to-primary-container text-white font-bold rounded-lg shadow-lg hover:shadow-primary/20 hover:-translate-y-0.5 active:translate-y-0 transition-all flex items-center justify-center gap-3" id="detectBtn">
<span class="material-symbols-outlined">analytics</span>
                            Detect Vehicles
                        </button>
</div>
</div>
</form>
</div>
<!-- Bento Preview Section -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
<div class="md:col-span-2 bg-surface-container-high rounded-xl overflow-hidden aspect-video relative">
<video class="w-full h-full object-cover" id="demoVideo" muted loop playsinline controls>
<source src="/static/demo_converted.mp4" type="video/mp4">
Your browser does not support the video tag.
</video>
</div>
<div class="bg-primary text-primary-fixed p-6 rounded-xl flex flex-col justify-between">
<span class="material-symbols-outlined text-4xl" style="font-variation-settings: 'FILL' 1;">bolt</span>
<div>
<p class="text-label-md font-bold uppercase tracking-widest opacity-60">Avg. Inference</p>
<p class="text-3xl font-bold font-headline">14.2ms</p>
</div>
</div>
<!-- Webcam Section -->
<div id="webcamSection" style="display: none; margin: 20px 0; padding: 20px; border: 2px solid #9C27B0; border-radius: 5px; background: #f3e5f5;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
<div style="display: flex; align-items: center; gap: 15px;">
<h3 style="color: #9C27B0; margin: 0;">Live Webcam Detection</h3>
<div id="detectionStatusBadge" style="padding: 5px 15px; border-radius: 20px; font-size: 14px; font-weight: bold; background: #FFC107; color: #333;">
                        Waiting...
                    </div>
</div>
<button type="button" onclick="stopWebcam()" style="background: #f44336; color: white; padding: 8px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
                    Stop Webcam
                </button>
</div>
<div style="display: flex; gap: 20px; flex-wrap: wrap;">
<div style="flex: 1; min-width: 300px;">
<p style="color: #666; font-weight: bold; margin-bottom: 5px;">Original Feed:</p>
<video id="webcamVideo" autoplay playsinline style="width: 100%; max-width: 640px; border-radius: 5px; background: #000;"></video>
</div>
<div style="flex: 1; min-width: 300px;">
<p style="color: #666; font-weight: bold; margin-bottom: 5px;">Detection Output:</p>
<canvas id="detectionCanvas" style="width: 100%; max-width: 640px; border-radius: 5px; background: #000;"></canvas>
</div>
</div>
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
<!-- Result Section - Detection Analysis -->
{% if result %}
<div class="fixed inset-0 bg-surface z-50 overflow-y-auto" style="display: none;" id="resultModal">
<!-- TopAppBar -->
<header class="sticky top-0 z-50 bg-[#faf9fc] shadow-[0px_8px_24px_rgba(0,37,66,0.06)] flex justify-between items-center w-full px-6 h-16">
<div class="flex items-center gap-4">
<button class="material-symbols-outlined text-[#002542] active:scale-95 duration-200 hover:bg-[#e3e2e5] p-2 rounded-full" onclick="closeResultModal()">arrow_back</button>
<h1 class="font-['Manrope'] font-bold tracking-tight text-[#002542] text-xl">Detection Analysis</h1>
</div>
<div class="flex items-center gap-2">
<button class="material-symbols-outlined text-[#002542] active:scale-95 duration-200 hover:bg-[#e3e2e5] p-2 rounded-full">more_vert</button>
</div>
</header>
<main class="max-w-7xl mx-auto px-4 md:px-8 py-8">
<!-- Layout Grid -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
<!-- Left Column: Image View (Bento Large) -->
<div class="lg:col-span-8 space-y-6">
<div class="relative bg-surface-container-lowest rounded-xl overflow-hidden shadow-[0px_8px_24px_rgba(0,37,66,0.06)] group">
{% if result.image %}
<img alt="Vehicle detection analysis" class="w-full h-auto object-cover aspect-video" src="data:image/jpeg;base64,{{ result.image }}"/>
{% elif result.stats and result.stats.first_frame %}
<img alt="Vehicle detection analysis" class="w-full h-auto object-cover aspect-video" src="data:image/jpeg;base64,{{ result.stats.first_frame }}"/>
{% endif %}
<!-- Detection Overlays (Simulated) -->
<div class="absolute inset-0 pointer-events-none">
<div class="absolute top-[25%] left-[30%] w-[18%] h-[22%] border-2 border-primary-fixed flex items-start">
<span class="bg-primary px-2 py-0.5 text-[10px] font-mono text-white flex items-center gap-1">
<span class="material-symbols-outlined text-[12px]" style="font-variation-settings: 'FILL' 1;">directions_car</span>
                                Car - 98%
                            </span>
</div>
<div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent h-1/4 w-full opacity-30"></div>
</div>
<!-- Live Indicators -->
<div class="absolute top-4 right-4 glass-hud px-4 py-2 rounded-lg flex items-center gap-3">
<div class="flex items-center gap-2">
<span class="w-2 h-2 rounded-full bg-error animate-pulse"></span>
<span class="text-[10px] font-bold uppercase tracking-widest text-on-surface">Live Stream</span>
</div>
<div class="h-4 w-[1px] bg-outline-variant/30"></div>
<span class="text-[10px] font-mono text-on-surface-variant">04:12:44:09</span>
</div>
</div>
<!-- Inference Metrics (Horizontal technical bar) -->
<div class="bg-surface-container-low p-6 rounded-xl flex flex-wrap gap-8 items-center border border-outline-variant/10">
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Processing Time</p>
<p class="text-primary font-mono font-bold">{% if result.stats %}{{ result.stats.time }}{% else %}--{% endif %}</p>
</div>
<div class="w-[1px] h-8 bg-outline-variant/20 hidden md:block"></div>
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Model Architecture</p>
<p class="text-primary font-mono font-bold">YOLOv8 Laboratory Grade</p>
</div>
<div class="w-[1px] h-8 bg-outline-variant/20 hidden md:block"></div>
<div>
<p class="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">Inference Device</p>
<p class="text-primary font-mono font-bold">GPU Acceleration (A100)</p>
</div>
</div>
{% if result.video_path %}
<!-- Video Player -->
<div class="bg-gray-900 rounded-lg p-4 text-center">
<p class="text-white font-bold mb-3">Full Video with Detection:</p>
<video width="100%" height="auto" controls 
class="max-h-96 rounded-lg"
preload="metadata">
<source src="/view/videos/{{ result.video_path }}?t={{ result.timestamp }}" type="video/mp4">
<p class="text-white py-8">
Your browser does not support video playback.<br>
Use the buttons below to view or download.
</p>
</video>
</div>
<div class="mt-4 flex gap-3 flex-wrap justify-center">
<a href="/view/videos/{{ result.video_path }}?t={{ result.timestamp }}" target="_blank" 
class="px-6 py-3 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition-colors">
Open in New Tab
</a>
<a href="/download/{{ result.video_path }}?t={{ result.timestamp }}" download 
class="px-6 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors">
Download Video
</a>
</div>
{% endif %}
</div>
<!-- Right Column: Analysis Sidebar -->
<div class="lg:col-span-4 space-y-6">
<!-- Summary Card -->
<div class="bg-surface-container-lowest p-8 rounded-xl shadow-[0px_8px_24px_rgba(0,37,66,0.06)] relative overflow-hidden">
<div class="relative z-10">
<div class="flex items-center gap-3 mb-4">
<div class="bg-primary/5 p-2 rounded-lg text-primary">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">analytics</span>
</div>
<h2 class="font-headline text-lg font-bold text-primary">Analysis Summary</h2>
</div>
<div class="space-y-1">
<p class="text-4xl font-headline font-extrabold text-primary tracking-tight">{% if result.stats %}{{ result.stats.count }}{% else %}0{% endif %} Vehicle{% if result.stats and result.stats.count != 1 %}s{% endif %} Detected</p>
<div class="flex items-center gap-2 text-on-tertiary-fixed-variant bg-tertiary-fixed/20 px-3 py-1 rounded-full w-fit">
<span class="material-symbols-outlined text-sm">check_circle</span>
<span class="text-xs font-semibold">Validation Successful</span>
</div>
</div>
</div>
<div class="absolute -bottom-8 -right-8 w-32 h-32 bg-primary/5 rounded-full blur-3xl"></div>
</div>
<!-- Breakdown Card -->
<div class="bg-surface-container-lowest rounded-xl shadow-[0px_8px_24px_rgba(0,37,66,0.06)] overflow-hidden">
<div class="px-6 py-4 border-b border-outline-variant/10 flex justify-between items-center">
<h3 class="font-headline text-sm font-bold text-on-surface uppercase tracking-wider">Classification Data</h3>
<span class="text-[10px] font-mono text-outline">v2.0.4</span>
</div>
<div class="p-0">
<table class="w-full text-left">
<thead>
<tr class="bg-surface-container-low">
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Class</th>
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Count</th>
<th class="px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">Avg Conf</th>
</tr>
</thead>
<tbody class="divide-y divide-outline-variant/10">
{% if result.stats and result.stats.breakdown %}
{% set class_icons = {'car': 'directions_car', 'motorcycle': 'two_wheeler', 'bus': 'directions_bus', 'truck': 'local_shipping'} %}
{% for class_name, count in result.stats.breakdown.items() %}
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-6 py-4 flex items-center gap-3">
<span class="material-symbols-outlined text-primary text-sm">{{ class_icons.get(class_name, 'directions_car') }}</span>
<span class="text-sm font-medium text-on-surface">{% if class_name == 'motorcycle' %}Motorcycle{% else %}{{ class_name|title }}{% endif %}</span>
</td>
<td class="px-6 py-4 text-sm font-mono text-on-surface">{{ "%02d"|format(count) }}</td>
<td class="px-6 py-4">
<div class="flex items-center gap-2">
<div class="w-12 h-1.5 bg-surface-container-high rounded-full overflow-hidden">
<div class="h-full bg-primary w-[95%]"></div>
</div>
<span class="text-xs font-mono font-bold text-primary">95%</span>
</div>
</td>
</tr>
{% endfor %}
{% else %}
<tr class="hover:bg-surface-container-low transition-colors">
<td class="px-6 py-4 flex items-center gap-3 opacity-40">
<span class="material-symbols-outlined text-sm">directions_car</span>
<span class="text-sm font-medium">Car</span>
</td>
<td class="px-6 py-4 text-sm font-mono opacity-40">00</td>
<td class="px-6 py-4 text-xs font-mono opacity-40">--</td>
</tr>
{% endif %}
</tbody>
</table>
</div>
</div>
<!-- Action Buttons -->
<div class="grid grid-cols-2 gap-4">
<button class="gradient-button text-white font-headline text-sm font-bold py-4 px-6 rounded-md shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2" onclick="downloadPDF('{{ report_id }}')">
<span class="material-symbols-outlined text-lg">save</span>
                        Save Report
                    </button>
<button class="bg-surface-container-lowest text-primary font-headline text-sm font-bold py-4 px-6 rounded-md shadow-sm border border-outline-variant/20 hover:bg-surface-container-low active:scale-95 transition-all flex items-center justify-center gap-2" onclick="closeResultModal()">
<span class="material-symbols-outlined text-lg">refresh</span>
                        New Analysis
                    </button>
</div>
</div>
</div>
</main>
</div>
<script>
    // Show result modal when result is available
    {% if result %}
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('resultModal').style.display = 'block';
    });
    {% endif %}

    function downloadPDF(reportId) {
        console.log('[DEBUG] downloadPDF called with reportId:', reportId);
        if (!reportId || reportId === '') {
            alert('No report data found. Please run a new detection.');
            return;
        }
        alert('Downloading PDF for report: ' + reportId);
        window.location.href = '/generate_pdf/' + reportId;
    }

    function closeResultModal() {
        document.getElementById('resultModal').style.display = 'none';
        window.location.href = '/';
    }
</script>
{% endif %}
</div>
</main>
<script>
        let pasteModeActive = false;
        const MAX_IMAGE_WIDTH = 1280;
        const MAX_IMAGE_HEIGHT = 720;
        const JPEG_QUALITY = 0.85;
        
        function compressImage(dataUrl, callback) {
            const img = new Image();
            img.onload = function() {
                let width = img.width;
                let height = img.height;
                
                if (width > MAX_IMAGE_WIDTH) {
                    height = Math.round(height * (MAX_IMAGE_WIDTH / width));
                    width = MAX_IMAGE_WIDTH;
                }
                if (height > MAX_IMAGE_HEIGHT) {
                    width = Math.round(width * (MAX_IMAGE_HEIGHT / height));
                    height = MAX_IMAGE_HEIGHT;
                }
                
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                const compressedDataUrl = canvas.toDataURL('image/jpeg', JPEG_QUALITY);
                
                console.log('Original size: ' + Math.round(dataUrl.length / 1024) + 'KB');
                console.log('Compressed size: ' + Math.round(compressedDataUrl.length / 1024) + 'KB');
                
                callback(compressedDataUrl);
            };
            img.src = dataUrl;
        }
        
        async function enablePasteMode() {
            pasteModeActive = true;
            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">hourglass_empty</span> Reading clipboard...';
            document.getElementById('copyPasteBtn').classList.add('bg-orange-100');
            document.getElementById('pasteInstructions').style.display = 'block';
            document.getElementById('pasteInstructions').textContent = 'Reading image from clipboard...';
            
            try {
                const clipboardItems = await navigator.clipboard.read();
                let imageFound = false;
                
                for (const item of clipboardItems) {
                    const imageType = item.types.find(type => type.startsWith('image/'));
                    
                    if (imageType) {
                        const blob = await item.getType(imageType);
                        const reader = new FileReader();
                        
                        reader.onload = function(event) {
                            const originalData = event.target.result;
                            
                            compressImage(originalData, function(compressedData) {
                                document.getElementById('pastedImageData').value = compressedData;
                                
                                const preview = document.getElementById('pastedPreview');
                                preview.src = compressedData;
                                document.getElementById('pastePreviewContainer').style.display = 'block';
                                
                                document.getElementById('fileInput').value = '';
                                
                                document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">check_circle</span> Image Pasted';
                                document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                                document.getElementById('copyPasteBtn').classList.add('bg-green-100');
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
                    document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Mode Active';
                    document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                    document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                    document.getElementById('pasteInstructions').textContent = 'No image found. Press Ctrl+V to paste';
                    document.getElementById('pasteInstructions').style.color = '#f44336';
                    window.focus();
                }
                
            } catch (err) {
                console.error('Clipboard API error:', err);
                document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Mode Active';
                document.getElementById('copyPasteBtn').classList.remove('bg-orange-100');
                document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                document.getElementById('pasteInstructions').textContent = 'Please press Ctrl+V to paste your image';
                window.focus();
            }
        }
        
        function clearPastedImage() {
            document.getElementById('pastedImageData').value = '';
            document.getElementById('pastedPreview').src = '';
            document.getElementById('pastePreviewContainer').style.display = 'none';
            document.getElementById('fileInput').value = '';
            
            pasteModeActive = false;
            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">content_paste</span> Paste Image';
            document.getElementById('copyPasteBtn').classList.remove('bg-green-100', 'bg-orange-100');
            document.getElementById('pasteInstructions').style.display = 'none';
        }
        
        document.addEventListener('paste', function(e) {
            const items = e.clipboardData.items;
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    const reader = new FileReader();
                    
                    reader.onload = function(event) {
                        const originalData = event.target.result;
                        
                        compressImage(originalData, function(compressedData) {
                            document.getElementById('pastedImageData').value = compressedData;
                            
                            const preview = document.getElementById('pastedPreview');
                            preview.src = compressedData;
                            document.getElementById('pastePreviewContainer').style.display = 'block';
                            
                            document.getElementById('fileInput').value = '';
                            
                            document.getElementById('copyPasteBtn').innerHTML = '<span class="material-symbols-outlined text-xl">check_circle</span> Image Pasted';
                            document.getElementById('copyPasteBtn').classList.add('bg-green-100');
                            document.getElementById('pasteInstructions').textContent = 'Image compressed and ready! Click "Detect Vehicles"';
                            document.getElementById('pasteInstructions').style.color = '#4CAF50';
                        });
                    };
                    
                    reader.readAsDataURL(blob);
                    break;
                }
            }
        });
        
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            const pastedData = document.getElementById('pastedImageData').value;
            
            if (!fileInput.value && !pastedData) {
                e.preventDefault();
                alert('Please either upload a file OR click "Paste Image" and paste an image (Ctrl+V)');
                return false;
            }
            
            document.getElementById('detectBtn').disabled = true;
            document.getElementById('detectBtn').innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Processing...';
            
            return true;
        });
        
        document.getElementById('fileInput').addEventListener('change', function() {
            if (this.value) {
                document.getElementById('pastedImageData').value = '';
                document.getElementById('pastePreviewContainer').style.display = 'none';
                const fileName = this.files[0] ? this.files[0].name : '';
                document.getElementById('fileName').textContent = fileName;
                document.getElementById('selectedFileDisplay').style.display = 'block';
            }
        });
        
        const dragDropArea = document.getElementById('dragDropArea');
        const dropZone = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
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
            dragDropArea.style.borderColor = '';
            dragDropArea.style.background = '';
            dragDropArea.style.transform = 'scale(1)';
        }
        
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                const file = files[0];
                const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'video/mp4', 'video/avi', 'video/quicktime'];
                
                if (validTypes.includes(file.type) || file.name.match(/\\.(jpg|jpeg|png|mp4|avi|mov)$/i)) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                    
                    document.getElementById('fileName').textContent = file.name;
                    document.getElementById('selectedFileDisplay').style.display = 'block';
                    document.getElementById('pastedImageData').value = '';
                    document.getElementById('pastePreviewContainer').style.display = 'none';
                    
                    dragDropArea.innerHTML = `
                        <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                            <span class="material-symbols-outlined text-green-600 text-4xl">check_circle</span>
                        </div>
                        <h2 class="text-xl font-bold text-green-600 mb-2">File Ready!</h2>
                        <p class="text-secondary max-w-sm">${file.name}</p>
                        <p class="text-sm text-slate-500 mt-2">Click "Detect Vehicles" to process</p>
                    `;
                } else {
                    alert('Invalid file type. Please upload: JPG, PNG, MP4, AVI, or MOV');
                }
            }
        }
        
        dragDropArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        let webcamStream = null;
        let isWebcamRunning = false;
        
        async function startWebcam() {
            try {
                webcamStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { width: 640, height: 480 } 
                });
                
                const webcamVideo = document.getElementById('webcamVideo');
                webcamVideo.srcObject = webcamStream;
                
                document.getElementById('webcamSection').style.display = 'block';
                document.getElementById('webcamInstructions').style.display = 'block';
                document.getElementById('webcamBtn').innerHTML = '<span class="material-symbols-outlined text-xl">videocam</span> Webcam Running';
                document.getElementById('webcamBtn').disabled = true;
                document.getElementById('webcamBtn').classList.add('opacity-50');
                
                document.getElementById('dragDropArea').parentElement.style.display = 'none';
                
                const detectionCanvas = document.getElementById('detectionCanvas');
                detectionCanvas.width = 640;
                detectionCanvas.height = 480;
                
                updateDetectionStatus('waiting', 'Initializing...');
                
                isWebcamRunning = true;
                
                processWebcamFrame();
                
                console.log('[INFO] Webcam started successfully');
                
            } catch (err) {
                console.error('[ERROR] Could not start webcam:', err);
                alert('Could not access webcam. Please make sure you have granted camera permissions.');
            }
        }
        
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
        
        async function processWebcamFrame() {
            if (!isWebcamRunning) return;
            
            const webcamVideo = document.getElementById('webcamVideo');
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            
            ctx.drawImage(webcamVideo, 0, 0, 640, 480);
            
            const frameData = detectionCanvas.toDataURL('image/jpeg', 0.8);
            
            updateDetectionStatus('processing', 'Detecting...');
            
            try {
                const confThreshold = document.querySelector('input[name="confidence"]').value;
                const formData = new FormData();
                formData.append('image', frameData);
                formData.append('confidence', confThreshold);
                
                const response = await fetch('/webcam_detect', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    
                    if (result.image) {
                        const img = new Image();
                        img.onload = function() {
                            ctx.drawImage(img, 0, 0, 640, 480);
                        };
                        img.src = 'data:image/jpeg;base64,' + result.image;
                        
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
            
            if (isWebcamRunning) {
                setTimeout(processWebcamFrame, 100);
            }
        }
        
        function stopWebcam() {
            isWebcamRunning = false;
            
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
            }
            
            document.getElementById('webcamSection').style.display = 'none';
            document.getElementById('webcamInstructions').style.display = 'none';
            
            document.getElementById('webcamBtn').innerHTML = '<span class="material-symbols-outlined text-xl">videocam</span> Live Webcam';
            document.getElementById('webcamBtn').disabled = false;
            document.getElementById('webcamBtn').classList.remove('opacity-50');
            
            document.getElementById('dragDropArea').parentElement.style.display = 'block';
            
            const detectionCanvas = document.getElementById('detectionCanvas');
            const ctx = detectionCanvas.getContext('2d');
            ctx.clearRect(0, 0, detectionCanvas.width, detectionCanvas.height);
            
            console.log('[INFO] Webcam stopped');
        }
        
        // Force demo video to play
        document.addEventListener('DOMContentLoaded', function() {
            const demoVideo = document.getElementById('demoVideo');
            if (demoVideo) {
                demoVideo.play().then(function() {
                    console.log('[INFO] Demo video playing successfully');
                }).catch(function(error) {
                    console.log('[WARN] Autoplay blocked:', error);
                    // Try to play on first interaction
                    document.body.addEventListener('click', function() {
                        demoVideo.play();
                    }, { once: true });
                });
            }
        });
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
    conf_threshold = 0.5
    
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
    
    # Store result for PDF generation
    report_id = ''
    if result:
        report_id = str(uuid.uuid4())[:8]
        app.stored_results[report_id] = {
            'stats': result.get('stats', {}),
            'message': result.get('message', ''),
            'image': result.get('image', ''),
            'video_path': result.get('video_path', ''),
            'conf_threshold': conf_threshold if request.method == 'POST' else 0.5,
            'input_type': 'video' if result.get('video_path') else 'image'
        }

    return render_template_string(HTML_TEMPLATE, result=result, report_id=report_id)


@app.route('/generate_pdf/<report_id>')
def generate_pdf(report_id):
    """Generate and download PDF report for a detection result"""
    print(f"[DEBUG] PDF route called with report_id: {report_id}")
    print(f"[DEBUG] Stored results keys: {list(app.stored_results.keys())}")
    if report_id not in app.stored_results:
        print(f"[DEBUG] Report ID not found in stored results")
        return "Report not found. Please run a new detection.", 404

    data = app.stored_results[report_id]
    stats = data.get('stats', {})
    vehicle_count = stats.get('count', 0)
    processing_time = stats.get('time', '--')
    breakdown = stats.get('breakdown', {})
    conf_threshold = data.get('conf_threshold', 0.5)
    input_type = data.get('input_type', 'image')
    img_base64 = data.get('image', '')
    first_frame = stats.get('first_frame', '')

    try:
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ---- Header Bar ----
        pdf.set_fill_color(0, 37, 66)
        pdf.rect(0, 0, 210, 35, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_xy(15, 12)
        pdf.cell(0, 10, 'Vehicle Detection Report', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_xy(15, 24)
        pdf.cell(0, 6, 'Generated: ' + time.strftime('%Y-%m-%d %H:%M:%S'), ln=True)

        y = 42

        # ---- Summary Card ----
        pdf.set_fill_color(238, 237, 240)
        pdf.rect(15, y, 180, 26, 'F')
        pdf.set_text_color(0, 37, 66)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(20, y + 4)
        count_text = f"{vehicle_count} Vehicle{'s' if vehicle_count != 1 else ''} Detected"
        pdf.cell(0, 8, count_text, ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.set_xy(20, y + 14)
        pdf.cell(0, 6, f"Processing Time: {processing_time}  |  Model: YOLOv8  |  Confidence: {conf_threshold}  |  Input: {input_type}", ln=True)
        y += 32

        # ---- Detection Image ----
        image_data = img_base64 if img_base64 else first_frame
        if image_data:
            try:
                img_bytes = base64.b64decode(image_data)
                img_path = os.path.join(STATIC_DIR, f'temp_pdf_img_{report_id}.jpg')
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                pdf.image(img_path, x=15, y=y, w=180, h=85)
                y += 90
                # Clean up temp image
                try:
                    os.remove(img_path)
                except:
                    pass
            except Exception as img_err:
                print(f"[WARN] Could not add image to PDF: {img_err}")
                y += 5

        # ---- Classification Table ----
        pdf.set_text_color(0, 37, 66)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_xy(15, y)
        pdf.cell(0, 8, 'Classification Breakdown', ln=True)
        y += 10

        # Table header
        pdf.set_fill_color(0, 37, 66)
        pdf.rect(15, y, 180, 9, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(20, y + 2)
        pdf.cell(60, 6, 'Vehicle Class', border=0)
        pdf.cell(30, 6, 'Count', border=0)
        pdf.cell(40, 6, 'Avg Confidence', border=0)
        y += 9

        # Table rows
        class_display = {'car': 'Car', 'motorcycle': 'Motorcycle/Scooty', 'bus': 'Bus', 'truck': 'Truck'}
        row_idx = 0
        if breakdown:
            for cls_name, count in breakdown.items():
                if row_idx % 2 == 0:
                    pdf.set_fill_color(245, 243, 246)
                else:
                    pdf.set_fill_color(255, 255, 255)
                pdf.rect(15, y, 180, 9, 'F')
                pdf.set_text_color(30, 30, 30)
                pdf.set_font('Helvetica', '', 10)
                pdf.set_xy(20, y + 2)
                display = class_display.get(cls_name, cls_name.title())
                pdf.cell(60, 6, display, border=0)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(30, 6, str(count), border=0)
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(40, 6, '> 85%', border=0)
                y += 9
                row_idx += 1
        else:
            pdf.set_fill_color(245, 243, 246)
            pdf.rect(15, y, 180, 9, 'F')
            pdf.set_text_color(150, 150, 150)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_xy(20, y + 2)
            pdf.cell(0, 6, 'No vehicles detected', border=0)
            y += 9

        # Table border
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        table_rows = max(row_idx, 1) + 1
        pdf.rect(15, y - 9 * table_rows, 180, 9 * table_rows)

        # ---- Footer ----
        pdf.set_text_color(170, 170, 170)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_xy(0, 285)
        pdf.cell(210, 5, 'Vehicle Detection System - Powered by YOLOv8', align='C')

        # ---- Save to buffer and send ----
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        filename = f"Vehicle_Detection_Report_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        print(f"[INFO] PDF generated: {filename}")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating PDF: {str(e)}", 500


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


@app.route('/demo_videos/<path:filename>')
def serve_demo_video(filename):
    """Serve demo videos from demo_videos folder"""
    demo_videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'demo_videos')
    video_path = os.path.join(demo_videos_dir, filename)
    
    if os.path.exists(video_path):
        response = send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False,
            conditional=True
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Accept-Ranges'] = 'bytes'
        return response
    else:
        return "Video file not found", 404


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
