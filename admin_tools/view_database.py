import sqlite3

def view_table(table_name):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if rows:
            print(f"\n📌 TABLE: {table_name}")
            for row in rows:
                print(row)
        else:
            print(f"\n⚠️ No records found in {table_name}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    conn.close()

if __name__ == "__main__":
    print("🔍 Viewing Database Contents...\n")
    
    view_table("students")
    view_table("teachers")
    view_table("questions")
