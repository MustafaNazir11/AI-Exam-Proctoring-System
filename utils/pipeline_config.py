# Pipeline Configuration
# Adjust these settings to fine-tune the integrated pipeline behavior

class PipelineConfig:
    # Local checks thresholds
    BLUR_THRESHOLD = 100  # Lower = more strict blur detection
    BRIGHTNESS_MIN = 50   # Minimum acceptable brightness
    BRIGHTNESS_MAX = 200  # Maximum acceptable brightness
    MOTION_THRESHOLD = 30 # Motion percentage threshold
    
    # Azure API triggers
    AZURE_ON_CRITICAL = True      # Send to Azure on critical flags (no face, multiple faces, motion)
    AZURE_ON_QUALITY_ISSUES = 2   # Send to Azure if this many quality issues detected
    
    # Suspicion logic
    LOCAL_SUSPICION_THRESHOLD = 2  # Number of failed local checks to be suspicious
    
    # Performance settings
    SKIP_HEAVY_PROCESSING = True   # Skip YOLO/MediaPipe if not suspicious locally
    
    @classmethod
    def get_critical_flags(cls):
        """Flags that trigger immediate Azure analysis"""
        return ['no_face', 'multiple_faces_local', 'excessive_motion']
    
    @classmethod
    def get_quality_flags(cls):
        """Quality-related flags"""
        return ['blur', 'brightness']