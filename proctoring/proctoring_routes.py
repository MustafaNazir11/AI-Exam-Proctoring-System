from flask import render_template, request, jsonify
import os, base64, io
from datetime import datetime
import numpy as np
from PIL import Image

# Global variables
peer_ids = set()
violation_counts = {}
violation_logs = []
reconnect_requests = set()
proctor_ids = set()

# Lazy-loaded ML components
face_mesh_instance = None
run_yolo_fn = None
detect_faces_fn = None
check_brightness_fn = None
upload_to_cloudinary_fn = None
create_violation_entry_fn = None
pipeline1_local_checks_fn = None

def init_proctoring_routes(app):
    @app.route("/violations")
    def show_violations():
        return render_template("violations.html", logs=violation_logs)

    @app.route("/violations/<peer_id>")
    def show_peer_violations(peer_id):
        peer_logs = [log for log in violation_logs if log.get('peer_id') == peer_id]
        return render_template("violations.html", logs=peer_logs, peer_id=peer_id)

    @app.route("/api/violations/<peer_id>")
    def get_peer_violations_api(peer_id):
        peer_logs = [log for log in violation_logs if log.get('peer_id') == peer_id]
        return jsonify({"peer_id": peer_id, "violations": peer_logs, "count": len(peer_logs)})

    @app.route("/pipeline1/analyze", methods=["POST"])
    def pipeline1_analyze():
        global pipeline1_local_checks_fn
        if pipeline1_local_checks_fn is None:
            from utils.pipeline1_local_checks import pipeline1_local_checks
            pipeline1_local_checks_fn = pipeline1_local_checks
        
        image_data = request.json.get("image")
        if not image_data:
            return jsonify({"error": "No image data"}), 400
        
        try:
            image_bytes = base64.b64decode(image_data.split(",")[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)[:, :, ::-1].copy()
            return jsonify(pipeline1_local_checks_fn(frame))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/pipeline0/frame", methods=["POST"])
    def pipeline0_frame():
        return jsonify({"received": bool(request.json.get("image"))})

    @app.route("/upload-screenshot", methods=["POST"])
    def upload_screenshot():
        global face_mesh_instance, run_yolo_fn, detect_faces_fn, check_brightness_fn, upload_to_cloudinary_fn, create_violation_entry_fn

        # Lazy load ML components
        if face_mesh_instance is None:
            import mediapipe as mp
            face_mesh_instance = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False, max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.5, min_tracking_confidence=0.5)
        if run_yolo_fn is None:
            from utils.yolo_detector import run_yolo
            run_yolo_fn = run_yolo
        if detect_faces_fn is None:
            from utils.face_detector import detect_faces
            detect_faces_fn = detect_faces
        if check_brightness_fn is None:
            from utils.brightness_check import check_brightness
            check_brightness_fn = check_brightness
        if upload_to_cloudinary_fn is None:
            from utils.cloud import upload_to_cloudinary
            upload_to_cloudinary_fn = upload_to_cloudinary
        if create_violation_entry_fn is None:
            from utils.violation_rules import create_violation_entry
            create_violation_entry_fn = create_violation_entry

        data = request.json
        peer_id, image_data = data.get("peerId"), data.get("image")
        
        if not peer_id or not image_data:
            return jsonify({"message": "Missing peer ID or image data"}), 400

        try:
            import cv2
            image_bytes = base64.b64decode(image_data.split(",")[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)[:, :, ::-1].copy()
        except Exception as e:
            return jsonify({"message": "Failed to decode image", "error": str(e)}), 400

        suspicious, reasons = False, []
        person_count, detections, yolo_frame = run_yolo_fn(frame)
        faces, face_frame = detect_faces_fn(frame)

        # Check violations
        for label, conf, xyxy in detections:
            suspicious = True
            reasons.append(f"{label} detected")
        if person_count > 1:
            suspicious = True
            reasons.append("Multiple people detected")
        if len(faces) == 0:
            suspicious = True
            reasons.append("No face detected")

        # FaceMesh gaze detection
        try:
            rgb_frame = frame[:, :, ::-1]
            import time
            time.sleep(0.001)
            results = face_mesh_instance.process(rgb_frame)
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                left_eye_ratio = landmarks[33].x - landmarks[133].x
                right_eye_ratio = landmarks[362].x - landmarks[263].x
                if abs(left_eye_ratio) < 0.03 or abs(right_eye_ratio) < 0.03:
                    suspicious = True
                    reasons.append("Possible looking away detected")
            else:
                suspicious = True
                reasons.append("Face not visible properly")
        except Exception as e:
            if "timestamp mismatch" not in str(e).lower():
                suspicious = True
                reasons.append(f"FaceMesh error: {str(e)}")

        # Brightness check
        if check_brightness_fn(frame) > 200:
            suspicious = True
            reasons.append("High brightness - possible screen reflection")

        if suspicious:
            violation_counts[peer_id] = violation_counts.get(peer_id, 0) + 1
            violation_logs.append(create_violation_entry_fn(peer_id, reasons))
            
            # Save and upload screenshot
            screenshots_folder = os.path.join(app.static_folder, "screenshots")
            os.makedirs(screenshots_folder, exist_ok=True)
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            image_path = os.path.join(screenshots_folder, filename)
            cv2.imwrite(image_path, yolo_frame)
            upload_result = upload_to_cloudinary_fn(image_path)
            os.remove(image_path)
            
            response = {
                "message": "Suspicious activity detected",
                "cloudinary_url": upload_result.get("secure_url"),
                "public_id": upload_result.get("public_id"),
                "reasons": reasons,
                "count": violation_counts[peer_id]
            }
            if violation_counts[peer_id] >= 5:
                response["action"] = "stop_exam"
            return jsonify(response)

        return jsonify({"message": "No suspicion detected.", "reasons": []})

    @app.route("/request-reconnect", methods=["POST"])
    def request_reconnect():
        reconnect_requests.clear()
        reconnect_requests.update(peer_ids)
        return jsonify({"message": "Reconnect requested"})

    @app.route("/check-reconnect/<peer_id>")
    def check_reconnect(peer_id):
        if peer_id in reconnect_requests:
            reconnect_requests.remove(peer_id)
            return jsonify({"reconnect": True})
        return jsonify({"reconnect": False})

    @app.route("/store-peer-id", methods=["POST"])
    def store_peer_id():
        data = request.json
        peer_id, peer_type = data.get("peerId"), data.get("type", "student")
        
        if peer_id:
            if peer_type == "proctor":
                proctor_ids.add(peer_id)
            else:
                peer_ids.discard(peer_id)
                peer_ids.add(peer_id)
            return jsonify({"message": "Peer ID stored", "peerId": peer_id})
        return jsonify({"message": "Peer ID missing"}), 400

    @app.route("/get-proctor-ids")
    def get_proctor_ids():
        return jsonify(list(proctor_ids))

    @app.route("/get-peer-ids")
    def get_peer_ids():
        return jsonify(list(peer_ids))

    @app.route("/delete-peer-id", methods=["POST"])
    def delete_peer_id():
        data = request.json
        peer_id, peer_type = data.get("peerId"), data.get("type", "student")
        
        if peer_id:
            if peer_type == "proctor" and peer_id in proctor_ids:
                proctor_ids.remove(peer_id)
            elif peer_id in peer_ids:
                peer_ids.remove(peer_id)
                violation_counts.pop(peer_id, None)
            return jsonify({"message": "Peer ID deleted", "peerId": peer_id})
        return jsonify({"message": "Peer ID not found"}), 404

    @app.route("/view_screenshots")
    def view_screenshots():
        screenshots_folder = os.path.join(app.static_folder, "screenshots")
        os.makedirs(screenshots_folder, exist_ok=True)
        images = [f"/static/screenshots/{f}" for f in os.listdir(screenshots_folder) if f.endswith(".png")]
        html = "<h1>Suspicious Screenshots</h1><div style='display:flex; flex-wrap: wrap;'>"
        for img in images:
            html += f'<div style="margin: 10px;"><img src="{img}" width="300" style="border:1px solid #ccc;"/><br><p>{img}</p></div>'
        return html + "</div>"