"""
Pipeline 2.2: Azure Computer Vision Analyzer
Analyzes images for prohibited objects and people count using Azure Computer Vision.
"""

import os
import cv2
import numpy as np
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()


class VisionAnalyzer:
    def __init__(self):
        """Initialize Azure Computer Vision client."""
        endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        key = os.getenv('AZURE_VISION_KEY')
        
        if not endpoint or not key:
            raise ValueError("AZURE_VISION_ENDPOINT and AZURE_VISION_KEY must be set")
        
        self.client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(key))
    
    def analyze_frame(self, frame):
        """
        Analyze frame for prohibited objects and people.
        
        Args:
            frame (np.ndarray): Image frame as numpy array
            
        Returns:
            dict: Normalized analysis results or None if failed
        """
        try:
            # Convert frame to bytes
            _, buffer = cv2.imencode('.jpg', frame)
            image_stream = BytesIO(buffer.tobytes())
            
            # Call Azure Computer Vision with retry
            features = [VisualFeatureTypes.objects, VisualFeatureTypes.faces]
            analysis = self._call_vision_with_retry(image_stream, features)
            
            if analysis is None:
                return None  # Graceful fallback
            
            # Normalize results
            return {
                "phone_detected": self._detect_phone(analysis.objects),
                "book_detected": self._detect_book(analysis.objects),
                "person_count": len(analysis.faces),
                "image_quality_issue": self._check_quality_issues(analysis)
            }
        except Exception:
            return None  # Graceful fallback
    
    def _call_vision_with_retry(self, image_stream, features, max_retries=1):
        """Call Azure Vision with retry logic."""
        for attempt in range(max_retries + 1):
            try:
                image_stream.seek(0)  # Reset stream position
                return self.client.analyze_image_in_stream(image_stream, visual_features=features)
            except Exception:
                if attempt == max_retries:
                    return None  # Final failure
        return None
    
    def _detect_phone(self, objects):
        """Check if mobile phone is detected."""
        phone_keywords = ['cell phone', 'mobile phone', 'phone', 'smartphone']
        return any(obj.object_property.lower() in phone_keywords for obj in objects)
    
    def _detect_book(self, objects):
        """Check if book/notebook is detected."""
        book_keywords = ['book', 'notebook', 'paper', 'document']
        return any(obj.object_property.lower() in book_keywords for obj in objects)
    
    def _check_quality_issues(self, analysis):
        """Check for image quality issues (basic implementation)."""
        # Azure doesn't directly provide blur/brightness metrics in object detection
        # This is a placeholder - could be enhanced with additional API calls
        return False