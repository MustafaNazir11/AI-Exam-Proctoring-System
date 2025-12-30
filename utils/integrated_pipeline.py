import cv2
import numpy as np
from .azure_face_api import get_azure_face_detector
from .pipeline_config import PipelineConfig

class IntegratedPipeline:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.prev_frame = None
        
    def local_checks(self, frame):
        """Pipeline 1: Fast local checks"""
        checks = {}
        
        # Blur detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        checks['blur'] = variance < PipelineConfig.BLUR_THRESHOLD
        
        # Brightness check
        mean_brightness = np.mean(gray)
        checks['brightness'] = (mean_brightness < PipelineConfig.BRIGHTNESS_MIN or 
                               mean_brightness > PipelineConfig.BRIGHTNESS_MAX)
        
        # Basic face presence
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        checks['no_face'] = len(faces) == 0
        checks['multiple_faces_local'] = len(faces) > 1
        
        # Motion detection
        gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.prev_frame is not None:
            frame_diff = cv2.absdiff(self.prev_frame, gray_blur)
            thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
            motion_pixels = cv2.countNonZero(thresh)
            motion_percentage = (motion_pixels / (frame.shape[0] * frame.shape[1])) * 100
            checks['excessive_motion'] = motion_percentage > PipelineConfig.MOTION_THRESHOLD
        else:
            checks['excessive_motion'] = False
        self.prev_frame = gray_blur
        
        return checks
    
    def is_suspicious_locally(self, local_results):
        """Determine if frame needs Azure API analysis"""
        if not PipelineConfig.AZURE_ON_CRITICAL:
            return len([k for k, v in local_results.items() if v]) >= PipelineConfig.LOCAL_SUSPICION_THRESHOLD
            
        critical_flags = PipelineConfig.get_critical_flags()
        quality_flags = PipelineConfig.get_quality_flags()
        
        # Send to Azure if any critical flag or multiple quality issues
        critical_count = sum(1 for flag in critical_flags if local_results.get(flag, False))
        quality_count = sum(1 for flag in quality_flags if local_results.get(flag, False))
        
        return critical_count > 0 or quality_count >= PipelineConfig.AZURE_ON_QUALITY_ISSUES
    
    def azure_analysis(self, frame):
        """Pipeline 2: Azure Face API for suspicious frames"""
        azure_detector = get_azure_face_detector()
        if not azure_detector:
            print("⚠️ Azure Face detector not available")
            return None

        # 🔥 HARD VALIDATION (CRITICAL)
        if frame is None:
            print("❌ Frame is None")
            return None

        if not isinstance(frame, np.ndarray):
            print("❌ Frame is not numpy array")
            return None

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            print(f"❌ Invalid frame shape: {frame.shape}")
            return None

        if frame.dtype != np.uint8:
            print(f"❌ Invalid frame dtype: {frame.dtype}")
            return None

        # Test encoding BEFORE Azure
        success, encoded = cv2.imencode(".jpg", frame)
        if not success or encoded is None or len(encoded) < 1000:
            print("❌ Frame encoding failed or too small")
            return None

        print(f"🧪 Azure Face API ready frame: {frame.shape}, {len(encoded)} bytes")

        try:
            result = azure_detector.detect_faces_azure(frame)
            if 'error' in result:
                print(f"⚠️ Azure Face API error: {result['error']}")
                return None
            print(f"✅ Azure Face API result: {result['face_count']} faces detected")
            return result
        except Exception as e:
            print(f"⚠️ Azure Face API exception: {e}")
            return None

    def analyze_frame(self, frame):
        """Main integrated analysis"""
        print("🔍 Starting frame analysis...")
        
        # Step 1: Local checks
        local_results = self.local_checks(frame)
        failed_local = [k for k, v in local_results.items() if v]
        print(f"📊 Local checks: {failed_local if failed_local else 'All passed'}")
        
        # Step 2: Determine if Azure analysis needed
        needs_azure = self.is_suspicious_locally(local_results)
        print(f"🌐 Azure needed: {needs_azure}")
        
        azure_results = None
        if needs_azure:
            print("🚀 Calling Azure Face API...")
            azure_results = self.azure_analysis(frame)
            if azure_results:
                print(f"✅ Azure result: {azure_results['face_count']} faces, {len(azure_results['suspicious_indicators'])} indicators")
            else:
                print("❌ Azure analysis failed")
        
        # Step 3: Final decision
        failed_checks = [check for check, failed in local_results.items() if failed]
        
        # Enhanced suspicion logic with Azure
        suspicious = False
        if azure_results:
            azure_suspicious = (
                azure_results['face_count'] != 1 or 
                len(azure_results['suspicious_indicators']) > 0
            )
            suspicious = azure_suspicious or len(failed_checks) >= PipelineConfig.LOCAL_SUSPICION_THRESHOLD
        else:
            suspicious = len(failed_checks) >= PipelineConfig.LOCAL_SUSPICION_THRESHOLD
        
        print(f"🎯 Final decision: {'SUSPICIOUS' if suspicious else 'NORMAL'}")
        print("─" * 50)
        
        return {
            'suspicious': bool(suspicious),
            'failed_checks': failed_checks,
            'local_results': {k: bool(v) for k, v in local_results.items()},
            'azure_results': azure_results,
            'azure_analyzed': bool(needs_azure),
            'pipeline_used': 'integrated'
        }

# Global instance
integrated_pipeline = IntegratedPipeline()

def integrated_pipeline_analysis(frame):
    """Main function for integrated pipeline"""
    return integrated_pipeline.analyze_frame(frame)