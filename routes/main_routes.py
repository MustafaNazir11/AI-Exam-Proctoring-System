from flask import render_template
from auth.auth_routes import init_auth_routes
from quiz.quiz_routes import init_quiz_routes

# Use enhanced proctoring with Azure CV
try:
    from proctoring.enhanced_proctoring_routes import init_enhanced_proctoring_routes as init_proctoring_routes
    print("Enhanced proctoring loaded")
except ImportError:
    from proctoring.proctoring_routes import init_proctoring_routes
    print("Using original proctoring")

def init_routes(app):
    # Simple dashboard routes
    @app.route('/adminprofile')
    def adminprofile():
        return render_template('adminprofile.html')

    @app.route('/stud_profile')
    def stud_profile():
        return render_template('profile.html')

    @app.route('/student_dashboard')
    def student_dashboard():
        return render_template('student-dashboard.html')

    @app.route('/admin_dashboard')
    def admin_dashboard():
        return render_template('admin-dashboard.html')

    @app.route("/admin")
    def admin():
        return render_template("admin-dashboard.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("proctor-dashboard.html")

    @app.route('/test')
    def test():
        return render_template('student-dashboard.html')

    # Initialize modular routes
    init_auth_routes(app)
    init_quiz_routes(app)
    init_proctoring_routes(app)