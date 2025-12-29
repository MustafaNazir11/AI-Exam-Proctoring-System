"""
Integrated Pipeline Usage Example
=================================

This example demonstrates how the integrated pipeline works:
1. Local checks are performed first (fast)
2. Only suspicious frames are sent to Azure Face API (expensive)
3. Final decision combines both results

Benefits:
- Reduced API costs (only suspicious frames sent to Azure)
- Faster processing (local checks are quick)
- Better accuracy (Azure provides detailed analysis when needed)
"""

import cv2
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_integrated_pipeline():
    """Demonstrate the integrated pipeline with different scenarios"""
    
    try:
        from utils.integrated_pipeline import integrated_pipeline_analysis
        from utils.pipeline_config import PipelineConfig
        
        print("🚀 Integrated Pipeline Demo")
        print("=" * 50)
        print(f"Configuration:")
        print(f"  - Blur threshold: {PipelineConfig.BLUR_THRESHOLD}")
        print(f"  - Brightness range: {PipelineConfig.BRIGHTNESS_MIN}-{PipelineConfig.BRIGHTNESS_MAX}")
        print(f"  - Motion threshold: {PipelineConfig.MOTION_THRESHOLD}%")
        print(f"  - Azure on critical: {PipelineConfig.AZURE_ON_CRITICAL}")
        print(f"  - Local suspicion threshold: {PipelineConfig.LOCAL_SUSPICION_THRESHOLD}")
        print()
        
        # Scenario 1: Normal frame (should pass local checks)
        print("📸 Scenario 1: Normal Frame")
        normal_frame = create_normal_frame()
        result = integrated_pipeline_analysis(normal_frame)
        print_result(result, "Normal frame should not trigger Azure API")
        
        # Scenario 2: Dark frame (should trigger Azure due to quality issues)
        print("📸 Scenario 2: Dark Frame")
        dark_frame = create_dark_frame()
        result = integrated_pipeline_analysis(dark_frame)
        print_result(result, "Dark frame should trigger local suspicion")
        
        # Scenario 3: No face frame (should trigger Azure due to critical flag)
        print("📸 Scenario 3: No Face Frame")
        no_face_frame = create_no_face_frame()
        result = integrated_pipeline_analysis(no_face_frame)
        print_result(result, "No face should trigger Azure analysis")
        
        print("\n✅ Demo completed! The pipeline efficiently routes frames:")
        print("   • Normal frames: Local checks only (fast)")
        print("   • Suspicious frames: Local + Azure analysis (accurate)")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("Make sure Azure Face API is properly configured if you want full functionality.")

def create_normal_frame():
    """Create a normal-looking frame"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128  # Medium brightness
    # Add a face-like rectangle
    cv2.rectangle(frame, (250, 150), (390, 330), (255, 200, 150), -1)
    return frame

def create_dark_frame():
    """Create a dark frame (brightness issue)"""
    return np.ones((480, 640, 3), dtype=np.uint8) * 20  # Very dark

def create_no_face_frame():
    """Create a frame with no detectable face"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    # Add some noise but no face-like features
    noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
    return cv2.add(frame, noise)

def print_result(result, description):
    """Print analysis result in a formatted way"""
    print(f"  Description: {description}")
    print(f"  Suspicious: {result['suspicious']}")
    print(f"  Failed checks: {result['failed_checks']}")
    print(f"  Azure analyzed: {result['azure_analyzed']}")
    if result['azure_results']:
        azure = result['azure_results']
        print(f"  Azure face count: {azure['face_count']}")
        print(f"  Azure indicators: {azure['suspicious_indicators']}")
    print()

if __name__ == "__main__":
    demo_integrated_pipeline()