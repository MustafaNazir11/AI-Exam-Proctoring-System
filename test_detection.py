from utils.pipeline1_local_checks import pipeline1_local_checks
import cv2
import numpy as np

# Test 1: Normal frame
normal_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
result1 = pipeline1_local_checks(normal_frame)
print("Normal frame:", result1['suspicious'], result1['failed_checks'])

# Test 2: Very dark frame (should fail brightness)
dark_frame = np.ones((480, 640, 3), dtype=np.uint8) * 10
result2 = pipeline1_local_checks(dark_frame)
print("Dark frame:", result2['suspicious'], result2['failed_checks'])

# Test 3: Very bright frame (should fail brightness)  
bright_frame = np.ones((480, 640, 3), dtype=np.uint8) * 250
result3 = pipeline1_local_checks(bright_frame)
print("Bright frame:", result3['suspicious'], result3['failed_checks'])