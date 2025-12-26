"""Test script for VisionTrigger"""

from vision_trigger import VisionTrigger
import time

def test_vision_trigger():
    trigger = VisionTrigger()
    
    print("Testing VisionTrigger...")
    
    # Test 1: Suspicious activity
    print(f"Suspicious=True: {trigger.should_call_vision(True)}")  # Should be True
    print(f"Immediate call again: {trigger.should_call_vision(True)}")  # Should be False (cooldown)
    
    # Test 2: Wait for cooldown
    time.sleep(2.1)
    print(f"After cooldown, suspicious=True: {trigger.should_call_vision(True)}")  # Should be True
    
    # Test 3: Heartbeat
    time.sleep(2.1)
    print(f"Non-suspicious after 2s: {trigger.should_call_vision(False)}")  # Should be False
    time.sleep(1)
    print(f"Non-suspicious after 3s total: {trigger.should_call_vision(False)}")  # Should be True (heartbeat)

if __name__ == "__main__":
    test_vision_trigger()