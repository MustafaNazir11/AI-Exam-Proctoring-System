from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import os, base64, sqlite3, io
from datetime import datetime
import numpy as np
from PIL import Image
import cloudinary
import cloudinary.uploader

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.secret_key = "super_secret_key_123"

# ---------------- DB FUNCTIONS -----------------
def init_db():
    conn = sqlite3.connect('Database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_option TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cursor.execute("INSERT OR IGNORE INTO students (email, password) VALUES (?, ?)", ("student@test.com", "password"))
    cursor.execute("INSERT OR IGNORE INTO teachers (email, password) VALUES (?, ?)", ("teacher@test.com", "admin123"))

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('Database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------- CLOUDINARY CONFIG --------------
cloudinary.config(
    cloud_name="dmbhhqmxf",
    api_key="267234471199724",
    api_secret="hZc5Bh9SR7LSL4Fy3tNAZsOhDbY",
)

# ------------ PROCTORING MEMORY --------------
peer_ids = set()
violation_counts = {}
violation_logs = []

# ---------------- ROUTES ----------------------
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
        if student:
            session['user_id'] = student['id']
            session['email'] = student['email']
            session['user_type'] = 'student'
            conn.close()
            return redirect(url_for('test'))
        conn.close()
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/adminprofile')
def adminprofile():
    return render_template('adminprofile.html')

@app.route('/stud_profile')
def stud_profile():
    return render_template('profile.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO students (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            return "❌ Email already exists! Try another."
    return render_template('register.html')

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin-dashboard.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        teacher = conn.execute("SELECT * FROM teachers WHERE email=? AND password=?", (email, password)).fetchone()
        if teacher:
            session['user_id'] = teacher['id']
            session['email'] = teacher['email']
            session['user_type'] = 'teacher'
            conn.close()
            return redirect(url_for('admin_dashboard'))
        conn.close()
        return "Invalid credentials"
    return render_template('admin-login.html')

@app.route("/admin")
def admin():
    return render_template("admin-dashboard.html")

@app.route("/dashboard")
def dashboard():
    return render_template("proctor-dashboard.html")

@app.route("/exam")
def exam():
    return render_template("exam.html", email=session.get("email"))

@app.route("/violations")
def show_violations():
    return render_template("violations.html", logs=violation_logs)

# ------------------ QUIZ ----------------------
@app.route("/input-questions", methods=['GET', 'POST'])
def input_questions():
    if request.method == 'POST':
        questions = request.form.getlist('question')
        option_as = request.form.getlist('option_a')
        option_bs = request.form.getlist('option_b')
        option_cs = request.form.getlist('option_c')
        option_ds = request.form.getlist('option_d')
        correct_options = request.form.getlist('correct_option')
        conn = get_db_connection()
        cursor = conn.cursor()
        count = 0
        for i in range(len(questions)):
            if questions[i].strip():
                cursor.execute('''INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                               (questions[i], option_as[i], option_bs[i], option_cs[i], option_ds[i], correct_options[i]))
                count += 1
        conn.commit()
        conn.close()
        return f"✅ {count} questions added successfully!"
    return render_template('questions.html')

@app.route("/quiz")
def quiz():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()
    return render_template("quiz.html", questions=questions)

@app.route('/test')
def test():
    return render_template('student-dashboard.html')

def student_dashboard():
    return render_template('student-dashboard')

@app.route("/submit", methods=['POST'])
def submit():
    submitted_answers = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    score = 0
    total = 0
    for key, selected_option in submitted_answers.items():
        if key.startswith('question_'):
            q_id = key.split('_')[1]
            cursor.execute("SELECT correct_option FROM questions WHERE id=?", (q_id,))
            correct_option = cursor.fetchone()[0]
            total += 1
            if selected_option.lower() == correct_option.lower():
                score += 1
    conn.close()
    percentage = (score / total) * 100 if total > 0 else 0
    return render_template("results.html", score=score, total=total, percentage=percentage, message="")

# ---------------- UPLOAD & ANALYSIS -----------------
face_mesh_instance = None  # Lazy-loaded
run_yolo_fn = None
detect_faces_fn = None
check_brightness_fn = None
upload_to_cloudinary_fn = None
create_violation_entry_fn = None

@app.route("/upload-screenshot", methods=["POST"])
def upload_screenshot():
    global face_mesh_instance, run_yolo_fn, detect_faces_fn, check_brightness_fn, upload_to_cloudinary_fn, create_violation_entry_fn

    # Lazy-load ML utils to avoid blocking Flask startup
    if face_mesh_instance is None:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh_instance = mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    if run_yolo_fn is None:
        from utils.yolo_detector import run_yolo as yolo_fn
        run_yolo_fn = yolo_fn
    if detect_faces_fn is None:
        from utils.face_detector import detect_faces as face_fn
        detect_faces_fn = face_fn
    if check_brightness_fn is None:
        from utils.brightness_check import check_brightness as brightness_fn
        check_brightness_fn = brightness_fn
    if upload_to_cloudinary_fn is None:
        from utils.cloud import upload_to_cloudinary as cloud_fn
        upload_to_cloudinary_fn = cloud_fn
    if create_violation_entry_fn is None:
        from utils.violation_rules import create_violation_entry as vio_fn
        create_violation_entry_fn = vio_fn

    data = request.json
    image_data = data.get("image")
    peer_id = data.get("peerId")

    if not peer_id:
        return jsonify({"message": "Peer ID missing"}), 400
    if not image_data:
        return jsonify({"message": "No image data received"}), 400

    try:
        import cv2
        image_bytes = base64.b64decode(image_data.split(",")[1])
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        frame = np.array(image)[:, :, ::-1].copy()  # RGB -> BGR
    except Exception as e:
        return jsonify({"message": "Failed to decode image", "error": str(e)}), 400

    suspicious = False
    reasons = []

    # 🚀 CHANGED: Get annotated frames with boxes!
    person_count, detections, yolo_frame = run_yolo_fn(frame)  # NEW: 3 values!
    faces, face_frame = detect_faces_fn(frame)                  # NEW: 2 values!

    for label, conf, xyxy in detections:
        suspicious = True
        reasons.append(f"{label} detected")
    if person_count > 1:
        suspicious = True
        reasons.append("Multiple people detected")

    if len(faces) == 0:
        suspicious = True
        reasons.append("No face detected")

    # FaceMesh + gaze
    try:
        rgb_frame = frame[:, :, ::-1]  # BGR -> RGB
        results = face_mesh_instance.process(rgb_frame)
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            left_eye_indices = [33, 133]
            right_eye_indices = [362, 263]
            left_eye_ratio = landmarks[left_eye_indices[0]].x - landmarks[left_eye_indices[1]].x
            right_eye_ratio = landmarks[right_eye_indices[0]].x - landmarks[right_eye_indices[1]].x
            if abs(left_eye_ratio) < 0.03 or abs(right_eye_ratio) < 0.03:
                suspicious = True
                reasons.append("Possible looking away detected")
        else:
            suspicious = True
            reasons.append("Face not visible properly")
    except Exception as e:
        suspicious = True
        reasons.append(f"FaceMesh error: {str(e)}")

    # Brightness check
    brightness = check_brightness_fn(frame)
    if brightness > 200:
        suspicious = True
        reasons.append("High brightness - possible screen reflection")

    # Handle suspicious
    if suspicious:
        violation_counts[peer_id] = violation_counts.get(peer_id, 0) + 1
        entry = create_violation_entry_fn(peer_id, reasons)
        violation_logs.append(entry)
        screenshots_folder = os.path.join(app.static_folder, "screenshots")
        os.makedirs(screenshots_folder, exist_ok=True)
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        import cv2
        image_path = os.path.join(screenshots_folder, filename)
        cv2.imwrite(image_path, yolo_frame)  # 🚀 CHANGED: Save ANNOTATED image!
        upload_result = upload_to_cloudinary_fn(image_path)
        os.remove(image_path)
        response = {
            "message": "Suspicious activity detected",
            "cloudinary_url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id"),
            "reasons": reasons
        }
        if violation_counts[peer_id] >= 5:
            response["action"] = "stop_exam"
        return jsonify(response)

    return jsonify({"message": "No suspicion detected.", "reasons": reasons})

# ------------  TAB / BROWSER VIOLATION ENDPOINT -----------------
@app.route("/tab-violation", methods=["POST"])
def tab_violation():
    global create_violation_entry_fn
    # Lazy-load create_violation function if not already
    if create_violation_entry_fn is None:
        try:
            from utils.violation_rules import create_violation_entry as vio_fn
            create_violation_entry_fn = vio_fn
        except Exception as e:
            # Fallback: simple entry creator
            def create_simple_entry(pid, reasons_list):
                return {
                    "peer_id": pid,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reasons": reasons_list
                }
            create_violation_entry_fn = create_simple_entry

    data = request.json or {}
    peer_id = data.get("peerId")
    reason = data.get("reason", "Browser/tab violation")

    if not peer_id:
        return jsonify({"message": "Peer ID missing"}), 400

    # increment and log
    violation_counts[peer_id] = violation_counts.get(peer_id, 0) + 1
    entry = create_violation_entry_fn(peer_id, [reason])
    violation_logs.append(entry)

    response = {
        "message": "Tab/Browser violation recorded",
        "reason": reason,
        "count": violation_counts[peer_id]
    }

    if violation_counts[peer_id] >= 5:
        response["action"] = "stop_exam"

    return jsonify(response)

# ------------ PEER ID HANDLING -----------------
@app.route("/store-peer-id", methods=["POST"])
def store_peer_id():
    data = request.json
    peer_id = data.get("peerId")
    if peer_id and peer_id not in peer_ids:
        peer_ids.add(peer_id)
        return jsonify({"message": "Peer ID stored", "peerId": peer_id})
    return jsonify({"message": "Peer ID missing or duplicate"}), 400

@app.route("/get-peer-ids")
def get_peer_ids():
    return jsonify(list(peer_ids))

@app.route("/delete-peer-id", methods=["POST"])
def delete_peer_id():
    data = request.json
    peer_id = data.get("peerId")
    if peer_id and peer_id in peer_ids:
        peer_ids.remove(peer_id)
        violation_counts.pop(peer_id, None)
        return jsonify({"message": "Peer ID deleted", "peerId": peer_id})
    return jsonify({"message": "Peer ID not found"}), 404

# ------------ VIEW SCREENSHOTS -----------------
@app.route("/view_screenshots")
def view_screenshots():
    screenshots_folder = os.path.join(app.static_folder, "screenshots")
    os.makedirs(screenshots_folder, exist_ok=True)
    files = os.listdir(screenshots_folder)
    images = [f"/static/screenshots/{file}" for file in files if file.endswith(".png")]
    html = "<h1>Suspicious Screenshots</h1><div style='display:flex; flex-wrap: wrap;'>"
    for img in images:
        html += f'''
        <div style="margin: 10px;">
            <img src="{img}" width="300" style="border:1px solid #ccc;"/><br>
            <p>{img}</p>
        </div>
        '''
    html += "</div>"
    return html

# ----------------- START APP ------------------
if __name__ == "__main__":
    init_db()
    # Flask will start instantly; ML models initialize lazily
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
