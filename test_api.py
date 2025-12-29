import requests
import base64
import cv2
import numpy as np

def test_pipeline_api():
    """Test the integrated pipeline via Flask API"""
    
    # Create test image
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    cv2.rectangle(frame, (250, 150), (390, 330), (255, 200, 150), -1)
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    img_data = f"data:image/jpeg;base64,{img_base64}"
    
    # Test API
    url = "http://127.0.0.1:5000/pipeline1/analyze"
    response = requests.post(url, json={"image": img_data})
    
    print("API Response:", response.json())
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing Pipeline API...")
    success = test_pipeline_api()
    print("✅ Success!" if success else "❌ Failed!")