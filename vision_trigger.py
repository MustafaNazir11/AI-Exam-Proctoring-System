"""
Pipeline 2 - Part 2.1: Azure Computer Vision Trigger
Decides when to call Azure Computer Vision based on suspicious activity and heartbeat intervals.
"""

import time


class VisionTrigger:
    def __init__(self, heartbeat_interval=2.5, cooldown_interval=2.0):
        """
        Initialize the vision trigger.
        
        Args:
            heartbeat_interval (float): Seconds between regular vision calls
            cooldown_interval (float): Minimum seconds between vision calls
        """
        self.heartbeat_interval = heartbeat_interval
        self.cooldown_interval = cooldown_interval
        self.last_vision_call = 0
        self.last_heartbeat = 0
    
    def should_call_vision(self, suspicious, timestamp=None):
        """
        Determine if Azure Computer Vision should be called.
        
        Args:
            suspicious (bool): Pipeline 1 suspicious flag
            timestamp (float, optional): Current timestamp. Uses time.time() if None
            
        Returns:
            bool: True if vision should be called, False otherwise
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Check cooldown - never call more frequently than cooldown_interval
        if timestamp - self.last_vision_call < self.cooldown_interval:
            return False
        
        # Trigger on suspicious activity
        if suspicious:
            self.last_vision_call = timestamp
            self.last_heartbeat = timestamp
            return True
        
        # Trigger on heartbeat interval
        if timestamp - self.last_heartbeat >= self.heartbeat_interval:
            self.last_vision_call = timestamp
            self.last_heartbeat = timestamp
            return True
        
        return False