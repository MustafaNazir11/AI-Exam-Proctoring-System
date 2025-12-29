"""Simple test for VisionAnalyzer without numpy"""

import os

# Mock environment variables
os.environ['AZURE_VISION_ENDPOINT'] = 'https://test.cognitiveservices.azure.com/'
os.environ['AZURE_VISION_KEY'] = 'test_key'

def test_azure_import():
    """Test if Azure SDK is properly installed."""
    try:
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from msrest.authentication import CognitiveServicesCredentials
        print("✓ Azure Computer Vision SDK imported successfully")
        
        # Test VisionAnalyzer import
        from vision_analyzer import VisionAnalyzer
        print("✓ VisionAnalyzer imported successfully")
        
        print("\nPipeline 2.2 is ready!")
        print("Note: Actual testing requires valid Azure credentials and numpy/opencv")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_azure_import()