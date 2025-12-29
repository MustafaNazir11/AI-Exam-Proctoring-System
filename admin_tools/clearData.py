import sqlite3

def clear_questions_table():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    
    # Check if questions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions';")
    if cursor.fetchone():
        cursor.execute("DELETE FROM questions;")
        print("Cleared questions table")
    else:
        print("Questions table does not exist")
    
    conn.commit()
    conn.close()

# Clear only questions table
clear_questions_table()
