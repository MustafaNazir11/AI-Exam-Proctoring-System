import os
import cv2
import io
import numpy as np
from dotenv import load_dotenv

from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

load_dotenv()

class AzureFaceDetector:
    def __init__(self, api_key=None, endpoint=None):
        self.api_key = api_key or os.getenv("AZURE_FACE_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_FACE_ENDPOINT")

        if not self.api_key or not self.endpoint:
            raise ValueError("Azure Face API key or endpoint missing")

        self.face_client = FaceClient(
            self.endpoint,
            CognitiveServicesCredentials(self.api_key)
        )

        print("🔗 Azure Face SDK initialized")

    def frame_to_bytes(self, frame):
        """Convert OpenCV frame to BytesIO"""
        success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not success:
            raise ValueError("Failed to encode image")
        return io.BytesIO(buffer.tobytes())

    def detect_faces_azure(self, frame):
        image_stream = self.frame_to_bytes(frame)

        faces = self.face_client.face.detect_with_stream(
            image=image_stream,
            detection_model="detection_03",
            recognition_model="recognition_04",
            return_face_id=False
        )

        return {
            "face_count": len(faces),
            "suspicious_indicators": []
        }

# ---------------- GLOBAL INSTANCE ----------------
azure_face_detector = None

def init_azure_face_detector(api_key, endpoint=None):
    global azure_face_detector
    try:
        azure_face_detector = AzureFaceDetector(api_key, endpoint)
        return azure_face_detector
    except Exception as e:
        print(f"❌ Failed to initialize Azure Face API: {e}")
        return None

def get_azure_face_detector():
    return azure_face_detector
