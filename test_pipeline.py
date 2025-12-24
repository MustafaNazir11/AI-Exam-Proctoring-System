import requests
import base64
import cv2
import json

# Create a test image
img = cv2.imread('static/screenshots/screenshot_20251220_134917_087765.png')
if img is None:
    # Create blank test image if no screenshot exists
    img = cv2.zeros((480, 640, 3), dtype=cv2.uint8)
    cv2.putText(img, 'TEST FRAME', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)

# Convert to base64
_, buffer = cv2.imencode('.jpg', img)
img_base64 = base64.b64encode(buffer).decode('utf-8')
img_data = f"data:image/jpeg;base64,{img_base64}"

# Test Pipeline 0
payload = {
    "image": img_data,
    "peerId": "test_peer_123"
}

try:
    response = requests.post('http://127.0.0.1:5000/pipeline0/frame', 
                           json=payload, 
                           timeout=10)
    print("✅ Pipeline 0 Response:", response.json())
except Exception as e:
    print("❌ Pipeline 0 Error:", e)