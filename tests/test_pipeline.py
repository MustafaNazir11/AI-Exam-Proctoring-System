import requests
import base64
import cv2
import numpy as np
import json
import os

# Check for any screenshot in the screenshots folder
screenshots_folder = 'static/screenshots/'
if os.path.exists(screenshots_folder):
    screenshot_files = [f for f in os.listdir(screenshots_folder) if f.endswith('.png')]
    if screenshot_files:
        # Use the first available screenshot
        screenshot_path = os.path.join(screenshots_folder, screenshot_files[0])
        print(f"📸 Found screenshot: {screenshot_path}")
    else:
        screenshot_path = 'static/screenshots/screenshot_20251220_134917_087765.png'
else:
    screenshot_path = 'static/screenshots/screenshot_20251220_134917_087765.png'
img = cv2.imread(screenshot_path)

if img is None:
    print(f"❌ No screenshot found at {screenshot_path}")
    print("This means no browser activity was captured.")
    
    # Test with no image data to simulate no browser activity
    payload = {
        "peerId": "test_peer_123"
    }
    
    try:
        response = requests.post('http://127.0.0.1:5000/pipeline0/frame', 
                               json=payload, 
                               timeout=10)
        print("✅ Pipeline 0 Response (No Image):", response.json())
    except Exception as e:
        print("❌ Pipeline 0 Error:", e)
else:
    print(f"✅ Screenshot found at {screenshot_path}")
    
    # Convert to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    img_data = f"data:image/jpeg;base64,{img_base64}"
    
    # Test Pipeline 0 with real screenshot
    payload = {
        "image": img_data,
        "peerId": "test_peer_123"
    }
    
    try:
        response = requests.post('http://127.0.0.1:5000/pipeline0/frame', 
                               json=payload, 
                               timeout=10)
        print("✅ Pipeline 0 Response (With Image):", response.json())
    except Exception as e:
        print("❌ Pipeline 0 Error:", e)