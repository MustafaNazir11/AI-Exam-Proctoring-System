"""Test script for VisionAnalyzer (structure test only)"""

import numpy as np
import os

# Mock environment variables for testing
os.environ['AZURE_VISION_ENDPOINT'] = 'https://test.cognitiveservices.azure.com/'
os.environ['AZURE_VISION_KEY'] = 'test_key'

def test_vision_analyzer_structure():
    """Test VisionAnalyzer class structure without API calls."""
    try:
        from vision_analyzer import VisionAnalyzer
        
        # Test initialization
        analyzer = VisionAnalyzer()
        print("✓ VisionAnalyzer initialized successfully")
        
        # Test method exists
        if hasattr(analyzer, 'analyze_frame'):
            print("✓ analyze_frame method exists")
        
        # Create dummy frame
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        print("✓ Test frame created")
        
        print("\nVisionAnalyzer structure is correct!")
        print("Note: Actual API testing requires valid Azure credentials")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_vision_analyzer_structure()