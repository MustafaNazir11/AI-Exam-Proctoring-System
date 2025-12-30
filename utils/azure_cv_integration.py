"""
Simplified Azure Computer Vision Integration
"""

import cv2
import numpy as np
from .azure_cv_enhanced import init_azure_cv_enhanced
from .integrated_face_object_detector import init_integrated_detector, analyze_frame_integrated
from .enhanced_violation_analyzer import EnhancedViolationAnalyzer

class AzureCVIntegration:
    def __init__(self):
        self.azure_cv = init_azure_cv_enhanced()
        self.integrated_detector = init_integrated_detector()
        self.violation_analyzer = EnhancedViolationAnalyzer()
        self.initialized = bool(self.azure_cv and self.integrated_detector)
    
    def analyze_frame_complete(self, frame, peer_id=None, use_azure=True):
        if not self.initialized:
            return {'error': 'System not initialized', 'is_suspicious': True, 'severity': 'CRITICAL'}
        
        try:
            detection_results = analyze_frame_integrated(frame, peer_id, use_azure)
            violation_analysis = self.violation_analyzer.analyze_comprehensive_violation(detection_results)
            
            return {
                'is_suspicious': violation_analysis['is_violation'],
                'suspicion_score': violation_analysis['total_score'],
                'severity': violation_analysis['severity'].value,
                'reasons': [v['description'] for v in violation_analysis['violations']],
                'annotated_frame': detection_results.get('annotated_frame')
            }
        except Exception as e:
            return {'error': str(e), 'is_suspicious': True, 'severity': 'CRITICAL', 'annotated_frame': frame}

# Global instance
azure_cv_integration = None

def init_azure_cv_integration():
    global azure_cv_integration
    try:
        azure_cv_integration = AzureCVIntegration()
        return azure_cv_integration if azure_cv_integration.initialized else None
    except Exception:
        return None

def get_azure_cv_integration():
    return azure_cv_integration

def analyze_frame_with_azure_cv(frame, peer_id=None, use_azure=True):
    integration = get_azure_cv_integration()
    if not integration:
        return {'error': 'Integration not available', 'is_suspicious': False, 'annotated_frame': frame}
    return integration.analyze_frame_complete(frame, peer_id, use_azure)

def test_azure_cv_integration():
    """Test function for Azure CV integration"""
    integration = get_azure_cv_integration()
    if not integration:
        print("❌ Azure CV Integration not initialized")
        return False
    print("✅ Azure CV Integration test passed")
    return True

def debug_azure_status():
    """Debug function to check Azure services status"""
    integration = get_azure_cv_integration()
    if not integration:
        return {"azure_integration": False, "azure_cv": False, "integrated_detector": False}
    
    return {
        "azure_integration": integration.initialized,
        "azure_cv": integration.azure_cv is not None,
        "integrated_detector": integration.integrated_detector is not None,
        "azure_cv_type": type(integration.azure_cv).__name__ if integration.azure_cv else None
    }