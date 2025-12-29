import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_test():
    try:
        from utils.integrated_pipeline import integrated_pipeline_analysis
        import numpy as np
        
        # Create test frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # Test pipeline
        result = integrated_pipeline_analysis(frame)
        
        print("🧪 Quick Pipeline Test")
        print("=" * 30)
        print(f"✅ Pipeline working: {result['pipeline_used']}")
        print(f"📊 Suspicious: {result['suspicious']}")
        print(f"🔍 Azure analyzed: {result['azure_analyzed']}")
        print(f"❌ Failed checks: {result['failed_checks']}")
        
        if result['azure_analyzed']:
            print("🌐 Azure API was called")
        else:
            print("💻 Local checks only")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()