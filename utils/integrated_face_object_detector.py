import cv2
import numpy as np
from .face_detector import detect_faces
from .azure_cv_enhanced import get_azure_cv_enhanced
from .violation_rules import create_violation_entry

class IntegratedDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.azure_cv = get_azure_cv_enhanced()
        
    def detect_comprehensive(self, frame, use_azure=True):
        """
        Comprehensive detection using both local OpenCV and Azure Computer Vision
        """
        results = {
            'local_detection': {},
            'azure_detection': {},
            'combined_analysis': {},
            'annotated_frame': frame.copy()
        }
        
        # Local OpenCV detection
        local_faces, annotated_frame = detect_faces(frame)
        results['local_detection'] = {
            'faces': local_faces,
            'face_count': len(local_faces)
        }
        results['annotated_frame'] = annotated_frame
        
        # Azure Computer Vision analysis (if enabled and available)
        if use_azure and self.azure_cv:
            try:
                azure_results = self.azure_cv.analyze_frame_comprehensive(frame)
                results['azure_detection'] = azure_results
                
                # Add Azure object annotations to frame
                if 'objects' in azure_results:
                    results['annotated_frame'] = self._annotate_azure_objects(
                        results['annotated_frame'], 
                        azure_results['objects']
                    )
                    
            except Exception as e:
                results['azure_detection'] = {
                    'error': str(e),
                    'objects': [],
                    'faces': [],
                    'suspicion_analysis': {
                        'is_suspicious': False,
                        'suspicion_score': 0,
                        'reasons': ['Azure analysis unavailable']
                    }
                }
        
        # Combined analysis
        results['combined_analysis'] = self._combine_analysis(
            results['local_detection'], 
            results['azure_detection']
        )
        
        return results
    
    def _annotate_azure_objects(self, frame, objects):
        """Add Azure-detected objects to the frame"""
        for obj in objects:
            if obj['confidence'] > 0.5:  # Only show high-confidence objects
                rect = obj['rectangle']
                x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']
                
                # Different colors for different object types
                color = self._get_object_color(obj['name'])
                
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw label with confidence
                label = f"{obj['name']} ({obj['confidence']:.1%})"
                cv2.putText(frame, label, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame
    
    def _get_object_color(self, object_name):
        """Get color based on object suspicion level"""
        suspicious_objects = {
            'phone', 'mobile phone', 'cell phone', 'smartphone',
            'book', 'notebook', 'paper', 'document'
        }
        
        if any(sus in object_name.lower() for sus in suspicious_objects):
            return (0, 0, 255)  # Red for suspicious objects
        else:
            return (255, 165, 0)  # Orange for other objects
    
    def _combine_analysis(self, local_results, azure_results):
        """Combine local and Azure analysis for final decision"""
        combined = {
            'is_suspicious': False,
            'suspicion_score': 0,
            'reasons': [],
            'violation_type': 'none',
            'confidence': 0.0
        }
        
        # Local face analysis
        local_face_count = local_results.get('face_count', 0)
        
        # Azure analysis (if available)
        azure_suspicion = azure_results.get('suspicion_analysis', {})
        azure_face_count = azure_results.get('face_count', 0)
        
        # Face count analysis (prioritize Azure if available)
        face_count = azure_face_count if azure_face_count > 0 else local_face_count
        
        if face_count == 0:
            combined['suspicion_score'] += 40
            combined['reasons'].append("No face detected - student absence")
            combined['violation_type'] = 'absence'
        elif face_count > 1:
            combined['suspicion_score'] += 60
            combined['reasons'].append(f"Multiple faces detected ({face_count})")
            combined['violation_type'] = 'multiple_persons'
        
        # Add Azure-specific analysis
        if azure_suspicion:
            combined['suspicion_score'] += azure_suspicion.get('suspicion_score', 0) * 0.6  # Weight Azure analysis
            combined['reasons'].extend(azure_suspicion.get('reasons', []))
            
            # Check for high-risk objects
            detected_objects = azure_suspicion.get('detected_objects', [])
            high_risk_objects = ['phone', 'book', 'paper', 'notebook']
            
            for obj in detected_objects:
                if any(risk in obj.lower() for risk in high_risk_objects):
                    combined['violation_type'] = 'unauthorized_materials'
                    break
        
        # Final decision
        combined['suspicion_score'] = min(combined['suspicion_score'], 100)
        combined['is_suspicious'] = combined['suspicion_score'] >= 50
        combined['confidence'] = min(combined['suspicion_score'] / 100.0, 1.0)
        
        # Determine violation severity
        if combined['suspicion_score'] >= 80:
            combined['severity'] = 'CRITICAL'
        elif combined['suspicion_score'] >= 60:
            combined['severity'] = 'HIGH'
        elif combined['suspicion_score'] >= 40:
            combined['severity'] = 'MEDIUM'
        else:
            combined['severity'] = 'LOW'
        
        return combined
    
    def create_violation_report(self, peer_id, analysis_results):
        """Create a violation report based on analysis results"""
        combined_analysis = analysis_results.get('combined_analysis', {})
        
        if combined_analysis.get('is_suspicious', False):
            return create_violation_entry(peer_id, combined_analysis.get('reasons', []))
        
        return None

# Global instance
integrated_detector = None

def init_integrated_detector():
    """Initialize the integrated detector"""
    global integrated_detector
    try:
        integrated_detector = IntegratedDetector()
        print("✅ Integrated Detector initialized")
        return integrated_detector
    except Exception as e:
        print(f"❌ Failed to initialize Integrated Detector: {e}")
        return None

def get_integrated_detector():
    """Get the global integrated detector instance"""
    return integrated_detector

def analyze_frame_integrated(frame, peer_id=None, use_azure=True):
    """
    Main function for integrated frame analysis
    Returns comprehensive analysis results
    """
    detector = get_integrated_detector()
    if not detector:
        return {
            'error': 'Integrated detector not initialized',
            'is_suspicious': True,
            'reasons': ['System error - detector unavailable']
        }
    
    # Perform comprehensive detection
    results = detector.detect_comprehensive(frame, use_azure=use_azure)
    
    # Create violation report if needed
    if peer_id and results['combined_analysis'].get('is_suspicious'):
        violation_report = detector.create_violation_report(peer_id, results)
        results['violation_report'] = violation_report
    
    return results