import cv2
import numpy as np

class Pipeline1LocalChecks:
    def __init__(self):
        # Initialize Haar Cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.prev_frame = None
        
    def blur_detection(self, frame):
        """Detect blur using Variance of Laplacian"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return variance < 100  # True if blurry
    
    def brightness_check(self, frame):
        """Check if frame is too dark or too bright"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return mean_brightness < 50 or mean_brightness > 200  # True if problematic
    
    def face_presence_check(self, frame):
        """Basic face presence using Haar Cascade"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) == 0  # True if no face detected
    
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
        return motion_percentage > 30  # True if excessive motion
    
    def analyze_frame(self, frame):
        """Run all local checks and return results"""
        checks = {
            'blur': self.blur_detection(frame),
            'brightness': self.brightness_check(frame),
            'no_face': self.face_presence_check(frame),
            'excessive_motion': self.motion_detection(frame)
        }
        
        failed_checks = [check for check, failed in checks.items() if failed]
        suspicious = len(failed_checks) >= 2
        
        return {
            'suspicious': suspicious,
            'failed_checks': failed_checks,
            'check_results': checks
        }

# Global instance for reuse
pipeline1_checker = Pipeline1LocalChecks()

def pipeline1_local_checks(frame):
    """Main function to be called from Flask route"""
    return pipeline1_checker.analyze_frame(frame)