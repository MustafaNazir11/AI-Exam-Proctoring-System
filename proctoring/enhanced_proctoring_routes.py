"""
Enhanced Proctoring Routes with Azure Computer Vision Integration
Maintains backward compatibility while adding Azure CV capabilities
"""

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

# Azure CV Integration
azure_cv_integration = None

def init_enhanced_proctoring_routes(app):
    """Initialize enhanced proctoring routes with Azure CV integration"""
    
    # Initialize Azure CV Integration
    global azure_cv_integration
    try:
        from utils.azure_cv_integration import init_azure_cv_integration
        azure_cv_integration = init_azure_cv_integration()
        if azure_cv_integration:
            print("✅ Enhanced proctoring with Azure CV enabled")
        else:
            print("⚠️ Azure CV integration failed - using fallback mode")
    except Exception as e:
        print(f"⚠️ Azure CV integration error: {e} - using fallback mode")

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

    @app.route("/enhanced-analyze", methods=["POST"])
    def enhanced_analyze():
        """New enhanced analysis endpoint with Azure CV"""
        global azure_cv_integration
        
        data = request.json
        peer_id, image_data = data.get("peerId"), data.get("image")
        
        if not peer_id or not image_data:
            return jsonify({"error": "Missing peer ID or image data"}), 400
        
        try:
            # Decode image
            image_bytes = base64.b64decode(image_data.split(",")[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)[:, :, ::-1].copy()
            
            # Use Azure CV integration if available
            if azure_cv_integration:
                from utils.azure_cv_integration import analyze_frame_with_azure_cv
                results = analyze_frame_with_azure_cv(frame, peer_id=peer_id, use_azure=True)
                
                return jsonify({
                    "enhanced_analysis": True,
                    "is_suspicious": results.get('is_suspicious', False),
                    "suspicion_score": results.get('suspicion_score', 0),
                    "severity": results.get('severity', 'LOW'),
                    "reasons": results.get('reasons', []),
                    "recommendations": results.get('recommendations', []),
                    "detection_summary": {
                        "faces_detected": results.get('detection_results', {}).get('azure_detection', {}).get('face_count', 0),
                        "objects_detected": len(results.get('detection_results', {}).get('azure_detection', {}).get('objects', [])),
                        "azure_analyzed": True
                    }
                })
            else:
                # Fallback to basic analysis
                from utils.integrated_pipeline import integrated_pipeline_analysis
                result = integrated_pipeline_analysis(frame)
                
                return jsonify({
                    "enhanced_analysis": False,
                    "is_suspicious": result.get('suspicious', False),
                    "reasons": result.get('failed_checks', []),
                    "azure_analyzed": result.get('azure_analyzed', False)
                })
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/upload-screenshot", methods=["POST"])
    def upload_screenshot_enhanced():
        """Enhanced screenshot upload with Azure CV integration"""
        print("🔥 ENHANCED UPLOAD-SCREENSHOT ROUTE CALLED!")
        
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

        # Use Azure CV integration for comprehensive analysis
        suspicious = False
        reasons = []
        severity = "LOW"
        
        try:
            if azure_cv_integration:
                from utils.azure_cv_integration import analyze_frame_with_azure_cv
                results = analyze_frame_with_azure_cv(frame, peer_id=peer_id, use_azure=True)
                
                suspicious = results.get('is_suspicious', False)
                reasons = results.get('reasons', [])
                severity = results.get('severity', 'LOW')
                
                print(f"✅ Azure CV Analysis - Suspicious: {suspicious}, Severity: {severity}")
                
                # Use annotated frame for saving
                annotated_frame = results.get('annotated_frame', frame)
                
            else:
                # Fallback to original method
                print("⚠️ Using fallback analysis method")
                from utils.integrated_pipeline import integrated_pipeline_analysis
                pipeline_result = integrated_pipeline_analysis(frame)
                
                suspicious = pipeline_result.get('suspicious', False)
                reasons = [f"Pipeline check: {check}" for check in pipeline_result.get('failed_checks', [])]
                annotated_frame = frame
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            suspicious = True
            reasons = [f"Analysis error: {str(e)}"]
            annotated_frame = frame

        # If suspicious, save screenshot and log violation
        if suspicious:
            violation_counts[peer_id] = violation_counts.get(peer_id, 0) + 1
            
            # Create enhanced violation entry
            if azure_cv_integration and 'results' in locals():
                # Use enhanced violation entry if available
                try:
                    from utils.enhanced_violation_analyzer import create_enhanced_violation_entry
                    violation_entry = create_enhanced_violation_entry(peer_id, results.get('detection_results', {}))
                    if violation_entry:
                        violation_logs.append(violation_entry)
                    else:
                        # Fallback to basic entry
                        from utils.violation_rules import create_violation_entry
                        violation_logs.append(create_violation_entry(peer_id, reasons))
                except:
                    from utils.violation_rules import create_violation_entry
                    violation_logs.append(create_violation_entry(peer_id, reasons))
            else:
                from utils.violation_rules import create_violation_entry
                violation_logs.append(create_violation_entry(peer_id, reasons))
            
            # Save screenshot
            screenshots_folder = os.path.join(app.static_folder, "screenshots")
            os.makedirs(screenshots_folder, exist_ok=True)
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            image_path = os.path.join(screenshots_folder, filename)
            
            cv2.imwrite(image_path, annotated_frame)
            
            # Upload to cloud (if available)
            try:
                from utils.cloud import upload_to_cloudinary
                upload_result = upload_to_cloudinary(image_path)
                os.remove(image_path)
                cloudinary_url = upload_result.get("secure_url")
                public_id = upload_result.get("public_id")
            except:
                cloudinary_url = None
                public_id = None
            
            response = {
                "message": "Suspicious activity detected",
                "severity": severity,
                "reasons": reasons,
                "count": violation_counts[peer_id],
                "enhanced_analysis": azure_cv_integration is not None
            }
            
            if cloudinary_url:
                response.update({
                    "cloudinary_url": cloudinary_url,
                    "public_id": public_id
                })
            
            if violation_counts[peer_id] >= 5:
                response["action"] = "stop_exam"
                
            return jsonify(response)

        return jsonify({
            "message": "No suspicion detected.", 
            "reasons": [],
            "enhanced_analysis": azure_cv_integration is not None
        })

    # Keep all existing routes for backward compatibility
    @app.route("/pipeline1/analyze", methods=["POST"])
    def pipeline1_analyze():
        """Original pipeline1 analysis - kept for compatibility"""
        image_data = request.json.get("image")
        if not image_data:
            return jsonify({"error": "No image data"}), 400
        
        try:
            image_bytes = base64.b64decode(image_data.split(",")[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)[:, :, ::-1].copy()
            
            from utils.integrated_pipeline import integrated_pipeline_analysis
            return jsonify(integrated_pipeline_analysis(frame))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/pipeline0/frame", methods=["POST"])
    def pipeline0_frame():
        """Enhanced pipeline0 with Azure CV object detection"""
        print("🔥 ENHANCED PIPELINE0 ROUTE CALLED!")
        
        data = request.json
        peer_id, image_data = data.get("peerId"), data.get("image")
        
        if not peer_id or not image_data:
            return jsonify({"received": False, "error": "Missing data"})
        
        try:
            import cv2
            image_bytes = base64.b64decode(image_data.split(",")[1])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)[:, :, ::-1].copy()
            
            # Use Azure CV integration for comprehensive analysis
            if azure_cv_integration:
                from utils.azure_cv_integration import analyze_frame_with_azure_cv
                results = analyze_frame_with_azure_cv(frame, peer_id=peer_id, use_azure=True)
                
                # Enhanced logging
                print(f"📊 ANALYSIS RESULTS for {peer_id}:")
                print(f"   🚨 Suspicious: {results.get('is_suspicious', False)}")
                print(f"   📈 Score: {results.get('suspicion_score', 0)}/100")
                print(f"   ⚠️ Severity: {results.get('severity', 'LOW')}")
                
                # Log detected objects
                detection_results = results.get('detection_results', {})
                azure_detection = detection_results.get('azure_detection', {})
                
                if 'objects' in azure_detection:
                    objects = azure_detection['objects']
                    if objects:
                        print(f"   📦 Objects detected ({len(objects)}):")
                        for obj in objects:
                            print(f"      - {obj['name']} ({obj['confidence']:.1%})")
                    else:
                        print("   📦 No objects detected")
                
                # Log reasons
                reasons = results.get('reasons', [])
                if reasons:
                    print(f"   📝 Violation reasons ({len(reasons)}):")
                    for reason in reasons:
                        print(f"      - {reason}")
                
                print("─" * 60)
                
                return jsonify({
                    "received": True,
                    "enhanced_analysis": True,
                    "pipeline_result": {
                        "suspicious": results.get('is_suspicious', False),
                        "suspicion_score": results.get('suspicion_score', 0),
                        "severity": results.get('severity', 'LOW'),
                        "reasons": reasons,
                        "objects_detected": len(objects) if 'objects' in locals() else 0,
                        "azure_analyzed": True
                    }
                })
            else:
                # Fallback to original pipeline
                print("⚠️ Using fallback pipeline - Azure CV not available")
                from utils.integrated_pipeline import integrated_pipeline_analysis
                pipeline_result = integrated_pipeline_analysis(frame)
                
                return jsonify({
                    "received": True,
                    "enhanced_analysis": False, 
                    "pipeline_result": pipeline_result
                })
            
        except Exception as e:
            print(f"❌ Pipeline0 error: {e}")
            return jsonify({"received": False, "error": str(e)})

    # All other existing routes remain the same
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

    @app.route("/azure-cv-status")
    def azure_cv_status():
        """New endpoint to check Azure CV integration status"""
        if azure_cv_integration:
            status = azure_cv_integration.get_system_status()
            return jsonify({
                "azure_cv_enabled": True,
                "status": status,
                "message": "Azure Computer Vision integration active"
            })
        else:
            return jsonify({
                "azure_cv_enabled": False,
                "message": "Using fallback detection methods"
            })
    
    @app.route("/debug-azure")
    def debug_azure():
        """Detailed Azure services debug info"""
        from utils.azure_cv_integration import debug_azure_status
        from utils.azure_face_api import get_azure_face_detector
        from utils.azure_cv_enhanced import get_azure_cv_enhanced
        
        return jsonify({
            "integration_status": debug_azure_status(),
            "face_api_available": get_azure_face_detector() is not None,
            "cv_enhanced_available": get_azure_cv_enhanced() is not None,
            "env_check": {
                "AZURE_FACE_API_KEY": "SET" if os.getenv("AZURE_FACE_API_KEY") else "MISSING",
                "AZURE_FACE_ENDPOINT": "SET" if os.getenv("AZURE_FACE_ENDPOINT") else "MISSING",
                "AZURE_CV_KEY": "SET" if os.getenv("AZURE_CV_KEY") else "MISSING",
                "AZURE_CV_ENDPOINT": "SET" if os.getenv("AZURE_CV_ENDPOINT") else "MISSING"
            }
        })

# Backward compatibility - keep original function name
def init_proctoring_routes(app):
    """Original function name for backward compatibility"""
    return init_enhanced_proctoring_routes(app)