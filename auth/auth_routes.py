from flask import render_template, request, redirect, url_for, session
from database.db_manager import get_db_connection

def init_auth_routes(app):
    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email, password = request.form['email'], request.form['password']
            conn = get_db_connection()
            student = conn.execute("SELECT * FROM students WHERE email=? AND password=?", (email, password)).fetchone()
            conn.close()
            if student:
                session.update({'user_id': student['id'], 'email': student['email'], 'user_type': 'student'})
                return redirect(url_for('student_dashboard'))
            return "Invalid credentials"
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email, password = request.form['email'], request.form['password']
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

    @app.route('/admin-login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            email, password = request.form['email'], request.form['password']
            conn = get_db_connection()
            teacher = conn.execute("SELECT * FROM teachers WHERE email=? AND password=?", (email, password)).fetchone()
            conn.close()
            if teacher:
                session.update({'user_id': teacher['id'], 'email': teacher['email'], 'user_type': 'teacher'})
                return redirect(url_for('admin_dashboard'))
            return "Invalid credentials"
        return render_template('admin-login.html')