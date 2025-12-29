import os
import sys
import cv2
import glob
from dotenv import load_dotenv
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.azure_face_api import init_azure_face_detector
from utils.pipeline_enhanced import pipeline_enhanced_checks

def test_with_existing_screenshots():
    """Test using existing screenshots from the static/screenshots folder"""
    
    screenshots_path = "static/screenshots/*.png"
    image_files = glob.glob(screenshots_path)
    
    if not image_files:
        print("No existing screenshots found in static/screenshots/")
        return False
    
    print(f"Found {len(image_files)} existing screenshots to test with")
    
    # Test with first few screenshots
    for i, img_path in enumerate(image_files[:3]):  # Test first 3 images
        print(f"\n--- Testing screenshot {i+1}: {os.path.basename(img_path)} ---")
        
        try:
            frame = cv2.imread(img_path)
            if frame is None:
                print(f"Could not load image: {img_path}")
                continue
                
            result = pipeline_enhanced_checks(frame)
            
            print(f"Suspicious: {result['suspicious']}")
            print(f"Failed checks: {result['failed_checks']}")
            
            if result.get('azure_results'):
                azure = result['azure_results']
                print(f"Azure face count: {azure['face_count']}")
                if azure['faces']:
                    face = azure['faces'][0]
                    emotions = face['emotions']
                    dominant = max(emotions, key=emotions.get)
                    print(f"Primary face: Age {face['age']}, {face['gender']}, {dominant}")
                    
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    
    return True

def quick_webcam_test():
    """Quick webcam test for Azure Face API"""
    
    print("Testing with webcam (press 'q' to quit, 's' to analyze frame)")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam")
        return False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        cv2.imshow('Webcam Test - Press S to analyze, Q to quit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("\nAnalyzing current frame...")
            try:
                result = pipeline_enhanced_checks(frame)
                print(f"Suspicious: {result['suspicious']}")
                print(f"Failed checks: {result['failed_checks']}")
                
                if result.get('azure_results'):
                    azure = result['azure_results']
                    print(f"Azure detected {azure['face_count']} faces")
                    for i, face in enumerate(azure['faces']):
                        emotions = face['emotions']
                        dominant = max(emotions, key=emotions.get)
                        print(f"Face {i+1}: {dominant} ({emotions[dominant]:.2f})")
                        
            except Exception as e:
                print(f"Analysis error: {e}")
    
    cap.release()
    cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Initialize Azure if available
    api_key = os.getenv('AZURE_FACE_API_KEY')
    if api_key and api_key != 'your_azure_face_api_key_here':
        try:
            init_azure_face_detector(api_key)
            print("Azure Face API initialized")
        except Exception as e:
            print(f"Azure init failed: {e}")
    else:
        print("Testing with fallback detection only")
    
    print("\nChoose test option:")
    print("1. Test with existing screenshots")
    print("2. Interactive webcam test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        quick_webcam_test()
    else:
        test_with_existing_screenshots()