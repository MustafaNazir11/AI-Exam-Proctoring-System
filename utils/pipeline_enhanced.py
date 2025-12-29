import cv2
import numpy as np
from .azure_face_api import get_azure_face_detector

class EnhancedPipeline:
    def __init__(self):
        # Initialize Haar Cascade for fallback
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.prev_frame = None
        
    def blur_detection(self, frame):
        """Detect blur using Variance of Laplacian"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance < 100
    
    def brightness_check(self, frame):
        """Check if frame is too dark or too bright"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return mean_brightness < 50 or mean_brightness > 200
    
    def motion_detection(self, frame):
        """Detect excessive motion using frame differencing"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return False
        
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
        motion_pixels = cv2.countNonZero(thresh)
        motion_percentage = (motion_pixels / (frame.shape[0] * frame.shape[1])) * 100
        
        self.prev_frame = gray
        return motion_percentage > 30
    
    def fallback_face_detection(self, frame):
        """Fallback face detection using Haar Cascade"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) == 0
    
    def analyze_frame_enhanced(self, frame):
        """Enhanced analysis with Azure Face API + local checks"""
        # Local checks
        local_checks = {
            'blur': self.blur_detection(frame),
            'brightness': self.brightness_check(frame),
            'excessive_motion': self.motion_detection(frame)
        }
        
        # Azure Face API analysis
        azure_detector = get_azure_face_detector()
        azure_results = None
        
        if azure_detector:
            try:
                azure_results = azure_detector.detect_faces_azure(frame)
                # Add Azure-specific checks
                local_checks['azure_no_face'] = azure_results['face_count'] == 0
                local_checks['azure_multiple_faces'] = azure_results['face_count'] > 1
                local_checks['azure_suspicious_behavior'] = len(azure_results['suspicious_indicators']) > 0
            except Exception as e:
                print(f"Azure API failed, using fallback: {e}")
                local_checks['no_face'] = self.fallback_face_detection(frame)
        else:
            # Fallback to Haar Cascade
            local_checks['no_face'] = self.fallback_face_detection(frame)
        
        # Determine suspicion level
        failed_checks = [check for check, failed in local_checks.items() if failed]
        
        # Enhanced suspicion logic
        critical_failures = ['azure_multiple_faces', 'azure_suspicious_behavior']
        has_critical = any(check in failed_checks for check in critical_failures)
        
        suspicious = has_critical or len(failed_checks) >= 2
        
        return {
            'suspicious': suspicious,
            'failed_checks': failed_checks,
            'check_results': local_checks,
            'azure_results': azure_results,
            'critical_violation': has_critical
        }

# Global instance
enhanced_pipeline = EnhancedPipeline()

def pipeline_enhanced_checks(frame):
    """Main function for enhanced pipeline with Azure Face API"""
    return enhanced_pipeline.analyze_frame_enhanced(frame)