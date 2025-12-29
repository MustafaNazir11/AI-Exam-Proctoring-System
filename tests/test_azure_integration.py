import os
import sys
import cv2
import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.azure_face_api import init_azure_face_detector, get_azure_face_detector
from utils.pipeline_enhanced import pipeline_enhanced_checks

def test_azure_integration():
    """Test Azure Face API integration"""
    
    # Test 1: Initialize Azure Face API
    print("🧪 Testing Azure Face API Integration...")
    
    # You'll need to set your API key here or in environment
    api_key = "YOUR_AZURE_FACE_API_KEY"  # Replace with your actual key
    endpoint = "https://your-region.api.cognitive.microsoft.com/"  # Replace with your endpoint
    
    try:
        detector = init_azure_face_detector(api_key, endpoint)
        print("✅ Azure Face API initialized successfully")
    except Exception as e:
        print(f"❌ Azure Face API initialization failed: {e}")
        return False
    
    # Test 2: Create test frames
    print("\n🧪 Testing with sample frames...")
    
    # Normal frame with simulated face region
    normal_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    cv2.rectangle(normal_frame, (200, 150), (400, 350), (180, 150, 120), -1)  # Face-like region
    
    # Test enhanced pipeline
    try:
        result = pipeline_enhanced_checks(normal_frame)
        print("✅ Enhanced pipeline working")
        print(f"   Suspicious: {result['suspicious']}")
        print(f"   Failed checks: {result['failed_checks']}")
        if result['azure_results']:
            print(f"   Azure face count: {result['azure_results']['face_count']}")
            print(f"   Azure indicators: {result['azure_results']['suspicious_indicators']}")
    except Exception as e:
        print(f"❌ Enhanced pipeline failed: {e}")
        return False
    
    print("\n✅ All tests passed! Azure Face API is ready to use.")
    return True

def create_env_file():
    """Create .env file with Azure configuration"""
    env_content = f"""# Azure Face API Configuration
AZURE_FACE_API_KEY=your_azure_face_api_key_here
AZURE_FACE_ENDPOINT=https://your-region.api.cognitive.microsoft.com/

# Cloudinary Configuration  
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("📝 Created .env file. Please update with your actual API keys.")

if __name__ == "__main__":
    print("🚀 Azure Face API Integration Test")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        create_env_file()
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("💡 Install python-dotenv: pip install python-dotenv")
    
    test_azure_integration()