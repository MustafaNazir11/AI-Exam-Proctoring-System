import os

# Check if screenshot exists
screenshot_path = 'static/screenshots/screenshot_20251220_134917_087765.png'

if os.path.exists(screenshot_path):
    print(f"Screenshot found at {screenshot_path}")
    print("Expected result: received=True, suspicious=True (if image has issues)")
else:
    print(f"No screenshot found at {screenshot_path}")
    print("Expected result: received=False, suspicious=False")
    print("This is the correct behavior when no browser activity is captured.")