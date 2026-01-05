import requests
import time

# Test the exam control API endpoints
BASE_URL = "http://localhost:5000"

def test_exam_control():
    print("🧪 Testing Exam Control System...")
    
    # Test getting exam sessions
    try:
        response = requests.get(f"{BASE_URL}/api/admin/exam/sessions")
        print(f"✅ Get sessions: {response.status_code}")
        if response.status_code == 200:
            sessions = response.json()
            print(f"   Found {len(sessions)} active sessions")
    except Exception as e:
        print(f"❌ Get sessions failed: {e}")
    
    # Test starting an exam session
    try:
        response = requests.post(f"{BASE_URL}/api/exam/start")
        print(f"✅ Start exam: {response.status_code}")
    except Exception as e:
        print(f"❌ Start exam failed: {e}")
    
    print("\n📋 Manual Testing Steps:")
    print("1. Start app: python app.py")
    print("2. Admin login: http://localhost:5000/login (teacher@test.com/admin123)")
    print("3. Go to Exam Control: http://localhost:5000/exam-control")
    print("4. Student login: http://localhost:5000/login (student@test.com/password)")
    print("5. Start exam: http://localhost:5000/exam")
    print("6. Test controls in admin dashboard")

if __name__ == "__main__":
    test_exam_control()