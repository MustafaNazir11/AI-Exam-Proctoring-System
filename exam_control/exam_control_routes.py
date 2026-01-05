from flask import jsonify, request, session
from database.db_manager import get_db_connection
from datetime import datetime

def init_exam_control_routes(app):
    
    @app.route("/api/exam/start", methods=['POST'])
    def start_exam():
        student_email = session.get('email')
        student_id = session.get('user_id')
        
        if not student_email:
            return jsonify({'error': 'Not authenticated'}), 401
            
        conn = get_db_connection()
        
        # Check if exam already exists
        existing = conn.execute(
            "SELECT * FROM exam_sessions WHERE student_email=? AND status IN ('active', 'paused')",
            (student_email,)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'session_id': existing['id'], 'status': existing['status']})
        
        # Get total questions
        total_questions = conn.execute("SELECT COUNT(*) as count FROM questions").fetchone()['count']
        
        # Create new exam session
        cursor = conn.execute(
            "INSERT INTO exam_sessions (student_id, student_email, student_name, total_questions) VALUES (?, ?, ?, ?)",
            (student_id, student_email, student_email.split('@')[0].title(), total_questions)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'session_id': session_id, 'status': 'active'})
    
    @app.route("/api/exam/status/<int:session_id>")
    def get_exam_status(session_id):
        conn = get_db_connection()
        session_data = conn.execute(
            "SELECT * FROM exam_sessions WHERE id=?", (session_id,)
        ).fetchone()
        conn.close()
        
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
            
        return jsonify(dict(session_data))
    
    @app.route("/api/admin/exam/sessions")
    def get_all_exam_sessions():
        conn = get_db_connection()
        sessions = conn.execute(
            "SELECT * FROM exam_sessions WHERE status IN ('active', 'paused') ORDER BY start_time DESC"
        ).fetchall()
        conn.close()
        
        return jsonify([dict(session) for session in sessions])
    
    @app.route("/api/admin/exam/control", methods=['POST'])
    def control_exam():
        data = request.get_json()
        session_id = data.get('session_id')
        action = data.get('action')  # 'pause', 'resume', 'end', 'restart'
        
        conn = get_db_connection()
        
        if action == 'pause':
            conn.execute(
                "UPDATE exam_sessions SET status='paused', paused_time=CURRENT_TIMESTAMP WHERE id=?",
                (session_id,)
            )
        elif action == 'resume':
            conn.execute(
                "UPDATE exam_sessions SET status='active', paused_time=NULL WHERE id=?",
                (session_id,)
            )
        elif action == 'end':
            conn.execute(
                "UPDATE exam_sessions SET status='ended', end_time=CURRENT_TIMESTAMP WHERE id=?",
                (session_id,)
            )
        elif action == 'restart':
            conn.execute(
                "UPDATE exam_sessions SET status='active', start_time=CURRENT_TIMESTAMP, end_time=NULL, paused_time=NULL, current_question=1, score=0 WHERE id=?",
                (session_id,)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'action': action})
    
    @app.route("/api/exam/update", methods=['POST'])
    def update_exam_progress():
        data = request.get_json()
        session_id = data.get('session_id')
        current_question = data.get('current_question')
        
        conn = get_db_connection()
        conn.execute(
            "UPDATE exam_sessions SET current_question=? WHERE id=?",
            (current_question, session_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})