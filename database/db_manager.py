import sqlite3

def get_db_connection():
    conn = sqlite3.connect('Database.db')
    conn.row_factory = sqlite3.Row
    return conn

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS exam_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        student_email TEXT,
        student_name TEXT,
        status TEXT DEFAULT 'active',
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        paused_time TIMESTAMP,
        total_pause_duration INTEGER DEFAULT 0,
        current_question INTEGER DEFAULT 1,
        total_questions INTEGER,
        score INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )''')

    cursor.execute("INSERT OR IGNORE INTO students (email, password) VALUES (?, ?)", ("student@test.com", "password"))
    cursor.execute("INSERT OR IGNORE INTO teachers (email, password) VALUES (?, ?)", ("teacher@test.com", "admin123"))

    conn.commit()
    conn.close()