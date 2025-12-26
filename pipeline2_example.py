"""
Pipeline 2 Integration Example
Shows how to use VisionTrigger (2.1) and VisionAnalyzer (2.2) together
"""

from vision_trigger import VisionTrigger

def pipeline2_integration_example():
    """Example of how Pipeline 2.1 and 2.2 work together."""
    
    # Initialize components
    trigger = VisionTrigger()
    
    # Simulate pipeline loop
    print("Pipeline 2 Integration Example")
    print("=" * 40)
    
    # Simulate Pipeline 1 outputs
    pipeline1_outputs = [
        {"suspicious": True, "timestamp": 1000},
        {"suspicious": False, "timestamp": 1001},
        {"suspicious": False, "timestamp": 1003.5},  # Should trigger heartbeat
    ]
    
    for i, p1_output in enumerate(pipeline1_outputs):
        print(f"\nFrame {i+1}:")
        print(f"  Pipeline 1 suspicious: {p1_output['suspicious']}")
        
        # Pipeline 2.1: Check if vision should be called
        should_call = trigger.should_call_vision(
            p1_output['suspicious'], 
            p1_output['timestamp']
        )
        print(f"  Pipeline 2.1 trigger: {should_call}")
        
        if should_call:
            print("  Pipeline 2.2: Would call Azure Vision")
            # Here you would call:
            # analyzer = VisionAnalyzer()
            # result = analyzer.analyze_frame(frame)
            # print(f"  Vision result: {result}")
        else:
            print("  Pipeline 2.2: Skipped (not triggered)")

if __name__ == "__main__":
    pipeline2_integration_example()