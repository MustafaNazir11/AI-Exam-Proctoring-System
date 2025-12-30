# Azure Computer Vision Integration

This integration adds comprehensive face and object detection capabilities to your existing proctoring system using Azure Computer Vision API.

## 🚀 Features

- **Enhanced Face Detection**: Combines local OpenCV detection with Azure Face API
- **Object Detection**: Identifies suspicious objects (phones, books, papers, etc.)
- **Suspicion Analysis**: Intelligent scoring system with detailed reasons
- **Violation Tracking**: Comprehensive violation logging and analysis
- **Real-time Processing**: Optimized for live webcam feeds
- **Backward Compatibility**: Works with existing codebase without modifications

## 📁 New Files Created

### Core Integration Files
- `utils/azure_cv_enhanced.py` - Enhanced Azure Computer Vision client
- `utils/integrated_face_object_detector.py` - Combined local + Azure detection
- `utils/enhanced_violation_analyzer.py` - Advanced violation analysis system
- `utils/azure_cv_integration.py` - Main integration module

### Test and Example Files
- `test_azure_cv_integration.py` - Test script for the integration
- `examples/azure_cv_proctoring_example.py` - Usage examples

## 🔧 Setup

### 1. Environment Variables
Ensure your `.env` file contains:
```
AZURE_CV_ENDPOINT=your_azure_cv_endpoint
AZURE_CV_KEY=your_azure_cv_key
```

### 2. Dependencies
The integration uses existing dependencies. No additional packages required.

## 📖 Usage

### Quick Start (Minimal Code Changes)

```python
from utils.azure_cv_integration import init_azure_cv_integration, analyze_frame_with_azure_cv

# Initialize once at startup
integration = init_azure_cv_integration()

# Analyze any frame
results = analyze_frame_with_azure_cv(frame, peer_id="student_123")

# Check results
if results['is_suspicious']:
    print(f"Violation detected: {results['severity']}")
    for reason in results['reasons']:
        print(f"- {reason}")
```

### Advanced Usage

```python
from utils.azure_cv_integration import (
    init_azure_cv_integration,
    analyze_frame_with_azure_cv,
    quick_face_object_analysis,
    get_violation_summary
)

# Initialize
integration = init_azure_cv_integration()

# Full analysis
full_results = analyze_frame_with_azure_cv(frame, peer_id="student_123")

# Quick analysis (faces + objects only)
quick_results = quick_face_object_analysis(frame)

# Get violation summary
summary = get_violation_summary(full_results)
```

## 🎯 Integration with Existing Code

### Replace Existing Face Detection

**Before:**
```python
from utils.face_detector import detect_faces
faces, annotated_frame = detect_faces(frame)
```

**After:**
```python
from utils.azure_cv_integration import analyze_frame_with_azure_cv
results = analyze_frame_with_azure_cv(frame, peer_id="student_id")
annotated_frame = results['annotated_frame']
is_suspicious = results['is_suspicious']
```

### Enhance Existing Pipeline

**Before:**
```python
from utils.integrated_pipeline import integrated_pipeline_analysis
result = integrated_pipeline_analysis(frame)
```

**After:**
```python
from utils.azure_cv_integration import analyze_frame_with_azure_cv
result = analyze_frame_with_azure_cv(frame, peer_id="student_id")
# Now includes object detection and enhanced analysis
```

## 📊 Analysis Results Structure

```python
{
    'is_suspicious': bool,           # True if violations detected
    'suspicion_score': int,          # 0-100 suspicion score
    'severity': str,                 # 'MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    'reasons': [str],               # List of violation reasons
    'recommendations': [str],        # Suggested actions
    'annotated_frame': np.array,    # Frame with detection boxes
    'detection_results': {          # Detailed detection data
        'local_detection': {...},   # OpenCV results
        'azure_detection': {...}    # Azure CV results
    },
    'violation_analysis': {...},    # Comprehensive violation data
    'violation_entry': {...}        # Violation log entry (if peer_id provided)
}
```

## 🔍 Detection Capabilities

### Face Detection
- **No Face**: Student absence detection
- **Multiple Faces**: Unauthorized assistance detection
- **Face Analysis**: Age, gender (from Azure)

### Object Detection
- **High-Risk Objects**: Phones, books, papers, documents
- **Medium-Risk Objects**: Computers, tablets, watches
- **Confidence Scoring**: Only high-confidence detections flagged

### Behavioral Analysis
- **Scene Analysis**: Overall scene understanding
- **Suspicious Patterns**: Multiple indicators correlation
- **Risk Assessment**: Automated risk level assignment

## 🚨 Violation Types

| Type | Description | Score Weight |
|------|-------------|--------------|
| `ABSENCE` | No face detected | 40 points |
| `MULTIPLE_PERSONS` | Multiple faces | 60 points |
| `UNAUTHORIZED_MATERIALS` | Phones, books, papers | 70 points |
| `SUSPICIOUS_BEHAVIOR` | Behavioral patterns | 30 points |
| `TECHNICAL_ISSUE` | System errors | 20 points |

## 🧪 Testing

### Run Tests
```bash
# Quick test
python test_azure_cv_integration.py quick

# Webcam test
python test_azure_cv_integration.py webcam

# Image test
python test_azure_cv_integration.py path/to/image.jpg
```

### Run Examples
```bash
python examples/azure_cv_proctoring_example.py
```

## ⚙️ Configuration

### Suspicion Thresholds
- **Minimal Risk**: 0-19 points
- **Low Risk**: 20-39 points  
- **Medium Risk**: 40-59 points
- **High Risk**: 60-79 points
- **Critical Risk**: 80-100 points

### Object Confidence
- **Minimum Confidence**: 50% for flagging
- **High Confidence**: 60% for violations

## 🔄 Backward Compatibility

The integration is designed to work alongside existing code:

- ✅ Existing `face_detector.py` still works
- ✅ Existing `integrated_pipeline.py` still works  
- ✅ Existing violation logging still works
- ✅ No breaking changes to current API

## 🚀 Performance

### Optimization Features
- **Lazy Loading**: Azure CV only called when needed
- **Local First**: Fast OpenCV checks before Azure
- **Caching**: Efficient frame processing
- **Error Handling**: Graceful fallbacks

### Recommended Usage
- **Real-time**: Use `quick_face_object_analysis()` for speed
- **Detailed**: Use `analyze_frame_with_azure_cv()` for comprehensive analysis
- **Batch**: Process multiple frames efficiently

## 🛠️ Troubleshooting

### Common Issues

**Azure CV not working:**
- Check `.env` file has correct credentials
- Verify internet connection
- Check Azure subscription status

**High false positives:**
- Adjust confidence thresholds in code
- Review object detection categories
- Fine-tune suspicion scoring

**Performance issues:**
- Use local detection only for speed
- Reduce frame processing frequency
- Optimize image resolution

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Future Enhancements

- **Custom Object Training**: Train for specific exam materials
- **Behavioral Patterns**: Advanced movement analysis  
- **Multi-Camera Support**: Multiple angle detection
- **Real-time Alerts**: Instant notification system
- **Analytics Dashboard**: Comprehensive reporting

## 🤝 Support

For issues or questions:
1. Check the test scripts work correctly
2. Verify Azure credentials and quotas
3. Review the example implementations
4. Check system logs for detailed error messages

---

**Note**: This integration enhances your existing system without replacing it. All original functionality remains intact while adding powerful Azure Computer Vision capabilities.