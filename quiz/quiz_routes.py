from flask import render_template, request, session
from database.db_manager import get_db_connection

def init_quiz_routes(app):
    @app.route("/input-questions", methods=['GET', 'POST'])
    def input_questions():
        if request.method == 'POST':
            questions = request.form.getlist('question')
            options = [request.form.getlist(f'option_{x}') for x in ['a', 'b', 'c', 'd']]
            correct_options = request.form.getlist('correct_option')
            
            conn = get_db_connection()
            count = 0
            for i, question in enumerate(questions):
                if question.strip():
                    conn.execute('''INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option)
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                               (question, *[opt[i] for opt in options], correct_options[i]))
                    count += 1
            conn.commit()
            conn.close()
            return f"✅ {count} questions added successfully!"
        return render_template('questions.html')

    @app.route("/preview")
    def preview():
        return render_template("preview.html", email=session.get("email"))

    @app.route("/exam")
    def exam():
        conn = get_db_connection()
        questions = conn.execute("SELECT * FROM questions").fetchall()
        conn.close()
        return render_template("exam.html", questions=questions)

    @app.route("/quiz")
    def quiz():
        conn = get_db_connection()
        questions = conn.execute("SELECT * FROM questions").fetchall()
        conn.close()
        return render_template("quiz.html", questions=questions)

    @app.route("/submit", methods=['POST'])
    def submit():
        conn = get_db_connection()
        score = total = 0
        for key, selected_option in request.form.items():
            if key.startswith('question_'):
                q_id = key.split('_')[1]
                correct_option = conn.execute("SELECT correct_option FROM questions WHERE id=?", (q_id,)).fetchone()[0]
                total += 1
                if selected_option.lower() == correct_option.lower():
                    score += 1
        conn.close()
        
        percentage = (score / total) * 100 if total > 0 else 0
        return render_template("results.html", score=score, total=total, percentage=percentage, message="")