import cv2
import numpy as np
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_integrated_pipeline():
    """Test the integrated pipeline with sample frames"""
    try:
        from utils.integrated_pipeline import integrated_pipeline_analysis
        
        # Create test frames
        # Normal frame (should not be suspicious)
        normal_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        cv2.rectangle(normal_frame, (250, 150), (390, 330), (255, 200, 150), -1)  # Face-like rectangle
        
        # Suspicious frame (very dark)
        dark_frame = np.ones((480, 640, 3), dtype=np.uint8) * 20
        
        # Blurry frame
        blurry_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        blurry_frame = cv2.GaussianBlur(blurry_frame, (51, 51), 0)
        
        print("🧪 Testing Integrated Pipeline")
        print("=" * 50)
        
        # Test normal frame
        result1 = integrated_pipeline_analysis(normal_frame)
        print(f"Normal frame - Suspicious: {result1['suspicious']}")
        print(f"Failed checks: {result1['failed_checks']}")
        print(f"Azure analyzed: {result1['azure_analyzed']}")
        print()
        
        # Test dark frame
        result2 = integrated_pipeline_analysis(dark_frame)
        print(f"Dark frame - Suspicious: {result2['suspicious']}")
        print(f"Failed checks: {result2['failed_checks']}")
        print(f"Azure analyzed: {result2['azure_analyzed']}")
        print()
        
        # Test blurry frame
        result3 = integrated_pipeline_analysis(blurry_frame)
        print(f"Blurry frame - Suspicious: {result3['suspicious']}")
        print(f"Failed checks: {result3['failed_checks']}")
        print(f"Azure analyzed: {result3['azure_analyzed']}")
        print()
        
        print("✅ Integrated pipeline test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_integrated_pipeline()