import os
import io
import cv2
import numpy as np
from dotenv import load_dotenv
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials

load_dotenv()

class AzureCVEnhanced:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_CV_ENDPOINT")
        self.key = os.getenv("AZURE_CV_KEY")
        
        if not self.endpoint or not self.key:
            raise RuntimeError("Azure CV credentials not found in .env")
        
        self.client = ComputerVisionClient(
            self.endpoint,
            CognitiveServicesCredentials(self.key)
        )
        
        # Suspicious objects for exam proctoring
        self.suspicious_objects = {
            'phone', 'mobile phone', 'cell phone', 'smartphone',
            'book', 'notebook', 'paper', 'document',
            'computer', 'laptop', 'tablet', 'monitor', 'screen',
            'person', 'people', 'human',
            'watch', 'smartwatch', 'clock'
        }
        
        # High-risk objects (immediate violation)
        self.high_risk_objects = {
            'phone', 'mobile phone', 'cell phone', 'smartphone',
            'book', 'notebook', 'paper', 'document'
        }

    def frame_to_bytes(self, frame):
        """Convert OpenCV frame to bytes"""
        success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not success:
            raise ValueError("Failed to encode frame")
        return buffer.tobytes()

    def analyze_frame_comprehensive(self, frame):
        """Comprehensive analysis using Azure Computer Vision"""
        try:
            image_bytes = self.frame_to_bytes(frame)
            
            # Analyze image with multiple features
            analysis = self.client.analyze_image_in_stream(
                io.BytesIO(image_bytes),
                visual_features=["Objects", "Categories", "Description", "Faces", "Adult"]
            )
            
            # Extract detected objects
            detected_objects = []
            for obj in analysis.objects:
                detected_objects.append({
                    'name': obj.object_property.lower(),
                    'confidence': obj.confidence,
                    'rectangle': {
                        'x': obj.rectangle.x,
                        'y': obj.rectangle.y,
                        'w': obj.rectangle.w,
                        'h': obj.rectangle.h
                    }
                })
            
            # Extract faces
            detected_faces = []
            if hasattr(analysis, 'faces') and analysis.faces:
                for face in analysis.faces:
                    detected_faces.append({
                        'age': face.age,
                        'gender': face.gender.value if face.gender else 'unknown',
                        'rectangle': {
                            'left': face.face_rectangle.left,
                            'top': face.face_rectangle.top,
                            'width': face.face_rectangle.width,
                            'height': face.face_rectangle.height
                        }
                    })
            
            # Generate suspicion analysis
            suspicion_analysis = self._analyze_suspicion(detected_objects, detected_faces, analysis)
            
            return {
                'objects': detected_objects,
                'faces': detected_faces,
                'face_count': len(detected_faces),
                'description': analysis.description.captions[0].text if analysis.description.captions else "",
                'suspicion_analysis': suspicion_analysis,
                'categories': [cat.name for cat in analysis.categories] if analysis.categories else []
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'objects': [],
                'faces': [],
                'face_count': 0,
                'suspicion_analysis': {
                    'is_suspicious': True,
                    'suspicion_score': 100,
                    'reasons': [f'Analysis failed: {str(e)}']
                }
            }

    def _analyze_suspicion(self, objects, faces, analysis):
        """Analyze suspicion level based on detected objects and faces"""
        suspicion_score = 0
        reasons = []
        
        # Face analysis
        face_count = len(faces)
        if face_count == 0:
            suspicion_score += 40
            reasons.append("No face detected - student may not be present")
        elif face_count > 1:
            suspicion_score += 60
            reasons.append(f"Multiple faces detected ({face_count}) - possible unauthorized assistance")
        
        # Object analysis
        suspicious_found = []
        high_risk_found = []
        
        for obj in objects:
            obj_name = obj['name'].lower()
            confidence = obj['confidence']
            
            # Check for suspicious objects
            for suspicious in self.suspicious_objects:
                if suspicious in obj_name and confidence > 0.5:
                    suspicious_found.append(f"{obj_name} ({confidence:.1%})")
                    
                    if any(risk in obj_name for risk in self.high_risk_objects):
                        suspicion_score += 50
                        high_risk_found.append(obj_name)
                    else:
                        suspicion_score += 25
        
        if high_risk_found:
            reasons.append(f"High-risk objects detected: {', '.join(high_risk_found)}")
        
        if suspicious_found:
            reasons.append(f"Suspicious objects detected: {', '.join(suspicious_found)}")
        
        # Multiple people detection
        person_objects = [obj for obj in objects if 'person' in obj['name'].lower() and obj['confidence'] > 0.6]
        if len(person_objects) > 1:
            suspicion_score += 45
            reasons.append(f"Multiple people detected ({len(person_objects)}) - unauthorized presence")
        
        # Scene analysis based on description
        if hasattr(analysis, 'description') and analysis.description.captions:
            description = analysis.description.captions[0].text.lower()
            
            # Check for concerning scenarios
            concerning_keywords = ['looking away', 'turned away', 'multiple people', 'phone', 'book', 'paper']
            for keyword in concerning_keywords:
                if keyword in description:
                    suspicion_score += 15
                    reasons.append(f"Scene analysis: {keyword} detected in image")
        
        # Determine final suspicion level
        is_suspicious = suspicion_score >= 50
        
        # Cap suspicion score at 100
        suspicion_score = min(suspicion_score, 100)
        
        return {
            'is_suspicious': is_suspicious,
            'suspicion_score': suspicion_score,
            'reasons': reasons,
            'detected_objects': [obj['name'] for obj in objects],
            'risk_level': self._get_risk_level(suspicion_score)
        }
    
    def _get_risk_level(self, score):
        """Get risk level based on suspicion score"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

# Global instance
azure_cv_enhanced = None

def init_azure_cv_enhanced():
    """Initialize the enhanced Azure CV detector"""
    global azure_cv_enhanced
    try:
        azure_cv_enhanced = AzureCVEnhanced()
        print("✅ Azure Computer Vision Enhanced initialized")
        return azure_cv_enhanced
    except Exception as e:
        print(f"❌ Failed to initialize Azure CV Enhanced: {e}")
        return None

def get_azure_cv_enhanced():
    """Get the global Azure CV Enhanced instance"""
    return azure_cv_enhanced