# Azure CV Integration Usage Guide

## 🎯 Integration Complete!

Your proctoring system now includes Azure Computer Vision capabilities.

## 🚀 New Features Available

### 1. Enhanced Analysis Endpoint
- **URL**: `/enhanced-analyze`
- **Method**: POST
- **Purpose**: Comprehensive face and object detection with Azure CV

### 2. Enhanced Screenshot Upload
- **URL**: `/upload-screenshot` (enhanced automatically)
- **Features**: 
  - Object detection (phones, books, papers)
  - Advanced face analysis
  - Detailed violation scoring
  - Intelligent recommendations

### 3. Azure CV Status Check
- **URL**: `/azure-cv-status`
- **Purpose**: Check if Azure CV is working properly

## 📊 Using in Your Frontend

### JavaScript Example:
```javascript
// Enhanced analysis
fetch('/enhanced-analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        peerId: 'student_123',
        image: base64ImageData
    })
})
.then(response => response.json())
.then(data => {
    if (data.is_suspicious) {
        console.log(`Violation detected: ${data.severity}`);
        console.log('Reasons:', data.reasons);
        console.log('Recommendations:', data.recommendations);
    }
});

// Check Azure CV status
fetch('/azure-cv-status')
.then(response => response.json())
.then(data => {
    console.log('Azure CV enabled:', data.azure_cv_enabled);
});
```

## 🔧 Configuration

Make sure your `.env` file contains:
```
AZURE_CV_ENDPOINT=your_azure_cv_endpoint
AZURE_CV_KEY=your_azure_cv_key
```

## 🧪 Testing

Run these commands to test:
```bash
# Test Azure CV integration
python test_azure_cv_integration.py quick

# Test with webcam
python test_azure_cv_integration.py webcam

# Test with image
python test_azure_cv_integration.py path/to/image.jpg

# Run examples
python examples/azure_cv_proctoring_example.py
```

## 🔄 Backward Compatibility

- ✅ All existing endpoints still work
- ✅ Original `/upload-screenshot` enhanced automatically
- ✅ Fallback to original methods if Azure CV fails
- ✅ No breaking changes to existing code

## 📈 What's Enhanced

1. **Face Detection**: Local OpenCV + Azure Face API
2. **Object Detection**: Phones, books, papers, unauthorized materials
3. **Violation Scoring**: 0-100 intelligent scoring system
4. **Risk Levels**: MINIMAL → LOW → MEDIUM → HIGH → CRITICAL
5. **Detailed Analysis**: Specific reasons and recommendations

## 🚨 Violation Detection

The system now detects:
- **Absence**: No face detected
- **Multiple Persons**: Multiple faces detected
- **Unauthorized Materials**: Phones, books, papers
- **Suspicious Behavior**: Based on scene analysis
- **Technical Issues**: System errors

## 💡 Next Steps

1. Update your frontend to use `/enhanced-analyze` for better results
2. Monitor `/azure-cv-status` to ensure Azure CV is working
3. Review violation logs for enhanced violation entries
4. Consider using the new detailed analysis data for better proctoring

---
**Note**: The integration maintains full backward compatibility. Your existing system continues to work while gaining powerful new capabilities!
