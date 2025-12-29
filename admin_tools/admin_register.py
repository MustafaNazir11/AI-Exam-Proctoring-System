import sqlite3

DB = "Database.db"

# 📌 Create admin table if not exists
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# 🧑‍🏫 Insert Admin
def insert_admin():
    email = input("Enter Admin Email: ")
    password = input("Enter Admin Password: ")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO teachers (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        print("✔ Admin registered successfully!")
    except sqlite3.IntegrityError:
        print("⚠ This email already exists! Choose a different one.")
    conn.close()

# 🔁 Menu Loop
def menu():
    init_db()
    print("\n===== ADMIN REGISTRATION =====")

    while True:
        insert_admin()
        choice = input("\nDo you want to add another admin? (yes/no): ").strip().lower()
        
        if choice != "yes":
            print("\n👋 Exiting... All Done!")
            break

# 🚀 Run Program
if __name__ == "__main__":
    menu()
